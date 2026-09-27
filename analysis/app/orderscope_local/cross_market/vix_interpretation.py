"""UWBS-096 VIX level/change/curve interpretation contract.

Interpretation consumes already-grounded VIX level/change/curve evidence. It does
not define calibrated numerical fear thresholds, substitute VIX-linked ETP prices
for VIX, or turn volatility evidence into a price-direction claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import Interpretation, InterpretationAssertionKind


class VixInterpretationState(StrEnum):
    PRESSURE_BUILDING = "pressure_building_candidate"
    PRESSURE_EASING = "pressure_easing_candidate"
    CURVE_STRESS_PERSISTING = "curve_stress_persisting_candidate"
    MIXED = "mixed_volatility_candidate"
    UNKNOWN = "unknown"


class VixInterpretationRating(StrEnum):
    SUPPORT = "SUPPORT"
    PARTIAL = "PARTIAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, kw_only=True)
class VixInterpretationAssessment:
    subject_ref: str
    state: VixInterpretationState
    rating: VixInterpretationRating
    observed_window_start: datetime
    observed_window_end: datetime
    level_metric_refs: tuple[str, ...] = ()
    point_change_metric_refs: tuple[str, ...] = ()
    percent_change_metric_refs: tuple[str, ...] = ()
    curve_metric_refs: tuple[str, ...] = ()
    curve_transition_refs: tuple[str, ...] = ()
    contradicting_evidence_refs: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "vix-interpretation-v0.1"

    def __post_init__(self) -> None:
        _canonical(self.subject_ref, "subject_ref")
        if not isinstance(self.state, VixInterpretationState):
            raise ContractViolation("state must be VixInterpretationState")
        if not isinstance(self.rating, VixInterpretationRating):
            raise ContractViolation("rating must be VixInterpretationRating")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed_window_end")
        _canonical(self.method_version, "method_version")

        groups = (
            (self.level_metric_refs, "level_metric_refs"),
            (self.point_change_metric_refs, "point_change_metric_refs"),
            (self.percent_change_metric_refs, "percent_change_metric_refs"),
            (self.curve_metric_refs, "curve_metric_refs"),
            (self.curve_transition_refs, "curve_transition_refs"),
            (self.contradicting_evidence_refs, "contradicting_evidence_refs"),
        )
        for refs, field in groups:
            _refs(refs, field)
        _disjoint(*(refs for refs, _ in groups))
        self._validate_semantics()

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.level_metric_refs
            + self.point_change_metric_refs
            + self.percent_change_metric_refs
            + self.curve_metric_refs
            + self.curve_transition_refs
            + self.contradicting_evidence_refs
        )

    def _validate_semantics(self) -> None:
        directional_groups = sum(
            bool(refs)
            for refs in (
                self.level_metric_refs,
                self.point_change_metric_refs,
                self.percent_change_metric_refs,
                self.curve_metric_refs,
                self.curve_transition_refs,
            )
        )
        if self.rating is VixInterpretationRating.UNKNOWN:
            if directional_groups or self.contradicting_evidence_refs:
                raise ContractViolation("UNKNOWN cannot carry directional evidence")
            if self.state is not VixInterpretationState.UNKNOWN:
                raise ContractViolation("UNKNOWN rating requires UNKNOWN state")
            return
        if self.state is VixInterpretationState.UNKNOWN:
            raise ContractViolation("directional rating cannot use UNKNOWN state")
        if self.rating is VixInterpretationRating.CONTRADICT:
            if not self.contradicting_evidence_refs:
                raise ContractViolation("CONTRADICT requires contradicting evidence")
            return
        if self.state is VixInterpretationState.CURVE_STRESS_PERSISTING:
            if not self.curve_metric_refs or not self.curve_transition_refs:
                raise ContractViolation("curve persistence requires curve level and transition/persistence evidence")
        required = 2 if self.rating is VixInterpretationRating.SUPPORT else 1
        if directional_groups < required:
            raise ContractViolation(
                f"{self.rating.value} requires at least {required} independent VIX evidence classes"
            )

    def to_interpretation(self, *, record_id: str, accepted_at: datetime) -> Interpretation:
        _canonical(record_id, "record_id")
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        if not self.basis_record_ids:
            raise ContractViolation("VIX interpretation requires evidence lineage")
        return Interpretation(
            record_id=record_id,
            schema_version="vix-level-change-curve-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            interpretation_type=f"volatility.{self.state.value}",
            statement={
                "state": self.state.value,
                "rating": self.rating.value,
                "level_evidence_count": len(self.level_metric_refs),
                "point_change_evidence_count": len(self.point_change_metric_refs),
                "percent_change_evidence_count": len(self.percent_change_metric_refs),
                "curve_evidence_count": len(self.curve_metric_refs),
                "curve_transition_evidence_count": len(self.curve_transition_refs),
                "contradicting_count": len(self.contradicting_evidence_refs),
                "fixed_threshold_calibrated": False,
            },
            basis_record_ids=self.basis_record_ids,
            method="vix_level_change_curve_interpretation",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        _canonical(value, field)


def _disjoint(*groups: tuple[str, ...]) -> None:
    sets = [set(group) for group in groups]
    for index, left in enumerate(sets):
        for right in sets[index + 1:]:
            if left & right:
                raise ContractViolation("VIX evidence classes cannot reuse references")
