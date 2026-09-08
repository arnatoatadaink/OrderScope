"""Alpaca News metadata adapter for N0-002.

Provider-specific request/response fields terminate in this module. The adapter
returns the common I0-007 AdapterPage/AdapterItem contract and never requests or
persists article body content. N0-004 owns temporary body acquisition.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Protocol

from orderscope_local.contracts import (
    AdapterItem,
    AdapterPage,
    AdapterRequest,
    ContentHash,
    ContentIdentity,
    ContractViolation,
    ErrorInfo,
    SourceTimestamp,
    StableIdentity,
)


ALPACA_NEWS_PROVIDER_KEY = "alpaca-news"
_CANARY_SOURCES = {
    "news:alpaca:amd": "AMD",
    "news:alpaca:nvda": "NVDA",
}


class AlpacaNewsTransport(Protocol):
    """Injected HTTP boundary; credentials and raw response handling stay outside Core."""

    def get_news(
        self,
        *,
        symbol: str,
        start: str,
        end: str,
        limit: int,
        page_token: str | None,
        include_content: bool,
        sort: str,
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class AlpacaNewsRequestFailure(Exception):
    """Sanitized provider/transport failure safe to cross the adapter boundary."""

    category: str
    retryable: bool
    retry_after: timedelta | None = None


@dataclass(frozen=True, slots=True)
class NewsArticleMetadata:
    """Provider-neutral durable News metadata emitted by the Alpaca adapter."""

    provider_key: str
    provider_article_id: str
    query_symbol: str
    headline: str
    publisher: str
    article_url: str
    published_at: SourceTimestamp
    provider_updated_at: SourceTimestamp | None
    author: str | None
    summary: str | None
    provider_symbols: tuple[str, ...]
    body_capability: bool

    def __post_init__(self) -> None:
        for field, value, limit in (
            ("provider_key", self.provider_key, 128),
            ("provider_article_id", self.provider_article_id, 512),
            ("query_symbol", self.query_symbol, 32),
            ("headline", self.headline, 2048),
            ("publisher", self.publisher, 256),
            ("article_url", self.article_url, 2048),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > limit:
                raise ContractViolation(f"news {field} must be bounded non-blank text")
        for field, value, limit in (("author", self.author, 512), ("summary", self.summary, 8192)):
            if value is not None and (not isinstance(value, str) or value != value.strip() or len(value) > limit):
                raise ContractViolation(f"news {field} must be bounded text when present")
        if not isinstance(self.published_at, SourceTimestamp):
            raise ContractViolation("news published_at must use SourceTimestamp")
        if self.provider_updated_at is not None and not isinstance(self.provider_updated_at, SourceTimestamp):
            raise ContractViolation("news provider_updated_at must use SourceTimestamp")
        if not isinstance(self.provider_symbols, tuple):
            raise ContractViolation("news provider_symbols must be an immutable tuple")
        if len(self.provider_symbols) != len(set(self.provider_symbols)):
            raise ContractViolation("news provider_symbols cannot contain duplicates")
        for symbol in self.provider_symbols:
            if not isinstance(symbol, str) or not symbol.strip() or symbol != symbol.strip() or len(symbol) > 32:
                raise ContractViolation("news provider symbol must be bounded text")
        if not isinstance(self.body_capability, bool):
            raise ContractViolation("news body_capability must be boolean")

    def to_normalized(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "provider_article_id": self.provider_article_id,
            "query_symbol": self.query_symbol,
            "headline": self.headline,
            "publisher": self.publisher,
            "article_url": self.article_url,
            "published_at": self.published_at,
            "provider_updated_at": self.provider_updated_at,
            "author": self.author,
            "summary": self.summary,
            "provider_symbols": self.provider_symbols,
            "body_capability": self.body_capability,
        }


class AlpacaNewsAdapter:
    """Fetch one bounded Alpaca News metadata page for AMD or NVIDIA."""

    def __init__(
        self,
        *,
        transport: AlpacaNewsTransport,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch(self, request: AdapterRequest) -> AdapterPage:
        symbol = _validate_request(request)
        retrieved_at = self._clock()
        _require_utc(retrieved_at, "retrieved_at")
        try:
            payload = self._transport.get_news(
                symbol=symbol,
                start=request.window_start.isoformat().replace("+00:00", "Z"),
                end=request.window_end.isoformat().replace("+00:00", "Z"),
                limit=request.page_size,
                page_token=request.cursor,
                include_content=False,
                sort="asc",
            )
            items, next_cursor = _decode_response(payload, request=request, query_symbol=symbol)
            return AdapterPage(
                items=items,
                next_cursor=next_cursor,
                partial=False,
                retrieved_at=retrieved_at,
                available_at=retrieved_at,
            )
        except AlpacaNewsRequestFailure as exc:
            return _error_page(retrieved_at, exc)
        except ContractViolation:
            raise
        except Exception:
            return _error_page(retrieved_at, AlpacaNewsRequestFailure("transport_error", True))


def _error_page(retrieved_at: datetime, failure: AlpacaNewsRequestFailure) -> AdapterPage:
    return AdapterPage(
        items=(),
        next_cursor=None,
        partial=False,
        retrieved_at=retrieved_at,
        available_at=retrieved_at,
        error=ErrorInfo(
            category=failure.category,
            retryable=failure.retryable,
            message="Alpaca News request failed",
            retry_after=failure.retry_after,
        ),
    )


def _validate_request(request: AdapterRequest) -> str:
    if not isinstance(request, AdapterRequest):
        raise ContractViolation("Alpaca News request must be an AdapterRequest")
    symbol = _CANARY_SOURCES.get(request.source_key)
    if symbol is None:
        raise ContractViolation("Alpaca News source is outside the AMD/NVDA Corporate Canary")
    _require_utc(request.window_start, "window_start")
    _require_utc(request.window_end, "window_end")
    if request.window_start >= request.window_end:
        raise ContractViolation("Alpaca News window must be non-empty and half-open")
    if not 1 <= request.page_size <= 50:
        raise ContractViolation("Alpaca News page_size must be between 1 and 50")
    if request.cursor is not None and (not request.cursor.strip() or len(request.cursor) > 2048):
        raise ContractViolation("Alpaca News page token must be bounded text")
    return symbol


def _decode_response(
    payload: Mapping[str, Any], *, request: AdapterRequest, query_symbol: str
) -> tuple[tuple[AdapterItem, ...], str | None]:
    if not isinstance(payload, Mapping):
        raise AlpacaNewsRequestFailure("invalid_response", False)
    raw_items = payload.get("news")
    if not isinstance(raw_items, list):
        raise AlpacaNewsRequestFailure("invalid_response", False)
    next_cursor = payload.get("next_page_token")
    if next_cursor is not None and (not isinstance(next_cursor, str) or not next_cursor.strip() or len(next_cursor) > 2048):
        raise AlpacaNewsRequestFailure("invalid_response", False)
    if next_cursor == request.cursor:
        raise AlpacaNewsRequestFailure("cursor_loop", False)
    if len(raw_items) > request.page_size:
        raise AlpacaNewsRequestFailure("invalid_response", False)
    items = tuple(_normalize_article(value, query_symbol=query_symbol) for value in raw_items)
    return items, next_cursor


def _normalize_article(value: object, *, query_symbol: str) -> AdapterItem:
    if not isinstance(value, Mapping):
        raise AlpacaNewsRequestFailure("invalid_response", False)
    if "content" in value:
        # N0-002 must never carry a body even if a transport accidentally requested it.
        raise AlpacaNewsRequestFailure("body_leak", False)

    article_id = _required_text(value.get("id"), coerce_int=True, maximum=512)
    headline = _required_text(value.get("headline"), maximum=2048)
    source = _required_text(value.get("source"), maximum=256)
    url = _required_text(value.get("url"), maximum=2048)
    created = decode_alpaca_news_timestamp(value.get("created_at"))
    updated_raw = value.get("updated_at")
    updated = decode_alpaca_news_timestamp(updated_raw) if updated_raw is not None else None
    if updated is not None and _timestamp_instant(updated) < _timestamp_instant(created):
        raise AlpacaNewsRequestFailure("invalid_response", False)

    symbols = _string_tuple(value.get("symbols", ()), maximum=32)
    author = _optional_text(value.get("author"), maximum=512)
    summary = _optional_text(value.get("summary"), maximum=8192)
    metadata = NewsArticleMetadata(
        provider_key=ALPACA_NEWS_PROVIDER_KEY,
        provider_article_id=article_id,
        query_symbol=query_symbol,
        headline=headline,
        publisher=source,
        article_url=url,
        published_at=created,
        provider_updated_at=updated,
        author=author,
        summary=summary,
        provider_symbols=symbols,
        body_capability=True,
    )
    normalized = metadata.to_normalized()
    canonical = _identity_payload(normalized)
    identity = ContentIdentity(
        StableIdentity.provider_article(ALPACA_NEWS_PROVIDER_KEY, article_id),
        ContentHash(hashlib.sha256(canonical.encode("utf-8")).hexdigest()),
    )
    return AdapterItem(normalized=normalized, content_identity=identity)


def decode_alpaca_news_timestamp(value: object) -> SourceTimestamp:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise AlpacaNewsRequestFailure("invalid_response", False)
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise AlpacaNewsRequestFailure("invalid_response", False) from exc
    if parsed.tzinfo is None:
        raise AlpacaNewsRequestFailure("invalid_response", False)
    parsed = parsed.astimezone(timezone.utc)
    return SourceTimestamp.at(parsed)


def _required_text(value: object, *, maximum: int, coerce_int: bool = False) -> str:
    if coerce_int and isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > maximum:
        raise AlpacaNewsRequestFailure("invalid_response", False)
    return value


def _optional_text(value: object, *, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value != value.strip() or len(value) > maximum:
        raise AlpacaNewsRequestFailure("invalid_response", False)
    return value or None


def _string_tuple(value: object, *, maximum: int) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise AlpacaNewsRequestFailure("invalid_response", False)
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or item != item.strip() or len(item) > maximum:
            raise AlpacaNewsRequestFailure("invalid_response", False)
        if item not in result:
            result.append(item)
    return tuple(result)


def _identity_payload(normalized: Mapping[str, object]) -> str:
    def encode(value: object) -> object:
        if isinstance(value, SourceTimestamp):
            return {
                "precision": value.precision.value,
                "instant": value.instant.isoformat() if value.instant is not None else None,
                "calendar_date": value.calendar_date.isoformat() if value.calendar_date is not None else None,
                "source_timezone": value.source_timezone,
            }
        if isinstance(value, tuple):
            return [encode(item) for item in value]
        return value

    serializable = {key: encode(value) for key, value in normalized.items()}
    return json.dumps(serializable, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _timestamp_instant(value: SourceTimestamp) -> datetime:
    if value.instant is None:
        raise AlpacaNewsRequestFailure("invalid_response", False)
    return value.instant


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
