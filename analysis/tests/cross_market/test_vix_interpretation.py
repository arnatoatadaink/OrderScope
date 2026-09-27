from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.vix_interpretation import (
    VixInterpretationAssessment,
    VixInterpretationRating,
    VixInterpretationState,
)

UTC = timezone.utc
START = datetime(2026, 9, 27, 13, 30, tzinfo=UTC)
END = datetime(2026, 9, 27, 14, 30, tzinfo=UTC)
GENERATED = datetime(2026, 9, 27, 14, 31, tzinfo=UTC)


def assessment(**overrides) -> VixInterpretationAssessment:
    values = dict(
        subject_ref="volatility.us-equity.vix",
        state=VixInterpretationState.PRESSURE_BUILDING,
        rating=VixInterpretationRating.SUPPORT,
        observed_window_start=START,
        observed_window_end=END,
        level_metric_refs=("metric.vix.level",),
        point_change_metric_refs=("metric.vix.point-change",),
        generated_at=GENERATED,
    )
    values.update(overrides)
    return VixInterpretationAssessment(**values)


def test_support_requires_two_independent_evidence_classes() -> None:
    with pytest.raises(ContractViolation, match="at least 2"):
        assessment(point_change_metric_refs=())


def test_partial_accepts_one_directional_evidence_class() -> None:
    item = assessment(
        rating=VixInterpretationRating.PARTIAL,
        point_change_metric_refs=(),
    )
    assert item.rating is VixInterpretationRating.PARTIAL


def test_unknown_cannot_carry_directional_evidence() -> None:
    with pytest.raises(ContractViolation, match="UNKNOWN cannot carry"):
        assessment(
            state=VixInterpretationState.UNKNOWN,
            rating=VixInterpretationRating.UNKNOWN,
        )


def test_clean_unknown_state_is_valid_but_not_materializable_without_lineage() -> None:
    item = assessment(
        state=VixInterpretationState.UNKNOWN,
        rating=VixInterpretationRating.UNKNOWN,
        level_metric_refs=(),
        point_change_metric_refs=(),
    )
    with pytest.raises(ContractViolation, match="requires evidence lineage"):
        item.to_interpretation(record_id="interpretation.vix.unknown", accepted_at=GENERATED)


def test_contradict_requires_explicit_contradicting_evidence() -> None:
    with pytest.raises(ContractViolation, match="requires contradicting evidence"):
        assessment(rating=VixInterpretationRating.CONTRADICT)


def test_contradict_preserves_conflicting_evidence() -> None:
    item = assessment(
        rating=VixInterpretationRating.CONTRADICT,
        contradicting_evidence_refs=("evidence.vix.counter",),
    )
    assert item.contradicting_evidence_refs == ("evidence.vix.counter",)


def test_curve_persistence_requires_curve_and_transition_evidence() -> None:
    with pytest.raises(ContractViolation, match="curve persistence"):
        assessment(
            state=VixInterpretationState.CURVE_STRESS_PERSISTING,
            curve_metric_refs=("metric.vix.curve",),
            level_metric_refs=(),
            point_change_metric_refs=(),
        )


def test_curve_persistence_accepts_curve_and_transition_classes() -> None:
    item = assessment(
        state=VixInterpretationState.CURVE_STRESS_PERSISTING,
        curve_metric_refs=("metric.vix.curve",),
        curve_transition_refs=("metric.vix.curve-transition",),
        level_metric_refs=(),
        point_change_metric_refs=(),
    )
    assert item.state is VixInterpretationState.CURVE_STRESS_PERSISTING


def test_evidence_classes_cannot_reuse_same_record() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse"):
        assessment(
            level_metric_refs=("metric.same",),
            point_change_metric_refs=("metric.same",),
        )


def test_materialized_interpretation_marks_threshold_as_uncalibrated() -> None:
    record = assessment().to_interpretation(
        record_id="interpretation.vix.pressure-building",
        accepted_at=GENERATED,
    )
    assert record.interpretation_type == "volatility.pressure_building_candidate"
    assert record.statement["rating"] == "SUPPORT"
    assert record.statement["fixed_threshold_calibrated"] is False
    assert "etp" not in record.interpretation_type
