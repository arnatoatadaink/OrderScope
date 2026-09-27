import pytest

from orderscope_local.contracts.cross_asset_canary import (
    CanaryDecision,
    CapacityObservation,
    CrossAssetCanaryAssessment,
    CrossAssetCanaryResult,
)
from orderscope_local.contracts import ContractViolation


def result(**overrides) -> CrossAssetCanaryResult:
    values = dict(
        scenario_id="fixture-risk-on",
        expected_regime="broad_risk_on",
        observed_regime="broad_risk_on",
        expected_alert=True,
        observed_alert=True,
    )
    values.update(overrides)
    return CrossAssetCanaryResult(**values)


def capacity(**overrides) -> CapacityObservation:
    values = dict(
        worker_requests_per_day=12000,
        d1_rows_read_per_day=50000,
        d1_rows_written_per_day=5000,
        d1_bytes_written_per_day=2_000_000,
        scheduled_invocations_per_day=1440,
        headroom_ratio=0.45,
    )
    values.update(overrides)
    return CapacityObservation(**values)


def test_clean_historical_replay_accepts() -> None:
    item = CrossAssetCanaryAssessment(results=(result(),), capacity=capacity())
    assert item.decision is CanaryDecision.ACCEPT
    assert item.false_positive_count == 0
    assert item.false_negative_count == 0


def test_false_positive_requires_review_not_acceptance() -> None:
    item = CrossAssetCanaryAssessment(
        results=(result(expected_alert=False, observed_alert=True),),
        capacity=capacity(),
    )
    assert item.decision is CanaryDecision.REVIEW
    assert item.false_positive_count == 1


def test_false_negative_rejects() -> None:
    item = CrossAssetCanaryAssessment(
        results=(result(expected_alert=True, observed_alert=False),),
        capacity=capacity(),
    )
    assert item.decision is CanaryDecision.REJECT


def test_regime_mismatch_rejects_even_if_alert_matches() -> None:
    item = CrossAssetCanaryAssessment(
        results=(result(observed_regime="crypto_risk_on"),),
        capacity=capacity(),
    )
    assert item.decision is CanaryDecision.REJECT
    assert item.regime_mismatch_count == 1


def test_capacity_headroom_below_floor_rejects() -> None:
    item = CrossAssetCanaryAssessment(
        results=(result(),),
        capacity=capacity(headroom_ratio=0.19),
    )
    assert item.decision is CanaryDecision.REJECT


def test_duplicate_scenario_identity_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="scenario_id"):
        CrossAssetCanaryAssessment(results=(result(), result()), capacity=capacity())


def test_capacity_values_are_non_negative() -> None:
    with pytest.raises(ContractViolation, match="worker_requests_per_day"):
        capacity(worker_requests_per_day=-1)
    with pytest.raises(ContractViolation, match="d1_rows_read_per_day"):
        capacity(d1_rows_read_per_day=-1)


def test_headroom_ratio_is_bounded() -> None:
    with pytest.raises(ContractViolation, match="between zero and one"):
        capacity(headroom_ratio=1.1)
