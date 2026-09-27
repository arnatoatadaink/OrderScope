from dataclasses import replace
from pathlib import Path

import pytest

from orderscope_local.contracts.cross_asset_canary import CanaryDecision
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.cross_asset_canary_replay import (
    CapacityEnvelope,
    ProjectedCapacityUsage,
)
from orderscope_local.cross_market.historical_canary_evaluation import (
    assess_historical_evaluation,
    evaluate_historical_manifests,
)
from orderscope_local.cross_market.historical_replay_manifest import load_historical_replay_manifest


MANIFEST = Path("analysis/config/cross_market/uwbs-086-2024-08-05-risk-off-v0.1.json")


def projected(**overrides) -> ProjectedCapacityUsage:
    values = dict(
        worker_requests_per_day=12_000,
        d1_rows_read_per_day=100_000,
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


def test_first_repository_historical_packet_is_clean() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    evaluation = evaluate_historical_manifests((manifest,))
    assert evaluation.historical_clean
    assert evaluation.false_positive_count == 0
    assert evaluation.false_negative_count == 0
    assert evaluation.regime_mismatch_count == 0
    assert evaluation.results[0].observed_regime == "risk_off"
    assert evaluation.results[0].observed_alert is True


def test_expected_label_change_does_not_change_classification() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    changed = replace(
        manifest,
        packet=replace(manifest.packet, expected_regime="broad_risk_on", expected_alert=False),
    )
    original = evaluate_historical_manifests((manifest,))
    modified = evaluate_historical_manifests((changed,))
    assert original.classifications[0].assessment == modified.classifications[0].assessment
    assert original.classifications[0].observed_alert == modified.classifications[0].observed_alert
    assert modified.false_positive_count == 1
    assert modified.regime_mismatch_count == 1


def test_clean_historical_result_with_healthy_capacity_accepts() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    evaluation = evaluate_historical_manifests((manifest,))
    assessment = assess_historical_evaluation(
        evaluation=evaluation,
        projected=projected(),
        envelope=envelope(),
    )
    assert assessment.decision is CanaryDecision.ACCEPT
    assert assessment.false_positive_count == 0
    assert assessment.false_negative_count == 0
    assert assessment.regime_mismatch_count == 0


def test_clean_historical_result_does_not_override_capacity_reject() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    evaluation = evaluate_historical_manifests((manifest,))
    assessment = assess_historical_evaluation(
        evaluation=evaluation,
        projected=projected(d1_rows_written_per_day=81_000),
        envelope=envelope(),
    )
    assert evaluation.historical_clean
    assert assessment.capacity.headroom_ratio == pytest.approx(0.19)
    assert assessment.decision is CanaryDecision.REJECT


def test_evaluation_requires_manifest_tuple() -> None:
    with pytest.raises(ContractViolation, match="at least one manifest"):
        evaluate_historical_manifests(())


def test_historical_evaluation_rejects_duplicate_scenario_ids() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    single = evaluate_historical_manifests((manifest,))
    with pytest.raises(ContractViolation, match="scenario ids"):
        replace(
            single,
            classifications=(single.classifications[0], single.classifications[0]),
            results=(single.results[0], single.results[0]),
        )


def test_assessment_requires_historical_evaluation() -> None:
    with pytest.raises(ContractViolation, match="HistoricalCanaryEvaluation"):
        assess_historical_evaluation(
            evaluation=None,  # type: ignore[arg-type]
            projected=projected(),
            envelope=envelope(),
        )
