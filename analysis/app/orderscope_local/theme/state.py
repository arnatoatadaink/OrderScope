"""UWBS-065 conservative theme activation, rotation and repricing states."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import Interpretation, InterpretationAssertionKind

from .observation import ThemeReactionObservation
from .ontology import ThemeId, require_ref, require_refs, require_utc
from .reaction import ReactionDirection


class ThemeState(StrEnum):
    UNKNOWN = "UNKNOWN"
    ACTIVATION_CANDIDATE = "THEME_ACTIVATION_CANDIDATE"
    ACTIVATION_CONFIRMED = "THEME_ACTIVATION_CONFIRMED"
    ROTATION_CANDIDATE = "THEME_ROTATION_CANDIDATE"
    ROTATION_CONFIRMED = "THEME_ROTATION_CONFIRMED"
    REPRICING_CANDIDATE = "THEME_REPRICING_CANDIDATE"
    REPRICING_CONFIRMED = "THEME_REPRICING_CONFIRMED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, kw_only=True)
class CalibratedCriteria:
    """Externally reviewed empirical criteria; no constants are embedded here."""

    calibration_ref: str
    min_members: int
    min_directional_breadth: float
    min_abs_median_relative_return_pct: float
    min_median_volume_ratio: float
    min_persistent_members: int

    def __post_init__(self) -> None:
        require_ref(self.calibration_ref, "calibration_ref")
        if (
            isinstance(self.min_members, bool)
            or not isinstance(self.min_members, int)
            or self.min_members < 2
            or isinstance(self.min_persistent_members, bool)
            or not isinstance(self.min_persistent_members, int)
            or self.min_persistent_members < 0
        ):
            raise ContractViolation("criteria require cross-sectional members and valid persistence")
        for field in ("min_directional_breadth", "min_abs_median_relative_return_pct", "min_median_volume_ratio"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ContractViolation(f"{field} must be finite and nonnegative")
        if self.min_directional_breadth > 1 or self.min_persistent_members > self.min_members:
            raise ContractViolation("criteria breadth/persistence bounds are invalid")


@dataclass(frozen=True)
class ThemeAssessment:
    state: ThemeState
    theme: ThemeId
    event_refs: tuple[str, ...]
    metric_refs: tuple[str, ...]
    calibration_ref: str | None
    reason: str

    def to_interpretation(
        self, *, record_id: str, generated_at: datetime, accepted_at: datetime,
        event_evidence_refs: tuple[str, ...],
    ) -> Interpretation:
        """Record a state as Interpretation with inspectable metric lineage."""
        require_utc(generated_at, "generated_at")
        require_utc(accepted_at, "accepted_at")
        require_refs(event_evidence_refs, "event_evidence_refs")
        if accepted_at < generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        return Interpretation(
            record_id=record_id,
            schema_version="theme-state-assessment-v0.1",
            subject_ref=f"theme:{self.theme.value}",
            accepted_at=accepted_at,
            created_at=generated_at,
            interpretation_type="theme_state",
            statement={
                "state": self.state.value,
                "event_ref_count": len(self.event_refs),
                "first_event_ref": self.event_refs[0] if self.event_refs else None,
                "second_event_ref": self.event_refs[1] if len(self.event_refs) > 1 else None,
                "calibration_ref": self.calibration_ref,
                "reason": self.reason,
            },
            basis_record_ids=tuple(dict.fromkeys(self.metric_refs + event_evidence_refs)),
            method="theme_state_rule",
            method_version="theme-state-v0.1",
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )


def assess_activation(
    observation: ThemeReactionObservation,
    *,
    criteria: CalibratedCriteria | None = None,
) -> ThemeAssessment:
    if observation.member_count < 2 or observation.directional_breadth is None:
        return ThemeAssessment(
            ThemeState.UNKNOWN, observation.hypothesis.theme,
            (observation.hypothesis.event_ref,), observation.metric_refs, None,
            "cross-sectional directional evidence unavailable",
        )
    if observation.directional_breadth == 0:
        return ThemeAssessment(
            ThemeState.REJECTED, observation.hypothesis.theme,
            (observation.hypothesis.event_ref,), observation.metric_refs, None,
            "all observed relative moves contradict the hypothesis",
        )
    if criteria is None:
        return ThemeAssessment(
            ThemeState.ACTIVATION_CANDIDATE, observation.hypothesis.theme,
            (observation.hypothesis.event_ref,), observation.metric_refs, None,
            "empirical confirmation criteria not supplied",
        )
    confirmed = (
        observation.member_count >= criteria.min_members
        and observation.directional_breadth >= criteria.min_directional_breadth
        and abs(observation.median_relative_return_pct) >= criteria.min_abs_median_relative_return_pct
        and observation.median_relative_return_pct * observation.hypothesis.expected_direction.sign > 0
        and observation.median_volume_ratio is not None
        and observation.volume_assessed_members >= criteria.min_members
        and observation.median_volume_ratio >= criteria.min_median_volume_ratio
        and observation.persistent_members >= criteria.min_persistent_members
        and observation.persistence_assessed_members >= criteria.min_members
    )
    return ThemeAssessment(
        ThemeState.ACTIVATION_CONFIRMED if confirmed else ThemeState.ACTIVATION_CANDIDATE,
        observation.hypothesis.theme,
        (observation.hypothesis.event_ref,),
        observation.metric_refs,
        criteria.calibration_ref,
        "calibrated cross-sectional criteria met" if confirmed else "calibrated criteria not met or evidence incomplete",
    )


def assess_rotation(
    source: ThemeReactionObservation,
    destination: ThemeReactionObservation,
    *,
    source_criteria: CalibratedCriteria | None = None,
    destination_criteria: CalibratedCriteria | None = None,
) -> ThemeAssessment:
    if source.hypothesis.event_ref != destination.hypothesis.event_ref:
        raise ContractViolation("rotation observations must share one catalyst event")
    if (source.window_start, source.window_end) != (destination.window_start, destination.window_end):
        raise ContractViolation("rotation observations must use the same window")
    if source.hypothesis.theme is destination.hypothesis.theme:
        raise ContractViolation("rotation requires distinct themes")
    refs = tuple(dict.fromkeys(source.metric_refs + destination.metric_refs))
    if (
        source.hypothesis.expected_direction.sign != -1
        or destination.hypothesis.expected_direction.sign != 1
        or source.median_relative_return_pct >= 0
        or destination.median_relative_return_pct <= 0
    ):
        return ThemeAssessment(ThemeState.UNKNOWN, destination.hypothesis.theme, (source.hypothesis.event_ref,), refs, None, "opposed relative reactions unavailable")
    source_state = assess_activation(source, criteria=source_criteria)
    destination_state = assess_activation(destination, criteria=destination_criteria)
    if source_state.state in (ThemeState.UNKNOWN, ThemeState.REJECTED) or destination_state.state in (ThemeState.UNKNOWN, ThemeState.REJECTED):
        return ThemeAssessment(ThemeState.UNKNOWN, destination.hypothesis.theme, (source.hypothesis.event_ref,), refs, None, "both baskets need cross-sectional evidence")
    confirmed = source_state.state is ThemeState.ACTIVATION_CONFIRMED and destination_state.state is ThemeState.ACTIVATION_CONFIRMED
    calibration_ref = None if not confirmed else f"{source_criteria.calibration_ref}+{destination_criteria.calibration_ref}"
    return ThemeAssessment(
        ThemeState.ROTATION_CONFIRMED if confirmed else ThemeState.ROTATION_CANDIDATE,
        destination.hypothesis.theme, (source.hypothesis.event_ref,), refs, calibration_ref,
        "temporary relative rotation; no permanent theme antagonism implied",
    )


def assess_repricing(
    first: ThemeReactionObservation,
    second: ThemeReactionObservation,
    *,
    criteria: CalibratedCriteria | None = None,
) -> ThemeAssessment:
    if first.hypothesis.theme is not second.hypothesis.theme:
        raise ContractViolation("repricing observations must share one theme")
    if first.hypothesis.event_ref == second.hypothesis.event_ref or first.window_end > second.window_start:
        raise ContractViolation("repricing requires two distinct, ordered catalyst windows")
    refs = tuple(dict.fromkeys(first.metric_refs + second.metric_refs))
    events = (first.hypothesis.event_ref, second.hypothesis.event_ref)
    if first.member_count < 2 or second.member_count < 2 or first.directional_breadth is None or second.directional_breadth is None:
        return ThemeAssessment(ThemeState.UNKNOWN, first.hypothesis.theme, events, refs, None, "repeated cross-sectional evidence unavailable")
    if first.hypothesis.expected_direction.sign != second.hypothesis.expected_direction.sign:
        return ThemeAssessment(ThemeState.UNKNOWN, first.hypothesis.theme, events, refs, None, "event directions disagree")
    if first.median_relative_return_pct * first.hypothesis.expected_direction.sign <= 0 or second.median_relative_return_pct * second.hypothesis.expected_direction.sign <= 0:
        return ThemeAssessment(ThemeState.REJECTED, first.hypothesis.theme, events, refs, None, "repeated relative reaction absent")
    confirmed = criteria is not None and all(
        assess_activation(item, criteria=criteria).state is ThemeState.ACTIVATION_CONFIRMED
        for item in (first, second)
    )
    return ThemeAssessment(
        ThemeState.REPRICING_CONFIRMED if confirmed else ThemeState.REPRICING_CANDIDATE,
        first.hypothesis.theme, events, refs,
        criteria.calibration_ref if confirmed else None,
        "repeated distinct catalysts with calibrated confirmation" if confirmed else "repeated catalysts observed; empirical confirmation incomplete",
    )
