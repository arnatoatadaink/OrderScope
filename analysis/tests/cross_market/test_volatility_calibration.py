from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.cross_asset_canary_replay import (
    CapacityEnvelope,
    ProjectedCapacityUsage,
)
from orderscope_local.cross_market.volatility_calibration import (
    CalibrationMethod,
    CalibrationRule,
    VolatilityCalibrationPoint,
    VolatilityCalibrationSuite,
    VolatilityWindowKind,
    compare_calibration_rules,
    evaluate_calibration_rule,
)

UTC = timezone.utc
BASE = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def point(
    window_id: str,
    kind: VolatilityWindowKind,
    value: str,
    expected: bool,
    *,
    minute: int,
    event_offset_minutes: int | None = None,
) -> VolatilityCalibrationPoint:
    observed_at = BASE + timedelta(minutes=minute)
    event_at = None
    if event_offset_minutes is not None:
        event_at = observed_at + timedelta(minutes=event_offset_minutes)
    return VolatilityCalibrationPoint(
        window_id=window_id,
        window_kind=kind,
        observed_at=observed_at,
        signal_value=Decimal(value),
        expected_alert=expected,
        event_at=event_at,
    )


def suite() -> VolatilityCalibrationSuite:
    return VolatilityCalibrationSuite(
        points=(
            point("calm", VolatilityWindowKind.CALM, "10", False, minute=0),
            point("correction", VolatilityWindowKind.CORRECTION, "30", True, minute=1, event_offset_minutes=1),
            point("shock", VolatilityWindowKind.SHOCK, "50", True, minute=2, event_offset_minutes=-2),
            point("recovery", VolatilityWindowKind.RECOVERY, "20", False, minute=3),
            point("divergence", VolatilityWindowKind.MSTR_BTC_DIVERGENCE, "40", True, minute=4, event_offset_minutes=0),
            point("control", VolatilityWindowKind.CONTROL, "15", False, minute=5),
        )
    )


def projected() -> ProjectedCapacityUsage:
    return ProjectedCapacityUsage(
        worker_requests_per_day=100,
        d1_rows_read_per_day=1_000,
        d1_rows_written_per_day=100,
        d1_bytes_written_per_day=10_000,
        scheduled_invocations_per_day=100,
    )


def envelope() -> CapacityEnvelope:
    return CapacityEnvelope(
        worker_requests_per_day=1_000,
        d1_rows_read_per_day=10_000,
        d1_rows_written_per_day=1_000,
        d1_bytes_available=100_000,
        scheduled_invocations_per_day=1_000,
    )


def test_suite_tracks_all_required_historical_window_kinds() -> None:
    result = suite()
    assert result.complete_window_coverage is True
    assert result.covered_window_kinds == frozenset(VolatilityWindowKind)


def test_absolute_threshold_confusion_matrix_is_deterministic() -> None:
    evaluation = evaluate_calibration_rule(
        suite=suite(),
        rule=CalibrationRule(
            method=CalibrationMethod.ABSOLUTE_THRESHOLD,
            boundary=Decimal("25"),
        ),
    )
    assert evaluation.true_positive_count == 3
    assert evaluation.false_positive_count == 0
    assert evaluation.true_negative_count == 3
    assert evaluation.false_negative_count == 0
    assert evaluation.error_count == 0
    assert evaluation.precision == Decimal("1")
    assert evaluation.recall == Decimal("1")


def test_percentile_candidate_is_evaluated_without_becoming_production_rule() -> None:
    evaluation = evaluate_calibration_rule(
        suite=suite(),
        rule=CalibrationRule(
            method=CalibrationMethod.EMPIRICAL_PERCENTILE,
            boundary=Decimal("0.50"),
        ),
    )
    assert evaluation.true_positive_count == 3
    assert evaluation.false_positive_count == 1
    assert evaluation.false_negative_count == 0
    assert evaluation.error_count == 1


def test_z_score_candidate_is_supported() -> None:
    evaluation = evaluate_calibration_rule(
        suite=suite(),
        rule=CalibrationRule(
            method=CalibrationMethod.Z_SCORE,
            boundary=Decimal("0.25"),
        ),
    )
    assert evaluation.true_positive_count >= 1
    assert evaluation.false_positive_count >= 0
    assert evaluation.false_negative_count >= 0


def test_negative_timing_means_lead_and_positive_means_lag() -> None:
    evaluation = evaluate_calibration_rule(
        suite=suite(),
        rule=CalibrationRule(
            method=CalibrationMethod.ABSOLUTE_THRESHOLD,
            boundary=Decimal("25"),
        ),
    )
    by_id = {item.window_id: item for item in evaluation.classifications}
    assert by_id["correction"].timing_seconds == -60.0
    assert by_id["shock"].timing_seconds == 120.0
    assert by_id["divergence"].timing_seconds == 0.0
    assert evaluation.mean_timing_seconds == 20.0


def test_comparison_ranks_candidates_but_does_not_activate_one() -> None:
    absolute = CalibrationRule(
        method=CalibrationMethod.ABSOLUTE_THRESHOLD,
        boundary=Decimal("25"),
    )
    percentile = CalibrationRule(
        method=CalibrationMethod.EMPIRICAL_PERCENTILE,
        boundary=Decimal("0.50"),
    )
    comparison = compare_calibration_rules(
        suite=suite(),
        rules=(percentile, absolute),
        projected=projected(),
        envelope=envelope(),
    )
    assert comparison.ranked_evaluations[0].rule == absolute
    assert comparison.capacity_acceptable is True
    assert not hasattr(comparison, "active_rule")


def test_capacity_uses_uwbs_086_headroom_contract() -> None:
    comparison = compare_calibration_rules(
        suite=suite(),
        rules=(
            CalibrationRule(
                method=CalibrationMethod.ABSOLUTE_THRESHOLD,
                boundary=Decimal("25"),
            ),
        ),
        projected=projected(),
        envelope=envelope(),
        minimum_headroom_ratio=0.20,
    )
    assert comparison.capacity.headroom_ratio == pytest.approx(0.90)
    assert comparison.capacity_acceptable is True


def test_capacity_can_fail_independently_of_classification_quality() -> None:
    tight = CapacityEnvelope(
        worker_requests_per_day=110,
        d1_rows_read_per_day=1_100,
        d1_rows_written_per_day=110,
        d1_bytes_available=11_000,
        scheduled_invocations_per_day=110,
    )
    comparison = compare_calibration_rules(
        suite=suite(),
        rules=(
            CalibrationRule(
                method=CalibrationMethod.ABSOLUTE_THRESHOLD,
                boundary=Decimal("25"),
            ),
        ),
        projected=projected(),
        envelope=tight,
        minimum_headroom_ratio=0.20,
    )
    assert comparison.evaluations[0].error_count == 0
    assert comparison.capacity_acceptable is False


def test_duplicate_window_ids_are_rejected() -> None:
    duplicate = point("same", VolatilityWindowKind.CALM, "10", False, minute=0)
    with pytest.raises(ContractViolation, match="window ids must be unique"):
        VolatilityCalibrationSuite(points=(duplicate, duplicate))


def test_percentile_boundary_must_be_fraction() -> None:
    with pytest.raises(ContractViolation, match="percentile boundary"):
        CalibrationRule(
            method=CalibrationMethod.EMPIRICAL_PERCENTILE,
            boundary=Decimal("1.01"),
        )


def test_z_score_rejects_zero_variance_suite() -> None:
    flat = VolatilityCalibrationSuite(
        points=(
            point("a", VolatilityWindowKind.CALM, "10", False, minute=0),
            point("b", VolatilityWindowKind.CONTROL, "10", False, minute=1),
        )
    )
    with pytest.raises(ContractViolation, match="non-zero signal variance"):
        evaluate_calibration_rule(
            suite=flat,
            rule=CalibrationRule(
                method=CalibrationMethod.Z_SCORE,
                boundary=Decimal("1"),
            ),
        )


def test_observation_timestamp_must_be_utc() -> None:
    with pytest.raises(ContractViolation, match="observed_at must be timezone-aware UTC"):
        VolatilityCalibrationPoint(
            window_id="bad-time",
            window_kind=VolatilityWindowKind.CALM,
            observed_at=datetime(2026, 9, 28, 12, 0),
            signal_value=Decimal("10"),
            expected_alert=False,
        )


def test_comparison_requires_rules() -> None:
    with pytest.raises(ContractViolation, match="requires at least one rule"):
        compare_calibration_rules(
            suite=suite(),
            rules=(),
            projected=projected(),
            envelope=envelope(),
        )
