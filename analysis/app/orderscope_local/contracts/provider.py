"""Small, provider-neutral boundary for bounded incremental adapters.

The module deliberately contains no HTTP, persistence, or provider-specific fields.
Adapters translate their response into :class:`AdapterPage`; the common test kit can
then exercise every adapter with the same invariants.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Protocol

from .errors import ContractViolation
from .provenance import ProviderRevision
from .identity import (
    ContentIdentity,
    IdempotencyClassification,
    RevisionRelationship,
    classify_idempotency,
)

if TYPE_CHECKING:
    from .checkpoint import AcquisitionCheckpoint
    from .temporary_content import TemporaryContent


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

    items: tuple[Mapping[str, Any] | AdapterItem, ...]
    next_cursor: str | None
    partial: bool
    retrieved_at: datetime
    available_at: datetime
    provider_revision: ProviderRevision | None = None
    error: ErrorInfo | None = None


@dataclass(frozen=True)
class AdapterItem:
    """One normalized item plus accepted identity and optional content handoff."""

    normalized: Mapping[str, Any]
    content_identity: ContentIdentity
    temporary_content: TemporaryContent | None = None


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
    if page.provider_revision is not None and not isinstance(page.provider_revision, ProviderRevision):
        raise ContractViolation("provider_revision must be a ProviderRevision")
    if page.error is not None and not page.partial and page.items:
        raise ContractViolation("an error page with items must be marked partial")
    if page.error is not None and page.next_cursor is not None:
        raise ContractViolation("an error page cannot advance the cursor")
    if page.error is not None and page.error.retry_after is not None:
        if page.error.retry_after < timedelta(0) or page.error.retry_after > timedelta(hours=24):
            raise ContractViolation("retry_after must be bounded to 24 hours")
    if page.partial and page.error is None:
        raise ContractViolation("partial page requires error information")
    if page.next_cursor is not None and page.next_cursor == request.cursor:
        raise ContractViolation("next_cursor did not advance")
    for item in page.items:
        if isinstance(item, AdapterItem):
            assert_adapter_item_contract(item)
        elif not isinstance(item, Mapping):
            raise ContractViolation("normalized items must be mappings or AdapterItems")
    assert_secret_free(page)


def assert_secret_free(value: Any, secret_names: Sequence[str] = ()) -> None:
    """Reject credentials and provider response bodies in normalized output."""

    forbidden_names = {name.casefold() for name in secret_names} | {
        "api_key", "apikey", "api_secret", "client_secret", "access_token",
        "authorization", "password", "secret", "token", "provider_response_body",
    }

    def visit(node: Any, path: str = "") -> None:
        if is_dataclass(node) and not isinstance(node, type):
            for field in fields(node):
                visit(getattr(node, field.name), f"{path}/{field.name}")
        elif isinstance(node, Mapping):
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


def assert_adapter_item_contract(item: AdapterItem) -> None:
    """Validate an adapter item's accepted identity and lifecycle handoff."""

    if not isinstance(item, AdapterItem):
        raise ContractViolation("item must be an AdapterItem")
    if not isinstance(item.normalized, Mapping):
        raise ContractViolation("normalized item must be a mapping")
    if not isinstance(item.content_identity, ContentIdentity):
        raise ContractViolation("content_identity must be a ContentIdentity")
    if item.temporary_content is not None:
        # Local import avoids a cycle: the lifecycle contract uses the shared
        # secret scanner for its bounded metadata fields.
        from .temporary_content import TemporaryContent, validate_temporary_content

        if not isinstance(item.temporary_content, TemporaryContent):
            raise ContractViolation("temporary_content must be a TemporaryContent")
        validate_temporary_content(item.temporary_content)
    assert_secret_free(item)


def classify_adapter_item(
    item: AdapterItem,
    accepted: ContentIdentity | None = None,
    *,
    revision_relationship: RevisionRelationship | None = None,
) -> IdempotencyClassification:
    """Apply the accepted stable-identity classifier to one adapter item."""

    assert_adapter_item_contract(item)
    if accepted is None:
        if revision_relationship is not None:
            raise ContractViolation("new item cannot have a revision relationship")
        return IdempotencyClassification.NEW
    return classify_idempotency(
        accepted,
        item.content_identity,
        revision_relationship=revision_relationship,
    )


def checkpoint_for_page(
    *, provider_key: str, request: AdapterRequest, page: AdapterPage
) -> AcquisitionCheckpoint:
    """Create the safe durable I0-003 checkpoint handoff for a validated page."""

    from .checkpoint import (
        AcquisitionCheckpoint,
        BoundedWindow,
        CheckpointError,
        CheckpointScope,
        CheckpointState,
        OpaqueCursor,
    )

    assert_page_contract(page, request)
    scope = CheckpointScope(provider_key, request.source_key)
    window = BoundedWindow(request.window_start, request.window_end)
    if page.error is not None:
        error = CheckpointError(page.error.category, page.error.retryable, page.error.retry_after)
        state = CheckpointState.PARTIAL if page.partial else CheckpointState.ERROR
        resume = None if request.cursor is None else OpaqueCursor(request.cursor)
        retry_not_before = (
            page.retrieved_at + page.error.retry_after
            if page.error.retryable and page.error.retry_after is not None
            else None
        )
        return AcquisitionCheckpoint(
            scope=scope, window=window, state=state, observed_at=page.retrieved_at,
            resume_cursor=resume, error=error, retry_not_before=retry_not_before,
        )
    if page.next_cursor is None:
        return AcquisitionCheckpoint(
            scope=scope, window=window, state=CheckpointState.COMPLETE,
            observed_at=page.retrieved_at,
        )
    return AcquisitionCheckpoint(
        scope=scope, window=window, state=CheckpointState.IN_PROGRESS,
        observed_at=page.retrieved_at, resume_cursor=OpaqueCursor(page.next_cursor),
    )


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
