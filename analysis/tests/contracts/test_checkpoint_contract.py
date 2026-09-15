from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    AcquisitionCheckpoint,
    BoundedWindow,
    CheckpointScope,
    CheckpointError,
    CheckpointState,
    ContractViolation,
    OpaqueCursor,
    assert_secret_free,
)


UTC = timezone.utc
START = datetime(2026, 9, 1, tzinfo=UTC)
WINDOW = BoundedWindow(START, START + timedelta(days=1))
SCOPE = CheckpointScope("sec", "submissions:amd")


def checkpoint(**overrides):
    values = {
        "scope": SCOPE,
        "window": WINDOW,
        "state": CheckpointState.IN_PROGRESS,
        "observed_at": START + timedelta(minutes=1),
        "resume_cursor": OpaqueCursor("provider-page-2"),
    }
    values.update(overrides)
    return AcquisitionCheckpoint(**values)


def test_checkpoint_is_scoped_to_provider_source_and_preserves_bounded_resume_cursor():
    value = checkpoint()

    assert value.scope == CheckpointScope("sec", "submissions:amd")
    assert value.window.start == START
    assert value.window.end == START + timedelta(days=1)
    assert value.resume_cursor == OpaqueCursor("provider-page-2")
    request = value.resume_request(page_size=50)
    assert (request.source_key, request.window_start, request.window_end, request.cursor, request.page_size) == (
        "submissions:amd", START, START + timedelta(days=1), "provider-page-2", 50
    )


def test_checkpoint_persistence_round_trip_keeps_partial_error_for_resume():
    error = CheckpointError("rate_limited", retryable=True, retry_after=timedelta(minutes=5))
    value = checkpoint(
        state=CheckpointState.PARTIAL,
        error=error,
        retry_not_before=START + timedelta(minutes=6),
    )

    record = value.to_record()
    restored = AcquisitionCheckpoint.from_record(record)

    assert restored == value
    assert restored.resume_cursor == OpaqueCursor("provider-page-2")
    assert restored.state is CheckpointState.PARTIAL
    assert_secret_free(record)
    assert "error_message" not in record
    assert "provider_response_body" not in record


def test_initial_request_error_is_resumable_without_inventing_a_cursor():
    error = CheckpointError("temporary_unavailable", retryable=True)
    value = checkpoint(state=CheckpointState.ERROR, resume_cursor=None, error=error)

    assert AcquisitionCheckpoint.from_record(value.to_record()) == value
    assert value.resume_request().cursor is None


def test_complete_checkpoint_cannot_be_resumed():
    value = checkpoint(state=CheckpointState.COMPLETE, resume_cursor=None)

    with pytest.raises(ContractViolation, match="cannot be resumed"):
        value.resume_request()


@pytest.mark.parametrize(
    "factory, match",
    [
        (lambda: BoundedWindow(START, START), "half-open"),
        (lambda: BoundedWindow(datetime(2026, 9, 1), START + timedelta(days=1)), "timezone"),
        (lambda: CheckpointScope("", "source"), "provider_key"),
        (lambda: OpaqueCursor(" "), "cursor"),
        (lambda: checkpoint(state=CheckpointState.IN_PROGRESS, resume_cursor=None), "resume_cursor"),
        (lambda: checkpoint(state=CheckpointState.COMPLETE), "complete checkpoint"),
    ],
)
def test_checkpoint_rejects_unbounded_or_ambiguous_state(factory, match):
    with pytest.raises(ContractViolation, match=match):
        factory()


def test_checkpoint_rejects_retry_time_without_retryable_partial_or_error():
    error = CheckpointError("permanent", retryable=False)

    with pytest.raises(ContractViolation, match="retryable"):
        checkpoint(
            state=CheckpointState.ERROR,
            error=error,
            retry_not_before=START + timedelta(minutes=2),
        )


def test_checkpoint_rejects_unknown_or_noncanonical_persistence_fields():
    record = checkpoint().to_record()
    record["provider_response_body"] = "raw payload"

    with pytest.raises(ContractViolation, match="fields"):
        AcquisitionCheckpoint.from_record(record)


def test_checkpoint_wraps_invalid_persisted_value_types_as_contract_violations():
    record = checkpoint().to_record()
    record["error_category"] = 123
    record["error_retryable"] = True

    with pytest.raises(ContractViolation, match="invalid checkpoint record"):
        AcquisitionCheckpoint.from_record(record)
