"""UWBS-089 deployment-funnel Derived Metrics and slippage interpretation.

Only reconciled, source-grounded UWBS-087 deployment observations that are
COMPLETED EVENT_INCREMENT quantities belong in this calculation boundary.
Cumulative/point-in-time bases, plans, backlog, billing, ARR and revenue are
explicitly outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import (
    DerivedMetric,
    Interpretation,
    InterpretationAssertionKind,
)
from orderscope_local.contracts.physical_saas_deployment import (
    PhysicalSaasDeploymentMilestone,
    PhysicalSaasDeploymentObservation,
    PhysicalSaasDeploymentState,
    PhysicalSaasQuantityBasis,
)


class DeploymentSlippageType(StrEnum):
    NO_OBSERVED_SLIPPAGE = "no_observed_slippage"
    OBSERVED_SLIPPAGE = "observed_slippage"
    INCONSISTENT_FUNNEL = "inconsistent_funnel"


@dataclass(frozen=True, kw_only=True)
class DeploymentFunnelInput:
    record_id: str
    observation: PhysicalSaasDeploymentObservation

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ContractViolation("record_id must be canonical non-empty text")
        if not isinstance(self.observation, PhysicalSaasDeploymentObservation):
            raise ContractViolation("observation must be PhysicalSaasDeploymentObservation")


@dataclass(frozen=True, kw_only=True)
class DeploymentFunnelStage:
    milestone: PhysicalSaasDeploymentMilestone
    quantity: Decimal
    quantity_unit: str
    input_record_ids: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class DeploymentFunnelPair:
    upstream: DeploymentFunnelStage
    downstream: DeploymentFunnelStage

    @property
    def slippage_quantity(self) -> Decimal:
        return self.upstream.quantity - self.downstream.quantity

    @property
    def conversion_ratio(self) -> Decimal | None:
        if self.upstream.quantity == 0:
            return None
        return self.downstream.quantity / self.upstream.quantity

    @property
    def slippage_type(self) -> DeploymentSlippageType:
        if self.downstream.quantity > self.upstream.quantity:
            return DeploymentSlippageType.INCONSISTENT_FUNNEL
        if self.downstream.quantity < self.upstream.quantity:
            return DeploymentSlippageType.OBSERVED_SLIPPAGE
        return DeploymentSlippageType.NO_OBSERVED_SLIPPAGE


def aggregate_stage(
    inputs: tuple[DeploymentFunnelInput, ...],
    *,
    milestone: PhysicalSaasDeploymentMilestone,
) -> DeploymentFunnelStage:
    """Aggregate comparable completed event increments for one milestone."""

    if not isinstance(inputs, tuple) or not inputs:
        raise ContractViolation("inputs must be a non-empty tuple")
    if not isinstance(milestone, PhysicalSaasDeploymentMilestone):
        raise ContractViolation("milestone must be PhysicalSaasDeploymentMilestone")

    record_ids: list[str] = []
    quantities: list[Decimal] = []
    units: set[str] = set()

    for item in inputs:
        if not isinstance(item, DeploymentFunnelInput):
            raise ContractViolation("inputs must contain DeploymentFunnelInput")
        obs = item.observation
        if obs.milestone is not milestone:
            continue
        if obs.state is not PhysicalSaasDeploymentState.COMPLETED:
            raise ContractViolation("deployment funnel accepts completed observations only")
        if obs.quantity_basis is not PhysicalSaasQuantityBasis.EVENT_INCREMENT:
            raise ContractViolation("deployment funnel accepts event_increment quantities only")
        if obs.quantity is None or obs.quantity_unit is None:
            raise ContractViolation("deployment funnel requires explicit quantity and unit")
        record_ids.append(item.record_id)
        quantities.append(obs.quantity)
        units.add(obs.quantity_unit)

    if not record_ids:
        raise ContractViolation("no observations matched requested milestone")
    if len(record_ids) != len(set(record_ids)):
        raise ContractViolation("input record ids must be unique")
    if len(units) != 1:
        raise ContractViolation("deployment funnel stage quantities require one comparable unit")

    return DeploymentFunnelStage(
        milestone=milestone,
        quantity=sum(quantities, Decimal("0")),
        quantity_unit=next(iter(units)),
        input_record_ids=tuple(record_ids),
    )


def compare_stages(
    upstream: DeploymentFunnelStage,
    downstream: DeploymentFunnelStage,
) -> DeploymentFunnelPair:
    if not isinstance(upstream, DeploymentFunnelStage) or not isinstance(
        downstream, DeploymentFunnelStage
    ):
        raise ContractViolation("compare_stages requires DeploymentFunnelStage values")
    if upstream.quantity_unit != downstream.quantity_unit:
        raise ContractViolation("funnel stages must use the same quantity unit")
    if set(upstream.input_record_ids) & set(downstream.input_record_ids):
        raise ContractViolation("upstream/downstream lineage cannot reuse the same record")
    return DeploymentFunnelPair(upstream=upstream, downstream=downstream)


def materialize_pair(
    pair: DeploymentFunnelPair,
    *,
    subject_ref: str,
    accepted_at: datetime,
    metric_record_prefix: str,
    interpretation_record_id: str,
) -> tuple[DerivedMetric, ...] | tuple[DerivedMetric, DerivedMetric, Interpretation]:
    """Materialize deterministic metrics plus a non-causal slippage interpretation."""

    if accepted_at.tzinfo is None or accepted_at.utcoffset() != timedelta(0):
        raise ContractViolation("accepted_at must be normalized to UTC")
    if not subject_ref.strip() or not metric_record_prefix.strip() or not interpretation_record_id.strip():
        raise ContractViolation("record identifiers and subject_ref must be non-empty")

    basis_ids = pair.upstream.input_record_ids + pair.downstream.input_record_ids
    slippage = DerivedMetric(
        record_id=f"{metric_record_prefix}.slippage_quantity",
        schema_version="physical-saas-deployment-funnel-v0.1",
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=accepted_at,
        metric_name="physical_saas.deployment_slippage_quantity",
        value=float(pair.slippage_quantity),
        calculation_method="upstream_quantity_minus_downstream_quantity",
        method_version="uwbs-089-v0.1",
        as_of=accepted_at,
        input_record_ids=basis_ids,
        unit=pair.upstream.quantity_unit,
    )

    metrics: list[DerivedMetric] = [slippage]
    if pair.conversion_ratio is not None:
        metrics.append(
            DerivedMetric(
                record_id=f"{metric_record_prefix}.conversion_ratio",
                schema_version="physical-saas-deployment-funnel-v0.1",
                subject_ref=subject_ref,
                accepted_at=accepted_at,
                created_at=accepted_at,
                metric_name="physical_saas.deployment_conversion_ratio",
                value=float(pair.conversion_ratio),
                calculation_method="downstream_quantity_divided_by_upstream_quantity",
                method_version="uwbs-089-v0.1",
                as_of=accepted_at,
                input_record_ids=basis_ids,
                unit="ratio",
            )
        )

    interpretation = Interpretation(
        record_id=interpretation_record_id,
        schema_version="physical-saas-deployment-slippage-interpretation-v0.1",
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=accepted_at,
        interpretation_type=f"physical_saas.{pair.slippage_type.value}",
        statement={
            "upstream_milestone": pair.upstream.milestone.value,
            "downstream_milestone": pair.downstream.milestone.value,
            "slippage_type": pair.slippage_type.value,
        },
        basis_record_ids=tuple(metric.record_id for metric in metrics),
        method="deployment_funnel_slippage_rule",
        method_version="uwbs-089-v0.1",
        assertion_kind=InterpretationAssertionKind.ASSESSMENT,
    )
    return (*metrics, interpretation)
