"""UWBS-087 provider-neutral Physical-SaaS deployment lifecycle Fact contract.

This boundary records source-observed physical deployment milestones only. It
must not turn backlog, bookings, contract value, management targets, connected-
base totals, billing, ARR, or recognized revenue into completed deployment
Facts. Commercial conversion and deployment-funnel interpretation are separate
UWBS-089/UWBS-090 layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp


class PhysicalSaasDeploymentMilestone(StrEnum):
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    INSTALLED = "installed"
    ACTIVATED = "activated"
    OPERATIONAL = "operational"
    CUSTOMER_ACCEPTED = "customer_accepted"
    DECOMMISSIONED = "decommissioned"


class PhysicalSaasDeploymentState(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PhysicalSaasQuantityBasis(StrEnum):
    EVENT_INCREMENT = "event_increment"
    CUMULATIVE_BASE = "cumulative_base"
    POINT_IN_TIME_BASE = "point_in_time_base"


@dataclass(frozen=True, kw_only=True)
class PhysicalSaasDeploymentObservation:
    """One source-grounded physical deployment lifecycle assertion."""

    subject_ref: str
    milestone: PhysicalSaasDeploymentMilestone
    state: PhysicalSaasDeploymentState
    accepted_at: datetime
    provenance: Provenance
    effective_start: SourceTimestamp | None = None
    effective_end: SourceTimestamp | None = None
    deployment_ref: str | None = None
    customer_ref: str | None = None
    site_ref: str | None = None
    product_ref: str | None = None
    quantity: Decimal | None = None
    quantity_unit: str | None = None
    quantity_basis: PhysicalSaasQuantityBasis | None = None

    def __post_init__(self) -> None:
        _canonical(self.subject_ref, "subject_ref")
        if not isinstance(self.milestone, PhysicalSaasDeploymentMilestone):
            raise ContractViolation("milestone must be PhysicalSaasDeploymentMilestone")
        if not isinstance(self.state, PhysicalSaasDeploymentState):
            raise ContractViolation("state must be PhysicalSaasDeploymentState")
        if self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() != timedelta(0):
            raise ContractViolation("accepted_at must be normalized to UTC")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")

        for value, field in (
            (self.deployment_ref, "deployment_ref"),
            (self.customer_ref, "customer_ref"),
            (self.site_ref, "site_ref"),
            (self.product_ref, "product_ref"),
            (self.quantity_unit, "quantity_unit"),
        ):
            if value is not None:
                _canonical(value, field)

        for value, field in (
            (self.effective_start, "effective_start"),
            (self.effective_end, "effective_end"),
        ):
            if value is not None and not isinstance(value, SourceTimestamp):
                raise ContractViolation(f"{field} must be SourceTimestamp")
        _validate_interval(self.effective_start, self.effective_end)

        if self.quantity is None:
            if self.quantity_unit is not None or self.quantity_basis is not None:
                raise ContractViolation("quantity_unit/quantity_basis require quantity")
        else:
            if isinstance(self.quantity, bool) or not isinstance(self.quantity, Decimal):
                raise ContractViolation("quantity must be Decimal when supplied")
            if not self.quantity.is_finite() or self.quantity < 0:
                raise ContractViolation("quantity must be finite and non-negative")
            if self.quantity_unit is None or self.quantity_basis is None:
                raise ContractViolation("quantity requires quantity_unit and quantity_basis")
            if not isinstance(self.quantity_basis, PhysicalSaasQuantityBasis):
                raise ContractViolation("quantity_basis must be PhysicalSaasQuantityBasis")

        if self.state is PhysicalSaasDeploymentState.CANCELLED and self.milestone is PhysicalSaasDeploymentMilestone.DECOMMISSIONED:
            raise ContractViolation("decommissioned is an observed lifecycle milestone, not a cancelled plan")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        value = {
            "milestone": self.milestone.value,
            "state": self.state.value,
            "deployment_ref": self.deployment_ref,
            "customer_ref": self.customer_ref,
            "site_ref": self.site_ref,
            "product_ref": self.product_ref,
            "quantity": str(self.quantity) if self.quantity is not None else None,
            "quantity_unit": self.quantity_unit,
            "quantity_basis": self.quantity_basis.value if self.quantity_basis is not None else None,
        }
        return Fact(
            record_id=record_id,
            schema_version="physical-saas-deployment-observation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type=f"physical_saas_deployment.{self.milestone.value}",
            value=value,
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
            period_start=self.effective_start,
            period_end=self.effective_end,
        )


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ContractViolation(f"{field} must be canonical non-empty text")
    if len(value) > 256:
        raise ContractViolation(f"{field} exceeds 256 characters")


def _validate_interval(start: SourceTimestamp | None, end: SourceTimestamp | None) -> None:
    if start is None or end is None or start.precision is not end.precision:
        return
    start_value = start.calendar_date if start.calendar_date is not None else start.instant
    end_value = end.calendar_date if end.calendar_date is not None else end.instant
    if start_value is not None and end_value is not None and start_value > end_value:
        raise ContractViolation("effective_start cannot be later than effective_end")
