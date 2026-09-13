from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.repricing_state import (
    RepricingState,
    RepricingStateAssessment,
    is_allowed_repricing_transition,
)


START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 5, tzinfo=timezone.utc)
GENERATED = datetime(2026, 9, 5, 1, tzinfo=timezone.utc)
ACCEPTED = datetime(2026, 9, 5, 2, tzinfo=timezone.utc)


def assessment(**overrides) -> RepricingStateAssessment:
    values = dict(
        state=RepricingState.RELATIVE_MEAN_REVERSION,
        subject_ref="instrument:CBRS",
        observed_window_start=START,
        observed_window_end=END,
        metric_record_ids=("metric:cbrs-relative-recovery",),
        catalyst_evidence_record_ids=("evidence:cbrs-positive-news",),
        generated_at=GENERATED,
    )
    values.update(overrides)
    return RepricingStateAssessment(**values)


def test_relative_mean_reversion_can_progress_to_overshoot_or_local_equilibrium() -> None:
    assert is_allowed_repricing_transition(
        RepricingState.RELATIVE_MEAN_REVERSION,
        RepricingState.REPRICING_OVERSHOOT,
    )
    assert is_allowed_repricing_transition(
        RepricingState.RELATIVE_MEAN_REVERSION,
        RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
    )


def test_relative_mean_reversion_cannot_jump_directly_to_confirmed_rediscovery() -> None:
    assert not is_allowed_repricing_transition(
        RepricingState.RELATIVE_MEAN_REVERSION,
        RepricingState.PRICE_REDISCOVERY_CONFIRMED,
    )


def test_assessment_rejects_disallowed_transition() -> None:
    with pytest.raises(ContractViolation, match="transition is not allowed"):
        assessment(
            state=RepricingState.PRICE_REDISCOVERY_CONFIRMED,
            previous_state=RepricingState.RELATIVE_MEAN_REVERSION,
            previous_state_record_id="interp:cbrs:mean-reversion",
            persistence_metric_record_ids=("metric:cbrs-persistence",),
        )


def test_confirmed_rediscovery_requires_catalyst_and_persistence_lineage() -> None:
    with pytest.raises(ContractViolation, match="requires catalyst and persistence"):
        assessment(
            state=RepricingState.PRICE_REDISCOVERY_CONFIRMED,
            previous_state=RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
            previous_state_record_id="interp:cbrs:local-equilibrium",
            catalyst_evidence_record_ids=(),
            persistence_metric_record_ids=("metric:cbrs-persistence",),
        )


def test_local_equilibrium_candidate_can_become_confirmed_with_lineage() -> None:
    item = assessment(
        state=RepricingState.PRICE_REDISCOVERY_CONFIRMED,
        previous_state=RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
        previous_state_record_id="interp:cbrs:local-equilibrium",
        persistence_metric_record_ids=("metric:cbrs-persistence",),
    )
    record = item.to_interpretation(
        record_id="interp:cbrs:rediscovery-confirmed",
        accepted_at=ACCEPTED,
    )
    assert record.interpretation_type == "repricing_state"
    assert record.statement["state"] == "price_rediscovery_confirmed"
    assert record.statement["previous_state"] == "local_equilibrium_candidate"
    assert record.statement["threshold_policy"] == "not_fixed_v0.1"


def test_lineage_cannot_reuse_same_record_across_classes() -> None:
    item = assessment(
        catalyst_evidence_record_ids=("metric:cbrs-relative-recovery",),
    )
    with pytest.raises(ContractViolation, match="cannot overlap"):
        _ = item.basis_record_ids


def test_materialization_preserves_interpretation_boundary() -> None:
    record = assessment().to_interpretation(
        record_id="interp:cbrs:mean-reversion",
        accepted_at=ACCEPTED,
    )
    assert record.interpretation_type == "repricing_state"
    assert record.method == "repricing_state_rule"
    assert record.statement["state"] == "relative_mean_reversion"
