"""FactStore materialization for UWBS-021 catalyst repricing assessments."""
from datetime import datetime, timedelta

from .catalyst_repricing_assessment import CatalystRepricingAssessment
from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


def catalyst_repricing_to_interpretation(
    assessment: CatalystRepricingAssessment,
    *,
    record_id: str,
    accepted_at: datetime,
) -> Interpretation:
    if accepted_at.tzinfo is None or accepted_at.utcoffset() != timedelta(0):
        raise ContractViolation("accepted_at must be normalized to UTC")
    if accepted_at < assessment.generated_at:
        raise ContractViolation("accepted_at cannot precede generated_at")
    return Interpretation(
        record_id=record_id,
        schema_version="catalyst-repricing-interpretation-v0.1",
        subject_ref=assessment.subject_ref,
        accepted_at=accepted_at,
        created_at=assessment.generated_at,
        interpretation_type=assessment.interpretation_type.value,
        statement={
            "catalyst_ref": assessment.catalyst_ref,
            "catalyst_direction": assessment.catalyst_direction.value,
            "initial_reaction_direction": assessment.initial_reaction_direction.value,
            "later_reaction_direction": assessment.later_reaction_direction.value if assessment.later_reaction_direction else None,
            "threshold_policy": "not_fixed_v0.1",
            "equilibrium_prediction": "none",
        },
        basis_record_ids=assessment.basis_record_ids,
        method="catalyst_repricing_rule",
        method_version=assessment.method_version,
        assertion_kind=InterpretationAssertionKind.ASSESSMENT,
    )
