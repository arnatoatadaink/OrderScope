"""UWBS-067 listing-compliance contracts.

This module keeps exchange/issuer observations separate from derived compliance
state and market interpretation. It deliberately does not encode venue-specific
minimum-price thresholds or cure durations as universal rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import Interpretation, InterpretationAssertionKind


class ListingComplianceEventType(StrEnum):
    DEFICIENCY_NOTICE = "deficiency_notice"
    COMPLIANCE_PERIOD_STARTED = "compliance_period_started"
    EXTENSION_GRANTED = "extension_granted"
    HEARING_REQUESTED = "hearing_requested"
    HEARING_DECISION = "hearing_decision"
    COMPLIANCE_REGAINED = "compliance_regained"
    SUSPENSION_ANNOUNCED = "suspension_announced"
    DELISTING_ANNOUNCED = "delisting_announced"
    DELISTING_EFFECTIVE = "delisting_effective"
    UNKNOWN = "unknown"


class ListingComplianceState(StrEnum):
    COMPLIANT = "compliant"
    DEFICIENT = "deficient"
    CURE_WINDOW_ACTIVE = "cure_window_active"
    REGAINED_CONFIRMED = "regained_confirmed"
    DELISTING_RISK_ACTIVE = "delisting_risk_active"
    DELISTING_EFFECTIVE = "delisting_effective"
    UNKNOWN = "unknown"


class ListingRepricingInterpretationType(StrEnum):
    LISTING_OVERHANG_REMOVED = "listing_overhang_removed"
    LISTING_RISK_REMAINS = "listing_risk_remains"
    LISTING_REPRICING_CANDIDATE = "listing_repricing_candidate"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _text(value: str, field: str, *, max_len: int = 255) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > max_len:
        raise ContractViolation(f"{field} must be bounded non-blank text")


def _refs(values: tuple[str, ...], field: str, *, required: bool = True) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if required and not values:
        raise ContractViolation(f"{field} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        _text(value, field)


@dataclass(frozen=True, kw_only=True)
class ListingComplianceEvent:
    """Source-grounded exchange/listing event without inferred issuer intent."""

    event_id: str
    subject_ref: str
    venue: str
    event_type: ListingComplianceEventType
    event_at: datetime
    available_at: datetime
    accepted_at: datetime
    evidence_record_ids: tuple[str, ...]
    rule_reference: str | None = None

    def __post_init__(self) -> None:
        _text(self.event_id, "event_id")
        _text(self.subject_ref, "subject_ref")
        _text(self.venue, "venue")
        if not isinstance(self.event_type, ListingComplianceEventType):
            raise ContractViolation("event_type must be ListingComplianceEventType")
        _utc(self.event_at, "event_at")
        _utc(self.available_at, "available_at")
        _utc(self.accepted_at, "accepted_at")
        if self.event_at > self.available_at:
            raise ContractViolation("event_at cannot be later than available_at")
        if self.available_at > self.accepted_at:
            raise ContractViolation("available_at cannot be later than accepted_at")
        _refs(self.evidence_record_ids, "evidence_record_ids")
        if self.rule_reference is not None:
            _text(self.rule_reference, "rule_reference", max_len=1024)


@dataclass(frozen=True, kw_only=True)
class ListingComplianceAssessment:
    subject_ref: str
    venue: str
    state: ListingComplianceState
    as_of: datetime
    basis_event_ids: tuple[str, ...]
    basis_evidence_record_ids: tuple[str, ...]
    method_version: str = "listing-compliance-v0.1"

    def __post_init__(self) -> None:
        _text(self.subject_ref, "subject_ref")
        _text(self.venue, "venue")
        if not isinstance(self.state, ListingComplianceState):
            raise ContractViolation("state must be ListingComplianceState")
        _utc(self.as_of, "as_of")
        _refs(self.basis_event_ids, "basis_event_ids")
        _refs(self.basis_evidence_record_ids, "basis_evidence_record_ids")
        _text(self.method_version, "method_version")


@dataclass(frozen=True, kw_only=True)
class ListingRepricingAssessment:
    """Interpretation that preserves listing and company evidence as distinct inputs."""

    subject_ref: str
    interpretation_type: ListingRepricingInterpretationType
    listing_evidence_record_ids: tuple[str, ...]
    company_evidence_record_ids: tuple[str, ...] = ()
    market_metric_record_ids: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "listing-repricing-v0.1"

    def __post_init__(self) -> None:
        _text(self.subject_ref, "subject_ref")
        if not isinstance(self.interpretation_type, ListingRepricingInterpretationType):
            raise ContractViolation("interpretation_type must be ListingRepricingInterpretationType")
        _refs(self.listing_evidence_record_ids, "listing_evidence_record_ids")
        _refs(self.company_evidence_record_ids, "company_evidence_record_ids", required=False)
        _refs(self.market_metric_record_ids, "market_metric_record_ids", required=False)
        _utc(self.generated_at, "generated_at")
        _text(self.method_version, "method_version")
        groups = [
            set(self.listing_evidence_record_ids),
            set(self.company_evidence_record_ids),
            set(self.market_metric_record_ids),
        ]
        if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
            raise ContractViolation("listing, company, and market evidence classes must remain distinct")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.listing_evidence_record_ids
            + self.company_evidence_record_ids
            + self.market_metric_record_ids
        )

    def to_interpretation(
        self,
        *,
        record_id: str,
        accepted_at: datetime,
        supersedes_record_id: str | None = None,
    ) -> Interpretation:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        return Interpretation(
            record_id=record_id,
            schema_version="listing-repricing-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type=self.interpretation_type.value,
            statement={
                "listing_evidence_count": len(self.listing_evidence_record_ids),
                "company_evidence_count": len(self.company_evidence_record_ids),
                "market_metric_count": len(self.market_metric_record_ids),
            },
            basis_record_ids=self.basis_record_ids,
            method="listing_compliance_repricing_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
