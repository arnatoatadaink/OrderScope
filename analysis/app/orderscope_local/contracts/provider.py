"""Small, provider-neutral boundary for bounded incremental adapters.

The module deliberately contains no HTTP, persistence, or provider-specific fields.
Adapters translate their response into :class:`AdapterPage`; the common test kit can
then exercise every adapter with the same invariants.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol


class ContractViolation(ValueError):
    """Raised when an adapter crosses the provider-neutral boundary incorrectly."""


@dataclass(frozen=True)
class AdapterRequest:
    """A bounded stream request.  A cursor is scoped to this exact stream."""

    source_key: str
    window_start: datetime
    window_end: datetime
    cursor: str | None = None
    page_size: int = 100


@dataclass(frozen=True)
class ErrorInfo:
    category: str
    retryable: bool
    message: str
    retry_after: timedelta | None = None


@dataclass(frozen=True)
class AdapterPage:
    """Normalized page returned by an adapter; provider payloads stop here."""

    items: tuple[Mapping[str, Any], ...]
    next_cursor: str | None
    partial: bool
    retrieved_at: datetime
    available_at: datetime
    provider_revision: str | None = None
    error: ErrorInfo | None = None


class ProviderAdapter(Protocol):
    def fetch(self, request: AdapterRequest) -> AdapterPage: ...


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ContractViolation(f"{field} must include an explicit timezone")


def assert_page_contract(page: AdapterPage, request: AdapterRequest) -> None:
    """Validate timestamps, bounded-page shape, and partial/error semantics."""

    _utc(request.window_start, "window_start")
    _utc(request.window_end, "window_end")
    _utc(page.retrieved_at, "retrieved_at")
    _utc(page.available_at, "available_at")
    if request.window_start >= request.window_end:
        raise ContractViolation("window must be non-empty and half-open")
    if not 1 <= request.page_size <= 10_000:
        raise ContractViolation("page_size is outside the bounded range")
    if len(page.items) > request.page_size:
        raise ContractViolation("adapter returned more items than page_size")
    if page.available_at > page.retrieved_at:
        raise ContractViolation("available_at cannot be later than retrieved_at")
    if page.error is not None and not page.partial and page.items:
        raise ContractViolation("an error page with items must be marked partial")
    if page.error is not None and page.error.retry_after is not None:
        if page.error.retry_after < timedelta(0) or page.error.retry_after > timedelta(hours=24):
            raise ContractViolation("retry_after must be bounded to 24 hours")
    if page.next_cursor is not None and page.next_cursor == request.cursor:
        raise ContractViolation("next_cursor did not advance")
    for item in page.items:
        if not isinstance(item, Mapping):
            raise ContractViolation("normalized items must be mappings")


def assert_secret_free(value: Any, secret_names: Sequence[str] = ()) -> None:
    """Reject credentials and provider response bodies in normalized output."""

    forbidden_names = {name.casefold() for name in secret_names} | {
        "api_key", "apikey", "api_secret", "client_secret", "access_token",
        "authorization", "password", "secret", "token", "provider_response_body",
    }

    def visit(node: Any, path: str = "") -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                key_text = str(key).casefold().replace("-", "_")
                if key_text in forbidden_names or any(part in key_text for part in ("credential", "authorization")):
                    raise ContractViolation(f"secret-like field crossed boundary at {path}/{key}")
                visit(child, f"{path}/{key}")
        elif isinstance(node, (list, tuple)):
            for index, child in enumerate(node):
                visit(child, f"{path}/{index}")
        elif isinstance(node, str):
            lowered = node.casefold()
            if "bearer " in lowered or "-----begin " in lowered:
                raise ContractViolation(f"secret-like value crossed boundary at {path}")

    visit(value)


def collect_pages(
    adapter: ProviderAdapter,
    request: AdapterRequest,
    *,
    max_pages: int = 100,
    on_page: Callable[[AdapterPage], None] | None = None,
) -> tuple[AdapterPage, ...]:
    """Collect a bounded cursor chain and reject loops or unbounded pagination."""

    if max_pages < 1:
        raise ContractViolation("max_pages must be positive")
    pages: list[AdapterPage] = []
    seen_cursors: set[str | None] = set()
    current = request
    for _ in range(max_pages):
        if current.cursor in seen_cursors:
            raise ContractViolation("cursor loop detected")
        seen_cursors.add(current.cursor)
        page = adapter.fetch(current)
        assert_page_contract(page, current)
        assert_secret_free(page.items)
        pages.append(page)
        if on_page:
            on_page(page)
        if page.error is not None or page.next_cursor is None:
            return tuple(pages)
        current = AdapterRequest(
            source_key=request.source_key,
            window_start=request.window_start,
            window_end=request.window_end,
            cursor=page.next_cursor,
            page_size=request.page_size,
        )
    raise ContractViolation("pagination exceeded max_pages")
