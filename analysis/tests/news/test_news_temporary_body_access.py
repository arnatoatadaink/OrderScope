from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import ContractViolation, RetentionClass, TemporaryContentState
from orderscope_local.news import (
    AlpacaNewsBodyAccessor,
    AlpacaNewsRequestFailure,
    exception_record,
)

UTC = timezone.utc
NOW = datetime(2026, 9, 9, 1, 0, tzinfo=UTC)


class FakeTransport:
    def __init__(self, body="temporary article body", failure=None):
        self.body = body
        self.failure = failure
        self.calls = []

    def get_article_content(self, *, article_id):
        self.calls.append(article_id)
        if self.failure is not None:
            raise self.failure
        return self.body


class FakeStore:
    def __init__(self, content_ref="tmp://news/alpaca/12345/body"):
        self.content_ref = content_ref
        self.calls = []

    def stage(self, **kwargs):
        self.calls.append(kwargs)
        return self.content_ref


def test_body_is_staged_and_not_returned_in_durable_result():
    transport = FakeTransport("sensitive temporary body")
    store = FakeStore()
    accessor = AlpacaNewsBodyAccessor(transport=transport, store=store, clock=lambda: NOW)

    result = accessor.acquire(article_id="12345", body_capability=True)

    assert result.article_id == "12345"
    assert result.temporary_content.state is TemporaryContentState.STAGED
    assert result.temporary_content.retention_class is RetentionClass.TEMPORARY_SUCCESS
    assert result.temporary_content.expires_at == NOW + timedelta(hours=6)
    assert result.temporary_content.content_ref == "tmp://news/alpaca/12345/body"
    assert not hasattr(result, "body")
    assert store.calls[0]["body"] == "sensitive temporary body"


def test_success_ttl_is_bounded_to_one_day():
    with pytest.raises(ContractViolation):
        AlpacaNewsBodyAccessor(
            transport=FakeTransport(),
            store=FakeStore(),
            clock=lambda: NOW,
            success_ttl=timedelta(days=2),
        )


def test_body_capability_false_blocks_transport_call():
    transport = FakeTransport()
    accessor = AlpacaNewsBodyAccessor(transport=transport, store=FakeStore(), clock=lambda: NOW)

    with pytest.raises(ContractViolation):
        accessor.acquire(article_id="12345", body_capability=False)

    assert transport.calls == []


def test_provider_failure_remains_sanitized_and_retryable():
    failure = AlpacaNewsRequestFailure("rate_limited", True, timedelta(seconds=20))
    accessor = AlpacaNewsBodyAccessor(
        transport=FakeTransport(failure=failure), store=FakeStore(), clock=lambda: NOW
    )

    with pytest.raises(AlpacaNewsRequestFailure) as caught:
        accessor.acquire(article_id="12345", body_capability=True)

    assert caught.value.category == "rate_limited"
    assert caught.value.retryable is True
    assert caught.value.retry_after == timedelta(seconds=20)


def test_empty_body_is_nonretryable_unavailable():
    accessor = AlpacaNewsBodyAccessor(
        transport=FakeTransport("   "), store=FakeStore(), clock=lambda: NOW
    )

    with pytest.raises(AlpacaNewsRequestFailure) as caught:
        accessor.acquire(article_id="12345", body_capability=True)

    assert caught.value.category == "body_unavailable"
    assert caught.value.retryable is False


def test_store_failure_is_sanitized_retryable_error():
    class FailingStore:
        def stage(self, **kwargs):
            raise RuntimeError("local path or raw body must not escape")

    accessor = AlpacaNewsBodyAccessor(
        transport=FakeTransport(), store=FailingStore(), clock=lambda: NOW
    )

    with pytest.raises(AlpacaNewsRequestFailure) as caught:
        accessor.acquire(article_id="12345", body_capability=True)

    assert caught.value.category == "temporary_store_error"
    assert caught.value.retryable is True


def test_exception_record_is_limited_to_thirty_days():
    record = exception_record(
        content_ref="tmp://news/alpaca/12345/body",
        captured_at=NOW,
        reason="extractor failed",
        expires_at=NOW + timedelta(days=30),
    )

    assert record.state is TemporaryContentState.EXCEPTION
    assert record.retention_class is RetentionClass.TEMPORARY_EXCEPTION
    assert record.exception_reason == "extractor failed"

    with pytest.raises(ContractViolation):
        exception_record(
            content_ref="tmp://news/alpaca/12345/body",
            captured_at=NOW,
            reason="extractor failed",
            expires_at=NOW + timedelta(days=31),
        )


def test_naive_capture_clock_is_rejected():
    accessor = AlpacaNewsBodyAccessor(
        transport=FakeTransport(),
        store=FakeStore(),
        clock=lambda: datetime(2026, 9, 9, 1, 0),
    )

    with pytest.raises(ContractViolation):
        accessor.acquire(article_id="12345", body_capability=True)
