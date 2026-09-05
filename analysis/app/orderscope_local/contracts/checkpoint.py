"""Durable, provider-neutral checkpoint contract for bounded acquisition.

This boundary stores only the information needed to resume an already bounded
provider/source stream.  It intentionally does not define item identity,
deduplication, provider payloads, or a database implementation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from .errors import ContractViolation


class CheckpointState(StrEnum):
    """Whether the saved cursor can be resumed or the bounded run is terminal."""

    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    PARTIAL = "partial"
    ERROR = "error"


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ContractViolation(f"{field} must include an explicit timezone")
    if value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _require_key(value: str, field: str) -> None:
    if not value.strip():
        raise ContractViolation(f"{field} cannot be blank")
    if len(value) > 256:
        raise ContractViolation(f"{field} exceeds 256 characters")


@dataclass(frozen=True)
class CheckpointScope:
    """Stable provider/source partition for one independent checkpoint stream."""

    provider_key: str
    source_key: str

    def __post_init__(self) -> None:
        _require_key(self.provider_key, "provider_key")
        _require_key(self.source_key, "source_key")


@dataclass(frozen=True)
class BoundedWindow:
    """A UTC half-open interval that a checkpoint may resume within."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _require_utc(self.start, "window_start")
        _require_utc(self.end, "window_end")
        if self.start >= self.end:
            raise ContractViolation("window must be non-empty and half-open")


@dataclass(frozen=True)
class OpaqueCursor:
    """Provider cursor retained verbatim only for the scoped bounded stream."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ContractViolation("cursor cannot be blank")
        if len(self.value) > 4096:
            raise ContractViolation("cursor exceeds 4096 characters")


@dataclass(frozen=True)
class CheckpointError:
    """Sanitized error state that is safe to retain with a checkpoint.

    Provider error text is intentionally excluded: it can contain response-body
    fragments or credentials and belongs only in bounded operational diagnostics.
    """

    category: str
    retryable: bool
    retry_after: timedelta | None = None

    def __post_init__(self) -> None:
        _require_key(self.category, "error_category")
        if not isinstance(self.retryable, bool):
            raise ContractViolation("error_retryable must be a boolean")
        if self.retry_after is not None:
            if self.retry_after < timedelta(0) or self.retry_after > timedelta(hours=24):
                raise ContractViolation("retry_after must be bounded to 24 hours")


@dataclass(frozen=True)
class AcquisitionCheckpoint:
    """Storage-neutral durable state for a bounded provider/source run.

    ``resume_cursor`` is the cursor to submit on the next request.  For a
    partial page or error it deliberately remains at the last safe request
    boundary (and may be ``None`` for a failure of the initial request), so a
    later adapter can safely replay rather than skip uncertain results.
    """

    scope: CheckpointScope
    window: BoundedWindow
    state: CheckpointState
    observed_at: datetime
    resume_cursor: OpaqueCursor | None = None
    error: CheckpointError | None = None
    retry_not_before: datetime | None = None

    def __post_init__(self) -> None:
        _require_utc(self.observed_at, "observed_at")
        if self.retry_not_before is not None:
            _require_utc(self.retry_not_before, "retry_not_before")
            if self.retry_not_before < self.observed_at:
                raise ContractViolation("retry_not_before cannot precede observed_at")
        if self.state is CheckpointState.COMPLETE:
            if self.resume_cursor is not None or self.error is not None or self.retry_not_before is not None:
                raise ContractViolation("complete checkpoint cannot retain resume or error state")
        elif self.state is CheckpointState.IN_PROGRESS:
            if self.resume_cursor is None:
                raise ContractViolation("in_progress checkpoint requires a resume_cursor")
            if self.error is not None or self.retry_not_before is not None:
                raise ContractViolation("in_progress checkpoint cannot retain error state")
        elif self.state is CheckpointState.ERROR and self.error is None:
            raise ContractViolation("error checkpoint requires error information")
        if self.retry_not_before is not None:
            if self.state not in {CheckpointState.PARTIAL, CheckpointState.ERROR}:
                raise ContractViolation("retry_not_before requires partial or error state")
            if self.error is None or not self.error.retryable:
                raise ContractViolation("retry_not_before requires a retryable error")

    def resume_request(self, *, page_size: int = 100):
        """Recreate the next adapter request without widening this checkpoint."""

        if self.state is CheckpointState.COMPLETE:
            raise ContractViolation("complete checkpoint cannot be resumed")
        # Local import keeps the durable checkpoint contract independent from
        # adapter implementation details at module-import time.
        from .provider import AdapterRequest

        return AdapterRequest(
            source_key=self.scope.source_key,
            window_start=self.window.start,
            window_end=self.window.end,
            cursor=None if self.resume_cursor is None else self.resume_cursor.value,
            page_size=page_size,
        )

    def to_record(self) -> dict[str, Any]:
        """Return a JSON/relational-storage-safe record without provider payloads."""

        return {
            "provider_key": self.scope.provider_key,
            "source_key": self.scope.source_key,
            "window_start": self.window.start.isoformat(),
            "window_end": self.window.end.isoformat(),
            "state": self.state.value,
            "observed_at": self.observed_at.isoformat(),
            "resume_cursor": None if self.resume_cursor is None else self.resume_cursor.value,
            "error_category": None if self.error is None else self.error.category,
            "error_retryable": None if self.error is None else self.error.retryable,
            "error_retry_after_seconds": (
                None if self.error is None or self.error.retry_after is None else self.error.retry_after.total_seconds()
            ),
            "retry_not_before": None if self.retry_not_before is None else self.retry_not_before.isoformat(),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> AcquisitionCheckpoint:
        """Restore a checkpoint written by :meth:`to_record`.

        The explicit field list prevents storage adapters from silently adding
        provider response bodies or credentials to the durable contract.
        """

        expected = {
            "provider_key", "source_key", "window_start", "window_end", "state", "observed_at",
            "resume_cursor", "error_category", "error_retryable",
            "error_retry_after_seconds", "retry_not_before",
        }
        if set(record) != expected:
            raise ContractViolation("checkpoint record fields do not match the durable contract")
        try:
            category = record["error_category"]
            retryable = record["error_retryable"]
            retry_after_seconds = record["error_retry_after_seconds"]
            error_fields = (category, retryable)
            if any(value is None for value in error_fields):
                if any(value is not None for value in (*error_fields, retry_after_seconds)):
                    raise ContractViolation("checkpoint error fields must be all present or absent")
                error = None
            else:
                if not isinstance(retryable, bool):
                    raise ContractViolation("error_retryable must be a boolean")
                retry_after = None if retry_after_seconds is None else timedelta(seconds=float(retry_after_seconds))
                error = CheckpointError(category=category, retryable=retryable, retry_after=retry_after)
            return cls(
                scope=CheckpointScope(record["provider_key"], record["source_key"]),
                window=BoundedWindow(datetime.fromisoformat(record["window_start"]), datetime.fromisoformat(record["window_end"])),
                state=CheckpointState(record["state"]),
                observed_at=datetime.fromisoformat(record["observed_at"]),
                resume_cursor=None if record["resume_cursor"] is None else OpaqueCursor(record["resume_cursor"]),
                error=error,
                retry_not_before=(
                    None if record["retry_not_before"] is None else datetime.fromisoformat(record["retry_not_before"])
                ),
            )
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ContractViolation("invalid checkpoint record") from exc
