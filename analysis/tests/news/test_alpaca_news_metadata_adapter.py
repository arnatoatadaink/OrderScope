from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import AdapterRequest, ContractViolation, assert_page_contract
from orderscope_local.news import AlpacaNewsAdapter, AlpacaNewsRequestFailure

UTC = timezone.utc
WINDOW_START = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
WINDOW_END = datetime(2026, 9, 2, 0, 0, tzinfo=UTC)
RETRIEVED = datetime(2026, 9, 2, 0, 1, tzinfo=UTC)


class FakeTransport:
    def __init__(self, payload=None, failure=None):
        self.payload = payload if payload is not None else {"news": [], "next_page_token": None}
        self.failure = failure
        self.calls = []

    def get_news(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure is not None:
            raise self.failure
        return self.payload


def _request(*, source_key="news:alpaca:amd", cursor=None, page_size=50):
    return AdapterRequest(
        source_key=source_key,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        cursor=cursor,
        page_size=page_size,
    )


def _article(**overrides):
    value = {
        "id": 12345,
        "headline": "AMD announces a bounded fixture event",
        "summary": "Fixture summary",
        "author": "Benzinga Newsdesk",
        "created_at": "2026-09-01T12:00:00Z",
        "updated_at": "2026-09-01T12:01:00Z",
        "url": "https://example.com/news/12345",
        "symbols": ["AMD", "NVDA"],
        "source": "benzinga",
    }
    value.update(overrides)
    return value


def test_adapter_fetches_bounded_metadata_without_body():
    transport = FakeTransport({"news": [_article()], "next_page_token": None})
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request())

    assert_page_contract(page, _request())
    assert page.error is None
    assert len(page.items) == 1
    item = page.items[0]
    assert item.normalized["provider_article_id"] == "12345"
    assert item.normalized["query_symbol"] == "AMD"
    assert item.normalized["publisher"] == "benzinga"
    assert item.normalized["provider_symbols"] == ("AMD", "NVDA")
    assert item.normalized["body_capability"] is True
    assert item.temporary_content is None
    assert transport.calls[0]["include_content"] is False
    assert transport.calls[0]["sort"] == "asc"
    assert transport.calls[0]["start"] == "2026-09-01T00:00:00Z"
    assert transport.calls[0]["end"] == "2026-09-02T00:00:00Z"


def test_page_token_is_forwarded_and_returned_without_provider_payload_leak():
    transport = FakeTransport({"news": [_article()], "next_page_token": "next-opaque-token"})
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request(cursor="current-opaque-token", page_size=10))

    assert page.next_cursor == "next-opaque-token"
    assert transport.calls[0]["page_token"] == "current-opaque-token"
    assert transport.calls[0]["limit"] == 10
    assert "news" not in page.items[0].normalized


def test_terminal_none_cursor_is_not_a_loop():
    adapter = AlpacaNewsAdapter(
        transport=FakeTransport({"news": [_article()], "next_page_token": None}),
        clock=lambda: RETRIEVED,
    )

    page = adapter.fetch(_request(cursor=None))

    assert page.error is None
    assert page.next_cursor is None
    assert len(page.items) == 1


def test_same_non_null_page_token_is_rejected_as_cursor_loop():
    adapter = AlpacaNewsAdapter(
        transport=FakeTransport({"news": [_article()], "next_page_token": "same-token"}),
        clock=lambda: RETRIEVED,
    )

    page = adapter.fetch(_request(cursor="same-token"))

    assert page.items == ()
    assert page.error is not None
    assert page.error.category == "cursor_loop"
    assert page.error.retryable is False


def test_provider_symbols_are_observations_not_query_identity_truth():
    transport = FakeTransport({"news": [_article(symbols=["NVDA"])], "next_page_token": None})
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request(source_key="news:alpaca:amd"))

    item = page.items[0]
    assert item.normalized["query_symbol"] == "AMD"
    assert item.normalized["provider_symbols"] == ("NVDA",)


def test_article_created_before_window_can_be_retained_when_provider_returns_update():
    transport = FakeTransport(
        {
            "news": [
                _article(
                    created_at="2026-08-20T12:00:00Z",
                    updated_at="2026-09-01T12:01:00Z",
                )
            ],
            "next_page_token": None,
        }
    )
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request())

    assert page.error is None
    assert len(page.items) == 1
    assert page.items[0].normalized["published_at"].instant == datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    assert page.items[0].normalized["provider_updated_at"].instant == datetime(2026, 9, 1, 12, 1, tzinfo=UTC)


def test_missing_article_url_is_retained_as_nullable_metadata():
    article = _article()
    article.pop("url")
    transport = FakeTransport({"news": [article], "next_page_token": None})
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request())

    assert page.error is None
    assert page.items[0].normalized["article_url"] is None
    assert page.items[0].normalized["provider_article_id"] == "12345"


def test_body_field_is_rejected_at_n0_002_boundary():
    transport = FakeTransport({"news": [_article(content="raw body must not cross")], "next_page_token": None})
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request())

    assert page.items == ()
    assert page.error is not None
    assert page.error.category == "body_leak"
    assert page.error.retryable is False


def test_429_style_failure_is_retryable_and_keeps_cursor_unadvanced():
    failure = AlpacaNewsRequestFailure("rate_limited", True, timedelta(seconds=30))
    transport = FakeTransport(failure=failure)
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    request = _request(cursor="resume-here")
    page = adapter.fetch(request)

    assert_page_contract(page, request)
    assert page.error is not None
    assert page.error.category == "rate_limited"
    assert page.error.retry_after == timedelta(seconds=30)
    assert page.next_cursor is None


def test_generic_transport_failure_is_sanitized_retryable_error():
    transport = FakeTransport(failure=RuntimeError("provider body or secret must not escape"))
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request())

    assert page.error is not None
    assert page.error.category == "transport_error"
    assert page.error.retryable is True
    assert page.error.message == "Alpaca News request failed"


def test_invalid_canary_source_and_provider_page_size_are_rejected():
    adapter = AlpacaNewsAdapter(transport=FakeTransport(), clock=lambda: RETRIEVED)

    with pytest.raises(ContractViolation):
        adapter.fetch(_request(source_key="news:alpaca:spy"))
    with pytest.raises(ContractViolation):
        adapter.fetch(_request(page_size=51))


def test_updated_before_created_is_rejected_as_invalid_response():
    transport = FakeTransport(
        {
            "news": [
                _article(
                    created_at="2026-09-01T12:00:00Z",
                    updated_at="2026-09-01T11:59:59Z",
                )
            ],
            "next_page_token": None,
        }
    )
    adapter = AlpacaNewsAdapter(transport=transport, clock=lambda: RETRIEVED)

    page = adapter.fetch(_request())

    assert page.error is not None
    assert page.error.category == "invalid_response"


def test_same_article_metadata_reproduces_same_content_identity():
    payload = {"news": [_article()], "next_page_token": None}
    first = AlpacaNewsAdapter(transport=FakeTransport(payload), clock=lambda: RETRIEVED).fetch(_request())
    second = AlpacaNewsAdapter(transport=FakeTransport(payload), clock=lambda: RETRIEVED).fetch(_request())

    assert first.items[0].content_identity == second.items[0].content_identity
