"""UWBS-091 M&A integration / legacy-system evidence overlay.

This boundary records source-observed integration milestones separately from
interpretation.  An acquisition closing, migration announcement, or legacy
system retirement is a Fact candidate; claims such as integration success,
legacy drag, or migration slippage remain downstream Interpretations requiring
multiple explicit evidence classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import (
    Fact,
    FactAssertionKind,
    Interpretation,
    InterpretationAssertionKind,
)
from orderscope_local.contracts.provenance import Provenance, SourceTimestamp


class IntegrationEventKind(StrEnum):
    ACQUISITION_ANNOUNCED = "acquisition_announced"
    ACQUISITION_CLOSED = "acquisition_closed"
    PLATFORM_MIGRATION_STARTED = "platform_migration_started"
    PLATFORM_MIGRATION_COMPLETED = "platform_migration_completed"
    CUSTOMER_MIGRATION_STARTED = "customer_migration_started"
    CUSTOMER_MIGRATION_COMPLETED = "customer_migration_completed"
    LEGACY_SYSTEM_RETIREMENT = "legacy_system_retirement"
    INTEGRATION_PROGRAM_COMPLETED = "integration_program_completed"


class IntegrationEventState(StrEnum):
    ANNOUNCED = "announced"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IntegrationInterpretationType(StrEnum):
    INTEGRATION_SUCCESS_CANDIDATE = "integration_success_candidate"
    LEGACY_DRAG_CANDIDATE = "legacy_drag_candidate"
    MIGRATION_SLIPPAGE_CANDIDATE = "migration_slippage_candidate"


class IntegrationInterpretationRating(StrEnum):
    SUPPORT = "SUPPORT"
    PARTIAL = "PARTIAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, kw_only=True)
class IntegrationEventObservation:
    subject_ref: str
    event_kind: IntegrationEventKind
    state: IntegrationEventState
    accepted_at: datetime
    provenance: Provenance
    acquisition_ref: str | None = None
    acquired_entity_ref: str | None = None
    platform_ref: str | None = None
    legacy_system_ref: str | None = None
    customer_ref: str | None = None
    deployment_ref: str | None = None
    effective_start: SourceTimestamp | None = None
    effective_end: SourceTimestamp | None = None

    def __post_init__(self) -> None:
        _canonical(self.subject_ref, "subject_ref")
        if not isinstance(self.event_kind, IntegrationEventKind):
            raise ContractViolation("event_kind must be IntegrationEventKind")
        if not isinstance(self.state, IntegrationEventState):
            raise ContractViolation("state must be IntegrationEventState")
        _utc(self.accepted_at, "accepted_at")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")
        for value, field in (
            (self.acquisition_ref, "acquisition_ref"),
            (self.acquired_entity_ref, "acquired_entity_ref"),
            (self.platform_ref, "platform_ref"),
            (self.legacy_system_ref, "legacy_system_ref"),
            (self.customer_ref, "customer_ref"),
            (self.deployment_ref, "deployment_ref"),
        ):
            if value is not None:
                _canonical(value, field)
        _interval(self.effective_start, self.effective_end)

        if self.event_kind in {
            IntegrationEventKind.ACQUISITION_ANNOUNCED,
            IntegrationEventKind.ACQUISITION_CLOSED,
        }:
            if self.acquisition_ref is None or self.acquired_entity_ref is None:
                raise ContractViolation("acquisition event requires acquisition_ref and acquired_entity_ref")
        if self.event_kind in {
            IntegrationEventKind.PLATFORM_MIGRATION_STARTED,
            IntegrationEventKind.PLATFORM_MIGRATION_COMPLETED,
        } and self.platform_ref is None:
            raise ContractViolation("platform migration requires platform_ref")
        if self.event_kind is IntegrationEventKind.LEGACY_SYSTEM_RETIREMENT and self.legacy_system_ref is None:
            raise ContractViolation("legacy retirement requires legacy_system_ref")
        if self.event_kind in {
            IntegrationEventKind.CUSTOMER_MIGRATION_STARTED,
            IntegrationEventKind.CUSTOMER_MIGRATION_COMPLETED,
        } and self.customer_ref is None:
            raise ContractViolation("customer migration requires customer_ref")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        return Fact(
            record_id=record_id,
            schema_version="physical-saas-integration-event-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type=f"physical_saas_integration.{self.event_kind.value}",
            value={
                "event_kind": self.event_kind.value,
                "state": self.state.value,
                "acquisition_ref": self.acquisition_ref,
                "acquired_entity_ref": self.acquired_entity_ref,
                "platform_ref": self.platform_ref,
                "legacy_system_ref": self.legacy_system_ref,
                "customer_ref": self.customer_ref,
                "deployment_ref": self.deployment_ref,
            },
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
            period_start=self.effective_start,
            period_end=self.effective_end,
        )


@dataclass(frozen=True, kw_only=True)
class IntegrationAssessment:
    interpretation_type: IntegrationInterpretationType
    rating: IntegrationInterpretationRating
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    milestone_fact_refs: tuple[str, ...] = ()
    deployment_metric_refs: tuple[str, ...] = ()
    financial_metric_refs: tuple[str, ...] = ()
    contradicting_evidence_refs: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "physical-saas-integration-assessment-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.interpretation_type, IntegrationInterpretationType):
            raise ContractViolation("interpretation_type must be IntegrationInterpretationType")
        if not isinstance(self.rating, IntegrationInterpretationRating):
            raise ContractViolation("rating must be IntegrationInterpretationRating")
        _canonical(self.subject_ref, "subject_ref")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed_window_end")
        groups = (
            (self.milestone_fact_refs, "milestone_fact_refs"),
            (self.deployment_metric_refs, "deployment_metric_refs"),
            (self.financial_metric_refs, "financial_metric_refs"),
            (self.contradicting_evidence_refs, "contradicting_evidence_refs"),
        )
        for values, field in groups:
            _refs(values, field)
        sets = [set(values) for values, _ in groups]
        for index, left in enumerate(sets):
            for right in sets[index + 1 :]:
                if left & right:
                    raise ContractViolation("integration evidence classes cannot reuse references")

        supporting_groups = sum(
            bool(values)
            for values in (
                self.milestone_fact_refs,
                self.deployment_metric_refs,
                self.financial_metric_refs,
            )
        )
        if self.rating is IntegrationInterpretationRating.UNKNOWN:
            if supporting_groups or self.contradicting_evidence_refs:
                raise ContractViolation("UNKNOWN cannot carry directional evidence")
            return
        if self.rating is IntegrationInterpretationRating.CONTRADICT:
            if not self.contradicting_evidence_refs:
                raise ContractViolation("CONTRADICT requires contradicting evidence")
            return
        if supporting_groups < 2:
            raise ContractViolation("supported integration interpretation requires at least two independent evidence classes")
        if not self.milestone_fact_refs:
            raise ContractViolation("supported integration interpretation requires integration milestone evidence")
        if self.interpretation_type is IntegrationInterpretationType.INTEGRATION_SUCCESS_CANDIDATE:
            if not (self.deployment_metric_refs or self.financial_metric_refs):
                raise ContractViolation("integration success requires deployment or financial confirmation")
        elif self.interpretation_type is IntegrationInterpretationType.LEGACY_DRAG_CANDIDATE:
            if not (self.deployment_metric_refs or self.financial_metric_refs):
                raise ContractViolation("legacy drag requires deployment or financial confirmation")
        elif self.interpretation_type is IntegrationInterpretationType.MIGRATION_SLIPPAGE_CANDIDATE:
            if not self.deployment_metric_refs:
                raise ContractViolation("migration slippage requires deployment metric evidence")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.milestone_fact_refs
            + self.deployment_metric_refs
            + self.financial_metric_refs
            + self.contradicting_evidence_refs
        )

    def to_interpretation(self, *, record_id: str, accepted_at: datetime) -> Interpretation:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        if not self.basis_record_ids:
            raise ContractViolation("Interpretation requires evidence lineage")
        return Interpretation(
            record_id=record_id,
            schema_version="physical-saas-integration-assessment-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            interpretation_type=self.interpretation_type.value,
            statement={
                "rating": self.rating.value,
                "milestone_count": len(self.milestone_fact_refs),
                "deployment_metric_count": len(self.deployment_metric_refs),
                "financial_metric_count": len(self.financial_metric_refs),
                "contradicting_count": len(self.contradicting_evidence_refs),
            },
            basis_record_ids=self.basis_record_ids,
            method="physical_saas_integration_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        _canonical(value, field)


def _interval(start: SourceTimestamp | None, end: SourceTimestamp | None) -> None:
    for value, field in ((start, "effective_start"), (end, "effective_end")):
        if value is not None and not isinstance(value, SourceTimestamp):
            raise ContractViolation(f"{field} must be SourceTimestamp")
    if start is None or end is None or start.precision is not end.precision:
        return
    start_value = start.calendar_date if start.calendar_date is not None else start.instant
    end_value = end.calendar_date if end.calendar_date is not None else end.instant
    if start_value is not None and end_value is not None and start_value > end_value:
        raise ContractViolation("effective_start cannot be later than effective_end")
