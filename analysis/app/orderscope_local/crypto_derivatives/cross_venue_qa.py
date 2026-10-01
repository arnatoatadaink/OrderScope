"""UWBS-077 deterministic cross-venue comparability and mismatch diagnostics.

The module compares already-normalized derivatives observations without
assuming that any venue is authoritative. Diagnostics are descriptive only:
large differences identify review candidates; they do not rank providers or
infer manipulation, capital flow, or trader intent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite
from statistics import median
from typing import Iterable

from .models import CryptoDerivativeContractError, CryptoDerivativeObservation


@dataclass(frozen=True, kw_only=True)
class CrossVenueDiagnostic:
    instrument_id: str
    as_of: datetime
    metric_name: str
    unit: str
    venue_values: tuple[tuple[str, float], ...]
    median_value: float
    max_abs_deviation: float
    max_relative_deviation: float | None
    input_observation_ids: tuple[str, ...]
    method_version: str = "uwbs-077-v1"

    def __post_init__(self) -> None:
        if not self.instrument_id or not self.metric_name or not self.unit or not self.method_version:
            raise CryptoDerivativeContractError("cross-venue diagnostic identifiers must be non-blank")
        if self.as_of.tzinfo is None or self.as_of.utcoffset() != timedelta(0):
            raise CryptoDerivativeContractError("as_of must be normalized to UTC")
        if len(self.venue_values) < 2:
            raise CryptoDerivativeContractError("cross-venue diagnostic requires at least two venues")
        venues = [venue for venue, _ in self.venue_values]
        if len(venues) != len(set(venues)):
            raise CryptoDerivativeContractError("cross-venue diagnostic cannot contain duplicate venues")
        for venue, value in self.venue_values:
            if not venue or isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
                raise CryptoDerivativeContractError("cross-venue values must be finite")
        if not isfinite(self.median_value) or not isfinite(self.max_abs_deviation) or self.max_abs_deviation < 0:
            raise CryptoDerivativeContractError("cross-venue diagnostic values must be finite and non-negative where required")
        if self.max_relative_deviation is not None:
            if not isfinite(self.max_relative_deviation) or self.max_relative_deviation < 0:
                raise CryptoDerivativeContractError("max_relative_deviation must be finite and non-negative")
        if len(self.input_observation_ids) != len(self.venue_values):
            raise CryptoDerivativeContractError("diagnostic lineage must match venue count")
        if len(self.input_observation_ids) != len(set(self.input_observation_ids)):
            raise CryptoDerivativeContractError("diagnostic lineage cannot contain duplicates")


def comparable_snapshot_group(
    observations: Iterable[CryptoDerivativeObservation],
    *,
    max_skew_seconds: int = 60,
) -> tuple[CryptoDerivativeObservation, ...]:
    """Validate and return a deterministic comparable cross-venue snapshot group."""

    items = tuple(observations)
    if len(items) < 2:
        raise CryptoDerivativeContractError("cross-venue comparison requires at least two observations")
    if not isinstance(max_skew_seconds, int) or isinstance(max_skew_seconds, bool) or max_skew_seconds < 0:
        raise CryptoDerivativeContractError("max_skew_seconds must be a non-negative integer")

    instrument_id = items[0].instrument_id
    contract_type = items[0].contract_type
    if any(item.instrument_id != instrument_id for item in items[1:]):
        raise CryptoDerivativeContractError("cross-venue observations must share instrument_id")
    if any(item.contract_type != contract_type for item in items[1:]):
        raise CryptoDerivativeContractError("cross-venue observations must share contract_type")

    venues = [item.venue for item in items]
    if len(venues) != len(set(venues)):
        raise CryptoDerivativeContractError("cross-venue comparison requires unique venues")

    observed_times = [item.observed_at for item in items]
    skew = (max(observed_times) - min(observed_times)).total_seconds()
    if skew > max_skew_seconds:
        raise CryptoDerivativeContractError("cross-venue observations exceed allowed time skew")

    return tuple(sorted(items, key=lambda item: (item.venue, item.observed_at, item.observation_id)))


def _diagnose(
    observations: Iterable[CryptoDerivativeObservation],
    *,
    metric_name: str,
    unit: str,
    extractor,
    max_skew_seconds: int,
) -> CrossVenueDiagnostic:
    items = comparable_snapshot_group(observations, max_skew_seconds=max_skew_seconds)
    extracted: list[tuple[CryptoDerivativeObservation, float]] = []
    for item in items:
        value = extractor(item)
        if value is None:
            raise CryptoDerivativeContractError(f"{metric_name} is required on every comparable observation")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
            raise CryptoDerivativeContractError(f"{metric_name} must be finite")
        extracted.append((item, float(value)))

    values = [value for _, value in extracted]
    center = float(median(values))
    max_abs = max(abs(value - center) for value in values)
    max_rel = None if center == 0 else max_abs / abs(center)
    as_of = max(item.observed_at for item, _ in extracted)

    return CrossVenueDiagnostic(
        instrument_id=items[0].instrument_id,
        as_of=as_of,
        metric_name=metric_name,
        unit=unit,
        venue_values=tuple((item.venue, value) for item, value in extracted),
        median_value=center,
        max_abs_deviation=max_abs,
        max_relative_deviation=max_rel,
        input_observation_ids=tuple(item.observation_id for item, _ in extracted),
    )


def diagnose_open_interest_usd(
    observations: Iterable[CryptoDerivativeObservation],
    *,
    max_skew_seconds: int = 60,
) -> CrossVenueDiagnostic:
    return _diagnose(
        observations,
        metric_name="open_interest_usd",
        unit="usd",
        extractor=lambda item: item.open_interest_usd,
        max_skew_seconds=max_skew_seconds,
    )


def diagnose_funding_rate(
    observations: Iterable[CryptoDerivativeObservation],
    *,
    max_skew_seconds: int = 60,
) -> CrossVenueDiagnostic:
    return _diagnose(
        observations,
        metric_name="funding_rate",
        unit="rate",
        extractor=lambda item: item.funding_rate,
        max_skew_seconds=max_skew_seconds,
    )


def diagnose_mark_price(
    observations: Iterable[CryptoDerivativeObservation],
    *,
    max_skew_seconds: int = 60,
) -> CrossVenueDiagnostic:
    return _diagnose(
        observations,
        metric_name="mark_price",
        unit="quote_asset",
        extractor=lambda item: item.mark_price,
        max_skew_seconds=max_skew_seconds,
    )


__all__ = [
    "CrossVenueDiagnostic",
    "comparable_snapshot_group",
    "diagnose_funding_rate",
    "diagnose_mark_price",
    "diagnose_open_interest_usd",
]
