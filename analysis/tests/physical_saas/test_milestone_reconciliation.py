from datetime import date, datetime, timezone
from decimal import Decimal

from orderscope_local.contracts import (
    ContentHash,
    PhysicalSaasDeploymentMilestone,
    PhysicalSaasDeploymentObservation,
    PhysicalSaasDeploymentState,
    PhysicalSaasQuantityBasis,
    Provenance,
    SourceReference,
    SourceTimestamp,
)
from orderscope_local.physical_saas.milestone_reconciliation import (
    MilestoneReconciliationStatus,
    reconcile_milestones,
)

UTC = timezone.utc
DAY = SourceTimestamp.date_only(date(2026, 9, 27))


def provenance(source: str, accepted_hour: int = 3) -> Provenance:
    accepted = datetime(2026, 9, 27, accepted_hour, 0, tzinfo=UTC)
    return Provenance(
        source_ref=SourceReference(source),
        content_hash=ContentHash(("a" if accepted_hour == 3 else "b") * 64),
        retrieved_at=accepted,
        available_at=accepted,
        accepted_at=accepted,
        event_time=DAY,
    )


def obs(**overrides) -> PhysicalSaasDeploymentObservation:
    prov = overrides.pop("provenance", provenance("official:fixture:1"))
    values = dict(
        subject_ref="company.fixture",
        milestone=PhysicalSaasDeploymentMilestone.INSTALLED,
        state=PhysicalSaasDeploymentState.COMPLETED,
        accepted_at=prov.accepted_at,
        provenance=prov,
        effective_start=DAY,
        deployment_ref="deployment.fixture.1",
        customer_ref="customer.fixture",
        site_ref="site.fixture",
        product_ref="product.fixture",
        quantity=Decimal("100"),
        quantity_unit="devices",
        quantity_basis=PhysicalSaasQuantityBasis.EVENT_INCREMENT,
    )
    values.update(overrides)
    return PhysicalSaasDeploymentObservation(**values)


def test_identical_same_source_assertion_is_duplicate() -> None:
    result = reconcile_milestones(obs(), obs())
    assert result.status is MilestoneReconciliationStatus.DUPLICATE
    assert result.conflict_fields == ()


def test_independent_sources_with_same_normalized_assertion_are_consistent() -> None:
    left = obs()
    right = obs(provenance=provenance("official:fixture:2", 4))
    result = reconcile_milestones(left, right)
    assert result.status is MilestoneReconciliationStatus.CONSISTENT
    assert result.conflict_fields == ()


def test_same_milestone_quantity_difference_is_explicit_conflict() -> None:
    result = reconcile_milestones(obs(), obs(quantity=Decimal("110")))
    assert result.status is MilestoneReconciliationStatus.CONFLICT
    assert result.conflict_fields == ("quantity",)


def test_same_milestone_state_difference_is_explicit_conflict() -> None:
    result = reconcile_milestones(
        obs(), obs(state=PhysicalSaasDeploymentState.IN_PROGRESS)
    )
    assert result.status is MilestoneReconciliationStatus.CONFLICT
    assert "state" in result.conflict_fields


def test_cumulative_base_is_not_equivalent_to_event_increment() -> None:
    result = reconcile_milestones(
        obs(), obs(quantity_basis=PhysicalSaasQuantityBasis.CUMULATIVE_BASE)
    )
    assert result.status is MilestoneReconciliationStatus.CONFLICT
    assert "quantity_basis" in result.conflict_fields


def test_different_milestones_are_not_forced_into_conflict() -> None:
    result = reconcile_milestones(
        obs(), obs(milestone=PhysicalSaasDeploymentMilestone.ACTIVATED)
    )
    assert result.status is MilestoneReconciliationStatus.CONSISTENT


def test_different_deployments_are_not_forced_into_conflict() -> None:
    result = reconcile_milestones(obs(), obs(deployment_ref="deployment.fixture.2"))
    assert result.status is MilestoneReconciliationStatus.CONSISTENT


def test_customer_site_pair_can_anchor_identity_without_deployment_ref() -> None:
    left = obs(deployment_ref=None)
    right = obs(deployment_ref=None, quantity=Decimal("101"))
    result = reconcile_milestones(left, right)
    assert result.status is MilestoneReconciliationStatus.CONFLICT
    assert result.conflict_fields == ("quantity",)


def test_weak_identity_does_not_create_false_conflict() -> None:
    left = obs(deployment_ref=None, site_ref=None)
    right = obs(deployment_ref=None, site_ref=None, quantity=Decimal("999"))
    result = reconcile_milestones(left, right)
    assert result.status is MilestoneReconciliationStatus.INSUFFICIENT_IDENTITY
    assert result.conflict_fields == ()
