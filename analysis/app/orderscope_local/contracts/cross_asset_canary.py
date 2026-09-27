"""UWBS-086 historical Canary and capacity-acceptance contract.

This boundary evaluates fixture/historical replay results only. It does not
activate providers, mutate Worker/Cron configuration, or write remote D1 state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from .errors import ContractViolation


class CanaryDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


@dataclass(frozen=True, kw_only=True)
class CrossAssetCanaryResult:
    scenario_id: str
    expected_regime: str
    observed_regime: str
    expected_alert: bool
    observed_alert: bool

    def __post_init__(self) -> None:
        for value, field in (
            (self.scenario_id, "scenario_id"),
            (self.expected_regime, "expected_regime"),
            (self.observed_regime, "observed_regime"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if not isinstance(self.expected_alert, bool) or not isinstance(self.observed_alert, bool):
            raise ContractViolation("alert flags must be boolean")

    @property
    def regime_match(self) -> bool:
        return self.expected_regime == self.observed_regime

    @property
    def alert_match(self) -> bool:
        return self.expected_alert == self.observed_alert


@dataclass(frozen=True, kw_only=True)
class CapacityObservation:
    worker_requests_per_day: int
    d1_rows_read_per_day: int
    d1_rows_written_per_day: int
    d1_bytes_written_per_day: int
    scheduled_invocations_per_day: int
    headroom_ratio: float

    def __post_init__(self) -> None:
        for value, field in (
            (self.worker_requests_per_day, "worker_requests_per_day"),
            (self.d1_rows_read_per_day, "d1_rows_read_per_day"),
            (self.d1_rows_written_per_day, "d1_rows_written_per_day"),
            (self.d1_bytes_written_per_day, "d1_bytes_written_per_day"),
            (self.scheduled_invocations_per_day, "scheduled_invocations_per_day"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractViolation(f"{field} must be a non-negative integer")
        if isinstance(self.headroom_ratio, bool) or not isinstance(self.headroom_ratio, (int, float)):
            raise ContractViolation("headroom_ratio must be numeric")
        if not isfinite(float(self.headroom_ratio)) or not 0 <= float(self.headroom_ratio) <= 1:
            raise ContractViolation("headroom_ratio must be between zero and one")


@dataclass(frozen=True, kw_only=True)
class CrossAssetCanaryAssessment:
    results: tuple[CrossAssetCanaryResult, ...]
    capacity: CapacityObservation
    minimum_headroom_ratio: float = 0.20

    def __post_init__(self) -> None:
        if not isinstance(self.results, tuple) or not self.results:
            raise ContractViolation("canary assessment requires at least one scenario")
        if len({item.scenario_id for item in self.results}) != len(self.results):
            raise ContractViolation("canary scenario_id values must be unique")
        if not isinstance(self.capacity, CapacityObservation):
            raise ContractViolation("capacity must be CapacityObservation")
        if not isinstance(self.minimum_headroom_ratio, (int, float)) or isinstance(self.minimum_headroom_ratio, bool):
            raise ContractViolation("minimum_headroom_ratio must be numeric")
        if not 0 <= float(self.minimum_headroom_ratio) <= 1:
            raise ContractViolation("minimum_headroom_ratio must be between zero and one")

    @property
    def false_positive_count(self) -> int:
        return sum(not item.expected_alert and item.observed_alert for item in self.results)

    @property
    def false_negative_count(self) -> int:
        return sum(item.expected_alert and not item.observed_alert for item in self.results)

    @property
    def regime_mismatch_count(self) -> int:
        return sum(not item.regime_match for item in self.results)

    @property
    def decision(self) -> CanaryDecision:
        if self.capacity.headroom_ratio < self.minimum_headroom_ratio:
            return CanaryDecision.REJECT
        if self.false_negative_count or self.regime_mismatch_count:
            return CanaryDecision.REJECT
        if self.false_positive_count:
            return CanaryDecision.REVIEW
        return CanaryDecision.ACCEPT
