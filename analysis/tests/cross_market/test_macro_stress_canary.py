from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import (
    ContractViolation,
    MacroStressAssessment,
    MacroStressInterpretationType,
    MacroStressRating,
)
from orderscope_local.cross_market import (
    CurveChange,
    CurveShape,
    classify_curve_change,
    classify_curve_shape,
)

UTC = timezone.utc
START = datetime(2026, 9, 1, tzinfo=UTC)
END = datetime(2026, 9, 4, tzinfo=UTC)
GENERATED = datetime(2026, 9, 5, tzinfo=UTC)


def assessment(**overrides):
    values = dict(
        interpretation_type=MacroStressInterpretationType.CARRY_UNWIND_CANDIDATE,
        rating=MacroStressRating.SUPPORT,
        subject_ref="macro:cross-market",
        observed_window_start=START,
        observed_window_end=END,
        macro_metric_refs=("metric:us_jp_2y_spread_delta", "metric:usdjpy_delta"),
        market_stress_metric_refs=("metric:qqq_drawdown", "metric:breadth_deterioration"),
        explicit_source_evidence_refs=(),
        contradicting_evidence_refs=(),
        generated_at=GENERATED,
    )
    values.update(overrides)
    return MacroStressAssessment(**values)


def test_policy_up_long_yield_down_and_curve_states_remain_metrics_not_cause():
    assert classify_curve_shape(-0.15) is CurveShape.INVERTED
    assert classify_curve_change(-0.05, -0.15) is CurveChange.FLATTENING
    assert classify_curve_change(-0.15, -0.02) is CurveChange.STEEPENING


def test_carry_unwind_requires_macro_and_market_stress_signal_classes():
    with pytest.raises(ContractViolation):
        assessment(market_stress_metric_refs=())


def test_rapid_jpy_move_alone_cannot_establish_carry_unwind():
    with pytest.raises(ContractViolation):
        assessment(
            macro_metric_refs=("metric:usdjpy_delta",),
            market_stress_metric_refs=(),
            explicit_source_evidence_refs=(),
        )


def test_broad_selloff_plus_macro_stress_can_support_candidate_without_company_attribution():
    result = assessment().to_interpretation(
        record_id="interpretation:macro:carry-unwind:20260905",
        accepted_at=GENERATED,
    )
    assert result.interpretation_type == "carry_unwind_candidate"
    assert "metric:qqq_drawdown" in result.basis_record_ids
    assert "metric:usdjpy_delta" in result.basis_record_ids


def test_explicit_carry_reduction_report_is_supporting_evidence_not_fact_conversion():
    result = assessment(
        explicit_source_evidence_refs=("evidence:carry-reduction-report",),
    ).to_interpretation(
        record_id="interpretation:macro:carry-unwind:reported:20260905",
        accepted_at=GENERATED,
    )
    assert result.interpretation_type == "carry_unwind_candidate"
    assert "evidence:carry-reduction-report" in result.basis_record_ids


def test_event_risk_or_company_specific_counterevidence_can_contradict_macro_story():
    result = assessment(
        rating=MacroStressRating.CONTRADICT,
        macro_metric_refs=(),
        market_stress_metric_refs=(),
        contradicting_evidence_refs=("evidence:company-specific-negative-event",),
    ).to_interpretation(
        record_id="interpretation:macro:carry-unwind:contradict:20260905",
        accepted_at=GENERATED,
    )
    assert result.statement["rating"] == "CONTRADICT"
    assert result.basis_record_ids == ("evidence:company-specific-negative-event",)
