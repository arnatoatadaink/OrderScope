"""Validated UWBS-021 catalyst-price divergence and delayed-repricing assessment."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from .catalyst_repricing_types import CatalystDirection, CatalystRepricingInterpretationType, ReactionDirection, reaction_contradicts_catalyst, reaction_supports_catalyst
from .errors import ContractViolation


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str, required: bool) -> None:
    if not isinstance(values, tuple) or (required and not values) or len(values) != len(set(values)):
        raise ContractViolation(f"{field} must be unique immutable references")
    if any(not isinstance(v, str) or not v.strip() or v != v.strip() for v in values):
        raise ContractViolation(f"{field} must contain canonical references")


@dataclass(frozen=True, kw_only=True)
class CatalystRepricingAssessment:
    interpretation_type: CatalystRepricingInterpretationType
    subject_ref: str
    catalyst_ref: str
    catalyst_direction: CatalystDirection
    initial_reaction_direction: ReactionDirection
    observed_window_start: datetime
    observed_window_end: datetime
    catalyst_evidence_record_ids: tuple[str, ...]
    initial_reaction_metric_record_ids: tuple[str, ...]
    generated_at: datetime
    later_reaction_direction: ReactionDirection | None = None
    later_reaction_metric_record_ids: tuple[str, ...] = ()
    conflicting_event_record_ids: tuple[str, ...] = ()
    method_version: str = "catalyst-repricing-v0.1"

    def __post_init__(self) -> None:
        if not self.subject_ref.strip() or not self.catalyst_ref.strip() or not self.method_version.strip():
            raise ContractViolation("catalyst repricing references cannot be blank")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end or self.generated_at < self.observed_window_end:
            raise ContractViolation("invalid catalyst repricing observation window")
        _refs(self.catalyst_evidence_record_ids, "catalyst_evidence_record_ids", True)
        _refs(self.initial_reaction_metric_record_ids, "initial_reaction_metric_record_ids", True)
        _refs(self.later_reaction_metric_record_ids, "later_reaction_metric_record_ids", False)
        _refs(self.conflicting_event_record_ids, "conflicting_event_record_ids", False)
        groups = [set(x) for x in (self.catalyst_evidence_record_ids, self.initial_reaction_metric_record_ids, self.later_reaction_metric_record_ids, self.conflicting_event_record_ids)]
        if any(groups[i] & groups[j] for i in range(len(groups)) for j in range(i + 1, len(groups))):
            raise ContractViolation("catalyst repricing evidence classes cannot overlap")
        if not reaction_contradicts_catalyst(self.catalyst_direction, self.initial_reaction_direction):
            raise ContractViolation("initial reaction must oppose catalyst direction")
        if self.interpretation_type is CatalystRepricingInterpretationType.CATALYST_PRICE_DIVERGENCE:
            if self.later_reaction_direction is not None or self.later_reaction_metric_record_ids:
                raise ContractViolation("divergence cannot include later reaction confirmation")
        else:
            if self.later_reaction_direction is None or not self.later_reaction_metric_record_ids:
                raise ContractViolation("delayed repricing requires later reaction evidence")
            if not reaction_supports_catalyst(self.catalyst_direction, self.later_reaction_direction):
                raise ContractViolation("later reaction must align with catalyst direction")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return self.catalyst_evidence_record_ids + self.initial_reaction_metric_record_ids + self.later_reaction_metric_record_ids + self.conflicting_event_record_ids
