"""UWBS-022 persistence gate for price-rediscovery confirmation.

This contract does not define price or volume thresholds. It requires independent
catalyst, old-range invalidation, retest, and multi-session persistence lineage
before an existing RepricingState can be confirmed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .catalyst_reaction_window import CatalystReactionWindow
from .errors import ContractViolation
from .repricing_state import RepricingState, RepricingStateAssessment

_MULTI_SESSION_WINDOWS = frozenset({
    CatalystReactionWindow.REACTION_3D,
    CatalystReactionWindow.REACTION_5D,
})


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple) or not values or len(values) != len(set(values)):
        raise ContractViolation(f"{field} must be non-empty unique immutable references")
    if any(not isinstance(value, str) or not value.strip() or value != value.strip() for value in values):
        raise ContractViolation(f"{field} must contain canonical references")


@dataclass(frozen=True, kw_only=True)
class PriceRediscoveryConfirmationAssessment:
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    catalyst_evidence_record_ids: tuple[str, ...]
    old_range_invalidation_metric_record_ids: tuple[str, ...]
    retest_metric_record_ids: tuple[str, ...]
    persistence_metric_record_ids: tuple[str, ...]
    persistence_windows: tuple[CatalystReactionWindow, ...]
    previous_state_record_id: str
    generated_at: datetime
    disqualifying_confounder_record_ids: tuple[str, ...] = ()
    method_version: str = "price-rediscovery-confirmation-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, str) or not self.subject_ref.strip():
            raise ContractViolation("subject_ref cannot be blank")
        if not isinstance(self.method_version, str) or not self.method_version.strip():
            raise ContractViolation("method_version cannot be blank")
        if not isinstance(self.previous_state_record_id, str) or not self.previous_state_record_id.strip():
            raise ContractViolation("previous_state_record_id cannot be blank")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed_window_end")
        for values, field in (
            (self.catalyst_evidence_record_ids, "catalyst_evidence_record_ids"),
            (self.old_range_invalidation_metric_record_ids, "old_range_invalidation_metric_record_ids"),
            (self.retest_metric_record_ids, "retest_metric_record_ids"),
            (self.persistence_metric_record_ids, "persistence_metric_record_ids"),
        ):
            _refs(values, field)
        if not isinstance(self.disqualifying_confounder_record_ids, tuple):
            raise ContractViolation("disqualifying_confounder_record_ids must be an immutable tuple")
        if self.disqualifying_confounder_record_ids:
            _refs(self.disqualifying_confounder_record_ids, "disqualifying_confounder_record_ids")
            raise ContractViolation("price rediscovery cannot be confirmed with unresolved confounders")
        groups = [
            set(self.catalyst_evidence_record_ids),
            set(self.old_range_invalidation_metric_record_ids),
            set(self.retest_metric_record_ids),
            set(self.persistence_metric_record_ids),
            {self.previous_state_record_id},
        ]
        if any(groups[i] & groups[j] for i in range(len(groups)) for j in range(i + 1, len(groups))):
            raise ContractViolation("price-rediscovery evidence classes cannot overlap")
        if not isinstance(self.persistence_windows, tuple) or not self.persistence_windows:
            raise ContractViolation("persistence_windows must be a non-empty tuple")
        if len(self.persistence_windows) != len(set(self.persistence_windows)):
            raise ContractViolation("persistence_windows cannot contain duplicates")
        if any(not isinstance(window, CatalystReactionWindow) for window in self.persistence_windows):
            raise ContractViolation("persistence_windows must contain CatalystReactionWindow values")
        if not set(self.persistence_windows) & _MULTI_SESSION_WINDOWS:
            raise ContractViolation("confirmed rediscovery requires 3d or 5d persistence evidence")

    def to_repricing_state_assessment(self) -> RepricingStateAssessment:
        metric_ids = self.old_range_invalidation_metric_record_ids + self.retest_metric_record_ids
        return RepricingStateAssessment(
            state=RepricingState.PRICE_REDISCOVERY_CONFIRMED,
            subject_ref=self.subject_ref,
            observed_window_start=self.observed_window_start,
            observed_window_end=self.observed_window_end,
            metric_record_ids=metric_ids,
            catalyst_evidence_record_ids=self.catalyst_evidence_record_ids,
            persistence_metric_record_ids=self.persistence_metric_record_ids,
            previous_state_record_id=self.previous_state_record_id,
            previous_state=RepricingState.NEW_EQUILIBRIUM_CANDIDATE,
            generated_at=self.generated_at,
            method_version=self.method_version,
        )
