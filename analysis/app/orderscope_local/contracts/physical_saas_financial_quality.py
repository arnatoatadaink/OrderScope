"""UWBS-090 recurring-revenue quality / cash-conversion / deleveraging model.

This boundary keeps financial quality separate from physical deployment Facts.
Deployment evidence may be contextual, but it cannot substitute for recurring-
revenue, cash-flow, or leverage evidence and it cannot establish revenue
recognition by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import DerivedMetric, Interpretation, InterpretationAssertionKind


class PhysicalSaasFinancialAssessmentType(StrEnum):
    RECURRING_REVENUE_QUALITY = "recurring_revenue_quality"
    CASH_CONVERSION_QUALITY = "cash_conversion_quality"
    DELEVERAGING_PROGRESS = "deleveraging_progress"
    COMBINED_FINANCIAL_QUALITY = "combined_financial_quality"


class PhysicalSaasFinancialRating(StrEnum):
    SUPPORT = "SUPPORT"
    PARTIAL = "PARTIAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, kw_only=True)
class PhysicalSaasFinancialInputs:
    subject_ref: str
    as_of: datetime
    recurring_revenue: Decimal
    total_revenue: Decimal
    free_cash_flow: Decimal
    adjusted_ebitda: Decimal
    net_debt: Decimal
    prior_net_debt: Decimal
    recurring_revenue_record_ids: tuple[str, ...]
    cash_conversion_record_ids: tuple[str, ...]
    leverage_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _canonical(self.subject_ref, "subject_ref")
        _utc(self.as_of, "as_of")
        for value, field in (
            (self.recurring_revenue, "recurring_revenue"),
            (self.total_revenue, "total_revenue"),
            (self.free_cash_flow, "free_cash_flow"),
            (self.adjusted_ebitda, "adjusted_ebitda"),
            (self.net_debt, "net_debt"),
            (self.prior_net_debt, "prior_net_debt"),
        ):
            _decimal(value, field)
        if self.total_revenue <= 0:
            raise ContractViolation("total_revenue must be positive")
        if self.adjusted_ebitda <= 0:
            raise ContractViolation("adjusted_ebitda must be positive for ratio construction")
        for values, field in (
            (self.recurring_revenue_record_ids, "recurring_revenue_record_ids"),
            (self.cash_conversion_record_ids, "cash_conversion_record_ids"),
            (self.leverage_record_ids, "leverage_record_ids"),
        ):
            _refs(values, field, required=True)
        _disjoint(
            self.recurring_revenue_record_ids,
            self.cash_conversion_record_ids,
            self.leverage_record_ids,
        )

    @property
    def all_record_ids(self) -> tuple[str, ...]:
        return (
            self.recurring_revenue_record_ids
            + self.cash_conversion_record_ids
            + self.leverage_record_ids
        )


def build_physical_saas_financial_metrics(
    inputs: PhysicalSaasFinancialInputs,
    *,
    record_id_prefix: str,
    accepted_at: datetime,
) -> tuple[DerivedMetric, ...]:
    if not isinstance(inputs, PhysicalSaasFinancialInputs):
        raise TypeError("inputs must be PhysicalSaasFinancialInputs")
    _canonical(record_id_prefix, "record_id_prefix")
    _utc(accepted_at, "accepted_at")
    if accepted_at < inputs.as_of:
        raise ContractViolation("accepted_at cannot precede metric as_of")

    recurring_share = inputs.recurring_revenue / inputs.total_revenue
    cash_conversion = inputs.free_cash_flow / inputs.adjusted_ebitda
    net_leverage = inputs.net_debt / inputs.adjusted_ebitda
    net_debt_change = inputs.net_debt - inputs.prior_net_debt

    return (
        _metric(
            record_id=f"{record_id_prefix}.recurring_revenue_share",
            subject_ref=inputs.subject_ref,
            accepted_at=accepted_at,
            as_of=inputs.as_of,
            metric_name="physical_saas.recurring_revenue_share",
            value=recurring_share,
            unit="ratio",
            method="recurring_revenue_div_total_revenue",
            inputs=inputs.recurring_revenue_record_ids,
        ),
        _metric(
            record_id=f"{record_id_prefix}.cash_conversion",
            subject_ref=inputs.subject_ref,
            accepted_at=accepted_at,
            as_of=inputs.as_of,
            metric_name="physical_saas.fcf_to_adjusted_ebitda",
            value=cash_conversion,
            unit="ratio",
            method="free_cash_flow_div_adjusted_ebitda",
            inputs=inputs.cash_conversion_record_ids,
        ),
        _metric(
            record_id=f"{record_id_prefix}.net_leverage",
            subject_ref=inputs.subject_ref,
            accepted_at=accepted_at,
            as_of=inputs.as_of,
            metric_name="physical_saas.net_debt_to_adjusted_ebitda",
            value=net_leverage,
            unit="ratio",
            method="net_debt_div_adjusted_ebitda",
            inputs=inputs.leverage_record_ids,
        ),
        _metric(
            record_id=f"{record_id_prefix}.net_debt_change",
            subject_ref=inputs.subject_ref,
            accepted_at=accepted_at,
            as_of=inputs.as_of,
            metric_name="physical_saas.net_debt_change",
            value=net_debt_change,
            unit="currency_source_unit",
            method="current_net_debt_minus_prior_net_debt",
            inputs=inputs.leverage_record_ids,
        ),
    )


@dataclass(frozen=True, kw_only=True)
class PhysicalSaasFinancialQualityAssessment:
    assessment_type: PhysicalSaasFinancialAssessmentType
    rating: PhysicalSaasFinancialRating
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    recurring_revenue_metric_refs: tuple[str, ...] = ()
    cash_conversion_metric_refs: tuple[str, ...] = ()
    leverage_metric_refs: tuple[str, ...] = ()
    deployment_context_refs: tuple[str, ...] = ()
    contradicting_evidence_refs: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "physical-saas-financial-quality-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.assessment_type, PhysicalSaasFinancialAssessmentType):
            raise ContractViolation("assessment_type must be PhysicalSaasFinancialAssessmentType")
        if not isinstance(self.rating, PhysicalSaasFinancialRating):
            raise ContractViolation("rating must be PhysicalSaasFinancialRating")
        _canonical(self.subject_ref, "subject_ref")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed window end")
        _canonical(self.method_version, "method_version")

        groups = (
            (self.recurring_revenue_metric_refs, "recurring_revenue_metric_refs"),
            (self.cash_conversion_metric_refs, "cash_conversion_metric_refs"),
            (self.leverage_metric_refs, "leverage_metric_refs"),
            (self.deployment_context_refs, "deployment_context_refs"),
            (self.contradicting_evidence_refs, "contradicting_evidence_refs"),
        )
        for values, field in groups:
            _refs(values, field)
        _disjoint(*(values for values, _ in groups))

        core_groups = sum(
            bool(values)
            for values in (
                self.recurring_revenue_metric_refs,
                self.cash_conversion_metric_refs,
                self.leverage_metric_refs,
            )
        )
        if self.rating is PhysicalSaasFinancialRating.UNKNOWN:
            if core_groups or self.contradicting_evidence_refs:
                raise ContractViolation("UNKNOWN assessment cannot carry directional financial evidence")
            return
        if self.rating is PhysicalSaasFinancialRating.CONTRADICT:
            if not self.contradicting_evidence_refs:
                raise ContractViolation("CONTRADICT assessment requires contradicting evidence")
            return

        if self.assessment_type is PhysicalSaasFinancialAssessmentType.RECURRING_REVENUE_QUALITY:
            if not self.recurring_revenue_metric_refs:
                raise ContractViolation("recurring-revenue assessment requires recurring-revenue metrics")
        elif self.assessment_type is PhysicalSaasFinancialAssessmentType.CASH_CONVERSION_QUALITY:
            if not self.cash_conversion_metric_refs:
                raise ContractViolation("cash-conversion assessment requires cash-conversion metrics")
        elif self.assessment_type is PhysicalSaasFinancialAssessmentType.DELEVERAGING_PROGRESS:
            if not self.leverage_metric_refs:
                raise ContractViolation("deleveraging assessment requires leverage metrics")
        elif self.assessment_type is PhysicalSaasFinancialAssessmentType.COMBINED_FINANCIAL_QUALITY:
            required = 3 if self.rating is PhysicalSaasFinancialRating.SUPPORT else 2
            if core_groups < required:
                raise ContractViolation(
                    f"combined financial quality {self.rating.value} requires at least {required} independent core classes"
                )

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.recurring_revenue_metric_refs
            + self.cash_conversion_metric_refs
            + self.leverage_metric_refs
            + self.deployment_context_refs
            + self.contradicting_evidence_refs
        )

    def to_interpretation(self, *, record_id: str, accepted_at: datetime) -> Interpretation:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        if not self.basis_record_ids:
            raise ContractViolation("Fact Store Interpretation requires evidence lineage")
        return Interpretation(
            record_id=record_id,
            schema_version="physical-saas-financial-quality-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            interpretation_type=f"physical_saas.{self.assessment_type.value}",
            statement={
                "rating": self.rating.value,
                "recurring_revenue_signal_count": len(self.recurring_revenue_metric_refs),
                "cash_conversion_signal_count": len(self.cash_conversion_metric_refs),
                "leverage_signal_count": len(self.leverage_metric_refs),
                "deployment_context_count": len(self.deployment_context_refs),
                "contradicting_count": len(self.contradicting_evidence_refs),
            },
            basis_record_ids=self.basis_record_ids,
            method="physical_saas_financial_quality_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )


def _metric(
    *,
    record_id: str,
    subject_ref: str,
    accepted_at: datetime,
    as_of: datetime,
    metric_name: str,
    value: Decimal,
    unit: str,
    method: str,
    inputs: tuple[str, ...],
) -> DerivedMetric:
    return DerivedMetric(
        record_id=record_id,
        schema_version="physical-saas-financial-metric-v0.1",
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=as_of,
        metric_name=metric_name,
        value=str(value),
        calculation_method=method,
        method_version="physical-saas-financial-metric-v0.1",
        as_of=as_of,
        input_record_ids=inputs,
        unit=unit,
    )


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _decimal(value: Decimal, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Decimal) or not value.is_finite():
        raise ContractViolation(f"{field} must be a finite Decimal")


def _refs(values: tuple[str, ...], field: str, *, required: bool = False) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if required and not values:
        raise ContractViolation(f"{field} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        _canonical(value, field)


def _disjoint(*groups: tuple[str, ...]) -> None:
    sets = [set(group) for group in groups]
    for index, left in enumerate(sets):
        for right in sets[index + 1 :]:
            if left & right:
                raise ContractViolation("financial evidence classes cannot reuse references")
