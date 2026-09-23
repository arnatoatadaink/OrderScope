"""UWBS-028 bounded relative repricing metrics.

Metrics describe relative price/volume behavior only. They do not assign a cause,
identify a buyer, or classify a catalyst.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import fmean

from orderscope_local.contracts import ContractViolation

from .validation import SeriesMeasure, SeriesObservation, SeriesRole


METHOD_VERSION = "relative-repricing-v0.1"


@dataclass(frozen=True, slots=True)
class RelativeRepricingMetrics:
    target_pre_return: float
    target_recovery_return: float
    market_pre_return: float
    market_recovery_return: float
    sector_pre_return: float
    sector_recovery_return: float
    leader_pre_return: float
    leader_recovery_return: float
    target_relative_pre_vs_market: float
    target_relative_pre_vs_sector: float
    target_relative_pre_vs_leader: float
    target_relative_recovery_vs_market: float
    target_relative_recovery_vs_sector: float
    target_relative_recovery_vs_leader: float
    target_volume_ratio: float
    market_volume_ratio: float
    relative_volume_participation: float


def evaluate_relative_repricing(
    *,
    observations: tuple[SeriesObservation, ...],
    pre_start: date,
    pivot_date: date,
    post_end: date,
    target_role: SeriesRole = SeriesRole.CBRS,
    market_role: SeriesRole = SeriesRole.US_MARKET,
    sector_role: SeriesRole = SeriesRole.AI_SEMICONDUCTOR_PROXY,
    leader_role: SeriesRole = SeriesRole.NVDA,
) -> RelativeRepricingMetrics:
    if not pre_start < pivot_date < post_end:
        raise ContractViolation("relative repricing windows must satisfy pre_start < pivot_date < post_end")

    def values(role: SeriesRole, measure: SeriesMeasure, start: date, end: date) -> list[float]:
        rows = sorted(
            (
                item for item in observations
                if item.role is role and item.measure is measure and start <= item.analysis_date < end
            ),
            key=lambda item: item.analysis_date,
        )
        if not rows:
            raise ContractViolation(f"missing relative repricing observations for {role.value}:{measure.value}")
        return [float(item.value) for item in rows]

    def window_return(role: SeriesRole, start: date, end: date) -> float:
        series = values(role, SeriesMeasure.PRICE, start, end)
        if series[0] == 0:
            raise ContractViolation(f"zero starting price for {role.value}")
        return series[-1] / series[0] - 1.0

    def recovery_return(role: SeriesRole) -> float:
        pre = values(role, SeriesMeasure.PRICE, pre_start, pivot_date)
        post = values(role, SeriesMeasure.PRICE, pivot_date, post_end)
        trough = min(pre[-1], post[0])
        if trough == 0:
            raise ContractViolation(f"zero pivot price for {role.value}")
        return post[-1] / trough - 1.0

    def volume_ratio(role: SeriesRole) -> float:
        pre = values(role, SeriesMeasure.VOLUME, pre_start, pivot_date)
        post = values(role, SeriesMeasure.VOLUME, pivot_date, post_end)
        pre_mean = fmean(pre)
        if pre_mean <= 0:
            raise ContractViolation(f"pre-window volume must be positive for {role.value}")
        return fmean(post) / pre_mean

    target_pre = window_return(target_role, pre_start, pivot_date)
    market_pre = window_return(market_role, pre_start, pivot_date)
    sector_pre = window_return(sector_role, pre_start, pivot_date)
    leader_pre = window_return(leader_role, pre_start, pivot_date)

    target_recovery = recovery_return(target_role)
    market_recovery = recovery_return(market_role)
    sector_recovery = recovery_return(sector_role)
    leader_recovery = recovery_return(leader_role)

    target_volume = volume_ratio(target_role)
    market_volume = volume_ratio(market_role)
    if market_volume <= 0:
        raise ContractViolation("market volume ratio must be positive")

    return RelativeRepricingMetrics(
        target_pre_return=target_pre,
        target_recovery_return=target_recovery,
        market_pre_return=market_pre,
        market_recovery_return=market_recovery,
        sector_pre_return=sector_pre,
        sector_recovery_return=sector_recovery,
        leader_pre_return=leader_pre,
        leader_recovery_return=leader_recovery,
        target_relative_pre_vs_market=target_pre - market_pre,
        target_relative_pre_vs_sector=target_pre - sector_pre,
        target_relative_pre_vs_leader=target_pre - leader_pre,
        target_relative_recovery_vs_market=target_recovery - market_recovery,
        target_relative_recovery_vs_sector=target_recovery - sector_recovery,
        target_relative_recovery_vs_leader=target_recovery - leader_recovery,
        target_volume_ratio=target_volume,
        market_volume_ratio=market_volume,
        relative_volume_participation=target_volume / market_volume,
    )
