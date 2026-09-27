import pytest

from orderscope_local.contracts.cross_asset_canary import CanaryDecision, CrossAssetCanaryResult
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.cross_asset_canary_replay import (
    CapacityEnvelope,
    ProjectedCapacityUsage,
    assess_replay,
    build_capacity_observation,
)


def replay_result(**overrides) -> CrossAssetCanaryResult:
    values = dict(
        scenario_id="synthetic-broad-risk-on",
        expected_regime="broad_risk_on",
        observed_regime="broad_risk_on",
        expected_alert=True,
        observed_alert=True,
    )
    values.update(overrides)
    return CrossAssetCanaryResult(**values)


def projected(**overrides) -> ProjectedCapacityUsage:
    values = dict(
        worker_requests_per_day=12_000,
        d1_rows_read_per_day=250_000,
        d1_rows_written_per_day=8_000,
        d1_bytes_written_per_day=4_000_000,
        scheduled_invocations_per_day=1_440,
    )
    values.update(overrides)
    return ProjectedCapacityUsage(**values)


def envelope(**overrides) -> CapacityEnvelope:
    values = dict(
        worker_requests_per_day=100_000,
        d1_rows_read_per_day=5_000_000,
        d1_rows_written_per_day=100_000,
        d1_bytes_available=500_000_000,
        scheduled_invocations_per_day=None,
    )
    values.update(overrides)
    return CapacityEnvelope(**values)


def test_capacity_headroom_uses_most_constrained_resource() -> None:
    item = build_capacity_observation(projected=projected(), envelope=envelope())
    assert item.headroom_ratio == pytest.approx(0.88)


def test_d1_read_rows_can_be_the_most_constrained_resource() -> None:
    item = build_capacity_observation(
        projected=projected(d1_rows_read_per_day=4_500_000),
        envelope=envelope(),
    )
    assert item.headroom_ratio == pytest.approx(0.10)
    assert item.d1_rows_read_per_day == 4_500_000


def test_capacity_over_limit_has_zero_headroom() -> None:
    item = build_capacity_observation(
        projected=projected(d1_rows_written_per_day=120_000),
        envelope=envelope(),
    )
    assert item.headroom_ratio == 0.0


def test_cron_trigger_count_is_not_mistaken_for_daily_invocations() -> None:
    item = build_capacity_observation(
        projected=projected(scheduled_invocations_per_day=1_440),
        envelope=envelope(scheduled_invocations_per_day=None),
    )
    assert item.scheduled_invocations_per_day == 1_440
    assert item.headroom_ratio == pytest.approx(0.88)


def test_explicit_scheduler_envelope_can_be_included_when_available() -> None:
    item = build_capacity_observation(
        projected=projected(scheduled_invocations_per_day=90),
        envelope=envelope(scheduled_invocations_per_day=100),
    )
    assert item.headroom_ratio == pytest.approx(0.10)


def test_clean_synthetic_replay_with_capacity_accepts() -> None:
    assessment = assess_replay(
        results=(
            replay_result(),
            replay_result(
                scenario_id="synthetic-crypto-only",
                expected_regime="crypto_risk_on",
                observed_regime="crypto_risk_on",
            ),
            replay_result(
                scenario_id="synthetic-noise",
                expected_regime="divergent",
                observed_regime="divergent",
                expected_alert=False,
                observed_alert=False,
            ),
        ),
        projected=projected(),
        envelope=envelope(),
    )
    assert assessment.decision is CanaryDecision.ACCEPT


def test_false_positive_remains_review() -> None:
    assessment = assess_replay(
        results=(replay_result(expected_alert=False, observed_alert=True),),
        projected=projected(),
        envelope=envelope(),
    )
    assert assessment.decision is CanaryDecision.REVIEW


def test_false_negative_remains_reject() -> None:
    assessment = assess_replay(
        results=(replay_result(expected_alert=True, observed_alert=False),),
        projected=projected(),
        envelope=envelope(),
    )
    assert assessment.decision is CanaryDecision.REJECT


def test_capacity_below_default_twenty_percent_rejects() -> None:
    assessment = assess_replay(
        results=(replay_result(),),
        projected=projected(worker_requests_per_day=81_000),
        envelope=envelope(),
    )
    assert assessment.capacity.headroom_ratio == pytest.approx(0.19)
    assert assessment.decision is CanaryDecision.REJECT


def test_capacity_envelope_requires_positive_limits() -> None:
    with pytest.raises(ContractViolation, match="positive integer"):
        envelope(worker_requests_per_day=0)


def test_projected_usage_cannot_be_negative() -> None:
    with pytest.raises(ContractViolation, match="non-negative integer"):
        projected(d1_rows_written_per_day=-1)
    with pytest.raises(ContractViolation, match="non-negative integer"):
        projected(d1_rows_read_per_day=-1)
