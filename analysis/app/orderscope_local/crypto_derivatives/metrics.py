"""Deterministic metrics for UWBS-068 crypto derivatives observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite

from .models import CryptoDerivativeContractError, CryptoDerivativeObservation, LiquidationObservation


@dataclass(frozen=True, kw_only=True)
class CryptoDerivativeMetric:
    metric_name: str
    instrument_id: str
    venue: str | None
    as_of: datetime
    value: float
    unit: str
    input_observation_ids: tuple[str, ...]
    method_version: str = "uwbs-068-v1"

    def __post_init__(self) -> None:
        if not self.metric_name or not self.instrument_id or not self.unit or not self.method_version:
            raise CryptoDerivativeContractError("metric identifiers must be non-blank")
        if self.as_of.tzinfo is None or self.as_of.utcoffset() != timedelta(0):
            raise CryptoDerivativeContractError("as_of must be normalized to UTC")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not isfinite(float(self.value)):
            raise CryptoDerivativeContractError("metric value must be finite")
        if not isinstance(self.input_observation_ids, tuple) or not self.input_observation_ids:
            raise CryptoDerivativeContractError("metric requires immutable input lineage")
        if len(self.input_observation_ids) != len(set(self.input_observation_ids)):
            raise CryptoDerivativeContractError("metric input lineage cannot contain duplicates")


def _same_series(previous: CryptoDerivativeObservation, current: CryptoDerivativeObservation) -> None:
    if previous.venue != current.venue or previous.instrument_id != current.instrument_id:
        raise CryptoDerivativeContractError("observations must belong to the same venue/instrument series")
    if previous.observed_at >= current.observed_at:
        raise CryptoDerivativeContractError("previous observation must precede current observation")


def open_interest_delta_usd(
    previous: CryptoDerivativeObservation,
    current: CryptoDerivativeObservation,
) -> CryptoDerivativeMetric:
    _same_series(previous, current)
    if previous.open_interest_usd is None or current.open_interest_usd is None:
        raise CryptoDerivativeContractError("open_interest_usd is required on both observations")
    return CryptoDerivativeMetric(
        metric_name="open_interest_delta_usd",
        instrument_id=current.instrument_id,
        venue=current.venue,
        as_of=current.observed_at,
        value=current.open_interest_usd - previous.open_interest_usd,
        unit="usd",
        input_observation_ids=(previous.observation_id, current.observation_id),
    )


def funding_delta(
    previous: CryptoDerivativeObservation,
    current: CryptoDerivativeObservation,
) -> CryptoDerivativeMetric:
    _same_series(previous, current)
    if previous.funding_rate is None or current.funding_rate is None:
        raise CryptoDerivativeContractError("funding_rate is required on both observations")
    return CryptoDerivativeMetric(
        metric_name="funding_delta",
        instrument_id=current.instrument_id,
        venue=current.venue,
        as_of=current.observed_at,
        value=current.funding_rate - previous.funding_rate,
        unit="rate",
        input_observation_ids=(previous.observation_id, current.observation_id),
    )


def basis_bps(observation: CryptoDerivativeObservation) -> CryptoDerivativeMetric:
    if observation.mark_price is None or observation.index_price is None:
        raise CryptoDerivativeContractError("mark_price and index_price are required")
    if observation.index_price == 0:
        raise CryptoDerivativeContractError("index_price cannot be zero")
    return CryptoDerivativeMetric(
        metric_name="basis_bps",
        instrument_id=observation.instrument_id,
        venue=observation.venue,
        as_of=observation.observed_at,
        value=(observation.mark_price / observation.index_price - 1.0) * 10_000.0,
        unit="bps",
        input_observation_ids=(observation.observation_id,),
    )


def liquidation_imbalance(observation: LiquidationObservation) -> CryptoDerivativeMetric:
    total = observation.long_liquidation_usd + observation.short_liquidation_usd
    value = 0.0 if total == 0 else (observation.long_liquidation_usd - observation.short_liquidation_usd) / total
    return CryptoDerivativeMetric(
        metric_name="liquidation_imbalance",
        instrument_id=observation.instrument_id,
        venue=observation.venue,
        as_of=observation.bucket_end,
        value=value,
        unit="ratio",
        input_observation_ids=(observation.observation_id,),
    )
