"""UWBS-088 operational-milestone extraction/reconciliation boundary.

This module reconciles already-normalized UWBS-087 deployment observations.
It never converts commercial guidance/backlog into deployment Facts and it never
silently resolves conflicting source assertions.  Conflicts remain explicit for
later interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from orderscope_local.contracts.physical_saas_deployment import (
    PhysicalSaasDeploymentObservation,
)


class MilestoneReconciliationStatus(StrEnum):
    CONSISTENT = "consistent"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    INSUFFICIENT_IDENTITY = "insufficient_identity"


@dataclass(frozen=True, kw_only=True)
class MilestoneReconciliationResult:
    status: MilestoneReconciliationStatus
    left: PhysicalSaasDeploymentObservation
    right: PhysicalSaasDeploymentObservation
    conflict_fields: tuple[str, ...] = ()


def reconcile_milestones(
    left: PhysicalSaasDeploymentObservation,
    right: PhysicalSaasDeploymentObservation,
) -> MilestoneReconciliationResult:
    """Compare two normalized source assertions without choosing a winner."""

    if not isinstance(left, PhysicalSaasDeploymentObservation) or not isinstance(
        right, PhysicalSaasDeploymentObservation
    ):
        raise TypeError("reconcile_milestones requires PhysicalSaasDeploymentObservation")

    if not _identity_is_sufficient(left) or not _identity_is_sufficient(right):
        return MilestoneReconciliationResult(
            status=MilestoneReconciliationStatus.INSUFFICIENT_IDENTITY,
            left=left,
            right=right,
        )

    if _identity_key(left) != _identity_key(right):
        return MilestoneReconciliationResult(
            status=MilestoneReconciliationStatus.CONSISTENT,
            left=left,
            right=right,
        )

    conflicts: list[str] = []
    for field in (
        "state",
        "quantity",
        "quantity_unit",
        "quantity_basis",
        "effective_start",
        "effective_end",
        "customer_ref",
        "site_ref",
        "product_ref",
    ):
        if getattr(left, field) != getattr(right, field):
            conflicts.append(field)

    if conflicts:
        return MilestoneReconciliationResult(
            status=MilestoneReconciliationStatus.CONFLICT,
            left=left,
            right=right,
            conflict_fields=tuple(conflicts),
        )

    if left.provenance == right.provenance:
        status = MilestoneReconciliationStatus.DUPLICATE
    else:
        status = MilestoneReconciliationStatus.CONSISTENT

    return MilestoneReconciliationResult(
        status=status,
        left=left,
        right=right,
    )


def _identity_is_sufficient(item: PhysicalSaasDeploymentObservation) -> bool:
    return item.deployment_ref is not None or (
        item.customer_ref is not None and item.site_ref is not None
    )


def _identity_key(item: PhysicalSaasDeploymentObservation) -> tuple[object, ...]:
    if item.deployment_ref is not None:
        anchor: tuple[object, ...] = ("deployment_ref", item.deployment_ref)
    else:
        anchor = ("customer_site", item.customer_ref, item.site_ref)
    return (*anchor, item.milestone)
