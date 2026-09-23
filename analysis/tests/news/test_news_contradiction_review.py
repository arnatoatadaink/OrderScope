from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContractViolation,
    Fact,
    FactAssertionKind,
    InterpretationAssertionKind,
    Provenance,
    SourceReference,
)
from orderscope_local.news import (
    NEWS_REVIEW_METHOD_VERSION,
    NewsReviewReasonKind,
    open_news_review_case,
    resolve_news_review_case,
)

UTC = timezone.utc
BASE = datetime(2026, 9, 9, 1, 0, tzinfo=UTC)
OPENED = BASE + timedelta(minutes=10)
RESOLVED = BASE + timedelta(minutes=30)
SUBJECT = "us-sec-0000002488-common"


def _fact(record_id, *, subject=SUBJECT, value="observed", accepted_at=BASE, pending=False, source="news"):
    provenance = Provenance(
        source_ref=SourceReference(f"https://example.com/{source}/{record_id}"),
        content_hash=ContentHash(("a" if source == "news" else "b") * 64),
        retrieved_at=accepted_at - timedelta(minutes=1),
        available_at=accepted_at - timedelta(minutes=1),
        accepted_at=accepted_at,
    )
    return Fact(
        record_id=record_id,
        schema_version="fixture-fact-v0.1",
        subject_ref=subject,
        accepted_at=accepted_at,
        created_at=accepted_at,
        provenance=provenance,
        fact_type="news.event.contract",
        value={"observed": value},
        assertion_kind=FactAssertionKind.PENDING_REVIEW if pending else FactAssertionKind.OBSERVATION,
        evidence_record_ids=() if pending else (f"evidence-{record_id}",),
    )


def test_source_conflict_opens_separate_pending_review_without_overwriting_sources():
    news = _fact("news-fact-1", value="contract announced", source="news")
    sec = _fact("sec-fact-1", value="contract not disclosed", source="sec")
    before = (news, sec)

    case = open_news_review_case(
        source_facts=(news, sec),
        reason_kind=NewsReviewReasonKind.SOURCE_CONFLICT,
        exception_reason="News and SEC assertions conflict on whether the contract is established.",
        opened_at=OPENED,
    )

    assert (news, sec) == before
    assert case.review_fact.assertion_kind is FactAssertionKind.PENDING_REVIEW
    assert case.review_fact.fact_type == "news.review.pending"
    assert case.review_fact.evidence_record_ids == ()
    assert case.source_fact_ids == ("news-fact-1", "sec-fact-1")
    assert case.review_fact.value["reason_kind"] == "source_conflict"
    assert case.review_fact.value["exception_reason"].startswith("News and SEC")


def test_single_source_ambiguity_can_be_held_for_review_without_inventing_resolution():
    fact = _fact("news-fact-ambiguous", value="customer not named")

    case = open_news_review_case(
        source_facts=(fact,),
        reason_kind=NewsReviewReasonKind.AMBIGUOUS_SUBJECT,
        exception_reason="The article does not establish the customer identity.",
        opened_at=OPENED,
    )

    assert case.source_fact_ids == (fact.record_id,)
    assert case.review_fact.value["status"] == "pending_review"
    assert "resolution" not in case.review_fact.value


@pytest.mark.parametrize("reason_kind", tuple(NewsReviewReasonKind))
def test_every_review_reason_kind_is_versioned_and_accepted(reason_kind):
    fact = _fact(f"fact-{reason_kind.value}")
    case = open_news_review_case(
        source_facts=(fact,),
        reason_kind=reason_kind,
        exception_reason=f"Fixture review reason for {reason_kind.value}.",
        opened_at=OPENED,
    )
    assert case.reason_kind is reason_kind


def test_source_order_does_not_change_review_identity_or_lineage_order():
    first = _fact("a-source")
    second = _fact("z-source", source="sec")
    reason = "Two accepted sources require reconciliation."

    forward = open_news_review_case(
        source_facts=(first, second),
        reason_kind=NewsReviewReasonKind.SOURCE_CONFLICT,
        exception_reason=reason,
        opened_at=OPENED,
    )
    reverse = open_news_review_case(
        source_facts=(second, first),
        reason_kind=NewsReviewReasonKind.SOURCE_CONFLICT,
        exception_reason=reason,
        opened_at=OPENED,
    )

    assert forward.review_fact.record_id == reverse.review_fact.record_id
    assert forward.source_fact_ids == reverse.source_fact_ids == ("a-source", "z-source")


def test_review_sources_must_share_resolved_subject_and_be_non_pending():
    amd = _fact("amd-source")
    nvda = _fact("nvda-source", subject="us-sec-0001045810-common")
    with pytest.raises(ContractViolation, match="share one resolved subject"):
        open_news_review_case(
            source_facts=(amd, nvda),
            reason_kind=NewsReviewReasonKind.SOURCE_CONFLICT,
            exception_reason="Cross-subject conflict must not be merged.",
            opened_at=OPENED,
        )

    pending = _fact("pending-source", pending=True)
    with pytest.raises(ContractViolation, match="not review records"):
        open_news_review_case(
            source_facts=(pending,),
            reason_kind=NewsReviewReasonKind.AMBIGUOUS_VALUE,
            exception_reason="Nested review records are not source evidence.",
            opened_at=OPENED,
        )


def test_review_cannot_open_before_source_fact_acceptance():
    future_fact = _fact("future-source", accepted_at=OPENED + timedelta(seconds=1))
    with pytest.raises(ContractViolation, match="cannot open before"):
        open_news_review_case(
            source_facts=(future_fact,),
            reason_kind=NewsReviewReasonKind.LATER_CONFIRMATION_REQUIRED,
            exception_reason="Confirmation has not yet arrived.",
            opened_at=OPENED,
        )


def test_later_confirmation_adds_resolution_interpretation_with_complete_lineage():
    news = _fact("news-source")
    ir = _fact("ir-source", source="ir")
    case = open_news_review_case(
        source_facts=(news, ir),
        reason_kind=NewsReviewReasonKind.SOURCE_CONFLICT,
        exception_reason="News and IR report different contract status.",
        opened_at=OPENED,
    )
    confirmation = _fact("sec-confirmation", value="contract confirmed", accepted_at=OPENED + timedelta(minutes=5), source="sec")

    result = resolve_news_review_case(
        case=case,
        confirmation_fact=confirmation,
        resolved_at=RESOLVED,
        resolution_reason="Later SEC filing explicitly confirms the contract.",
    )

    assert result.resolution.assertion_kind is InterpretationAssertionKind.REVISION
    assert result.resolution.method_version == NEWS_REVIEW_METHOD_VERSION
    assert result.resolution.statement["status"] == "resolved"
    assert result.resolution.statement["confirmation_fact_id"] == confirmation.record_id
    assert result.resolution.basis_record_ids == (
        "ir-source",
        "news-source",
        case.review_fact.record_id,
        confirmation.record_id,
    )
    assert case.review_fact.assertion_kind is FactAssertionKind.PENDING_REVIEW


def test_confirmation_must_be_new_independent_fact_for_same_subject():
    source = _fact("source-fact")
    case = open_news_review_case(
        source_facts=(source,),
        reason_kind=NewsReviewReasonKind.LATER_CONFIRMATION_REQUIRED,
        exception_reason="Await an independent filing.",
        opened_at=OPENED,
    )

    with pytest.raises(ContractViolation, match="later independent"):
        resolve_news_review_case(
            case=case,
            confirmation_fact=source,
            resolved_at=RESOLVED,
            resolution_reason="Reusing the same source is not confirmation.",
        )

    wrong_subject = _fact("nvda-confirmation", subject="us-sec-0001045810-common", accepted_at=OPENED)
    with pytest.raises(ContractViolation, match="subject must match"):
        resolve_news_review_case(
            case=case,
            confirmation_fact=wrong_subject,
            resolved_at=RESOLVED,
            resolution_reason="Wrong issuer cannot resolve the case.",
        )


def test_resolution_time_and_confirmation_acceptance_order_are_enforced():
    source = _fact("source-time")
    case = open_news_review_case(
        source_facts=(source,),
        reason_kind=NewsReviewReasonKind.AMBIGUOUS_TIME,
        exception_reason="The effective time is not established.",
        opened_at=OPENED,
    )
    confirmation = _fact("confirmation-time", accepted_at=RESOLVED + timedelta(seconds=1), source="sec")

    with pytest.raises(ContractViolation, match="accepted after resolution"):
        resolve_news_review_case(
            case=case,
            confirmation_fact=confirmation,
            resolved_at=RESOLVED,
            resolution_reason="Cannot use future-accepted confirmation.",
        )

    valid_confirmation = _fact("confirmation-valid", accepted_at=OPENED, source="sec")
    with pytest.raises(ContractViolation, match="earlier than review opening"):
        resolve_news_review_case(
            case=case,
            confirmation_fact=valid_confirmation,
            resolved_at=OPENED - timedelta(seconds=1),
            resolution_reason="Resolution cannot precede the review case.",
        )


def test_blank_exception_or_resolution_reason_is_rejected():
    source = _fact("source-reason")
    with pytest.raises(ContractViolation, match="review reason"):
        open_news_review_case(
            source_facts=(source,),
            reason_kind=NewsReviewReasonKind.AMBIGUOUS_VALUE,
            exception_reason=" ",
            opened_at=OPENED,
        )

    case = open_news_review_case(
        source_facts=(source,),
        reason_kind=NewsReviewReasonKind.AMBIGUOUS_VALUE,
        exception_reason="The numeric value is not established.",
        opened_at=OPENED,
    )
    confirmation = _fact("confirmation-reason", accepted_at=OPENED, source="sec")
    with pytest.raises(ContractViolation, match="review reason"):
        resolve_news_review_case(
            case=case,
            confirmation_fact=confirmation,
            resolved_at=RESOLVED,
            resolution_reason="",
        )
