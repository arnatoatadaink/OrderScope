"""UWBS-064 cross-sectional theme market observations.

Inputs are existing return/volume metric values with durable references. This
module summarizes observed behavior; it does not infer trades or causation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from statistics import median

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import DerivedMetric

from .ontology import ThemeId, require_ref, require_refs, require_utc
from .reaction import EventThemeHypothesis


@dataclass(frozen=True, kw_only=True)
class MemberReaction:
    subject_ref: str
    theme: ThemeId
    window_start: datetime
    window_end: datetime
    return_pct: float
    benchmark_return_pct: float
    volume_ratio: float | None
    metric_refs: tuple[str, ...]
    next_session_persisted: bool | None = None

    def __post_init__(self) -> None:
        require_ref(self.subject_ref, "subject_ref")
        if not isinstance(self.theme, ThemeId):
            raise ContractViolation("theme must be ThemeId")
        require_utc(self.window_start, "window_start")
        require_utc(self.window_end, "window_end")
        if self.window_start >= self.window_end:
            raise ContractViolation("observation window must be non-empty")
        for field in ("return_pct", "benchmark_return_pct"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ContractViolation(f"{field} must be finite")
        if self.volume_ratio is not None:
            if isinstance(self.volume_ratio, bool) or not isinstance(self.volume_ratio, (int, float)) or not isfinite(self.volume_ratio) or self.volume_ratio < 0:
                raise ContractViolation("volume_ratio must be finite and nonnegative")
        if self.next_session_persisted is not None and not isinstance(self.next_session_persisted, bool):
            raise ContractViolation("next_session_persisted must be boolean or unknown")
        require_refs(self.metric_refs, "metric_refs")

    @property
    def relative_return_pct(self) -> float:
        return self.return_pct - self.benchmark_return_pct


@dataclass(frozen=True)
class ThemeReactionObservation:
    hypothesis: EventThemeHypothesis
    members: tuple[MemberReaction, ...]
    median_relative_return_pct: float
    median_volume_ratio: float | None
    volume_assessed_members: int
    directional_breadth: float | None
    persistent_members: int
    persistence_assessed_members: int

    @property
    def window_start(self) -> datetime:
        return self.members[0].window_start

    @property
    def window_end(self) -> datetime:
        return self.members[0].window_end

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def metric_refs(self) -> tuple[str, ...]:
        return tuple(ref for member in self.members for ref in member.metric_refs)

    def to_derived_metric(self, *, record_id: str, accepted_at: datetime) -> DerivedMetric:
        """Preserve input lineage and descriptive values without causal labels."""
        require_utc(accepted_at, "accepted_at")
        if accepted_at < self.window_end:
            raise ContractViolation("metric acceptance cannot precede observation window end")
        return DerivedMetric(
            record_id=record_id,
            schema_version="theme-reaction-observation-v0.1",
            subject_ref=f"theme:{self.hypothesis.theme.value}",
            accepted_at=accepted_at,
            created_at=self.window_end,
            metric_name="theme_reaction_observation",
            value={
                "event_ref": self.hypothesis.event_ref,
                "member_count": self.member_count,
                "median_relative_return_pct": self.median_relative_return_pct,
                "median_volume_ratio": self.median_volume_ratio,
                "volume_assessed_members": self.volume_assessed_members,
                "directional_breadth": self.directional_breadth,
                "persistent_members": self.persistent_members,
                "persistence_assessed_members": self.persistence_assessed_members,
            },
            calculation_method="cross_sectional_theme_summary",
            method_version="theme-observation-v0.1",
            as_of=self.window_end,
            input_record_ids=self.metric_refs,
        )


def observe_theme_reaction(
    hypothesis: EventThemeHypothesis,
    members: tuple[MemberReaction, ...],
) -> ThemeReactionObservation:
    if not isinstance(hypothesis, EventThemeHypothesis):
        raise ContractViolation("hypothesis must be EventThemeHypothesis")
    if not isinstance(members, tuple) or not members:
        raise ContractViolation("members must be a non-empty immutable tuple")
    if any(not isinstance(item, MemberReaction) for item in members):
        raise ContractViolation("members must contain MemberReaction")
    if any(item.theme is not hypothesis.theme for item in members):
        raise ContractViolation("member theme must match the event-theme hypothesis")
    if len({item.subject_ref for item in members}) != len(members):
        raise ContractViolation("one member cannot be counted twice")
    if len({(item.window_start, item.window_end) for item in members}) != 1:
        raise ContractViolation("members must share one observation window")
    all_refs = [ref for member in members for ref in member.metric_refs]
    if len(all_refs) != len(set(all_refs)):
        raise ContractViolation("metric references cannot be shared across members")
    sign = hypothesis.expected_direction.sign
    breadth = None if sign == 0 else sum(item.relative_return_pct * sign > 0 for item in members) / len(members)
    volumes = [item.volume_ratio for item in members if item.volume_ratio is not None]
    assessed = sum(item.next_session_persisted is not None for item in members)
    persisted = sum(item.next_session_persisted is True for item in members)
    return ThemeReactionObservation(
        hypothesis=hypothesis,
        members=members,
        median_relative_return_pct=median(item.relative_return_pct for item in members),
        median_volume_ratio=median(volumes) if volumes else None,
        volume_assessed_members=len(volumes),
        directional_breadth=breadth,
        persistent_members=persisted,
        persistence_assessed_members=assessed,
    )
