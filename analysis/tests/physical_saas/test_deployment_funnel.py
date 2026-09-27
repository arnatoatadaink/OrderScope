from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, Provenance, SourceReference, SourceTimestamp
from orderscope_local.contracts.fact_store import DerivedMetric, Interpretation
from orderscope_local.contracts.physical_saas_deployment import (
    PhysicalSaasDeploymentMilestone,
    PhysicalSaasDeploymentObservation,
    PhysicalSaasDeploymentState,
    PhysicalSaasQuantityBasis,
)
from orderscope_local.physical_saas.deployment_funnel import (
    DeploymentFunnelInput,
    DeploymentSlippageType,
    aggregate_stage,
    compare_stages,
    materialize_pair,
)

UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
DAY = SourceTimestamp.date_only(date(2026, 9, 27))


def provenance(seed: str) -> Provenance:
    return Provenance(
        source_ref=SourceReference(f"official:physical-saas:{seed}"),
        content_hash=ContentHash(seed[0] * 64),
        retrieved_at=ACCEPTED,
        available_at=ACCEPTED,
        accepted_at=ACCEPTED,
        event_time=DAY,
    )


def observation(
    milestone: PhysicalSaasDeploymentMilestone,
    quantity: str,
    *,
    seed: str,
    state: PhysicalSaasDeploymentState = PhysicalSaasDeploymentState.COMPLETED,
    basis: PhysicalSaasQuantityBasis = PhysicalSaasQuantityBasis.EVENT_INCREMENT,
    unit: str = "device",
) -> PhysicalSaasDeploymentObservation:
    return PhysicalSaasDeploymentObservation(
        subject_ref="issuer.fixture",
        milestone=milestone,
        state=state,
        accepted_at=ACCEPTED,
        provenance=provenance(seed),
        effective_start=DAY,
        deployment_ref=f"deployment.{seed}",
        quantity=Decimal(quantity),
        quantity_unit=unit,
        quantity_basis=basis,
    )


def item(record_id: str, milestone: PhysicalSaasDeploymentMilestone, quantity: str, seed: str) -> DeploymentFunnelInput:
    return DeploymentFunnelInput(
        record_id=record_id,
        observation=observation(milestone, quantity, seed=seed),
    )


def test_aggregate_stage_sums_comparable_completed_event_increments() -> None:
    stage = aggregate_stage(
        (
            item("fact.shipped.1", PhysicalSaasDeploymentMilestone.SHIPPED, "10", "a"),
            item("fact.shipped.2", PhysicalSaasDeploymentMilestone.SHIPPED, "15", "b"),
        ),
        milestone=PhysicalSaasDeploymentMilestone.SHIPPED,
    )
    assert stage.quantity == Decimal("25")
    assert stage.quantity_unit == "device"
    assert stage.input_record_ids == ("fact.shipped.1", "fact.shipped.2")


def test_aggregate_stage_rejects_planned_or_in_progress_values() -> None:
    planned = DeploymentFunnelInput(
        record_id="fact.shipped.planned",
        observation=observation(
            PhysicalSaasDeploymentMilestone.SHIPPED,
            "10",
            seed="c",
            state=PhysicalSaasDeploymentState.PLANNED,
        ),
    )
    with pytest.raises(ContractViolation, match="completed"):
        aggregate_stage((planned,), milestone=PhysicalSaasDeploymentMilestone.SHIPPED)


def test_aggregate_stage_rejects_cumulative_base() -> None:
    cumulative = DeploymentFunnelInput(
        record_id="fact.installed.cumulative",
        observation=observation(
            PhysicalSaasDeploymentMilestone.INSTALLED,
            "1000",
            seed="d",
            basis=PhysicalSaasQuantityBasis.CUMULATIVE_BASE,
        ),
    )
    with pytest.raises(ContractViolation, match="event_increment"):
        aggregate_stage((cumulative,), milestone=PhysicalSaasDeploymentMilestone.INSTALLED)


def test_aggregate_stage_rejects_mixed_units() -> None:
    left = item("fact.shipped.device", PhysicalSaasDeploymentMilestone.SHIPPED, "10", "e")
    right = DeploymentFunnelInput(
        record_id="fact.shipped.site",
        observation=observation(
            PhysicalSaasDeploymentMilestone.SHIPPED,
            "2",
            seed="f",
            unit="site",
        ),
    )
    with pytest.raises(ContractViolation, match="one comparable unit"):
        aggregate_stage((left, right), milestone=PhysicalSaasDeploymentMilestone.SHIPPED)


def test_compare_stages_computes_positive_slippage() -> None:
    upstream = aggregate_stage(
        (item("fact.shipped.10", PhysicalSaasDeploymentMilestone.SHIPPED, "100", "1"),),
        milestone=PhysicalSaasDeploymentMilestone.SHIPPED,
    )
    downstream = aggregate_stage(
        (item("fact.activated.10", PhysicalSaasDeploymentMilestone.ACTIVATED, "80", "2"),),
        milestone=PhysicalSaasDeploymentMilestone.ACTIVATED,
    )
    pair = compare_stages(upstream, downstream)
    assert pair.slippage_quantity == Decimal("20")
    assert pair.conversion_ratio == Decimal("0.8")
    assert pair.slippage_type is DeploymentSlippageType.OBSERVED_SLIPPAGE


def test_equal_stage_quantity_has_no_observed_slippage() -> None:
    upstream = aggregate_stage(
        (item("fact.shipped.eq", PhysicalSaasDeploymentMilestone.SHIPPED, "40", "3"),),
        milestone=PhysicalSaasDeploymentMilestone.SHIPPED,
    )
    downstream = aggregate_stage(
        (item("fact.operational.eq", PhysicalSaasDeploymentMilestone.OPERATIONAL, "40", "4"),),
        milestone=PhysicalSaasDeploymentMilestone.OPERATIONAL,
    )
    assert compare_stages(upstream, downstream).slippage_type is DeploymentSlippageType.NO_OBSERVED_SLIPPAGE


def test_downstream_greater_than_upstream_is_inconsistent_not_negative_slippage() -> None:
    upstream = aggregate_stage(
        (item("fact.shipped.low", PhysicalSaasDeploymentMilestone.SHIPPED, "10", "5"),),
        milestone=PhysicalSaasDeploymentMilestone.SHIPPED,
    )
    downstream = aggregate_stage(
        (item("fact.activated.high", PhysicalSaasDeploymentMilestone.ACTIVATED, "12", "6"),),
        milestone=PhysicalSaasDeploymentMilestone.ACTIVATED,
    )
    assert compare_stages(upstream, downstream).slippage_type is DeploymentSlippageType.INCONSISTENT_FUNNEL


def test_compare_stages_rejects_mixed_units() -> None:
    upstream = aggregate_stage(
        (item("fact.shipped.u", PhysicalSaasDeploymentMilestone.SHIPPED, "10", "7"),),
        milestone=PhysicalSaasDeploymentMilestone.SHIPPED,
    )
    downstream = aggregate_stage(
        (
            DeploymentFunnelInput(
                record_id="fact.activated.u",
                observation=observation(
                    PhysicalSaasDeploymentMilestone.ACTIVATED,
                    "8",
                    seed="8",
                    unit="site",
                ),
            ),
        ),
        milestone=PhysicalSaasDeploymentMilestone.ACTIVATED,
    )
    with pytest.raises(ContractViolation, match="same quantity unit"):
        compare_stages(upstream, downstream)


def test_zero_upstream_omits_conversion_ratio_but_preserves_slippage_metric() -> None:
    upstream = aggregate_stage(
        (item("fact.shipped.zero", PhysicalSaasDeploymentMilestone.SHIPPED, "0", "9"),),
        milestone=PhysicalSaasDeploymentMilestone.SHIPPED,
    )
    downstream = aggregate_stage(
        (item("fact.activated.zero", PhysicalSaasDeploymentMilestone.ACTIVATED, "0", "a"),),
        milestone=PhysicalSaasDeploymentMilestone.ACTIVATED,
    )
    records = materialize_pair(
        compare_stages(upstream, downstream),
        subject_ref="issuer.fixture",
        accepted_at=ACCEPTED,
        metric_record_prefix="metric.funnel.zero",
        interpretation_record_id="interpretation.funnel.zero",
    )
    assert len(records) == 2
    assert isinstance(records[0], DerivedMetric)
    assert isinstance(records[1], Interpretation)


def test_materialization_keeps_derived_metric_and_interpretation_layers_separate() -> None:
    upstream = aggregate_stage(
        (item("fact.shipped.m", PhysicalSaasDeploymentMilestone.SHIPPED, "100", "b"),),
        milestone=PhysicalSaasDeploymentMilestone.SHIPPED,
    )
    downstream = aggregate_stage(
        (item("fact.accepted.m", PhysicalSaasDeploymentMilestone.CUSTOMER_ACCEPTED, "75", "c"),),
        milestone=PhysicalSaasDeploymentMilestone.CUSTOMER_ACCEPTED,
    )
    records = materialize_pair(
        compare_stages(upstream, downstream),
        subject_ref="issuer.fixture",
        accepted_at=ACCEPTED,
        metric_record_prefix="metric.funnel.fixture",
        interpretation_record_id="interpretation.funnel.fixture",
    )
    assert len(records) == 3
    assert isinstance(records[0], DerivedMetric)
    assert isinstance(records[1], DerivedMetric)
    assert isinstance(records[2], Interpretation)
    assert records[0].metric_name == "physical_saas.deployment_slippage_quantity"
    assert records[1].metric_name == "physical_saas.deployment_conversion_ratio"
    assert records[2].interpretation_type == "physical_saas.observed_slippage"
    assert records[2].basis_record_ids == (records[0].record_id, records[1].record_id)
