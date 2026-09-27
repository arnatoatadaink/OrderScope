"""A0-001 cross-market hypothesis contract.

Capital movement remains an Interpretation, never a Fact.  FX contributes
support/contradiction evidence but cannot by itself establish capital movement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class FxDirectionConsistency(StrEnum):
    SUPPORT = "SUPPORT"
    NEUTRAL = "NEUTRAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


class HypothesisConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ProposedFlowDirection(StrEnum):
    SOURCE_TO_DESTINATION = "SOURCE_TO_DESTINATION"
    DESTINATION_TO_SOURCE = "DESTINATION_TO_SOURCE"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


def _identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
        raise ContractViolation(f"{field} must be bounded non-empty canonical text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        _identifier(value, field)


@dataclass(frozen=True, kw_only=True)
class CrossMarketHypothesis:
    hypothesis_type: str
    source_region: str
    destination_region: str
    proposed_direction: ProposedFlowDirection
    observed_window_start: datetime
    observed_window_end: datetime
    supporting_evidence_refs: tuple[str, ...]
    contradicting_evidence_refs: tuple[str, ...]
    fx_direction_consistency: FxDirectionConsistency
    confidence: HypothesisConfidence
    generated_at: datetime
    model_or_rule_version: str

    def __post_init__(self) -> None:
        for value, field in (
            (self.hypothesis_type, "hypothesis_type"),
            (self.source_region, "source_region"),
            (self.destination_region, "destination_region"),
            (self.model_or_rule_version, "model_or_rule_version"),
        ):
            _identifier(value, field)
        if self.source_region == self.destination_region:
            raise ContractViolation("source_region and destination_region must differ")
        if not isinstance(self.proposed_direction, ProposedFlowDirection):
            raise ContractViolation("proposed_direction must be ProposedFlowDirection")
        if not isinstance(self.fx_direction_consistency, FxDirectionConsistency):
            raise ContractViolation("fx_direction_consistency must be FxDirectionConsistency")
        if not isinstance(self.confidence, HypothesisConfidence):
            raise ContractViolation("confidence must be HypothesisConfidence")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed window end")
        _refs(self.supporting_evidence_refs, "supporting_evidence_refs")
        _refs(self.contradicting_evidence_refs, "contradicting_evidence_refs")
        if set(self.supporting_evidence_refs) & set(self.contradicting_evidence_refs):
            raise ContractViolation("one Evidence reference cannot both support and contradict")
        if not self.supporting_evidence_refs and not self.contradicting_evidence_refs:
            if self.confidence is not HypothesisConfidence.UNKNOWN:
                raise ContractViolation("hypothesis without Evidence must have UNKNOWN confidence")
        if self.fx_direction_consistency is FxDirectionConsistency.CONTRADICT and self.confidence is HypothesisConfidence.HIGH:
            raise ContractViolation("FX contradiction blocks HIGH confidence in v0.1")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return self.supporting_evidence_refs + self.contradicting_evidence_refs

    def to_interpretation(
        self,
        *,
        record_id: str,
        subject_ref: str,
        accepted_at: datetime,
        schema_version: str = "cross-market-hypothesis-v0.1",
        supersedes_record_id: str | None = None,
    ) -> Interpretation:
        """Materialize the hypothesis only as an I0-005 Interpretation."""
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        return Interpretation(
            record_id=record_id,
            schema_version=schema_version,
            subject_ref=subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type="cross_market_capital_movement_hypothesis",
            statement={
                "hypothesis_type": self.hypothesis_type,
                "source_region": self.source_region,
                "destination_region": self.destination_region,
                "proposed_direction": self.proposed_direction.value,
                "observed_window_start": self.observed_window_start.isoformat(),
                "observed_window_end": self.observed_window_end.isoformat(),
                "supporting_evidence_refs": ",".join(self.supporting_evidence_refs),
                "contradicting_evidence_refs": ",".join(self.contradicting_evidence_refs),
                "fx_direction_consistency": self.fx_direction_consistency.value,
                "confidence": self.confidence.value,
            },
            basis_record_ids=self.basis_record_ids,
            method="cross_market_rule",
            method_version=self.model_or_rule_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
