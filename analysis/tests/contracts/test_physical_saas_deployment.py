from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContractViolation,
    PhysicalSaasDeploymentMilestone,
    PhysicalSaasDeploymentObservation,
    PhysicalSaasDeploymentState,
    PhysicalSaasQuantityBasis,
    Provenance,
    SourceReference,
    SourceTimestamp,
)

UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 10, 0, tzinfo=UTC)
START = SourceTimestamp.date_only(date(2026, 9, 26))


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("official:physical-saas:fixture"),
        content_hash=ContentHash("d" * 64),
        retrieved_at=ACCEPTED,
        available_at=ACCEPTED,
        accepted_at=ACCEPTED,
        event_time=START,
    )


def observation(**overrides) -> PhysicalSaasDeploymentObservation:
    values = dict(
        subject_ref="issuer.physical-saas.fixture",
        milestone=PhysicalSaasDeploymentMilestone.INSTALLED,
        state=PhysicalSaasDeploymentState.COMPLETED,
        accepted_at=ACCEPTED,
        provenance=provenance(),
        effective_start=START,
        deployment_ref="deployment.fixture.1",
        customer_ref="customer.fixture",
        product_ref="product.fixture",
        quantity=Decimal("125"),
        quantity_unit="devices",
        quantity_basis=PhysicalSaasQuantityBasis.EVENT_INCREMENT,
    )
    values.update(overrides)
    return PhysicalSaasDeploymentObservation(**values)


def test_completed_installation_materializes_as_fact() -> None:
    fact = observation().to_fact(
        record_id="fact.physical-saas.fixture",
        evidence_record_ids=("evidence.official.1",),
    )

    assert fact.fact_type == "physical_saas_deployment.installed"
    assert fact.value["state"] == "completed"
    assert fact.value["quantity"] == "125"
    assert fact.value["quantity_basis"] == "event_increment"


def test_planned_activation_is_not_silently_promoted_to_completed() -> None:
    item = observation(
        milestone=PhysicalSaasDeploymentMilestone.ACTIVATED,
        state=PhysicalSaasDeploymentState.PLANNED,
    )
    assert item.state is PhysicalSaasDeploymentState.PLANNED


def test_quantity_requires_source_unit_and_basis() -> None:
    with pytest.raises(ContractViolation, match="quantity requires"):
        observation(quantity_unit=None)
    with pytest.raises(ContractViolation, match="quantity requires"):
        observation(quantity_basis=None)


def test_quantity_metadata_cannot_exist_without_quantity() -> None:
    with pytest.raises(ContractViolation, match="require quantity"):
        observation(quantity=None, quantity_unit="devices")
    with pytest.raises(ContractViolation, match="require quantity"):
        observation(quantity=None, quantity_unit=None, quantity_basis=PhysicalSaasQuantityBasis.CUMULATIVE_BASE)


def test_quantity_must_be_non_negative_finite_decimal() -> None:
    with pytest.raises(ContractViolation, match="Decimal"):
        observation(quantity=1)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation, match="non-negative"):
        observation(quantity=Decimal("-1"))
    with pytest.raises(ContractViolation, match="finite"):
        observation(quantity=Decimal("NaN"))


def test_cumulative_base_is_distinct_from_event_increment() -> None:
    cumulative = observation(
        quantity=Decimal("25000"),
        quantity_basis=PhysicalSaasQuantityBasis.CUMULATIVE_BASE,
    )
    assert cumulative.quantity_basis is PhysicalSaasQuantityBasis.CUMULATIVE_BASE
    assert cumulative.quantity_basis is not PhysicalSaasQuantityBasis.EVENT_INCREMENT


def test_decommissioned_cannot_be_a_cancelled_plan() -> None:
    with pytest.raises(ContractViolation, match="decommissioned"):
        observation(
            milestone=PhysicalSaasDeploymentMilestone.DECOMMISSIONED,
            state=PhysicalSaasDeploymentState.CANCELLED,
        )


def test_effective_interval_cannot_run_backwards() -> None:
    with pytest.raises(ContractViolation, match="effective_start"):
        observation(
            effective_start=SourceTimestamp.date_only(date(2026, 9, 28)),
            effective_end=SourceTimestamp.date_only(date(2026, 9, 27)),
        )


def test_deployment_taxonomy_excludes_commercial_and_revenue_states() -> None:
    names = {item.value for item in PhysicalSaasDeploymentMilestone}
    assert names == {
        "shipped", "delivered", "installed", "activated", "operational",
        "customer_accepted", "decommissioned",
    }
    for forbidden in ("booked", "contracted", "backlog", "billed", "revenue_recognized", "arr"):
        assert forbidden not in names


def test_state_taxonomy_preserves_source_completion_semantics_only() -> None:
    names = {item.value for item in PhysicalSaasDeploymentState}
    assert names == {"planned", "in_progress", "completed", "cancelled"}
    assert "bullish" not in names
    assert "successful" not in names
