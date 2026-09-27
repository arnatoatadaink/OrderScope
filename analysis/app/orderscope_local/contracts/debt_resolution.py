"""UWBS-018 debt-resolution attention Interpretation boundary.

The contract marks a capital instrument for attention when contractual timing and
supporting financing evidence make resolution activity relevant.  It never predicts
repayment, extension, refinancing, or conversion as an outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .capital_instrument_state import CapitalInstrumentState
from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class DebtResolutionAttentionLevel(StrEnum):
    WATCH = "watch"
    ELEVATED = "elevated"


_TERMINAL_STATES = frozenset({
    CapitalInstrumentState.FULLY_REPAID,
    CapitalInstrumentState.CONVERTED,
    CapitalInstrumentState.TERMINATED,
})


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str, *, required: bool = False) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if required and not values:
        raise ContractViolation(f"{field} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class DebtResolutionWindowAssessment:
    subject_ref: str
    instrument_ref: str
    current_state: CapitalInstrumentState
    attention_level: DebtResolutionAttentionLevel
    observed_window_start: datetime
    observed_window_end: datetime
    instrument_fact_record_ids: tuple[str, ...]
    timing_metric_record_ids: tuple[str, ...]
    financing_fact_record_ids: tuple[str, ...] = ()
    repayment_use_evidence_record_ids: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "debt-resolution-window-v0.1"

    def __post_init__(self) -> None:
        for value, field in ((self.subject_ref, "subject_ref"), (self.instrument_ref, "instrument_ref"), (self.method_version, "method_version")):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if not isinstance(self.current_state, CapitalInstrumentState):
            raise ContractViolation("current_state must be CapitalInstrumentState")
        if self.current_state in _TERMINAL_STATES:
            raise ContractViolation("resolved capital instrument cannot enter a debt-resolution window")
        if not isinstance(self.attention_level, DebtResolutionAttentionLevel):
            raise ContractViolation("attention_level must be DebtResolutionAttentionLevel")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed window end")

        for values, field, required in (
            (self.instrument_fact_record_ids, "instrument_fact_record_ids", True),
            (self.timing_metric_record_ids, "timing_metric_record_ids", True),
            (self.financing_fact_record_ids, "financing_fact_record_ids", False),
            (self.repayment_use_evidence_record_ids, "repayment_use_evidence_record_ids", False),
        ):
            _refs(values, field, required=required)

        groups = [
            set(self.instrument_fact_record_ids),
            set(self.timing_metric_record_ids),
            set(self.financing_fact_record_ids),
            set(self.repayment_use_evidence_record_ids),
        ]
        for index, left in enumerate(groups):
            for right in groups[index + 1 :]:
                if left & right:
                    raise ContractViolation("debt-resolution evidence classes cannot reuse record references")

        if self.attention_level is DebtResolutionAttentionLevel.ELEVATED:
            if not self.financing_fact_record_ids or not self.repayment_use_evidence_record_ids:
                raise ContractViolation("ELEVATED attention requires financing and explicit repayment-use evidence")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.instrument_fact_record_ids
            + self.timing_metric_record_ids
            + self.financing_fact_record_ids
            + self.repayment_use_evidence_record_ids
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
            schema_version="debt-resolution-window-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type="debt_resolution_window",
            statement={
                "instrument_ref": self.instrument_ref,
                "current_state": self.current_state.value,
                "attention_level": self.attention_level.value,
                "observed_window_start": self.observed_window_start.isoformat(),
                "observed_window_end": self.observed_window_end.isoformat(),
                "outcome_prediction": "none",
                "threshold_policy": "not_fixed_v0.1",
            },
            basis_record_ids=self.basis_record_ids,
            method="debt_resolution_attention_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
