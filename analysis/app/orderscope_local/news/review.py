"""Contradiction and pending-review boundary for News Facts (N1-004).

Source-grounded SEC/IR/News Facts remain immutable. Ambiguity and conflicts are
represented by a separate PENDING_REVIEW Fact that records bounded scalar review
metadata while the typed NewsReviewCase retains the full immutable source-Fact
lineage. A later confirmation produces an Interpretation that resolves the review
case without deleting or rewriting any source Fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
import hashlib
import re

from orderscope_local.contracts import (
    ContractViolation,
    Fact,
    FactAssertionKind,
    Interpretation,
    InterpretationAssertionKind,
    Provenance,
)


NEWS_REVIEW_SCHEMA_VERSION = "news-review-v0.1"
NEWS_REVIEW_RESOLUTION_SCHEMA_VERSION = "news-review-resolution-v0.1"
NEWS_REVIEW_METHOD_VERSION = "news-review-controller-v0.1"


class NewsReviewReasonKind(StrEnum):
    SOURCE_CONFLICT = "source_conflict"
    AMBIGUOUS_SUBJECT = "ambiguous_subject"
    AMBIGUOUS_VALUE = "ambiguous_value"
    AMBIGUOUS_TIME = "ambiguous_time"
    LATER_CONFIRMATION_REQUIRED = "later_confirmation_required"


@dataclass(frozen=True, slots=True)
class NewsReviewCase:
    review_fact: Fact
    source_fact_ids: tuple[str, ...]
    reason_kind: NewsReviewReasonKind
    exception_reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.review_fact, Fact):
            raise ContractViolation("news review case requires a Fact")
        if self.review_fact.assertion_kind is not FactAssertionKind.PENDING_REVIEW:
            raise ContractViolation("news review case Fact must be pending_review")
        if not isinstance(self.source_fact_ids, tuple) or not self.source_fact_ids:
            raise ContractViolation("news review case requires source Fact IDs")
        if len(self.source_fact_ids) != len(set(self.source_fact_ids)):
            raise ContractViolation("news review source Fact IDs cannot contain duplicates")
        if any(not _identifier(value) for value in self.source_fact_ids):
            raise ContractViolation("news review source Fact ID is invalid")
        if not isinstance(self.reason_kind, NewsReviewReasonKind):
            raise ContractViolation("news review reason kind is invalid")
        _reason(self.exception_reason)
        expected_hash = _source_ids_hash(self.source_fact_ids)
        if self.review_fact.value["source_fact_count"] != len(self.source_fact_ids):
            raise ContractViolation("news review Fact source count must match case")
        if self.review_fact.value["source_fact_ids_hash"] != expected_hash:
            raise ContractViolation("news review Fact source lineage hash must match case")
        if self.review_fact.value["reason_kind"] != self.reason_kind.value:
            raise ContractViolation("news review Fact reason kind must match case")
        if self.review_fact.value["exception_reason"] != self.exception_reason:
            raise ContractViolation("news review Fact exception reason must match case")


@dataclass(frozen=True, slots=True)
class NewsReviewResolution:
    case: NewsReviewCase
    resolution: Interpretation
    confirmation_fact_id: str
    resolution_reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.case, NewsReviewCase):
            raise ContractViolation("news review resolution requires a review case")
        if not isinstance(self.resolution, Interpretation):
            raise ContractViolation("news review resolution requires Interpretation")
        if not _identifier(self.confirmation_fact_id):
            raise ContractViolation("confirmation_fact_id is invalid")
        _reason(self.resolution_reason)
        expected_basis = self.case.source_fact_ids + (
            self.case.review_fact.record_id,
            self.confirmation_fact_id,
        )
        if self.resolution.basis_record_ids != expected_basis:
            raise ContractViolation("review resolution basis must preserve source/review/confirmation lineage")


def open_news_review_case(
    *,
    source_facts: tuple[Fact, ...],
    reason_kind: NewsReviewReasonKind,
    exception_reason: str,
    opened_at: datetime,
) -> NewsReviewCase:
    """Open an immutable pending-review record without altering source Facts."""

    _utc(opened_at, "opened_at")
    _reason(exception_reason)
    if not isinstance(reason_kind, NewsReviewReasonKind):
        raise ContractViolation("reason_kind must be NewsReviewReasonKind")
    if not isinstance(source_facts, tuple) or not source_facts:
        raise ContractViolation("source_facts must be a non-empty immutable tuple")
    if any(not isinstance(fact, Fact) for fact in source_facts):
        raise ContractViolation("source_facts contains a non-Fact record")
    ordered_facts = tuple(sorted(source_facts, key=lambda fact: fact.record_id))
    source_ids = tuple(fact.record_id for fact in ordered_facts)
    if len(source_ids) != len(set(source_ids)):
        raise ContractViolation("source_facts cannot contain duplicate record IDs")
    subjects = {fact.subject_ref for fact in ordered_facts}
    if len(subjects) != 1:
        raise ContractViolation("review case source Facts must share one resolved subject")
    if any(fact.assertion_kind is FactAssertionKind.PENDING_REVIEW for fact in ordered_facts):
        raise ContractViolation("review case source Facts must be source-grounded assertions, not review records")
    if any(fact.accepted_at > opened_at for fact in ordered_facts):
        raise ContractViolation("review case cannot open before a source Fact is accepted")

    digest = hashlib.sha256(
        ("|".join(source_ids) + "|" + reason_kind.value + "|" + exception_reason).encode("utf-8")
    ).hexdigest()[:20]
    record_id = f"news-review-{digest}"
    subject_ref = ordered_facts[0].subject_ref
    source_provenance = ordered_facts[0].provenance
    review_provenance = Provenance(
        source_ref=source_provenance.source_ref,
        content_hash=source_provenance.content_hash,
        retrieved_at=source_provenance.retrieved_at,
        available_at=source_provenance.available_at,
        accepted_at=opened_at,
        provider_revision=source_provenance.provider_revision,
        event_time=source_provenance.event_time,
        published_at=source_provenance.published_at,
        filed_at=source_provenance.filed_at,
        source_accepted_at=source_provenance.source_accepted_at,
    )
    review_fact = Fact(
        record_id=record_id,
        schema_version=NEWS_REVIEW_SCHEMA_VERSION,
        subject_ref=subject_ref,
        accepted_at=opened_at,
        created_at=opened_at,
        provenance=review_provenance,
        fact_type="news.review.pending",
        value={
            "status": "pending_review",
            "reason_kind": reason_kind.value,
            "exception_reason": exception_reason,
            "source_fact_count": len(source_ids),
            "source_fact_ids_hash": _source_ids_hash(source_ids),
        },
        assertion_kind=FactAssertionKind.PENDING_REVIEW,
        evidence_record_ids=(),
    )
    return NewsReviewCase(
        review_fact=review_fact,
        source_fact_ids=source_ids,
        reason_kind=reason_kind,
        exception_reason=exception_reason,
    )


def resolve_news_review_case(
    *,
    case: NewsReviewCase,
    confirmation_fact: Fact,
    resolved_at: datetime,
    resolution_reason: str,
) -> NewsReviewResolution:
    """Resolve a pending case by adding lineage; never mutate the source Facts."""

    if not isinstance(case, NewsReviewCase):
        raise ContractViolation("case must be NewsReviewCase")
    if not isinstance(confirmation_fact, Fact):
        raise ContractViolation("confirmation_fact must be Fact")
    _utc(resolved_at, "resolved_at")
    _reason(resolution_reason)
    if confirmation_fact.assertion_kind is FactAssertionKind.PENDING_REVIEW:
        raise ContractViolation("confirmation Fact cannot itself be pending_review")
    if confirmation_fact.subject_ref != case.review_fact.subject_ref:
        raise ContractViolation("confirmation Fact subject must match review case subject")
    if confirmation_fact.record_id in case.source_fact_ids:
        raise ContractViolation("confirmation Fact must be a later independent source Fact")
    if resolved_at < case.review_fact.accepted_at:
        raise ContractViolation("resolved_at cannot be earlier than review opening")
    if confirmation_fact.accepted_at > resolved_at:
        raise ContractViolation("confirmation Fact cannot be accepted after resolution time")

    suffix = hashlib.sha256(
        f"{case.review_fact.record_id}|{confirmation_fact.record_id}|{resolution_reason}".encode("utf-8")
    ).hexdigest()[:20]
    basis = case.source_fact_ids + (case.review_fact.record_id, confirmation_fact.record_id)
    resolution = Interpretation(
        record_id=f"news-review-resolution-{suffix}",
        schema_version=NEWS_REVIEW_RESOLUTION_SCHEMA_VERSION,
        subject_ref=case.review_fact.subject_ref,
        accepted_at=resolved_at,
        created_at=resolved_at,
        interpretation_type="news.review.resolution",
        statement={
            "status": "resolved",
            "reason_kind": case.reason_kind.value,
            "resolution_reason": resolution_reason,
            "confirmation_fact_id": confirmation_fact.record_id,
            "review_fact_id": case.review_fact.record_id,
        },
        basis_record_ids=basis,
        method="news-review-controller",
        method_version=NEWS_REVIEW_METHOD_VERSION,
        assertion_kind=InterpretationAssertionKind.REVISION,
    )
    return NewsReviewResolution(
        case=case,
        resolution=resolution,
        confirmation_fact_id=confirmation_fact.record_id,
        resolution_reason=resolution_reason,
    )


def _source_ids_hash(source_fact_ids: tuple[str, ...]) -> str:
    return hashlib.sha256("|".join(source_fact_ids).encode("utf-8")).hexdigest()


def _identifier(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,255}", value) is not None


def _reason(value: object) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 1024:
        raise ContractViolation("review reason must be bounded non-blank canonical text")


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
