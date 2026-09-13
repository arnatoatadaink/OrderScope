"""Unified as-of timeline query for X0-001.

The timeline is ordered by when information became available to OrderScope, not
by a fabricated event instant. Source event/publication/filing timestamps remain
attached as metadata on Fact records and are never coerced from date-only values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Iterable

import pyarrow.parquet as pq

from orderscope_local.contracts import ContractViolation, Fact
from orderscope_local.market_import import CanonicalBarDataset


UNIFIED_TIMELINE_SCHEMA_VERSION = "unified-timeline-v0.1"


class TimelineSourceKind(StrEnum):
    MARKET = "market"
    FILING = "filing"
    EARNINGS = "earnings"
    NEWS = "news"
    OFFICIAL = "official"
    OTHER_FACT = "other_fact"


@dataclass(frozen=True, slots=True)
class MarketTimelineBar:
    symbol: str
    bar_time: datetime
    receipt_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source_manifest_id: str
    source_artifact_sha256: str

    def __post_init__(self) -> None:
        _utc(self.bar_time, "bar_time")
        _utc(self.receipt_time, "receipt_time")
        if self.receipt_time < self.bar_time:
            raise ContractViolation("market receipt_time cannot precede bar_time")
        if not isinstance(self.symbol, str) or not self.symbol or self.symbol != self.symbol.strip():
            raise ContractViolation("market symbol must be canonical text")
        if not isinstance(self.volume, int) or isinstance(self.volume, bool) or self.volume < 0:
            raise ContractViolation("market volume must be a non-negative integer")
        if not self.source_manifest_id.startswith("d1-export-"):
            raise ContractViolation("market bar requires D1 manifest lineage")
        _sha256(self.source_artifact_sha256, "source_artifact_sha256")


@dataclass(frozen=True, slots=True)
class TimelineItem:
    schema_version: str
    source_kind: TimelineSourceKind
    item_id: str
    subject_ref: str
    available_at: datetime
    accepted_at: datetime
    event_time: datetime | None = None
    payload_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != UNIFIED_TIMELINE_SCHEMA_VERSION:
            raise ContractViolation("unsupported unified timeline schema version")
        if not isinstance(self.source_kind, TimelineSourceKind):
            raise ContractViolation("source_kind must be TimelineSourceKind")
        for value, field in ((self.item_id, "item_id"), (self.subject_ref, "subject_ref")):
            if not isinstance(value, str) or not value.strip() or len(value) > 512:
                raise ContractViolation(f"{field} must be bounded non-blank text")
        _utc(self.available_at, "available_at")
        _utc(self.accepted_at, "accepted_at")
        if self.available_at > self.accepted_at:
            raise ContractViolation("timeline available_at cannot exceed accepted_at")
        if self.event_time is not None:
            _utc(self.event_time, "event_time")
        if self.payload_ref is not None and (not self.payload_ref.strip() or len(self.payload_ref) > 2048):
            raise ContractViolation("payload_ref must be bounded non-blank text")


def read_market_timeline_bars(*, dataset: CanonicalBarDataset, dataset_root: Path) -> tuple[MarketTimelineBar, ...]:
    """Read canonical market bars without exposing raw fixture SQL."""

    if not isinstance(dataset, CanonicalBarDataset):
        raise ContractViolation("dataset must be CanonicalBarDataset")
    path = dataset_root / dataset.relative_path
    if not path.is_file():
        raise ContractViolation("canonical market dataset file is missing")
    table = pq.read_table(path)
    rows = table.to_pylist()
    if len(rows) != dataset.row_count:
        raise ContractViolation("canonical market dataset row count changed")

    bars = []
    for row in rows:
        bars.append(
            MarketTimelineBar(
                symbol=row["symbol"],
                bar_time=row["bar_time"],
                receipt_time=row["receipt_time"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                source_manifest_id=row["source_manifest_id"],
                source_artifact_sha256=row["source_artifact_sha256"],
            )
        )
    return tuple(bars)


def query_unified_timeline(
    *,
    facts: Iterable[Fact],
    market_bars: Iterable[MarketTimelineBar],
    as_of: datetime,
) -> tuple[TimelineItem, ...]:
    """Return deterministic read-only items known by ``as_of``.

    Facts require both source availability and internal acceptance to be no later
    than ``as_of``. Market bars use receipt_time for both availability and local
    acceptance because the canonical dataset contains receipt provenance but no
    later Fact-Store acceptance timestamp.
    """

    _utc(as_of, "as_of")
    items: list[TimelineItem] = []

    for fact in facts:
        if not isinstance(fact, Fact):
            raise ContractViolation("facts must contain only Fact records")
        if fact.provenance.available_at > as_of or fact.accepted_at > as_of:
            continue
        event_time = None
        if fact.provenance.event_time is not None and fact.provenance.event_time.instant is not None:
            event_time = fact.provenance.event_time.instant
        items.append(
            TimelineItem(
                schema_version=UNIFIED_TIMELINE_SCHEMA_VERSION,
                source_kind=_fact_source_kind(fact.fact_type),
                item_id=fact.record_id,
                subject_ref=fact.subject_ref,
                available_at=fact.provenance.available_at,
                accepted_at=fact.accepted_at,
                event_time=event_time,
                payload_ref=fact.provenance.source_ref.value,
            )
        )

    for bar in market_bars:
        if not isinstance(bar, MarketTimelineBar):
            raise ContractViolation("market_bars must contain only MarketTimelineBar records")
        if bar.receipt_time > as_of:
            continue
        items.append(
            TimelineItem(
                schema_version=UNIFIED_TIMELINE_SCHEMA_VERSION,
                source_kind=TimelineSourceKind.MARKET,
                item_id=f"market:{bar.source_manifest_id}:{bar.symbol}:{bar.bar_time.isoformat()}",
                subject_ref=bar.symbol,
                available_at=bar.receipt_time,
                accepted_at=bar.receipt_time,
                event_time=bar.bar_time,
                payload_ref=bar.source_manifest_id,
            )
        )

    return tuple(
        sorted(
            items,
            key=lambda item: (
                item.available_at,
                item.accepted_at,
                item.source_kind.value,
                item.subject_ref,
                item.item_id,
            ),
        )
    )


def _fact_source_kind(fact_type: str) -> TimelineSourceKind:
    if fact_type.startswith(("filing.", "sec.filing", "sec.")):
        return TimelineSourceKind.FILING
    if fact_type.startswith(("earnings.", "fundamental.", "segment.")):
        return TimelineSourceKind.EARNINGS
    if fact_type.startswith("news."):
        return TimelineSourceKind.NEWS
    if fact_type.startswith(("official.", "policy.")):
        return TimelineSourceKind.OFFICIAL
    return TimelineSourceKind.OTHER_FACT


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ContractViolation(f"{field} must be lowercase SHA-256 hex")
