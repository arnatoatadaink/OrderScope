"""UWBS-078 NEAR futures-position Canary.

This module composes accepted derivatives observations into a deterministic
NEAR-specific monitoring snapshot.  The Canary is descriptive QA/position
context only: it does not predict price direction, identify traders, or claim
an exact position ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite
from typing import Iterable

from .cross_venue_qa import (
    diagnose_funding_rate,
    diagnose_mark_price,
    diagnose_open_interest_usd,
)
from .models import CryptoDerivativeContractError, CryptoDerivativeObservation, LiquidationObservation
from .position_map import PositionBandEstimate


@dataclass(frozen=True, kw_only=True)
class NearFuturesPositionCanary:
    instrument_id: str
    as_of: datetime
    venue_count: int
    median_open_interest_usd: float
    median_funding_rate: float
    median_mark_price: float
    oi_max_relative_deviation: float | None
    funding_max_abs_deviation: float
    mark_max_relative_deviation: float | None
    weighted_position_retention_ratio: float | None
    long_liquidation_usd: float
    short_liquidation_usd: float
    liquidation_directional_share: float
    qa_flags: tuple[str, ...]
    input_observation_ids: tuple[str, ...]
    method_version: str = "uwbs-078-v1"

    def __post_init__(self) -> None:
        if not self.instrument_id.upper().startswith("NEAR"):
            raise CryptoDerivativeContractError("UWBS-078 Canary only accepts NEAR instruments")
        if self.as_of.tzinfo is None or self.as_of.utcoffset() != timedelta(0):
            raise CryptoDerivativeContractError("as_of must be normalized to UTC")
        if self.venue_count < 2:
            raise CryptoDerivativeContractError("NEAR Canary requires at least two venues")
        for value, field in (
            (self.median_open_interest_usd, "median_open_interest_usd"),
            (self.median_funding_rate, "median_funding_rate"),
            (self.median_mark_price, "median_mark_price"),
            (self.funding_max_abs_deviation, "funding_max_abs_deviation"),
            (self.long_liquidation_usd, "long_liquidation_usd"),
            (self.short_liquidation_usd, "short_liquidation_usd"),
            (self.liquidation_directional_share, "liquidation_directional_share"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
                raise CryptoDerivativeContractError(f"{field} must be finite")
        for value, field in (
            (self.oi_max_relative_deviation, "oi_max_relative_deviation"),
            (self.mark_max_relative_deviation, "mark_max_relative_deviation"),
            (self.weighted_position_retention_ratio, "weighted_position_retention_ratio"),
        ):
            if value is not None and (not isfinite(float(value)) or value < 0):
                raise CryptoDerivativeContractError(f"{field} must be finite and non-negative when present")
        if self.weighted_position_retention_ratio is not None and self.weighted_position_retention_ratio > 1:
            raise CryptoDerivativeContractError("weighted_position_retention_ratio must be in [0, 1]")
        if not -1.0 <= self.liquidation_directional_share <= 1.0:
            raise CryptoDerivativeContractError("liquidation_directional_share must be in [-1, 1]")
        if len(self.qa_flags) != len(set(self.qa_flags)):
            raise CryptoDerivativeContractError("qa_flags cannot contain duplicates")
        if not self.input_observation_ids or len(self.input_observation_ids) != len(set(self.input_observation_ids)):
            raise CryptoDerivativeContractError("NEAR Canary lineage must be non-empty and unique")


def _nonnegative_threshold(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or value < 0:
        raise CryptoDerivativeContractError(f"{field} must be finite and non-negative")
    return float(value)


def build_near_futures_position_canary(
    observations: Iterable[CryptoDerivativeObservation],
    *,
    position_bands: Iterable[PositionBandEstimate] = (),
    liquidations: Iterable[LiquidationObservation] = (),
    max_skew_seconds: int = 60,
    oi_relative_warn: float = 0.15,
    funding_abs_warn: float = 0.001,
    mark_relative_warn: float = 0.01,
    retention_warn: float = 0.50,
) -> NearFuturesPositionCanary:
    """Build an auditable NEAR futures-position monitoring snapshot.

    Warning thresholds are QA thresholds only.  They must not be interpreted as
    long/short recommendations or probability estimates.
    """

    items = tuple(observations)
    if not items:
        raise CryptoDerivativeContractError("NEAR Canary requires observations")
    if not all(item.instrument_id.upper().startswith("NEAR") for item in items):
        raise CryptoDerivativeContractError("UWBS-078 Canary only accepts NEAR instruments")

    oi_warn = _nonnegative_threshold(oi_relative_warn, "oi_relative_warn")
    funding_warn = _nonnegative_threshold(funding_abs_warn, "funding_abs_warn")
    mark_warn = _nonnegative_threshold(mark_relative_warn, "mark_relative_warn")
    retention_threshold = _nonnegative_threshold(retention_warn, "retention_warn")
    if retention_threshold > 1:
        raise CryptoDerivativeContractError("retention_warn must be in [0, 1]")

    oi_diag = diagnose_open_interest_usd(items, max_skew_seconds=max_skew_seconds)
    funding_diag = diagnose_funding_rate(items, max_skew_seconds=max_skew_seconds)
    mark_diag = diagnose_mark_price(items, max_skew_seconds=max_skew_seconds)

    lineage = list(oi_diag.input_observation_ids)
    band_items = tuple(position_bands)
    total_added = 0.0
    total_retained = 0.0
    for band in band_items:
        if band.instrument_id != oi_diag.instrument_id:
            raise CryptoDerivativeContractError("position-band instrument must match NEAR Canary instrument")
        total_added += band.added_open_interest_usd
        total_retained += band.retained_open_interest_usd
        lineage.extend(band.input_observation_ids)
    retention_ratio = None if total_added == 0 else total_retained / total_added

    long_liq = 0.0
    short_liq = 0.0
    for item in liquidations:
        if item.instrument_id != oi_diag.instrument_id:
            raise CryptoDerivativeContractError("liquidation instrument must match NEAR Canary instrument")
        long_liq += item.long_liquidation_usd
        short_liq += item.short_liquidation_usd
        lineage.append(item.observation_id)
    total_liq = long_liq + short_liq
    directional_share = 0.0 if total_liq == 0 else (long_liq - short_liq) / total_liq

    flags: list[str] = []
    if oi_diag.max_relative_deviation is not None and oi_diag.max_relative_deviation > oi_warn:
        flags.append("oi_cross_venue_mismatch")
    if funding_diag.max_abs_deviation > funding_warn:
        flags.append("funding_cross_venue_mismatch")
    if mark_diag.max_relative_deviation is not None and mark_diag.max_relative_deviation > mark_warn:
        flags.append("mark_cross_venue_mismatch")
    if retention_ratio is not None and retention_ratio < retention_threshold:
        flags.append("position_retention_below_threshold")

    unique_lineage = tuple(dict.fromkeys(lineage))
    return NearFuturesPositionCanary(
        instrument_id=oi_diag.instrument_id,
        as_of=max(oi_diag.as_of, funding_diag.as_of, mark_diag.as_of),
        venue_count=len(oi_diag.venue_values),
        median_open_interest_usd=oi_diag.median_value,
        median_funding_rate=funding_diag.median_value,
        median_mark_price=mark_diag.median_value,
        oi_max_relative_deviation=oi_diag.max_relative_deviation,
        funding_max_abs_deviation=funding_diag.max_abs_deviation,
        mark_max_relative_deviation=mark_diag.max_relative_deviation,
        weighted_position_retention_ratio=retention_ratio,
        long_liquidation_usd=long_liq,
        short_liquidation_usd=short_liq,
        liquidation_directional_share=directional_share,
        qa_flags=tuple(flags),
        input_observation_ids=unique_lineage,
    )


__all__ = ["NearFuturesPositionCanary", "build_near_futures_position_canary"]
