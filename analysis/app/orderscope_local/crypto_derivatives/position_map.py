"""UWBS-076 deterministic Position Map / OI-retention estimates.

A Position Map is an inference layer over aggregate derivatives observations.
It does not claim trader-level entry prices or a true position ledger.  The
implementation anchors newly added open interest to the contemporaneous price
band and measures how much of that incremental OI remains at a later snapshot.
Funding and subsequent liquidation totals are retained as auditable context.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import floor, isfinite
from typing import Iterable

from .models import CryptoDerivativeContractError, CryptoDerivativeObservation, LiquidationObservation


@dataclass(frozen=True, kw_only=True)
class PositionBandEstimate:
    venue: str
    instrument_id: str
    band_low: float
    band_high: float
    anchor_at: datetime
    as_of: datetime
    baseline_open_interest_usd: float
    added_open_interest_usd: float
    retained_open_interest_usd: float
    retention_ratio: float
    anchor_funding_rate: float | None
    long_liquidation_usd_after_anchor: float
    short_liquidation_usd_after_anchor: float
    input_observation_ids: tuple[str, ...]
    method_version: str = "uwbs-076-v1"

    def __post_init__(self) -> None:
        if not self.venue or not self.instrument_id or not self.method_version:
            raise CryptoDerivativeContractError("position-map identifiers must be non-blank")
        if self.band_low < 0 or self.band_high <= self.band_low:
            raise CryptoDerivativeContractError("position-map price band must be positive and ordered")
        for value, field in ((self.anchor_at, "anchor_at"), (self.as_of, "as_of")):
            if value.tzinfo is None or value.utcoffset() != timedelta(0):
                raise CryptoDerivativeContractError(f"{field} must be normalized to UTC")
        if self.anchor_at > self.as_of:
            raise CryptoDerivativeContractError("anchor_at cannot be later than as_of")
        for value, field in (
            (self.baseline_open_interest_usd, "baseline_open_interest_usd"),
            (self.added_open_interest_usd, "added_open_interest_usd"),
            (self.retained_open_interest_usd, "retained_open_interest_usd"),
            (self.long_liquidation_usd_after_anchor, "long_liquidation_usd_after_anchor"),
            (self.short_liquidation_usd_after_anchor, "short_liquidation_usd_after_anchor"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or value < 0:
                raise CryptoDerivativeContractError(f"{field} must be finite and non-negative")
        if not 0.0 <= self.retention_ratio <= 1.0:
            raise CryptoDerivativeContractError("retention_ratio must be in [0, 1]")
        if not self.input_observation_ids or len(self.input_observation_ids) != len(set(self.input_observation_ids)):
            raise CryptoDerivativeContractError("position-map lineage must be non-empty and unique")


def _price(observation: CryptoDerivativeObservation) -> float:
    value = observation.mark_price if observation.mark_price is not None else observation.index_price
    if value is None or value <= 0:
        raise CryptoDerivativeContractError("mark_price or positive index_price is required for Position Map")
    return value


def _validate_series(*observations: CryptoDerivativeObservation) -> None:
    if not observations:
        raise CryptoDerivativeContractError("at least one observation is required")
    venue = observations[0].venue
    instrument_id = observations[0].instrument_id
    if any(item.venue != venue or item.instrument_id != instrument_id for item in observations[1:]):
        raise CryptoDerivativeContractError("Position Map observations must belong to one venue/instrument series")


def _price_band(price: float, band_width_bps: int) -> tuple[float, float]:
    if not isinstance(band_width_bps, int) or isinstance(band_width_bps, bool) or band_width_bps <= 0:
        raise CryptoDerivativeContractError("band_width_bps must be a positive integer")
    width = price * band_width_bps / 10_000.0
    if width <= 0:
        raise CryptoDerivativeContractError("price-band width must be positive")
    low = floor(price / width) * width
    high = low + width
    if low <= 0:
        low = max(price - width / 2.0, 1e-12)
        high = low + width
    return low, high


def estimate_position_band(
    baseline: CryptoDerivativeObservation,
    anchor: CryptoDerivativeObservation,
    as_of: CryptoDerivativeObservation,
    *,
    liquidations: Iterable[LiquidationObservation] = (),
    band_width_bps: int = 100,
) -> PositionBandEstimate:
    """Estimate OI retained from an anchor-time OI increase.

    ``baseline -> anchor`` defines newly added OI.  ``as_of`` measures how much
    of that incremental OI is still present above the original baseline:

    retained = min(added, max(as_of_oi - baseline_oi, 0))

    This intentionally avoids claiming exact entry-price ownership.
    """

    _validate_series(baseline, anchor, as_of)
    if not (baseline.observed_at < anchor.observed_at <= as_of.observed_at):
        raise CryptoDerivativeContractError("Position Map observations must be time ordered")
    if baseline.open_interest_usd is None or anchor.open_interest_usd is None or as_of.open_interest_usd is None:
        raise CryptoDerivativeContractError("open_interest_usd is required for Position Map")

    added = anchor.open_interest_usd - baseline.open_interest_usd
    if added <= 0:
        raise CryptoDerivativeContractError("anchor must contain a positive OI increase versus baseline")
    retained = min(added, max(as_of.open_interest_usd - baseline.open_interest_usd, 0.0))
    ratio = retained / added
    low, high = _price_band(_price(anchor), band_width_bps)

    long_liq = 0.0
    short_liq = 0.0
    lineage = [baseline.observation_id, anchor.observation_id, as_of.observation_id]
    for item in liquidations:
        if item.venue != anchor.venue or item.instrument_id != anchor.instrument_id:
            continue
        if item.bucket_start < anchor.observed_at or item.bucket_end > as_of.observed_at:
            continue
        long_liq += item.long_liquidation_usd
        short_liq += item.short_liquidation_usd
        lineage.append(item.observation_id)

    return PositionBandEstimate(
        venue=anchor.venue,
        instrument_id=anchor.instrument_id,
        band_low=low,
        band_high=high,
        anchor_at=anchor.observed_at,
        as_of=as_of.observed_at,
        baseline_open_interest_usd=baseline.open_interest_usd,
        added_open_interest_usd=added,
        retained_open_interest_usd=retained,
        retention_ratio=ratio,
        anchor_funding_rate=anchor.funding_rate,
        long_liquidation_usd_after_anchor=long_liq,
        short_liquidation_usd_after_anchor=short_liq,
        input_observation_ids=tuple(lineage),
    )


__all__ = ["PositionBandEstimate", "estimate_position_band"]
