"""UWBS-075 source-neutral liquidation normalization.

The module deliberately stays below provider/network orchestration.  It
normalizes already-observed liquidation events into a deterministic event
contract and aggregates aligned events into the existing
``LiquidationObservation`` bucket contract.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Iterable

from .models import CryptoDerivativeContractError, LiquidationObservation


class LiquidationSide(StrEnum):
    """Side of the position that was liquidated, not aggressor trade side."""

    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True, kw_only=True)
class LiquidationEvent:
    event_id: str
    venue: str
    instrument_id: str
    liquidated_side: LiquidationSide
    occurred_at: datetime
    accepted_at: datetime
    source_ref: str
    liquidation_usd: float
    event_count: int = 1
    source_revision: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.event_id, "event_id"),
            (self.venue, "venue"),
            (self.instrument_id, "instrument_id"),
            (self.source_ref, "source_ref"),
        ):
            if not isinstance(value, str) or not value.strip() or len(value) > 256:
                raise CryptoDerivativeContractError(f"{field} must be non-blank and bounded")
        if not isinstance(self.liquidated_side, LiquidationSide):
            raise CryptoDerivativeContractError("liquidated_side must be LiquidationSide")
        for value, field in ((self.occurred_at, "occurred_at"), (self.accepted_at, "accepted_at")):
            if value.tzinfo is None or value.utcoffset() != timedelta(0):
                raise CryptoDerivativeContractError(f"{field} must be normalized to UTC")
        if self.occurred_at > self.accepted_at:
            raise CryptoDerivativeContractError("occurred_at cannot be later than accepted_at")
        if isinstance(self.liquidation_usd, bool) or not isinstance(self.liquidation_usd, (int, float)):
            raise CryptoDerivativeContractError("liquidation_usd must be a finite number")
        if not isfinite(float(self.liquidation_usd)) or self.liquidation_usd < 0:
            raise CryptoDerivativeContractError("liquidation_usd must be finite and non-negative")
        if not isinstance(self.event_count, int) or isinstance(self.event_count, bool) or self.event_count <= 0:
            raise CryptoDerivativeContractError("event_count must be a positive integer")
        if self.source_revision is not None:
            if not isinstance(self.source_revision, str) or not self.source_revision.strip() or len(self.source_revision) > 256:
                raise CryptoDerivativeContractError("source_revision must be non-blank and bounded")


def liquidation_event(
    *,
    event_id: str,
    venue: str,
    instrument_id: str,
    liquidated_side: str | LiquidationSide,
    occurred_at: datetime,
    accepted_at: datetime,
    source_ref: str,
    liquidation_usd: float,
    event_count: int = 1,
    source_revision: str | None = None,
) -> LiquidationEvent:
    """Normalize explicit source fields into the UWBS-075 event contract.

    This adapter intentionally requires callers to map provider-specific side
    semantics before construction.  It prevents a venue's buy/sell field from
    being silently reinterpreted as the liquidated position side.
    """

    try:
        side = liquidated_side if isinstance(liquidated_side, LiquidationSide) else LiquidationSide(liquidated_side.lower())
    except (AttributeError, ValueError) as exc:
        raise CryptoDerivativeContractError("liquidated_side must be 'long' or 'short'") from exc
    return LiquidationEvent(
        event_id=event_id,
        venue=venue.strip().upper(),
        instrument_id=instrument_id.strip(),
        liquidated_side=side,
        occurred_at=occurred_at,
        accepted_at=accepted_at,
        source_ref=source_ref,
        liquidation_usd=liquidation_usd,
        event_count=event_count,
        source_revision=source_revision,
    )


def aggregate_liquidation_bucket(
    events: Iterable[LiquidationEvent],
    *,
    bucket_start: datetime,
    bucket_end: datetime,
    accepted_at: datetime | None = None,
) -> LiquidationObservation:
    """Aggregate one venue/instrument series into a deterministic time bucket."""

    items = tuple(events)
    if not items:
        raise CryptoDerivativeContractError("liquidation bucket requires at least one event")
    for value, field in ((bucket_start, "bucket_start"), (bucket_end, "bucket_end")):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise CryptoDerivativeContractError(f"{field} must be normalized to UTC")
    if bucket_start >= bucket_end:
        raise CryptoDerivativeContractError("bucket_start must be earlier than bucket_end")

    venue = items[0].venue
    instrument_id = items[0].instrument_id
    for item in items:
        if item.venue != venue or item.instrument_id != instrument_id:
            raise CryptoDerivativeContractError("bucket events must belong to one venue/instrument series")
        if item.occurred_at < bucket_start or item.occurred_at >= bucket_end:
            raise CryptoDerivativeContractError("event occurred_at must fall inside [bucket_start, bucket_end)")

    resolved_accepted_at = accepted_at or max(item.accepted_at for item in items)
    if resolved_accepted_at.tzinfo is None or resolved_accepted_at.utcoffset() != timedelta(0):
        raise CryptoDerivativeContractError("accepted_at must be normalized to UTC")
    if resolved_accepted_at < max(item.accepted_at for item in items):
        raise CryptoDerivativeContractError("accepted_at cannot precede an input event acceptance time")
    if resolved_accepted_at < bucket_end:
        raise CryptoDerivativeContractError("accepted_at cannot be earlier than bucket_end")

    long_usd = sum(item.liquidation_usd for item in items if item.liquidated_side is LiquidationSide.LONG)
    short_usd = sum(item.liquidation_usd for item in items if item.liquidated_side is LiquidationSide.SHORT)
    event_count = sum(item.event_count for item in items)
    lineage = "|".join(sorted(item.event_id for item in items))
    digest = hashlib.sha256(lineage.encode("utf-8")).hexdigest()[:20]
    source_refs = ",".join(sorted({item.source_ref for item in items}))

    return LiquidationObservation(
        observation_id=f"uwbs075:{venue}:{instrument_id}:{bucket_start.isoformat()}:{digest}",
        venue=venue,
        instrument_id=instrument_id,
        bucket_start=bucket_start,
        bucket_end=bucket_end,
        accepted_at=resolved_accepted_at,
        source_ref=f"aggregate:{source_refs}",
        long_liquidation_usd=long_usd,
        short_liquidation_usd=short_usd,
        event_count=event_count,
    )


__all__ = [
    "LiquidationEvent",
    "LiquidationSide",
    "aggregate_liquidation_bucket",
    "liquidation_event",
]
