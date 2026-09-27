"""Retrospective News candidate population for N1-006 benchmark labeling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

from orderscope_local.contracts import AdapterRequest, ContractViolation, collect_pages
from .alpaca import ALPACA_NEWS_PROVIDER_KEY, AlpacaNewsAdapter


NEWS_RECALL_CANDIDATE_SCHEMA_VERSION = "news-recall-candidates-v0.1"
_MIN_WINDOW = timedelta(days=30)
_MAX_WINDOW = timedelta(days=93)
_SOURCE_KEYS = (("news:alpaca:amd", "AMD"), ("news:alpaca:nvda", "NVDA"))


@dataclass(frozen=True, slots=True)
class NewsRecallCandidate:
    provider_article_id: str
    query_symbols: tuple[str, ...]
    headline: str
    publisher: str | None
    article_url: str | None
    provider_symbols: tuple[str, ...]
    provider_published_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.provider_article_id, str) or not self.provider_article_id:
            raise ContractViolation("candidate provider_article_id must be non-blank text")
        if not isinstance(self.query_symbols, tuple) or not self.query_symbols:
            raise ContractViolation("candidate query_symbols must be non-empty immutable tuple")
        if tuple(sorted(set(self.query_symbols))) != self.query_symbols:
            raise ContractViolation("candidate query_symbols must be sorted unique values")
        if not isinstance(self.provider_symbols, tuple):
            raise ContractViolation("candidate provider_symbols must be immutable tuple")
        if not isinstance(self.headline, str) or not self.headline:
            raise ContractViolation("candidate headline must be non-blank text")
        if self.publisher is not None and (not isinstance(self.publisher, str) or not self.publisher):
            raise ContractViolation("candidate publisher must be non-blank text when present")
        _utc(self.provider_published_at, "candidate provider_published_at")


def collect_news_recall_candidates(
    *,
    transport,
    window_start: datetime,
    window_end: datetime,
    page_size: int = 50,
    max_pages_per_symbol: int = 100,
) -> tuple[NewsRecallCandidate, ...]:
    _window(window_start, window_end)
    if not 1 <= page_size <= 50:
        raise ContractViolation("candidate page_size must be between 1 and 50")
    if not 1 <= max_pages_per_symbol <= 500:
        raise ContractViolation("candidate max_pages_per_symbol must be between 1 and 500")

    merged: dict[str, dict[str, object]] = {}
    adapter = AlpacaNewsAdapter(transport=transport)
    for source_key, query_symbol in _SOURCE_KEYS:
        request = AdapterRequest(
            source_key=source_key,
            window_start=window_start,
            window_end=window_end,
            page_size=page_size,
        )
        pages = collect_pages(adapter, request, max_pages=max_pages_per_symbol)
        for page in pages:
            if page.error is not None:
                raise ContractViolation(f"News candidate acquisition failed: {page.error.category}")
            for item in page.items:
                normalized = item.normalized
                published = normalized["published_at"].instant
                if published is None:
                    raise ContractViolation("News candidate requires provider publication instant")
                article_id = str(normalized["provider_article_id"])
                existing = merged.get(article_id)
                if existing is None:
                    merged[article_id] = {
                        "provider_article_id": article_id,
                        "query_symbols": {query_symbol},
                        "headline": normalized["headline"],
                        "publisher": normalized["publisher"],
                        "article_url": normalized["article_url"],
                        "provider_symbols": tuple(normalized["provider_symbols"]),
                        "provider_published_at": published,
                    }
                else:
                    existing["query_symbols"].add(query_symbol)
                    if (
                        existing["headline"] != normalized["headline"]
                        or existing["publisher"] != normalized["publisher"]
                        or existing["article_url"] != normalized["article_url"]
                        or existing["provider_symbols"] != tuple(normalized["provider_symbols"])
                        or existing["provider_published_at"] != published
                    ):
                        raise ContractViolation("same provider article ID returned conflicting normalized metadata")

    candidates = [
        NewsRecallCandidate(
            provider_article_id=value["provider_article_id"],
            query_symbols=tuple(sorted(value["query_symbols"])),
            headline=value["headline"],
            publisher=value["publisher"],
            article_url=value["article_url"],
            provider_symbols=value["provider_symbols"],
            provider_published_at=value["provider_published_at"],
        )
        for value in merged.values()
    ]
    return tuple(sorted(candidates, key=lambda item: (item.provider_published_at, item.provider_article_id)))


def write_news_recall_candidates(
    *,
    data_root: Path,
    filename: str,
    window_start: datetime,
    window_end: datetime,
    candidates: tuple[NewsRecallCandidate, ...],
) -> Path:
    _window(window_start, window_end)
    if not isinstance(data_root, Path):
        raise ContractViolation("data_root must be pathlib.Path")
    if not isinstance(filename, str) or not filename.endswith(".json") or Path(filename).name != filename:
        raise ContractViolation("candidate filename must be a simple .json filename")
    if not isinstance(candidates, tuple) or any(not isinstance(item, NewsRecallCandidate) for item in candidates):
        raise ContractViolation("candidates must be immutable NewsRecallCandidate tuple")

    destination = data_root / "benchmarks" / "n1-006" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": NEWS_RECALL_CANDIDATE_SCHEMA_VERSION,
        "provider_key": ALPACA_NEWS_PROVIDER_KEY,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "candidate_count": len(candidates),
        "candidates": [
            {
                "provider_article_id": item.provider_article_id,
                "query_symbols": list(item.query_symbols),
                "headline": item.headline,
                "publisher": item.publisher,
                "article_url": item.article_url,
                "provider_symbols": list(item.provider_symbols),
                "provider_published_at": item.provider_published_at.isoformat(),
            }
            for item in candidates
        ],
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _window(start: datetime, end: datetime) -> None:
    _utc(start, "window_start")
    _utc(end, "window_end")
    duration = end - start
    if duration < _MIN_WINDOW or duration > _MAX_WINDOW:
        raise ContractViolation("News candidate window must span 30 through 93 days")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
