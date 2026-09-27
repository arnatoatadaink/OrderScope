"""UWBS-082 provider-neutral commodity supply/logistics/geopolitical event contract.

This boundary records source-observed event assertions only.  It does not score
severity, infer barrels-at-risk, label an oil-price move, or classify a cross-asset
regime.  Those are downstream interpretation layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp


class CommodityEventKind(StrEnum):
    UPSTREAM_OUTAGE = "upstream_outage"
    REFINERY_OUTAGE = "refinery_outage"
    PIPELINE_DISRUPTION = "pipeline_disruption"
    PORT_DISRUPTION = "port_disruption"
    SHIPPING_ROUTE_DISRUPTION = "shipping_route_disruption"
    MARITIME_SECURITY_INCIDENT = "maritime_security_incident"
    SANCTIONS_ACTION = "sanctions_action"
    EXPORT_RESTRICTION = "export_restriction"
    IMPORT_RESTRICTION = "import_restriction"
    STRATEGIC_RELEASE = "strategic_release"
    PRODUCTION_POLICY_ACTION = "production_policy_action"
    ARMED_CONFLICT = "armed_conflict"
    BLOCKADE_OR_CLOSURE = "blockade_or_closure"


class CommodityEventState(StrEnum):
    REPORTED = "reported"
    ANNOUNCED = "announced"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


@dataclass(frozen=True, kw_only=True)
class CommoditySupplyEventObservation:
    """One externally grounded commodity-supply/logistics event assertion."""

    subject_ref: str
    event_kind: CommodityEventKind
    event_state: CommodityEventState
    geography_ref: str
    accepted_at: datetime
    provenance: Provenance
    effective_start: SourceTimestamp | None = None
    effective_end: SourceTimestamp | None = None
    actor_ref: str | None = None
    asset_ref: str | None = None
    route_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_kind, CommodityEventKind):
            raise ContractViolation("event_kind must be CommodityEventKind")
        if not isinstance(self.event_state, CommodityEventState):
            raise ContractViolation("event_state must be CommodityEventState")
        for value, field in (
            (self.subject_ref, "subject_ref"),
            (self.geography_ref, "geography_ref"),
        ):
            _canonical(value, field)
        for value, field in (
            (self.actor_ref, "actor_ref"),
            (self.asset_ref, "asset_ref"),
            (self.route_ref, "route_ref"),
        ):
            if value is not None:
                _canonical(value, field)
        if self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() != timedelta(0):
            raise ContractViolation("accepted_at must be normalized to UTC")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")
        for value, field in (
            (self.effective_start, "effective_start"),
            (self.effective_end, "effective_end"),
        ):
            if value is not None and not isinstance(value, SourceTimestamp):
                raise ContractViolation(f"{field} must be SourceTimestamp")
        _validate_interval(self.effective_start, self.effective_end)

        if self.event_kind is CommodityEventKind.PIPELINE_DISRUPTION and self.asset_ref is None:
            raise ContractViolation("pipeline disruption requires asset_ref")
        if self.event_kind is CommodityEventKind.REFINERY_OUTAGE and self.asset_ref is None:
            raise ContractViolation("refinery outage requires asset_ref")
        if self.event_kind in {
            CommodityEventKind.SHIPPING_ROUTE_DISRUPTION,
            CommodityEventKind.BLOCKADE_OR_CLOSURE,
        } and self.route_ref is None:
            raise ContractViolation("shipping-route disruption/closure requires route_ref")
        if self.event_kind in {
            CommodityEventKind.SANCTIONS_ACTION,
            CommodityEventKind.EXPORT_RESTRICTION,
            CommodityEventKind.IMPORT_RESTRICTION,
            CommodityEventKind.PRODUCTION_POLICY_ACTION,
        } and self.actor_ref is None:
            raise ContractViolation("policy/geopolitical action requires actor_ref")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        value = {
            "event_kind": self.event_kind.value,
            "event_state": self.event_state.value,
            "geography_ref": self.geography_ref,
            "actor_ref": self.actor_ref,
            "asset_ref": self.asset_ref,
            "route_ref": self.route_ref,
        }
        return Fact(
            record_id=record_id,
            schema_version="commodity-supply-event-observation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type=f"commodity_event.{self.event_kind.value}",
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
