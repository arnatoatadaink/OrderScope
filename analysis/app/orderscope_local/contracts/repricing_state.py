"""UWBS-030 repricing state vocabulary and transition boundary.

States are Interpretation-layer classifications.  This module does not define
percentage, volume, or session-count thresholds; those require later historical
calibration and validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class RepricingState(StrEnum):
    NO_REACTION = "no_reaction"
    PARTIAL_REACTION = "partial_reaction"
    DIRECTIONAL_REACTION = "directional_reaction"
    CATALYST_PRICE_DIVERGENCE = "catalyst_price_divergence"
    DELAYED_REPRICING = "delayed_repricing"
    PRICE_SPIKE = "price_spike"
    PRICE_DISCOVERY_ACTIVE = "price_discovery_active"
    NEW_EQUILIBRIUM_CANDIDATE = "new_equilibrium_candidate"
    PRICE_REDISCOVERY_CONFIRMED = "price_rediscovery_confirmed"
    PRICE_REDISCOVERY_FAILED = "price_rediscovery_failed"
    RELATIVE_OVERSHOOT = "relative_overshoot"
    RELATIVE_MEAN_REVERSION = "relative_mean_reversion"
    REPRICING_OVERSHOOT = "repricing_overshoot"
    LOCAL_EQUILIBRIUM_CANDIDATE = "local_equilibrium_candidate"


_ALLOWED_TRANSITIONS: dict[RepricingState, frozenset[RepricingState]] = {
    RepricingState.NO_REACTION: frozenset({
        RepricingState.PARTIAL_REACTION,
        RepricingState.DIRECTIONAL_REACTION,
        RepricingState.CATALYST_PRICE_DIVERGENCE,
        RepricingState.DELAYED_REPRICING,
        RepricingState.PRICE_DISCOVERY_ACTIVE,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.PARTIAL_REACTION: frozenset({
        RepricingState.DIRECTIONAL_REACTION,
        RepricingState.CATALYST_PRICE_DIVERGENCE,
        RepricingState.DELAYED_REPRICING,
        RepricingState.PRICE_DISCOVERY_ACTIVE,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.DIRECTIONAL_REACTION: frozenset({
        RepricingState.PRICE_SPIKE,
        RepricingState.PRICE_DISCOVERY_ACTIVE,
        RepricingState.NEW_EQUILIBRIUM_CANDIDATE,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.CATALYST_PRICE_DIVERGENCE: frozenset({
        RepricingState.DELAYED_REPRICING,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.DELAYED_REPRICING: frozenset({
        RepricingState.DIRECTIONAL_REACTION,
        RepricingState.PRICE_DISCOVERY_ACTIVE,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.PRICE_SPIKE: frozenset({
        RepricingState.PRICE_DISCOVERY_ACTIVE,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.PRICE_DISCOVERY_ACTIVE: frozenset({
        RepricingState.NEW_EQUILIBRIUM_CANDIDATE,
        RepricingState.REPRICING_OVERSHOOT,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.NEW_EQUILIBRIUM_CANDIDATE: frozenset({
        RepricingState.PRICE_REDISCOVERY_CONFIRMED,
        RepricingState.PRICE_REDISCOVERY_FAILED,
        RepricingState.REPRICING_OVERSHOOT,
    }),
    RepricingState.RELATIVE_OVERSHOOT: frozenset({
        RepricingState.RELATIVE_MEAN_REVERSION,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.RELATIVE_MEAN_REVERSION: frozenset({
        RepricingState.REPRICING_OVERSHOOT,
        RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.REPRICING_OVERSHOOT: frozenset({
        RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
        RepricingState.PRICE_REDISCOVERY_FAILED,
    }),
    RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE: frozenset({
        RepricingState.PRICE_REDISCOVERY_CONFIRMED,
        RepricingState.PRICE_REDISCOVERY_FAILED,
        RepricingState.PRICE_DISCOVERY_ACTIVE,
    }),
    RepricingState.PRICE_REDISCOVERY_CONFIRMED: frozenset(),
    RepricingState.PRICE_REDISCOVERY_FAILED: frozenset(),
}


def is_allowed_repricing_transition(previous: RepricingState, current: RepricingState) -> bool:
    if not isinstance(previous, RepricingState) or not isinstance(current, RepricingState):
        raise ContractViolation("repricing transition requires RepricingState values")
    return current in _ALLOWED_TRANSITIONS[previous]


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str, *, required: bool = True) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if required and not values:
        raise ContractViolation(f"{field} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class RepricingStateAssessment:
    state: RepricingState
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    metric_record_ids: tuple[str, ...]
    catalyst_evidence_record_ids: tuple[str, ...] = ()
    persistence_metric_record_ids: tuple[str, ...] = ()
    previous_state_record_id: str | None = None
    previous_state: RepricingState | None = None
    generated_at: datetime
    method_version: str = "repricing-state-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.state, RepricingState):
            raise ContractViolation("state must be RepricingState")
        if not isinstance(self.subject_ref, str) or not self.subject_ref.strip():
            raise ContractViolation("subject_ref cannot be blank")
        if not isinstance(self.method_version, str) or not self.method_version.strip():
            raise ContractViolation("method_version cannot be blank")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed window end")
        _refs(self.metric_record_ids, "metric_record_ids")
        _refs(self.catalyst_evidence_record_ids, "catalyst_evidence_record_ids", required=False)
        _refs(self.persistence_metric_record_ids, "persistence_metric_record_ids", required=False)
        if (self.previous_state_record_id is None) != (self.previous_state is None):
            raise ContractViolation("previous state id and value must be provided together")
        if self.previous_state is not None:
            if not is_allowed_repricing_transition(self.previous_state, self.state):
                raise ContractViolation("repricing state transition is not allowed")
        if self.state is RepricingState.PRICE_REDISCOVERY_CONFIRMED:
            if not self.catalyst_evidence_record_ids or not self.persistence_metric_record_ids:
                raise ContractViolation("confirmed rediscovery requires catalyst and persistence lineage")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        refs = (
            self.metric_record_ids
            + self.catalyst_evidence_record_ids
            + self.persistence_metric_record_ids
        )
        if self.previous_state_record_id is not None:
            refs += (self.previous_state_record_id,)
        if len(refs) != len(set(refs)):
            raise ContractViolation("repricing lineage references cannot overlap")
        return refs

    def to_interpretation(
        self,
        *,
        record_id: str,
        accepted_at: datetime,
        supersedes_record_id: str | None = None,
    ) -> Interpretation:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        return Interpretation(
            record_id=record_id,
            schema_version="repricing-state-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type="repricing_state",
            statement={
                "state": self.state.value,
                "observed_window_start": self.observed_window_start.isoformat(),
                "observed_window_end": self.observed_window_end.isoformat(),
                "previous_state": self.previous_state.value if self.previous_state else None,
                "threshold_policy": "not_fixed_v0.1",
            },
            basis_record_ids=self.basis_record_ids,
            method="repricing_state_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
