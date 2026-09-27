from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.catalyst_reaction_window import CatalystReactionWindow
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.price_rediscovery_confirmation import PriceRediscoveryConfirmationAssessment
from orderscope_local.contracts.repricing_state import RepricingState


def _assessment(**overrides):
    values = dict(
        subject_ref="ticker:CHPT",
        observed_window_start=datetime(2026, 9, 3, tzinfo=timezone.utc),
        observed_window_end=datetime(2026, 9, 10, tzinfo=timezone.utc),
        catalyst_evidence_record_ids=("ev:catalyst",),
        old_range_invalidation_metric_record_ids=("metric:old-range",),
        retest_metric_record_ids=("metric:retest",),
        persistence_metric_record_ids=("metric:3d",),
        persistence_windows=(CatalystReactionWindow.REACTION_3D,),
        previous_state_record_id="interp:new-equilibrium",
        generated_at=datetime(2026, 9, 10, 1, tzinfo=timezone.utc),
    )
    values.update(overrides)
    return PriceRediscoveryConfirmationAssessment(**values)


def test_confirmed_rediscovery_requires_multi_session_persistence() -> None:
    assessment = _assessment()
    state = assessment.to_repricing_state_assessment()
    assert state.state is RepricingState.PRICE_REDISCOVERY_CONFIRMED
    assert state.previous_state is RepricingState.NEW_EQUILIBRIUM_CANDIDATE
    assert state.catalyst_evidence_record_ids == ("ev:catalyst",)
    assert state.persistence_metric_record_ids == ("metric:3d",)


def test_single_session_persistence_cannot_confirm_rediscovery() -> None:
    with pytest.raises(ContractViolation, match="3d or 5d"):
        _assessment(persistence_windows=(CatalystReactionWindow.REACTION_SESSION_CLOSE,))


def test_confirmation_requires_independent_lineage_classes() -> None:
    with pytest.raises(ContractViolation, match="cannot overlap"):
        _assessment(retest_metric_record_ids=("metric:old-range",))


def test_confirmation_requires_retest_and_old_range_invalidation() -> None:
    with pytest.raises(ContractViolation, match="retest_metric_record_ids"):
        _assessment(retest_metric_record_ids=())
    with pytest.raises(ContractViolation, match="old_range_invalidation_metric_record_ids"):
        _assessment(old_range_invalidation_metric_record_ids=())
