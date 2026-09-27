from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.physical_saas.applicability import (
    PhysicalSaasApplicabilityAssessment,
    PhysicalSaasApplicabilityRating,
    PhysicalSaasEvidenceClass,
    classify_physical_saas_applicability,
)

UTC = timezone.utc
NOW = datetime(2026, 9, 27, 12, 30, tzinfo=UTC)


def classify(*, evidence_by_class=(), contradicting=()):
    return classify_physical_saas_applicability(
        subject_ref="company.fixture",
        evidence_by_class=evidence_by_class,
        contradicting_record_ids=contradicting,
        generated_at=NOW,
    )


def test_physical_plus_recurring_is_applicable() -> None:
    result = classify(
        evidence_by_class=(
            (PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.1",)),
            (PhysicalSaasEvidenceClass.RECURRING_SERVICE, ("fact.recurring.1",)),
        )
    )
    assert result.rating is PhysicalSaasApplicabilityRating.APPLICABLE
    assert result.downstream_allowed is True


def test_financial_recurring_revenue_can_support_recurring_side() -> None:
    result = classify(
        evidence_by_class=(
            (PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.1",)),
            (PhysicalSaasEvidenceClass.FINANCIAL_RECURRING_REVENUE, ("metric.arr.share",)),
        )
    )
    assert result.rating is PhysicalSaasApplicabilityRating.APPLICABLE


def test_physical_only_is_conditional_not_applicable() -> None:
    result = classify(
        evidence_by_class=((PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.1",)),)
    )
    assert result.rating is PhysicalSaasApplicabilityRating.CONDITIONAL
    assert result.downstream_allowed is False


def test_recurring_only_is_conditional_not_applicable() -> None:
    result = classify(
        evidence_by_class=((PhysicalSaasEvidenceClass.RECURRING_SERVICE, ("fact.recurring.1",)),)
    )
    assert result.rating is PhysicalSaasApplicabilityRating.CONDITIONAL


def test_no_evidence_is_unknown() -> None:
    result = classify()
    assert result.rating is PhysicalSaasApplicabilityRating.UNKNOWN
    assert result.basis_record_ids == ()


def test_contradiction_without_required_pair_is_not_applicable() -> None:
    result = classify(
        evidence_by_class=((PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.1",)),),
        contradicting=("evidence.no.recurring.1",),
    )
    assert result.rating is PhysicalSaasApplicabilityRating.NOT_APPLICABLE


def test_required_pair_plus_contradiction_is_conditional() -> None:
    result = classify(
        evidence_by_class=(
            (PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.1",)),
            (PhysicalSaasEvidenceClass.RECURRING_SERVICE, ("fact.recurring.1",)),
        ),
        contradicting=("evidence.counter.1",),
    )
    assert result.rating is PhysicalSaasApplicabilityRating.CONDITIONAL
    assert result.downstream_allowed is False


def test_duplicate_evidence_class_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="repeat an evidence class"):
        classify(
            evidence_by_class=(
                (PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.1",)),
                (PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.2",)),
            )
        )


def test_same_record_cannot_support_multiple_classes() -> None:
    with pytest.raises(ContractViolation, match="cannot be reused"):
        classify(
            evidence_by_class=(
                (PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.shared",)),
                (PhysicalSaasEvidenceClass.RECURRING_SERVICE, ("fact.shared",)),
            )
        )


def test_interpretation_preserves_lineage_and_guard_state() -> None:
    result = classify(
        evidence_by_class=(
            (PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT, ("fact.deploy.1",)),
            (PhysicalSaasEvidenceClass.RECURRING_SERVICE, ("fact.recurring.1",)),
        )
    )
    interpretation = result.to_interpretation(
        record_id="interpretation.physical_saas.fixture",
        accepted_at=NOW,
    )
    assert interpretation.interpretation_type == "physical_saas_applicability"
    assert interpretation.statement["rating"] == "applicable"
    assert interpretation.statement["downstream_allowed"] is True
    assert interpretation.basis_record_ids == ("fact.deploy.1", "fact.recurring.1")
