from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.catalyst_reaction_window import CatalystReactionWindow
from orderscope_local.contracts.catalyst_repricing_assessment import CatalystRepricingAssessment
from orderscope_local.contracts.catalyst_repricing_materialize import catalyst_repricing_to_interpretation
from orderscope_local.contracts.catalyst_repricing_types import (
    CatalystDirection,
    CatalystRepricingInterpretationType,
    ReactionDirection,
)
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.price_rediscovery_confirmation import PriceRediscoveryConfirmationAssessment


UTC = timezone.utc
START = datetime(2026, 9, 3, tzinfo=UTC)
END = datetime(2026, 9, 10, tzinfo=UTC)
GENERATED = datetime(2026, 9, 11, tzinfo=UTC)


def test_chpt_canary_confirms_rediscovery_only_with_multi_session_persistence() -> None:
    confirmation = PriceRediscoveryConfirmationAssessment(
        subject_ref="instrument:CHPT",
        observed_window_start=START,
        observed_window_end=END,
        catalyst_evidence_record_ids=("evidence:chpt-q2-results",),
        old_range_invalidation_metric_record_ids=("metric:chpt-old-range-invalidated",),
        retest_metric_record_ids=("metric:chpt-retest-held",),
        persistence_metric_record_ids=("metric:chpt-3d-persistence",),
        persistence_windows=(CatalystReactionWindow.REACTION_3D,),
        previous_state_record_id="interpretation:chpt-new-equilibrium",
        generated_at=GENERATED,
    )
    state = confirmation.to_repricing_state_assessment()
    assert state.state.value == "price_rediscovery_confirmed"
    assert state.previous_state.value == "new_equilibrium_candidate"


def test_tnon_canary_classifies_delayed_repricing_without_confirming_equilibrium() -> None:
    assessment = CatalystRepricingAssessment(
        interpretation_type=CatalystRepricingInterpretationType.DELAYED_REPRICING,
        subject_ref="instrument:TNON",
        catalyst_ref="event:tnon-note-repayment",
        catalyst_direction=CatalystDirection.POSITIVE,
        initial_reaction_direction=ReactionDirection.NEGATIVE,
        later_reaction_direction=ReactionDirection.POSITIVE,
        observed_window_start=datetime(2026, 9, 9, tzinfo=UTC),
        observed_window_end=datetime(2026, 9, 10, tzinfo=UTC),
        catalyst_evidence_record_ids=("evidence:tnon-note-repayment",),
        initial_reaction_metric_record_ids=("metric:tnon-session-close",),
        later_reaction_metric_record_ids=("metric:tnon-next-close",),
        generated_at=datetime(2026, 9, 10, 23, tzinfo=UTC),
    )
    interpretation = catalyst_repricing_to_interpretation(
        assessment,
        record_id="interpretation:tnon-delayed-repricing",
        accepted_at=datetime(2026, 9, 11, tzinfo=UTC),
    )
    assert interpretation.interpretation_type == "delayed_repricing"
    assert interpretation.statement["equilibrium_prediction"] == "none"


def test_microcap_single_session_spike_cannot_confirm_rediscovery() -> None:
    with pytest.raises(ContractViolation, match="3d or 5d persistence evidence"):
        PriceRediscoveryConfirmationAssessment(
            subject_ref="instrument:MICROCAP",
            observed_window_start=START,
            observed_window_end=END,
            catalyst_evidence_record_ids=("evidence:headline",),
            old_range_invalidation_metric_record_ids=("metric:gap",),
            retest_metric_record_ids=("metric:intraday-retest",),
            persistence_metric_record_ids=("metric:next-close",),
            persistence_windows=(CatalystReactionWindow.REACTION_NEXT_CLOSE,),
            previous_state_record_id="interpretation:microcap-new-equilibrium",
            generated_at=GENERATED,
        )


def test_tnon_like_divergence_without_later_alignment_cannot_be_delayed_repricing() -> None:
    with pytest.raises(ContractViolation, match="later reaction must align with catalyst direction"):
        CatalystRepricingAssessment(
            interpretation_type=CatalystRepricingInterpretationType.DELAYED_REPRICING,
            subject_ref="instrument:TNON",
            catalyst_ref="event:tnon-note-repayment",
            catalyst_direction=CatalystDirection.POSITIVE,
            initial_reaction_direction=ReactionDirection.NEGATIVE,
            later_reaction_direction=ReactionDirection.NEGATIVE,
            observed_window_start=datetime(2026, 9, 9, tzinfo=UTC),
            observed_window_end=datetime(2026, 9, 10, tzinfo=UTC),
            catalyst_evidence_record_ids=("evidence:tnon-note-repayment",),
            initial_reaction_metric_record_ids=("metric:tnon-session-close",),
            later_reaction_metric_record_ids=("metric:tnon-next-close",),
            generated_at=datetime(2026, 9, 10, 23, tzinfo=UTC),
        )
