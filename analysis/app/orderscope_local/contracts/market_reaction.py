"""UWBS-029 market-reaction interpretation boundary.

The contract requires independent company-positive, macro-pressure, and relative-
repricing evidence before emitting a market-reaction assessment.  It never turns
price/volume behavior into buyer identity or capital-flow Fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class MarketReactionInterpretationType(StrEnum):
    LATENT_POSITIVE_CATALYST = "latent_positive_catalyst"
    MACRO_PRESSURE_DOMINANT = "macro_pressure_dominant"


class MarketReactionConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple) or not values:
        raise ContractViolation(f"{field} must be a non-empty immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class MarketReactionAssessment:
    interpretation_type: MarketReactionInterpretationType
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    company_positive_evidence_refs: tuple[str, ...]
    macro_pressure_evidence_refs: tuple[str, ...]
    relative_repricing_metric_refs: tuple[str, ...]
    confidence: MarketReactionConfidence
    generated_at: datetime
    method_version: str = "market-reaction-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.interpretation_type, MarketReactionInterpretationType):
            raise ContractViolation("interpretation_type must be MarketReactionInterpretationType")
        if not isinstance(self.confidence, MarketReactionConfidence):
            raise ContractViolation("confidence must be MarketReactionConfidence")
        if not isinstance(self.subject_ref, str) or not self.subject_ref.strip():
            raise ContractViolation("subject_ref cannot be blank")
        if not isinstance(self.method_version, str) or not self.method_version.strip():
            raise ContractViolation("method_version cannot be blank")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed window end")
        _refs(self.company_positive_evidence_refs, "company_positive_evidence_refs")
        _refs(self.macro_pressure_evidence_refs, "macro_pressure_evidence_refs")
        _refs(self.relative_repricing_metric_refs, "relative_repricing_metric_refs")
        groups = (
            set(self.company_positive_evidence_refs),
            set(self.macro_pressure_evidence_refs),
            set(self.relative_repricing_metric_refs),
        )
        if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
            raise ContractViolation("independent evidence classes cannot reuse the same record reference")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.company_positive_evidence_refs
            + self.macro_pressure_evidence_refs
            + self.relative_repricing_metric_refs
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
            schema_version="market-reaction-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type=self.interpretation_type.value,
            statement={
                "observed_window_start": self.observed_window_start.isoformat(),
                "observed_window_end": self.observed_window_end.isoformat(),
                "confidence": self.confidence.value,
                "company_positive_evidence_count": len(self.company_positive_evidence_refs),
                "macro_pressure_evidence_count": len(self.macro_pressure_evidence_refs),
                "relative_repricing_metric_count": len(self.relative_repricing_metric_refs),
            },
            basis_record_ids=self.basis_record_ids,
            method="market_reaction_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
