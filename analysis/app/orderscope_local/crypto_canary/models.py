"""Multi-layer crypto Canary contracts for UWBS-072."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class CanaryLayerState(StrEnum):
    SUPPORTING = "SUPPORTING"
    CONTRADICTING = "CONTRADICTING"
    MISSING = "MISSING"


class NearBtcCanaryState(StrEnum):
    MULTI_LAYER_CONFIRMATION_CANDIDATE = "MULTI_LAYER_CONFIRMATION_CANDIDATE"
    BTC_ONLY_MOVE = "BTC_ONLY_MOVE"
    NEAR_IDIOSYNCRATIC_MOVE = "NEAR_IDIOSYNCRATIC_MOVE"
    LIQUIDATION_ONLY_AMPLIFICATION = "LIQUIDATION_ONLY_AMPLIFICATION"
    WEEKEND_THIN_LIQUIDITY_CANDIDATE = "WEEKEND_THIN_LIQUIDITY_CANDIDATE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def _utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    normalized = value.astimezone(timezone.utc)
    if normalized.utcoffset() != timezone.utc.utcoffset(normalized):
        raise ValueError(f"{name} must normalize to UTC")
    return normalized


@dataclass(frozen=True)
class NearBtcCanaryInput:
    observed_at: datetime
    btc_direction: CanaryLayerState
    near_direction: CanaryLayerState
    btc_relative_strength: CanaryLayerState
    derivatives_positioning: CanaryLayerState
    liquidation_context: CanaryLayerState
    weekend_liquidity_context: CanaryLayerState
    catalyst_context: CanaryLayerState

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _utc(self.observed_at, "observed_at"))

    @property
    def layer_states(self) -> tuple[CanaryLayerState, ...]:
        return (
            self.btc_direction,
            self.near_direction,
            self.btc_relative_strength,
            self.derivatives_positioning,
            self.liquidation_context,
            self.weekend_liquidity_context,
            self.catalyst_context,
        )


@dataclass(frozen=True)
class NearBtcCanaryAssessment:
    state: NearBtcCanaryState
    observed_at: datetime
    supporting_layers: tuple[str, ...]
    contradicting_layers: tuple[str, ...]
    missing_layers: tuple[str, ...]
    method_version: str = "uwbs-072-v0.1"
    causal_status: str = "candidate_only"
