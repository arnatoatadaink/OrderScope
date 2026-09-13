"""Read-only Corporate coverage summary for X0-002."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.checkpoint import AcquisitionCheckpoint, CheckpointState
from orderscope_local.contracts.temporary_content import TemporaryContent, TemporaryContentState


CORPORATE_COVERAGE_SCHEMA_VERSION = "corporate-coverage-summary-v0.1"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _bounded(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be non-blank and bounded")


@dataclass(frozen=True, slots=True)
class RetentionObservation:
    """Explicitly associates one temporary-content lifecycle record with a source."""

    source_key: str
    content: TemporaryContent

    def __post_init__(self) -> None:
        _bounded(self.source_key, "source_key")
        if not isinstance(self.content, TemporaryContent):
            raise ContractViolation("content must be TemporaryContent")


@dataclass(frozen=True, slots=True)
class SourceCoverageInput:
    provider_key: str
    source_key: str
    checkpoints: tuple[AcquisitionCheckpoint, ...]
    retention: tuple[RetentionObservation, ...] = ()

    def __post_init__(self) -> None:
        _bounded(self.provider_key, "provider_key")
        _bounded(self.source_key, "source_key")
        if not isinstance(self.checkpoints, tuple):
            raise ContractViolation("checkpoints must be an immutable tuple")
        if not isinstance(self.retention, tuple):
            raise ContractViolation("retention must be an immutable tuple")
        for checkpoint in self.checkpoints:
            if not isinstance(checkpoint, AcquisitionCheckpoint):
                raise ContractViolation("unsupported checkpoint input")
            if checkpoint.scope.provider_key != self.provider_key or checkpoint.scope.source_key != self.source_key:
                raise ContractViolation("checkpoint scope must match coverage source")
        for observation in self.retention:
            if not isinstance(observation, RetentionObservation):
                raise ContractViolation("unsupported retention observation")
            if observation.source_key != self.source_key:
                raise ContractViolation("retention observation source must match coverage source")


@dataclass(frozen=True, slots=True)
class SourceCoverageSummary:
    schema_version: str
    provider_key: str
    source_key: str
    last_success_at: datetime | None
    latest_observed_at: datetime | None
    latest_state: CheckpointState | None
    resume_cursor: str | None
    lag_seconds: float | None
    error_category: str | None
    error_retryable: bool | None
    retry_not_before: datetime | None
    retention_pending_count: int
    retention_overdue_count: int
    retention_next_due_at: datetime | None

    def __post_init__(self) -> None:
        if self.schema_version != CORPORATE_COVERAGE_SCHEMA_VERSION:
            raise ContractViolation("unsupported Corporate coverage schema version")
        _bounded(self.provider_key, "provider_key")
        _bounded(self.source_key, "source_key")
        for value, field in (
            (self.last_success_at, "last_success_at"),
            (self.latest_observed_at, "latest_observed_at"),
            (self.retry_not_before, "retry_not_before"),
            (self.retention_next_due_at, "retention_next_due_at"),
        ):
            if value is not None:
                _utc(value, field)
        if self.lag_seconds is not None and self.lag_seconds < 0:
            raise ContractViolation("lag_seconds cannot be negative")
        for value, field in (
            (self.retention_pending_count, "retention_pending_count"),
            (self.retention_overdue_count, "retention_overdue_count"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ContractViolation(f"{field} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class CorporateCoverageSummary:
    schema_version: str
    as_of: datetime
    sources: tuple[SourceCoverageSummary, ...]

    def __post_init__(self) -> None:
        if self.schema_version != CORPORATE_COVERAGE_SCHEMA_VERSION:
            raise ContractViolation("unsupported Corporate coverage schema version")
        _utc(self.as_of, "as_of")
        if not isinstance(self.sources, tuple):
            raise ContractViolation("sources must be an immutable tuple")
        keys: set[tuple[str, str]] = set()
        for source in self.sources:
            if not isinstance(source, SourceCoverageSummary):
                raise ContractViolation("unsupported source coverage summary")
            key = (source.provider_key, source.source_key)
            if key in keys:
                raise ContractViolation("coverage source must be unique")
            keys.add(key)


def summarize_corporate_coverage(
    *,
    as_of: datetime,
    sources: tuple[SourceCoverageInput, ...],
) -> CorporateCoverageSummary:
    """Summarize acquisition/retention state without mutating adapter state."""

    _utc(as_of, "as_of")
    if not isinstance(sources, tuple):
        raise ContractViolation("sources must be an immutable tuple")

    summaries = tuple(
        sorted(
            (_summarize_source(as_of=as_of, source=source) for source in sources),
            key=lambda item: (item.provider_key, item.source_key),
        )
    )
    return CorporateCoverageSummary(
        schema_version=CORPORATE_COVERAGE_SCHEMA_VERSION,
        as_of=as_of,
        sources=summaries,
    )


def _summarize_source(*, as_of: datetime, source: SourceCoverageInput) -> SourceCoverageSummary:
    if not isinstance(source, SourceCoverageInput):
        raise ContractViolation("source must be SourceCoverageInput")

    visible = tuple(checkpoint for checkpoint in source.checkpoints if checkpoint.observed_at <= as_of)
    latest = max(visible, key=lambda item: item.observed_at, default=None)
    complete = tuple(item for item in visible if item.state is CheckpointState.COMPLETE)
    last_success = max((item.observed_at for item in complete), default=None)
    lag = None if last_success is None else (as_of - last_success).total_seconds()

    pending = tuple(
        observation.content
        for observation in source.retention
        if observation.content.captured_at <= as_of and observation.content.state is not TemporaryContentState.DELETED
    )
    overdue = tuple(content for content in pending if content.expires_at <= as_of)
    next_due = min((content.expires_at for content in pending), default=None)

    error = None if latest is None else latest.error
    return SourceCoverageSummary(
        schema_version=CORPORATE_COVERAGE_SCHEMA_VERSION,
        provider_key=source.provider_key,
        source_key=source.source_key,
        last_success_at=last_success,
        latest_observed_at=None if latest is None else latest.observed_at,
        latest_state=None if latest is None else latest.state,
        resume_cursor=None if latest is None or latest.resume_cursor is None else latest.resume_cursor.value,
        lag_seconds=lag,
        error_category=None if error is None else error.category,
        error_retryable=None if error is None else error.retryable,
        retry_not_before=None if latest is None else latest.retry_not_before,
        retention_pending_count=len(pending),
        retention_overdue_count=len(overdue),
        retention_next_due_at=next_due,
    )
