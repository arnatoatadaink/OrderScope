from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.physical_saas.applicability import (
    PhysicalSaasApplicabilityAssessment,
    PhysicalSaasApplicabilityRating,
    PhysicalSaasEvidenceClass,
)
from orderscope_local.physical_saas.canary import (
    PhysicalSaasCanaryDecision,
    PhysicalSaasCanaryLabel,
    PhysicalSaasCanaryObservation,
    PhysicalSaasCanarySignals,
    classify_physical_saas_canary,
    evaluate_physical_saas_canary,
)


NOW = datetime(2026, 9, 27, tzinfo=timezone.utc)


def applicability(rating=PhysicalSaasApplicabilityRating.APPLICABLE):
    if rating is PhysicalSaasApplicabilityRating.APPLICABLE:
        return PhysicalSaasApplicabilityAssessment(
            subject_ref="company:example",
            rating=rating,
            evidence_classes=(
                PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT,
                PhysicalSaasEvidenceClass.RECURRING_SERVICE,
            ),
            supporting_record_ids=("fact:deploy", "fact:recurring"),
            generated_at=NOW,
        )
    if rating is PhysicalSaasApplicabilityRating.UNKNOWN:
        return PhysicalSaasApplicabilityAssessment(
            subject_ref="company:example",
            rating=rating,
            evidence_classes=(),
            supporting_record_ids=(),
            generated_at=NOW,
        )
    return PhysicalSaasApplicabilityAssessment(
        subject_ref="company:example",
        rating=rating,
        evidence_classes=(PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT,),
        supporting_record_ids=("fact:deploy",),
        contradicting_record_ids=("fact:contradict",),
        generated_at=NOW,
    )


def test_support_requires_two_independent_support_classes():
    result = classify_physical_saas_canary(
        PhysicalSaasCanarySignals(
            applicability=applicability(),
            deployment_support_refs=("metric:deploy",),
            financial_support_refs=("metric:financial",),
        )
    )
    assert result.label is PhysicalSaasCanaryLabel.SUPPORT
    assert result.alert is False
    assert result.support_class_count == 2


def test_single_support_class_is_caution():
    result = classify_physical_saas_canary(
        PhysicalSaasCanarySignals(
            applicability=applicability(),
            deployment_support_refs=("metric:deploy",),
        )
    )
    assert result.label is PhysicalSaasCanaryLabel.CAUTION
    assert result.alert is True


def test_two_caution_classes_trigger_caution_alert():
    result = classify_physical_saas_canary(
        PhysicalSaasCanarySignals(
            applicability=applicability(),
            deployment_caution_refs=("interp:slippage",),
            integration_caution_refs=("interp:legacy-drag",),
        )
    )
    assert result.label is PhysicalSaasCanaryLabel.CAUTION
    assert result.alert is True


def test_no_directional_signals_is_unknown_without_alert():
    result = classify_physical_saas_canary(
        PhysicalSaasCanarySignals(applicability=applicability())
    )
    assert result.label is PhysicalSaasCanaryLabel.UNKNOWN
    assert result.alert is False


def test_applicability_guard_rejects_downstream_canary():
    result = classify_physical_saas_canary(
        PhysicalSaasCanarySignals(
            applicability=applicability(PhysicalSaasApplicabilityRating.UNKNOWN),
            deployment_support_refs=("metric:deploy",),
            financial_support_refs=("metric:financial",),
        )
    )
    assert result.label is PhysicalSaasCanaryLabel.REJECT
    assert result.alert is True


def test_signal_refs_cannot_be_reused_across_classes():
    with pytest.raises(ContractViolation):
        PhysicalSaasCanarySignals(
            applicability=applicability(),
            deployment_support_refs=("same:ref",),
            financial_support_refs=("same:ref",),
        )


def test_clean_held_out_match_accepts():
    observed = PhysicalSaasCanaryObservation(
        label=PhysicalSaasCanaryLabel.SUPPORT,
        alert=False,
        support_class_count=2,
        caution_class_count=0,
    )
    result = evaluate_physical_saas_canary(
        expected_label=PhysicalSaasCanaryLabel.SUPPORT,
        expected_alert=False,
        observed=observed,
    )
    assert result.decision is PhysicalSaasCanaryDecision.ACCEPT
    assert result.clean is True


def test_false_positive_is_review():
    observed = PhysicalSaasCanaryObservation(
        label=PhysicalSaasCanaryLabel.SUPPORT,
        alert=True,
        support_class_count=2,
        caution_class_count=0,
    )
    result = evaluate_physical_saas_canary(
        expected_label=PhysicalSaasCanaryLabel.SUPPORT,
        expected_alert=False,
        observed=observed,
    )
    assert result.false_positive_count == 1
    assert result.decision is PhysicalSaasCanaryDecision.REVIEW


def test_false_negative_rejects():
    observed = PhysicalSaasCanaryObservation(
        label=PhysicalSaasCanaryLabel.CAUTION,
        alert=False,
        support_class_count=1,
        caution_class_count=1,
    )
    result = evaluate_physical_saas_canary(
        expected_label=PhysicalSaasCanaryLabel.CAUTION,
        expected_alert=True,
        observed=observed,
    )
    assert result.false_negative_count == 1
    assert result.decision is PhysicalSaasCanaryDecision.REJECT


def test_label_mismatch_rejects_even_when_alert_matches():
    observed = PhysicalSaasCanaryObservation(
        label=PhysicalSaasCanaryLabel.CAUTION,
        alert=True,
        support_class_count=1,
        caution_class_count=1,
    )
    result = evaluate_physical_saas_canary(
        expected_label=PhysicalSaasCanaryLabel.REJECT,
        expected_alert=True,
        observed=observed,
    )
    assert result.label_mismatch_count == 1
    assert result.decision is PhysicalSaasCanaryDecision.REJECT
