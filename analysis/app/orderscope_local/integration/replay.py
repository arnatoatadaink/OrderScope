"""Registered bounded replay execution for Packet E.

Only explicitly registered local/operator replay sources may execute.  The first
concrete source is the accepted metadata-only Alpaca News AMD/NVDA canary.  Raw
article bodies are never requested or persisted by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from orderscope_local.contracts import AdapterRequest, ContractViolation, collect_pages
from orderscope_local.news.alpaca import AlpacaNewsAdapter, AlpacaNewsTransport


REPLAY_REGISTRY_VERSION = "operator-replay-registry-v0.1"
ALPACA_NEWS_REPLAY_SOURCE = "alpaca-news"
ALPACA_NEWS_REPLAY_SCHEMA_VERSION = "alpaca-news-replay-v0.1"
_MAX_WORK_IDS = 100
_SOURCE_KEYS = (("news:alpaca:amd", "AMD"), ("news:alpaca:nvda", "NVDA"))


class RegisteredReplayHandler(Protocol):
    def replay(self, *, start: datetime, end: datetime, work_ids: Sequence[str]) -> int: ...


class RegisteredReplayExecutor:
    """Dispatch one bounded replay only to an explicitly registered handler."""

    def __init__(self, handlers: Mapping[str, RegisteredReplayHandler]) -> None:
        if not handlers:
            raise ContractViolation("replay registry must contain at least one source")
        checked: dict[str, RegisteredReplayHandler] = {}
        for source, handler in handlers.items():
            _identity(source, "registered replay source")
            if source in checked:
                raise ContractViolation("duplicate registered replay source")
            checked[source] = handler
        self._handlers = checked

    def replay(self, *, source: str, start: datetime, end: datetime, work_ids: Sequence[str]) -> int:
        _identity(source, "replay source")
        _window(start, end)
        ids = _work_ids(work_ids)
        handler = self._handlers.get(source)
        if handler is None:
            raise ContractViolation("replay source is not registered")
        completed = handler.replay(start=start, end=end, work_ids=ids)
        if not isinstance(completed, int) or isinstance(completed, bool) or completed < 0 or completed > len(ids):
            raise ContractViolation("registered replay handler returned invalid completion count")
        return completed


@dataclass(slots=True)
class AlpacaNewsMetadataReplay:
    transport: AlpacaNewsTransport
    data_root: Path
    page_size: int = 50
    max_pages_per_symbol: int = 10
    clock: callable | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.data_root, Path):
            raise ContractViolation("replay data_root must be pathlib.Path")
        if not 1 <= self.page_size <= 50:
            raise ContractViolation("replay page_size must be between 1 and 50")
        if not 1 <= self.max_pages_per_symbol <= 100:
            raise ContractViolation("replay max_pages_per_symbol must be between 1 and 100")
        if self.clock is None:
            self.clock = lambda: datetime.now(timezone.utc)

    def replay(self, *, start: datetime, end: datetime, work_ids: Sequence[str]) -> int:
        _window(start, end)
        ids = _work_ids(work_ids)
        generated_at = self.clock()
        _utc(generated_at, "replay generated_at")
        adapter = AlpacaNewsAdapter(transport=self.transport, clock=lambda: generated_at)
        items: list[dict[str, object]] = []
        for source_key, symbol in _SOURCE_KEYS:
            request = AdapterRequest(
                source_key=source_key,
                window_start=start,
                window_end=end,
                page_size=self.page_size,
            )
            pages = collect_pages(adapter, request, max_pages=self.max_pages_per_symbol)
            for page in pages:
                if page.error is not None:
                    raise ContractViolation(f"registered replay failed: {page.error.category}")
                for item in page.items:
                    normalized = item.normalized
                    published = normalized["published_at"].instant
                    if published is None:
                        raise ContractViolation("registered replay requires provider publication instant")
                    items.append({
                        "provider_article_id": str(normalized["provider_article_id"]),
                        "query_symbol": symbol,
                        "provider_published_at": published.isoformat(),
                        "provider_symbols": list(normalized["provider_symbols"]),
                    })

        items.sort(key=lambda value: (
            str(value["provider_published_at"]), str(value["provider_article_id"]), str(value["query_symbol"]),
        ))
        relative = self._write_receipt(
            start=start,
            end=end,
            work_ids=ids,
            generated_at=generated_at,
            items=items,
        )
        if relative.is_absolute():
            raise ContractViolation("replay receipt path must remain relative")
        return len(ids)

    def _write_receipt(
        self,
        *,
        start: datetime,
        end: datetime,
        work_ids: tuple[str, ...],
        generated_at: datetime,
        items: list[dict[str, object]],
    ) -> Path:
        identity = "|".join((ALPACA_NEWS_REPLAY_SOURCE, start.isoformat(), end.isoformat(), *work_ids))
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        relative = Path("operator") / "replays" / f"alpaca-news-{digest}.json"
        destination = self.data_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": ALPACA_NEWS_REPLAY_SCHEMA_VERSION,
            "registry_version": REPLAY_REGISTRY_VERSION,
            "source": ALPACA_NEWS_REPLAY_SOURCE,
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "work_ids": list(work_ids),
            "generated_at": generated_at.isoformat(),
            "item_count": len(items),
            "items": items,
        }
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return relative


def _work_ids(values: Sequence[str]) -> tuple[str, ...]:
    ids = tuple(values)
    if not ids:
        raise ContractViolation("bounded replay requires at least one work_id")
    if len(ids) > _MAX_WORK_IDS:
        raise ContractViolation("bounded replay work_id count exceeds 100")
    if len(set(ids)) != len(ids):
        raise ContractViolation("bounded replay work_ids must be unique")
    for value in ids:
        _identity(value, "work_id")
    return ids


def _window(start: datetime, end: datetime) -> None:
    _utc(start, "start")
    _utc(end, "end")
    if start >= end:
        raise ContractViolation("bounded replay requires start < end")
    if end - start > timedelta(days=31):
        raise ContractViolation("bounded replay exceeds 31 days")


def _identity(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 512:
        raise ContractViolation(f"{field} must be bounded non-blank canonical text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
