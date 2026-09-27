from datetime import datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.physical_saas_financial_quality import (
    PhysicalSaasFinancialAssessmentType,
    PhysicalSaasFinancialInputs,
    PhysicalSaasFinancialQualityAssessment,
    PhysicalSaasFinancialRating,
    build_physical_saas_financial_metrics,
)

UTC = timezone.utc
AS_OF = datetime(2026, 9, 27, 0, 0, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 27, 1, 0, tzinfo=UTC)
WINDOW_START = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
WINDOW_END = datetime(2026, 9, 27, 0, 0, tzinfo=UTC)


def inputs(**overrides) -> PhysicalSaasFinancialInputs:
    values = dict(
        subject_ref="issuer.fixture",
        as_of=AS_OF,
        recurring_revenue=Decimal("80"),
        total_revenue=Decimal("100"),
        free_cash_flow=Decimal("15"),
        adjusted_ebitda=Decimal("20"),
        net_debt=Decimal("40"),
        prior_net_debt=Decimal("50"),
        recurring_revenue_record_ids=("fact.revenue.recurring", "fact.revenue.total"),
        cash_conversion_record_ids=("fact.cash.fcf", "fact.ebitda.adjusted"),
        leverage_record_ids=("fact.debt.net.current", "fact.debt.net.prior"),
    )
    values.update(overrides)
    return PhysicalSaasFinancialInputs(**values)


def assessment(**overrides) -> PhysicalSaasFinancialQualityAssessment:
    values = dict(
        assessment_type=PhysicalSaasFinancialAssessmentType.COMBINED_FINANCIAL_QUALITY,
        rating=PhysicalSaasFinancialRating.SUPPORT,
        subject_ref="issuer.fixture",
        observed_window_start=WINDOW_START,
        observed_window_end=WINDOW_END,
        recurring_revenue_metric_refs=("metric.recurring_share",),
        cash_conversion_metric_refs=("metric.cash_conversion",),
        leverage_metric_refs=("metric.net_leverage", "metric.net_debt_change"),
        generated_at=WINDOW_END,
    )
    values.update(overrides)
    return PhysicalSaasFinancialQualityAssessment(**values)


def test_builds_four_lineage_preserving_derived_metrics() -> None:
    metrics = build_physical_saas_financial_metrics(
        inputs(), record_id_prefix="metric.physical_saas.fixture", accepted_at=ACCEPTED
    )
    assert len(metrics) == 4
    by_name = {metric.metric_name: metric for metric in metrics}
    assert by_name["physical_saas.recurring_revenue_share"].value == "0.8"
    assert by_name["physical_saas.fcf_to_adjusted_ebitda"].value == "0.75"
    assert by_name["physical_saas.net_debt_to_adjusted_ebitda"].value == "2"
    assert by_name["physical_saas.net_debt_change"].value == "-10"


def test_metric_lineage_keeps_financial_evidence_classes_separate() -> None:
    metrics = build_physical_saas_financial_metrics(
        inputs(), record_id_prefix="metric.physical_saas.fixture", accepted_at=ACCEPTED
    )
    assert metrics[0].input_record_ids == ("fact.revenue.recurring", "fact.revenue.total")
    assert metrics[1].input_record_ids == ("fact.cash.fcf", "fact.ebitda.adjusted")
    assert metrics[2].input_record_ids == ("fact.debt.net.current", "fact.debt.net.prior")


def test_non_positive_revenue_or_ebitda_rejected() -> None:
    with pytest.raises(ContractViolation, match="total_revenue"):
        inputs(total_revenue=Decimal("0"))
    with pytest.raises(ContractViolation, match="adjusted_ebitda"):
        inputs(adjusted_ebitda=Decimal("0"))


def test_financial_evidence_references_cannot_be_reused_between_classes() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse references"):
        inputs(cash_conversion_record_ids=("fact.revenue.total", "fact.cash.fcf"))


def test_combined_support_requires_all_three_core_financial_classes() -> None:
    with pytest.raises(ContractViolation, match="at least 3"):
        assessment(leverage_metric_refs=())


def test_combined_partial_requires_two_core_financial_classes() -> None:
    item = assessment(
        rating=PhysicalSaasFinancialRating.PARTIAL,
        leverage_metric_refs=(),
    )
    assert item.rating is PhysicalSaasFinancialRating.PARTIAL
    with pytest.raises(ContractViolation, match="at least 2"):
        assessment(
            rating=PhysicalSaasFinancialRating.PARTIAL,
            cash_conversion_metric_refs=(),
            leverage_metric_refs=(),
        )


def test_type_specific_assessment_requires_its_financial_signal_class() -> None:
    with pytest.raises(ContractViolation, match="recurring-revenue"):
        assessment(
            assessment_type=PhysicalSaasFinancialAssessmentType.RECURRING_REVENUE_QUALITY,
            recurring_revenue_metric_refs=(),
            rating=PhysicalSaasFinancialRating.SUPPORT,
        )


def test_deployment_context_cannot_substitute_for_financial_evidence() -> None:
    with pytest.raises(ContractViolation, match="at least 3"):
        assessment(
            recurring_revenue_metric_refs=(),
            cash_conversion_metric_refs=(),
            leverage_metric_refs=(),
            deployment_context_refs=("metric.deployment.operational",),
        )


def test_unknown_and_contradict_ratings_are_fail_closed() -> None:
    unknown = assessment(
        rating=PhysicalSaasFinancialRating.UNKNOWN,
        recurring_revenue_metric_refs=(),
        cash_conversion_metric_refs=(),
        leverage_metric_refs=(),
    )
    assert unknown.rating is PhysicalSaasFinancialRating.UNKNOWN
    with pytest.raises(ContractViolation, match="requires contradicting evidence"):
        assessment(
            rating=PhysicalSaasFinancialRating.CONTRADICT,
            recurring_revenue_metric_refs=(),
            cash_conversion_metric_refs=(),
            leverage_metric_refs=(),
        )


def test_materializes_interpretation_without_claiming_revenue_from_deployment() -> None:
    item = assessment(deployment_context_refs=("metric.deployment.operational",))
    interpretation = item.to_interpretation(
        record_id="interpretation.physical_saas.financial.fixture",
        accepted_at=ACCEPTED,
    )
    assert interpretation.interpretation_type == "physical_saas.combined_financial_quality"
    assert interpretation.statement["rating"] == "SUPPORT"
    assert interpretation.statement["deployment_context_count"] == 1
    assert "revenue_recognized" not in interpretation.statement
