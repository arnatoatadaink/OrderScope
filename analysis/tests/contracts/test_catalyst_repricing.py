from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.catalyst_repricing_assessment import CatalystRepricingAssessment
from orderscope_local.contracts.catalyst_repricing_materialize import catalyst_repricing_to_interpretation
from orderscope_local.contracts.catalyst_repricing_types import CatalystDirection, CatalystRepricingInterpretationType, ReactionDirection
from orderscope_local.contracts import ContractViolation

UTC = timezone.utc


def _base(**overrides):
    values = dict(
        interpretation_type=CatalystRepricingInterpretationType.CATALYST_PRICE_DIVERGENCE,
        subject_ref="issuer:TNON",
        catalyst_ref="event:TNON-note-repayment",
        catalyst_direction=CatalystDirection.POSITIVE,
        initial_reaction_direction=ReactionDirection.NEGATIVE,
        observed_window_start=datetime(2026, 9, 9, 12, 30, tzinfo=UTC),
        observed_window_end=datetime(2026, 9, 9, 20, 0, tzinfo=UTC),
        catalyst_evidence_record_ids=("evidence:repayment",),
        initial_reaction_metric_record_ids=("metric:session-close",),
        generated_at=datetime(2026, 9, 10, 21, 0, tzinfo=UTC),
    )
    values.update(overrides)
    return CatalystRepricingAssessment(**values)


def test_catalyst_price_divergence_accepts_opposite_initial_reaction() -> None:
    assessment = _base()
    assert assessment.interpretation_type is CatalystRepricingInterpretationType.CATALYST_PRICE_DIVERGENCE


def test_delayed_repricing_requires_later_alignment() -> None:
    assessment = _base(
        interpretation_type=CatalystRepricingInterpretationType.DELAYED_REPRICING,
        later_reaction_direction=ReactionDirection.POSITIVE,
        later_reaction_metric_record_ids=("metric:next-close",),
    )
    assert assessment.later_reaction_direction is ReactionDirection.POSITIVE


def test_delayed_repricing_rejects_later_reaction_against_catalyst() -> None:
    with pytest.raises(ContractViolation, match="later reaction must align"):
        _base(
            interpretation_type=CatalystRepricingInterpretationType.DELAYED_REPRICING,
            later_reaction_direction=ReactionDirection.NEGATIVE,
            later_reaction_metric_record_ids=("metric:next-close",),
        )


def test_materializes_without_equilibrium_prediction() -> None:
    assessment = _base(
        interpretation_type=CatalystRepricingInterpretationType.DELAYED_REPRICING,
        later_reaction_direction=ReactionDirection.POSITIVE,
        later_reaction_metric_record_ids=("metric:next-close",),
    )
    record = catalyst_repricing_to_interpretation(
        assessment,
        record_id="interpretation:TNON-delayed-repricing",
        accepted_at=datetime(2026, 9, 10, 21, 1, tzinfo=UTC),
    )
    assert record.interpretation_type == "delayed_repricing"
    assert record.statement["equilibrium_prediction"] == "none"
    assert record.basis_record_ids == ("evidence:repayment", "metric:session-close", "metric:next-close")
