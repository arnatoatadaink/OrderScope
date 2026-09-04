from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    AdapterPage,
    AdapterRequest,
    ContractViolation,
    ErrorInfo,
    assert_page_contract,
    assert_secret_free,
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
        provider_revision="fixture-v1",
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
