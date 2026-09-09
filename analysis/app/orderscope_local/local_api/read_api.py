"""Localhost-only read API for accepted Local Corporate Intelligence views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping

from fastapi import FastAPI, Query

from orderscope_local.contracts import ContractViolation, Fact
from orderscope_local.integration import (
    CorporateCoverageSummary,
    TimelineSourceKind,
    query_unified_timeline,
)
from orderscope_local.integration.timeline import MarketTimelineBar
from .health import LOCAL_HEALTH_SCHEMA_VERSION, LocalServerBinding


LOCAL_READ_API_SCHEMA_VERSION = "local-read-api-v0.1"


@dataclass(frozen=True, slots=True)
class LocalReadSnapshot:
    facts: tuple[Fact, ...] = ()
    market_bars: tuple[MarketTimelineBar, ...] = ()
    coverage: CorporateCoverageSummary | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.facts, tuple) or any(not isinstance(item, Fact) for item in self.facts):
            raise ContractViolation("facts must be an immutable tuple of Fact records")
        if not isinstance(self.market_bars, tuple) or any(not isinstance(item, MarketTimelineBar) for item in self.market_bars):
            raise ContractViolation("market_bars must be an immutable tuple of MarketTimelineBar records")
        if self.coverage is not None and not isinstance(self.coverage, CorporateCoverageSummary):
            raise ContractViolation("coverage must be CorporateCoverageSummary")


def create_read_app(
    *,
    snapshot: LocalReadSnapshot,
    binding: LocalServerBinding | None = None,
) -> FastAPI:
    if not isinstance(snapshot, LocalReadSnapshot):
        raise ContractViolation("snapshot must be LocalReadSnapshot")
    effective = binding or LocalServerBinding()
    if not isinstance(effective, LocalServerBinding):
        raise ContractViolation("binding must be LocalServerBinding")

    app = FastAPI(title="OrderScope Local", version="0.1.0")
    app.state.local_binding = effective
    app.state.read_snapshot = snapshot

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "schema_version": LOCAL_HEALTH_SCHEMA_VERSION,
            "bind_host": effective.host,
        }

    @app.get("/facts")
    def facts(
        as_of: datetime | None = Query(default=None),
        subject_ref: str | None = Query(default=None),
    ) -> dict[str, object]:
        cutoff = _as_of(as_of)
        records = tuple(
            fact for fact in snapshot.facts
            if fact.provenance.available_at <= cutoff and fact.accepted_at <= cutoff
            and (subject_ref is None or fact.subject_ref == subject_ref)
        )
        records = tuple(sorted(records, key=lambda item: (item.provenance.available_at, item.accepted_at, item.record_id)))
        return _collection("facts", cutoff, (_fact_record(item) for item in records))

    @app.get("/filings")
    def filings(as_of: datetime | None = Query(default=None), subject_ref: str | None = Query(default=None)) -> dict[str, object]:
        return _fact_subset(snapshot=snapshot, cutoff=_as_of(as_of), kind=TimelineSourceKind.FILING, subject_ref=subject_ref, name="filings")

    @app.get("/earnings")
    def earnings(as_of: datetime | None = Query(default=None), subject_ref: str | None = Query(default=None)) -> dict[str, object]:
        return _fact_subset(snapshot=snapshot, cutoff=_as_of(as_of), kind=TimelineSourceKind.EARNINGS, subject_ref=subject_ref, name="earnings")

    @app.get("/news")
    def news(as_of: datetime | None = Query(default=None), subject_ref: str | None = Query(default=None)) -> dict[str, object]:
        return _fact_subset(snapshot=snapshot, cutoff=_as_of(as_of), kind=TimelineSourceKind.NEWS, subject_ref=subject_ref, name="news")

    @app.get("/sources/health")
    def sources_health() -> dict[str, object]:
        if snapshot.coverage is None:
            return {
                "schema_version": LOCAL_READ_API_SCHEMA_VERSION,
                "coverage_schema_version": None,
                "as_of": None,
                "sources": [],
            }
        coverage = snapshot.coverage
        return {
            "schema_version": LOCAL_READ_API_SCHEMA_VERSION,
            "coverage_schema_version": coverage.schema_version,
            "as_of": coverage.as_of.isoformat(),
            "sources": [_coverage_record(source) for source in coverage.sources],
        }

    return app


def _fact_subset(*, snapshot: LocalReadSnapshot, cutoff: datetime, kind: TimelineSourceKind, subject_ref: str | None, name: str) -> dict[str, object]:
    timeline = query_unified_timeline(facts=snapshot.facts, market_bars=(), as_of=cutoff)
    ids = {item.item_id for item in timeline if item.source_kind is kind and (subject_ref is None or item.subject_ref == subject_ref)}
    records = tuple(sorted((fact for fact in snapshot.facts if fact.record_id in ids), key=lambda item: (item.provenance.available_at, item.accepted_at, item.record_id)))
    return _collection(name, cutoff, (_fact_record(item) for item in records))


def _collection(name: str, cutoff: datetime, records: Iterable[Mapping[str, object]]) -> dict[str, object]:
    materialized = list(records)
    return {
        "schema_version": LOCAL_READ_API_SCHEMA_VERSION,
        "collection": name,
        "as_of": cutoff.isoformat(),
        "count": len(materialized),
        "items": materialized,
    }


def _fact_record(fact: Fact) -> dict[str, object]:
    return {
        "record_id": fact.record_id,
        "schema_version": fact.schema_version,
        "subject_ref": fact.subject_ref,
        "fact_type": fact.fact_type,
        "assertion_kind": fact.assertion_kind.value,
        "value": _json_value(fact.value),
        "unit": fact.unit,
        "available_at": fact.provenance.available_at.isoformat(),
        "accepted_at": fact.accepted_at.isoformat(),
        "source_ref": fact.provenance.source_ref.value,
        "content_hash": fact.provenance.content_hash.digest,
        "evidence_record_ids": list(fact.evidence_record_ids),
    }


def _coverage_record(source) -> dict[str, object]:
    return {
        "provider_key": source.provider_key,
        "source_key": source.source_key,
        "last_success_at": _iso(source.last_success_at),
        "latest_observed_at": _iso(source.latest_observed_at),
        "latest_state": None if source.latest_state is None else source.latest_state.value,
        "resume_cursor": source.resume_cursor,
        "lag_seconds": source.lag_seconds,
        "error_category": source.error_category,
        "error_retryable": source.error_retryable,
        "retry_not_before": _iso(source.retry_not_before),
        "retention_pending_count": source.retention_pending_count,
        "retention_overdue_count": source.retention_overdue_count,
        "retention_next_due_at": _iso(source.retention_next_due_at),
    }


def _json_value(value):
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, Mapping):
        return dict(value)
    return value


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _as_of(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation("as_of must be normalized to UTC")
    return value
