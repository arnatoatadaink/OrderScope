"""Deterministic UWBS-075 liquidation and cascade metrics.

No composite risk score or causal market interpretation is produced here.
Metrics expose directly auditable arithmetic over normalized liquidation
buckets and preserve immutable observation lineage.
"""

from __future__ import annotations

from .metrics import CryptoDerivativeMetric
from .models import CryptoDerivativeContractError, LiquidationObservation


def _total(observation: LiquidationObservation) -> float:
    return observation.long_liquidation_usd + observation.short_liquidation_usd


def _ordered_same_series(previous: LiquidationObservation, current: LiquidationObservation) -> None:
    if previous.venue != current.venue or previous.instrument_id != current.instrument_id:
        raise CryptoDerivativeContractError("liquidation buckets must belong to the same venue/instrument series")
    if previous.bucket_end != current.bucket_start:
        raise CryptoDerivativeContractError("cascade metrics require contiguous liquidation buckets")


def liquidation_total_usd(observation: LiquidationObservation) -> CryptoDerivativeMetric:
    return CryptoDerivativeMetric(
        metric_name="liquidation_total_usd",
        instrument_id=observation.instrument_id,
        venue=observation.venue,
        as_of=observation.bucket_end,
        value=_total(observation),
        unit="usd",
        input_observation_ids=(observation.observation_id,),
        method_version="uwbs-075-v1",
    )


def liquidation_event_rate(observation: LiquidationObservation) -> CryptoDerivativeMetric:
    if observation.event_count is None:
        raise CryptoDerivativeContractError("event_count is required for liquidation_event_rate")
    duration_seconds = (observation.bucket_end - observation.bucket_start).total_seconds()
    return CryptoDerivativeMetric(
        metric_name="liquidation_event_rate",
        instrument_id=observation.instrument_id,
        venue=observation.venue,
        as_of=observation.bucket_end,
        value=observation.event_count / duration_seconds,
        unit="events_per_second",
        input_observation_ids=(observation.observation_id,),
        method_version="uwbs-075-v1",
    )


def liquidation_acceleration_usd(
    previous: LiquidationObservation,
    current: LiquidationObservation,
) -> CryptoDerivativeMetric:
    """Bucket-over-bucket change in gross liquidation notional."""

    _ordered_same_series(previous, current)
    return CryptoDerivativeMetric(
        metric_name="liquidation_acceleration_usd",
        instrument_id=current.instrument_id,
        venue=current.venue,
        as_of=current.bucket_end,
        value=_total(current) - _total(previous),
        unit="usd",
        input_observation_ids=(previous.observation_id, current.observation_id),
        method_version="uwbs-075-v1",
    )


def liquidation_multiplier(
    previous: LiquidationObservation,
    current: LiquidationObservation,
) -> CryptoDerivativeMetric:
    """Gross liquidation multiple versus the immediately preceding bucket."""

    _ordered_same_series(previous, current)
    previous_total = _total(previous)
    if previous_total <= 0:
        raise CryptoDerivativeContractError("previous liquidation total must be positive for multiplier")
    return CryptoDerivativeMetric(
        metric_name="liquidation_multiplier",
        instrument_id=current.instrument_id,
        venue=current.venue,
        as_of=current.bucket_end,
        value=_total(current) / previous_total,
        unit="ratio",
        input_observation_ids=(previous.observation_id, current.observation_id),
        method_version="uwbs-075-v1",
    )


def liquidation_directional_share(observation: LiquidationObservation) -> CryptoDerivativeMetric:
    """Signed long-vs-short liquidation share in [-1, 1]."""

    total = _total(observation)
    value = 0.0 if total == 0 else (observation.long_liquidation_usd - observation.short_liquidation_usd) / total
    return CryptoDerivativeMetric(
        metric_name="liquidation_directional_share",
        instrument_id=observation.instrument_id,
        venue=observation.venue,
        as_of=observation.bucket_end,
        value=value,
        unit="ratio",
        input_observation_ids=(observation.observation_id,),
        method_version="uwbs-075-v1",
    )


__all__ = [
    "liquidation_acceleration_usd",
    "liquidation_directional_share",
    "liquidation_event_rate",
    "liquidation_multiplier",
    "liquidation_total_usd",
]
