from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    AdapterItem,
    AdapterPage,
    AdapterRequest,
    CheckpointState,
    ContentHash,
    ContentIdentity,
    ContractViolation,
    ErrorInfo,
    IdempotencyClassification,
    ProviderRevision,
    RetentionClass,
    RevisionRelationship,
    StableIdentity,
    TemporaryContent,
    TemporaryContentState,
    assert_adapter_item_contract,
    assert_page_contract,
    assert_secret_free,
    checkpoint_for_page,
    classify_adapter_item,
    collect_pages,
)


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
REQUEST = AdapterRequest("sec:submissions:amd", START, START + timedelta(days=1), page_size=2)


class ScriptedAdapter:
    def __init__(self, pages):
        self.pages = pages
        self.requests = []

    def fetch(self, request):
        self.requests.append(request)
        return self.pages[len(self.requests) - 1]


def page(items=(), *, cursor=None, partial=False, error=None, available=START):
    return AdapterPage(
        items=tuple(items),
        next_cursor=cursor,
        partial=partial,
        retrieved_at=available + timedelta(seconds=1),
        available_at=available,
        provider_revision=ProviderRevision("fixture-v1"),
        error=error,
    )


def test_common_kit_accepts_bounded_pagination_and_preserves_timestamps():
    adapter = ScriptedAdapter([
        page(({"article_id": "a"},), cursor="p2"),
        page(({"article_id": "b"},)),
    ])

    pages = collect_pages(adapter, REQUEST)

    assert [item["article_id"] for p in pages for item in p.items] == ["a", "b"]
    assert adapter.requests[1].cursor == "p2"
    assert pages[0].available_at == START
    assert pages[0].retrieved_at == START + timedelta(seconds=1)


def test_common_kit_accepts_partial_retryable_failure_without_advancing_as_complete():
    failure = ErrorInfo("temporary_unavailable", retryable=True, message="upstream unavailable", retry_after=timedelta(seconds=5))
    adapter = ScriptedAdapter([page(({"filing_id": "x"},), partial=True, error=failure)])

    pages = collect_pages(adapter, REQUEST)

    assert pages[0].partial is True
    assert pages[0].error.retryable is True
    assert pages[0].error.retry_after == timedelta(seconds=5)


@pytest.mark.parametrize("bad", [
    {"api_key": "fixture-secret"},
    {"Authorization": "Bearer fixture-secret"},
    {"provider_response_body": "raw body must not cross boundary"},
])
def test_common_kit_rejects_secrets_and_raw_provider_payloads(bad):
    with pytest.raises(ContractViolation):
        assert_secret_free((bad,))


def test_common_kit_rejects_cursor_loop():
    adapter = ScriptedAdapter([page(cursor="p2"), page(cursor="p2")])
    with pytest.raises(ContractViolation, match="cursor"):
        collect_pages(adapter, REQUEST)


def test_common_kit_rejects_unzoned_timestamp_and_unbounded_page():
    with pytest.raises(ContractViolation, match="timezone"):
        assert_page_contract(
            AdapterPage((), None, False, datetime(2026, 1, 1), START, None), REQUEST
        )
    with pytest.raises(ContractViolation, match="page_size"):
        assert_page_contract(
            AdapterPage(({}, {}, {}), None, False, START + timedelta(seconds=1), START, None), REQUEST
        )


def test_common_kit_requires_typed_provider_revision():
    valid = page()
    assert valid.provider_revision == ProviderRevision("fixture-v1")

    with pytest.raises(ContractViolation, match="ProviderRevision"):
        assert_page_contract(
            AdapterPage((), None, False, START + timedelta(seconds=1), START, "fixture-v1"),
            REQUEST,
        )


def content(identity, digest="a"):
    return ContentIdentity(identity, ContentHash(digest * 64))


def adapter_item(identity, digest="a", *, temporary_content=None, **normalized):
    return AdapterItem(normalized, content(identity, digest), temporary_content)


def test_common_kit_hands_successful_and_partial_pages_to_accepted_checkpoint_contract():
    first_request = REQUEST
    first_page = page(({"filing_id": "x"},), cursor="p2")
    progress = checkpoint_for_page(provider_key="sec", request=first_request, page=first_page)

    assert progress.state is CheckpointState.IN_PROGRESS
    assert progress.resume_request().cursor == "p2"
    assert progress.resume_request().window_start == REQUEST.window_start
    assert progress.resume_request().window_end == REQUEST.window_end

    partial_request = progress.resume_request(page_size=REQUEST.page_size)
    failure = ErrorInfo("rate_limited", True, "sanitized", timedelta(minutes=5))
    partial_page = page(({"filing_id": "y"},), partial=True, error=failure)
    partial = checkpoint_for_page(provider_key="sec", request=partial_request, page=partial_page)

    assert partial.state is CheckpointState.PARTIAL
    assert partial.resume_request().cursor == "p2"
    assert partial.retry_not_before == partial_page.retrieved_at + timedelta(minutes=5)
    assert "message" not in partial.to_record()


def test_common_kit_hands_terminal_page_to_complete_checkpoint():
    complete = checkpoint_for_page(provider_key="sec", request=REQUEST, page=page())

    assert complete.state is CheckpointState.COMPLETE
    assert complete.resume_cursor is None


def test_common_kit_uses_accepted_identity_classification_without_guessing_updates():
    identity = StableIdentity.provider_article("newswire", "article-42")
    accepted = content(identity, "a")
    duplicate = adapter_item(identity, "a", headline="same")
    changed = adapter_item(identity, "b", headline="changed")
    revision = RevisionRelationship(accepted, changed.content_identity)

    assert classify_adapter_item(duplicate, accepted) is IdempotencyClassification.DUPLICATE
    assert classify_adapter_item(changed, accepted) is IdempotencyClassification.CONFLICT
    assert classify_adapter_item(changed, accepted, revision_relationship=revision) is IdempotencyClassification.UPDATE
    distinct = adapter_item(StableIdentity.provider_article("newswire", "article-43"), "a")
    assert classify_adapter_item(distinct, accepted) is IdempotencyClassification.NEW


def test_common_kit_validates_temporary_content_lifecycle_handoff():
    staged = TemporaryContent(
        content_ref="tmp:sha256:article-42",
        retention_class=RetentionClass.TEMPORARY_SUCCESS,
        captured_at=START,
        expires_at=START + timedelta(hours=1),
        state=TemporaryContentState.STAGED,
    )
    item = adapter_item(
        StableIdentity.provider_article("newswire", "article-42"),
        headline="bounded metadata",
        temporary_content=staged,
    )

    assert_adapter_item_contract(item)
    assert not hasattr(item, "body")

    pages = collect_pages(ScriptedAdapter([page((item,))]), REQUEST)
    assert pages[0].items == (item,)


def test_common_kit_scans_error_metadata_and_lifecycle_handoffs_for_secrets():
    exposed_error = ErrorInfo("temporary", True, "Bearer fixture-secret")
    with pytest.raises(ContractViolation, match="secret-like"):
        assert_page_contract(page(error=exposed_error), REQUEST)

    with pytest.raises(ContractViolation, match="temporary_content"):
        assert_adapter_item_contract(
            adapter_item(
                StableIdentity.provider_signal("official", "signal-1"),
                temporary_content={"provider_response_body": "raw"},
            )
        )


def test_common_kit_rejects_ambiguous_partial_page_without_error():
    with pytest.raises(ContractViolation, match="partial page"):
        assert_page_contract(page(partial=True), REQUEST)

    failure = ErrorInfo("temporary", True, "sanitized")
    with pytest.raises(ContractViolation, match="cannot advance"):
        assert_page_contract(page(cursor="unsafe", partial=True, error=failure), REQUEST)
