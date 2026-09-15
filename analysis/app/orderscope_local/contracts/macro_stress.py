"""UWBS-013 macro-stress / carry-unwind Interpretation boundary.

Observed rates, yields, FX, volume, and explicit source statements remain Facts or
Evidence. Carry unwind, deleveraging, rate shock, and FX shock are assessments only.
No single FX move or news item may establish capital movement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class MacroStressInterpretationType(StrEnum):
    CARRY_UNWIND_CANDIDATE = "carry_unwind_candidate"
    DELEVERAGING_REGIME = "deleveraging_regime"
    RATE_SHOCK = "rate_shock"
    FX_SHOCK_JPY = "fx_shock_jpy"


class MacroStressRating(StrEnum):
    SUPPORT = "SUPPORT"
    PARTIAL = "PARTIAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class MacroStressAssessment:
    interpretation_type: MacroStressInterpretationType
    rating: MacroStressRating
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    macro_metric_refs: tuple[str, ...]
    market_stress_metric_refs: tuple[str, ...]
    explicit_source_evidence_refs: tuple[str, ...] = ()
    contradicting_evidence_refs: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "macro-stress-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.interpretation_type, MacroStressInterpretationType):
            raise ContractViolation("interpretation_type must be MacroStressInterpretationType")
        if not isinstance(self.rating, MacroStressRating):
            raise ContractViolation("rating must be MacroStressRating")
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

        for values, field in (
            (self.macro_metric_refs, "macro_metric_refs"),
            (self.market_stress_metric_refs, "market_stress_metric_refs"),
            (self.explicit_source_evidence_refs, "explicit_source_evidence_refs"),
            (self.contradicting_evidence_refs, "contradicting_evidence_refs"),
        ):
            _refs(values, field)

        groups = [
            set(self.macro_metric_refs),
            set(self.market_stress_metric_refs),
            set(self.explicit_source_evidence_refs),
            set(self.contradicting_evidence_refs),
        ]
        for index, left in enumerate(groups):
            for right in groups[index + 1 :]:
                if left & right:
                    raise ContractViolation("macro-stress evidence classes cannot reuse record references")

        supporting_groups = sum(
            bool(values)
            for values in (
                self.macro_metric_refs,
                self.market_stress_metric_refs,
                self.explicit_source_evidence_refs,
            )
        )
        if self.rating is MacroStressRating.UNKNOWN:
            if supporting_groups or self.contradicting_evidence_refs:
                raise ContractViolation("UNKNOWN macro-stress assessment cannot carry directional evidence")
            return

        if self.rating is MacroStressRating.CONTRADICT:
            if not self.contradicting_evidence_refs:
                raise ContractViolation("CONTRADICT macro-stress assessment requires contradicting evidence")
            return

        if supporting_groups < 2:
            raise ContractViolation("macro-stress support requires at least two independent signal classes")

        if self.interpretation_type in {
            MacroStressInterpretationType.CARRY_UNWIND_CANDIDATE,
            MacroStressInterpretationType.DELEVERAGING_REGIME,
        }:
            if not self.macro_metric_refs or not self.market_stress_metric_refs:
                raise ContractViolation("carry/deleveraging assessment requires both macro and market-stress signals")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.macro_metric_refs
            + self.market_stress_metric_refs
            + self.explicit_source_evidence_refs
            + self.contradicting_evidence_refs
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
        if not self.basis_record_ids:
            raise ContractViolation("Fact Store Interpretation requires evidence lineage")
        return Interpretation(
            record_id=record_id,
            schema_version="macro-stress-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type=self.interpretation_type.value,
            statement={
                "rating": self.rating.value,
                "observed_window_start": self.observed_window_start.isoformat(),
                "observed_window_end": self.observed_window_end.isoformat(),
                "macro_signal_count": len(self.macro_metric_refs),
                "market_stress_signal_count": len(self.market_stress_metric_refs),
                "explicit_source_count": len(self.explicit_source_evidence_refs),
                "contradicting_count": len(self.contradicting_evidence_refs),
            },
            basis_record_ids=self.basis_record_ids,
            method="macro_stress_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
