"""UWBS-079 Pacific weekend handoff / weekday re-risking validation.

The validator stores episode-level observations and summarizes recurrence over
multiple independent weekends.  It deliberately separates descriptive
recurrence from causal interpretation: time-window labels never identify
participant nationality, and a repeated pattern is not proof of systematic or
agent-driven execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from statistics import median
from typing import Iterable

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.crypto_time import CryptoDayType, CryptoTimeContext


class WeekendValidationStatus(StrEnum):
    INSUFFICIENT_SAMPLE = "insufficient_sample"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True, slots=True, kw_only=True)
class WeekendHandoffEpisode:
    episode_id: str
    weekend_context: CryptoTimeContext
    weekday_context: CryptoTimeContext
    btc_return: float
    altcoin_return: float
    synchronized_breadth: float
    max_btc_alt_lag_minutes: int
    spot_volume_change: float
    derivatives_volume_change: float
    open_interest_change: float
    funding_change: float
    liquidation_imbalance: float
    persistence_1h: float
    persistence_3h: float
    persistence_6h: float
    persistence_24h: float
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.episode_id, str) or not self.episode_id.strip() or len(self.episode_id) > 128:
            raise ContractViolation("episode_id must be non-blank and bounded")
        if self.weekend_context.day_type is not CryptoDayType.WEEKEND:
            raise ContractViolation("weekend_context must classify as weekend")
        if self.weekday_context.day_type is not CryptoDayType.WEEKDAY:
            raise ContractViolation("weekday_context must classify as weekday")
        if self.weekend_context.observed_at >= self.weekday_context.observed_at:
            raise ContractViolation("weekend_context must precede weekday_context")
        gap = self.weekday_context.observed_at - self.weekend_context.observed_at
        if gap > timedelta(days=3):
            raise ContractViolation("weekend-to-weekday handoff gap must be within three days")
        for value, field in (
            (self.btc_return, "btc_return"),
            (self.altcoin_return, "altcoin_return"),
            (self.synchronized_breadth, "synchronized_breadth"),
            (self.spot_volume_change, "spot_volume_change"),
            (self.derivatives_volume_change, "derivatives_volume_change"),
            (self.open_interest_change, "open_interest_change"),
            (self.funding_change, "funding_change"),
            (self.liquidation_imbalance, "liquidation_imbalance"),
            (self.persistence_1h, "persistence_1h"),
            (self.persistence_3h, "persistence_3h"),
            (self.persistence_6h, "persistence_6h"),
            (self.persistence_24h, "persistence_24h"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
                raise ContractViolation(f"{field} must be finite")
        if not 0.0 <= self.synchronized_breadth <= 1.0:
            raise ContractViolation("synchronized_breadth must be in [0, 1]")
        if not -1.0 <= self.liquidation_imbalance <= 1.0:
            raise ContractViolation("liquidation_imbalance must be in [-1, 1]")
        if not isinstance(self.max_btc_alt_lag_minutes, int) or isinstance(self.max_btc_alt_lag_minutes, bool):
            raise ContractViolation("max_btc_alt_lag_minutes must be an integer")
        if abs(self.max_btc_alt_lag_minutes) > 60:
            raise ContractViolation("max_btc_alt_lag_minutes must be within [-60, 60]")
        if not self.source_refs or len(self.source_refs) != len(set(self.source_refs)):
            raise ContractViolation("source_refs must be non-empty and unique")
        if any(not isinstance(item, str) or not item.strip() for item in self.source_refs):
            raise ContractViolation("source_refs must contain non-blank strings")


@dataclass(frozen=True, slots=True, kw_only=True)
class WeekendReriskingValidation:
    status: WeekendValidationStatus
    episode_count: int
    positive_btc_weekends: int
    negative_btc_weekends: int
    flat_btc_weekends: int
    same_direction_fraction: float
    median_synchronized_breadth: float
    median_max_btc_alt_lag_minutes: float
    median_spot_volume_change: float
    median_derivatives_volume_change: float
    median_open_interest_change: float
    median_funding_change: float
    median_liquidation_imbalance: float
    median_persistence_1h: float
    median_persistence_3h: float
    median_persistence_6h: float
    median_persistence_24h: float
    episode_ids: tuple[str, ...]
    source_refs: tuple[str, ...]
    method_version: str = "uwbs-079-v1"

    def __post_init__(self) -> None:
        if self.episode_count <= 0 or self.episode_count != len(self.episode_ids):
            raise ContractViolation("episode_count must match non-empty episode_ids")
        if self.positive_btc_weekends + self.negative_btc_weekends + self.flat_btc_weekends != self.episode_count:
            raise ContractViolation("BTC regime counts must sum to episode_count")
        if not 0.0 <= self.same_direction_fraction <= 1.0:
            raise ContractViolation("same_direction_fraction must be in [0, 1]")
        if not 0.0 <= self.median_synchronized_breadth <= 1.0:
            raise ContractViolation("median_synchronized_breadth must be in [0, 1]")
        if len(self.episode_ids) != len(set(self.episode_ids)):
            raise ContractViolation("episode_ids cannot contain duplicates")
        if not self.source_refs or len(self.source_refs) != len(set(self.source_refs)):
            raise ContractViolation("source_refs must be non-empty and unique")


def validate_weekend_rerisking(
    episodes: Iterable[WeekendHandoffEpisode],
    *,
    minimum_independent_weekends: int = 4,
    flat_return_abs: float = 0.001,
) -> WeekendReriskingValidation:
    """Summarize recurrence without promoting it to a causal Fact.

    ``EXPERIMENTAL`` means only that the configured minimum independent-weekend
    sample size has been met.  It does not mean the recurrence is statistically
    established or causal.
    """

    items = tuple(episodes)
    if not items:
        raise ContractViolation("weekend validation requires at least one episode")
    if not isinstance(minimum_independent_weekends, int) or isinstance(minimum_independent_weekends, bool) or minimum_independent_weekends < 2:
        raise ContractViolation("minimum_independent_weekends must be an integer >= 2")
    if isinstance(flat_return_abs, bool) or not isinstance(flat_return_abs, (int, float)) or not isfinite(float(flat_return_abs)) or flat_return_abs < 0:
        raise ContractViolation("flat_return_abs must be finite and non-negative")

    episode_ids = [item.episode_id for item in items]
    if len(episode_ids) != len(set(episode_ids)):
        raise ContractViolation("weekend validation requires unique episode_id values")
    weekend_dates = [item.weekend_context.observed_at.date() for item in items]
    if len(weekend_dates) != len(set(weekend_dates)):
        raise ContractViolation("episodes must represent independent weekend dates")

    positive = sum(item.btc_return > flat_return_abs for item in items)
    negative = sum(item.btc_return < -flat_return_abs for item in items)
    flat = len(items) - positive - negative
    same_direction = sum(
        1
        for item in items
        if item.btc_return == 0.0 and item.altcoin_return == 0.0
        or item.btc_return * item.altcoin_return > 0
    )
    refs: list[str] = []
    for item in items:
        refs.extend(item.source_refs)

    return WeekendReriskingValidation(
        status=(
            WeekendValidationStatus.EXPERIMENTAL
            if len(items) >= minimum_independent_weekends
            else WeekendValidationStatus.INSUFFICIENT_SAMPLE
        ),
        episode_count=len(items),
        positive_btc_weekends=positive,
        negative_btc_weekends=negative,
        flat_btc_weekends=flat,
        same_direction_fraction=same_direction / len(items),
        median_synchronized_breadth=float(median(item.synchronized_breadth for item in items)),
        median_max_btc_alt_lag_minutes=float(median(item.max_btc_alt_lag_minutes for item in items)),
        median_spot_volume_change=float(median(item.spot_volume_change for item in items)),
        median_derivatives_volume_change=float(median(item.derivatives_volume_change for item in items)),
        median_open_interest_change=float(median(item.open_interest_change for item in items)),
        median_funding_change=float(median(item.funding_change for item in items)),
        median_liquidation_imbalance=float(median(item.liquidation_imbalance for item in items)),
        median_persistence_1h=float(median(item.persistence_1h for item in items)),
        median_persistence_3h=float(median(item.persistence_3h for item in items)),
        median_persistence_6h=float(median(item.persistence_6h for item in items)),
        median_persistence_24h=float(median(item.persistence_24h for item in items)),
        episode_ids=tuple(sorted(episode_ids)),
        source_refs=tuple(dict.fromkeys(refs)),
    )


__all__ = [
    "WeekendHandoffEpisode",
    "WeekendReriskingValidation",
    "WeekendValidationStatus",
    "validate_weekend_rerisking",
]
