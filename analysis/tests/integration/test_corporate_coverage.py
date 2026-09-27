from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.checkpoint import (
    AcquisitionCheckpoint,
    BoundedWindow,
    CheckpointError,
    CheckpointScope,
    CheckpointState,
    OpaqueCursor,
)
from orderscope_local.contracts.fact_store import RetentionClass
from orderscope_local.contracts.temporary_content import TemporaryContent, TemporaryContentState
from orderscope_local.integration import (
    CORPORATE_COVERAGE_SCHEMA_VERSION,
    RetentionObservation,
    SourceCoverageInput,
    summarize_corporate_coverage,
)


UTC = timezone.utc
BASE = datetime(2026, 9, 9, 0, 0, tzinfo=UTC)


def _checkpoint(
    *,
    provider: str = "alpaca-news",
    source: str = "amd-news",
    state: CheckpointState,
    observed_minutes: int,
    cursor: str | None = None,
    error: CheckpointError | None = None,
    retry_minutes: int | None = None,
) -> AcquisitionCheckpoint:
    return AcquisitionCheckpoint(
        scope=CheckpointScope(provider, source),
        window=BoundedWindow(BASE - timedelta(hours=1), BASE + timedelta(hours=1)),
        state=state,
        observed_at=BASE + timedelta(minutes=observed_minutes),
        resume_cursor=None if cursor is None else OpaqueCursor(cursor),
        error=error,
        retry_not_before=None if retry_minutes is None else BASE + timedelta(minutes=retry_minutes),
    )


def _retention(
    *,
    source: str = "amd-news",
    state: TemporaryContentState,
    captured_minutes: int,
    expires_minutes: int,
) -> RetentionObservation:
    kwargs = dict(
        content_ref=f"tmp-{source}-{captured_minutes}",
        captured_at=BASE + timedelta(minutes=captured_minutes),
        expires_at=BASE + timedelta(minutes=expires_minutes),
    )
    if state is TemporaryContentState.STAGED:
        content = TemporaryContent(retention_class=RetentionClass.TEMPORARY_SUCCESS, state=state, **kwargs)
    elif state is TemporaryContentState.EXTRACTION_SUCCEEDED:
        content = TemporaryContent(
            retention_class=RetentionClass.TEMPORARY_SUCCESS,
            state=state,
            extraction_completed_at=BASE + timedelta(minutes=captured_minutes + 1),
            **kwargs,
        )
    elif state is TemporaryContentState.EXCEPTION:
        content = TemporaryContent(
            retention_class=RetentionClass.TEMPORARY_EXCEPTION,
            state=state,
            exception_reason="fixture exception",
            **kwargs,
        )
    else:
        content = TemporaryContent(
            retention_class=RetentionClass.TEMPORARY_SUCCESS,
            state=state,
            extraction_completed_at=BASE + timedelta(minutes=captured_minutes + 1),
            deleted_at=BASE + timedelta(minutes=captured_minutes + 2),
            deletion_proof="fixture-proof",
            **kwargs,
        )
    return RetentionObservation(source_key=source, content=content)


def test_complete_checkpoint_sets_last_success_and_lag() -> None:
    source = SourceCoverageInput(
        provider_key="sec",
        source_key="amd-submissions",
        checkpoints=(
            _checkpoint(provider="sec", source="amd-submissions", state=CheckpointState.COMPLETE, observed_minutes=1),
            _checkpoint(provider="sec", source="amd-submissions", state=CheckpointState.COMPLETE, observed_minutes=5),
        ),
    )
    report = summarize_corporate_coverage(as_of=BASE + timedelta(minutes=15), sources=(source,))
    item = report.sources[0]
    assert item.schema_version == CORPORATE_COVERAGE_SCHEMA_VERSION
    assert item.last_success_at == BASE + timedelta(minutes=5)
    assert item.latest_state is CheckpointState.COMPLETE
    assert item.lag_seconds == 600


def test_latest_partial_exposes_cursor_and_sanitized_error_without_losing_prior_success() -> None:
    error = CheckpointError(category="provider_rate_limit", retryable=True, retry_after=timedelta(minutes=5))
    source = SourceCoverageInput(
        provider_key="alpaca-news",
        source_key="amd-news",
        checkpoints=(
            _checkpoint(state=CheckpointState.COMPLETE, observed_minutes=1),
            _checkpoint(
                state=CheckpointState.PARTIAL,
                observed_minutes=8,
                cursor="opaque-next",
                error=error,
                retry_minutes=13,
            ),
        ),
    )
    item = summarize_corporate_coverage(as_of=BASE + timedelta(minutes=10), sources=(source,)).sources[0]
    assert item.last_success_at == BASE + timedelta(minutes=1)
    assert item.latest_state is CheckpointState.PARTIAL
    assert item.resume_cursor == "opaque-next"
    assert item.error_category == "provider_rate_limit"
    assert item.error_retryable is True
    assert item.retry_not_before == BASE + timedelta(minutes=13)


def test_error_without_prior_complete_does_not_invent_last_success() -> None:
    source = SourceCoverageInput(
        provider_key="official",
        source_key="treasury-feed",
        checkpoints=(
            _checkpoint(
                provider="official",
                source="treasury-feed",
                state=CheckpointState.ERROR,
                observed_minutes=4,
                error=CheckpointError(category="timeout", retryable=True),
            ),
        ),
    )
    item = summarize_corporate_coverage(as_of=BASE + timedelta(minutes=10), sources=(source,)).sources[0]
    assert item.last_success_at is None
    assert item.lag_seconds is None
    assert item.latest_state is CheckpointState.ERROR


def test_future_checkpoint_is_excluded_from_as_of_summary() -> None:
    source = SourceCoverageInput(
        provider_key="sec",
        source_key="nvda-submissions",
        checkpoints=(
            _checkpoint(provider="sec", source="nvda-submissions", state=CheckpointState.COMPLETE, observed_minutes=2),
            _checkpoint(provider="sec", source="nvda-submissions", state=CheckpointState.COMPLETE, observed_minutes=20),
        ),
    )
    item = summarize_corporate_coverage(as_of=BASE + timedelta(minutes=10), sources=(source,)).sources[0]
    assert item.last_success_at == BASE + timedelta(minutes=2)
    assert item.latest_observed_at == BASE + timedelta(minutes=2)


def test_retention_pending_overdue_and_next_due_are_counted_by_explicit_source() -> None:
    source = SourceCoverageInput(
        provider_key="alpaca-news",
        source_key="amd-news",
        checkpoints=(),
        retention=(
            _retention(state=TemporaryContentState.STAGED, captured_minutes=0, expires_minutes=30),
            _retention(state=TemporaryContentState.EXCEPTION, captured_minutes=1, expires_minutes=5),
            _retention(state=TemporaryContentState.DELETED, captured_minutes=2, expires_minutes=20),
        ),
    )
    item = summarize_corporate_coverage(as_of=BASE + timedelta(minutes=10), sources=(source,)).sources[0]
    assert item.retention_pending_count == 2
    assert item.retention_overdue_count == 1
    assert item.retention_next_due_at == BASE + timedelta(minutes=5)


def test_future_retention_record_is_not_visible_as_of() -> None:
    source = SourceCoverageInput(
        provider_key="alpaca-news",
        source_key="amd-news",
        checkpoints=(),
        retention=(_retention(state=TemporaryContentState.STAGED, captured_minutes=20, expires_minutes=40),),
    )
    item = summarize_corporate_coverage(as_of=BASE + timedelta(minutes=10), sources=(source,)).sources[0]
    assert item.retention_pending_count == 0
    assert item.retention_next_due_at is None


def test_scope_mismatch_is_rejected_instead_of_inferred() -> None:
    with pytest.raises(ContractViolation, match="checkpoint scope"):
        SourceCoverageInput(
            provider_key="sec",
            source_key="amd-submissions",
            checkpoints=(
                _checkpoint(provider="sec", source="nvda-submissions", state=CheckpointState.COMPLETE, observed_minutes=1),
            ),
        )
    with pytest.raises(ContractViolation, match="retention observation source"):
        SourceCoverageInput(
            provider_key="alpaca-news",
            source_key="amd-news",
            checkpoints=(),
            retention=(_retention(source="nvda-news", state=TemporaryContentState.STAGED, captured_minutes=0, expires_minutes=10),),
        )


def test_summary_is_deterministically_sorted_by_provider_and_source() -> None:
    first = SourceCoverageInput(provider_key="z-provider", source_key="b", checkpoints=())
    second = SourceCoverageInput(provider_key="a-provider", source_key="z", checkpoints=())
    third = SourceCoverageInput(provider_key="a-provider", source_key="a", checkpoints=())
    report = summarize_corporate_coverage(as_of=BASE, sources=(first, second, third))
    assert [(item.provider_key, item.source_key) for item in report.sources] == [
        ("a-provider", "a"),
        ("a-provider", "z"),
        ("z-provider", "b"),
    ]


def test_as_of_and_input_collections_require_utc_immutable_contracts() -> None:
    with pytest.raises(ContractViolation, match="normalized to UTC"):
        summarize_corporate_coverage(as_of=BASE.replace(tzinfo=None), sources=())
    with pytest.raises(ContractViolation, match="immutable tuple"):
        summarize_corporate_coverage(as_of=BASE, sources=[])
