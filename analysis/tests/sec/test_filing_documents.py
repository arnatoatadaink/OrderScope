from datetime import date, datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import ContractViolation, TemporaryContentState
from orderscope_local.sec import (
    FilingRecord,
    SecFilingDocumentAcquirer,
    SecRequestFailure,
)


NOW = datetime(2026, 9, 8, 3, tzinfo=timezone.utc)
DOCUMENT = b"<html><body>AMD filing</body></html>"


class Transport:
    def __init__(self, result: bytes | Exception) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []

    def get_bytes(self, url: str, *, user_agent: str) -> bytes:
        self.calls.append((url, user_agent))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class Store:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def put(self, content_ref: str, content: bytes) -> None:
        self.values[content_ref] = content


class Limiter:
    def __init__(self) -> None:
        self.calls = 0

    def acquire(self) -> None:
        self.calls += 1


def filing(**overrides: object) -> FilingRecord:
    values = {
        "accession": "0000002488-26-000121",
        "content_hash": "a" * 64,
        "cik": "0000002488",
        "ticker": "AMD",
        "form": "8-K",
        "filed_at": date(2026, 8, 4),
        "period_end": date(2026, 6, 27),
        "primary_document_ref": "https://www.sec.gov/Archives/edgar/data/2488/000000248826000121/amd.htm",
        "source_ref": "https://www.sec.gov/Archives/edgar/data/2488/000000248826000121",
        "retrieved_at": NOW,
        **overrides,
    }
    return FilingRecord(**values)


def acquirer(result: bytes | Exception = DOCUMENT, **overrides: object):
    transport = Transport(result)
    store = Store()
    limiter = Limiter()
    value = SecFilingDocumentAcquirer(
        transport=transport,
        store=store,
        user_agent="OrderScope ops@example.test",
        limiter=limiter,
        clock=lambda: NOW,
        **overrides,
    )
    return value, transport, store, limiter


def test_stages_hashed_document_with_temporary_lifecycle() -> None:
    value, transport, store, limiter = acquirer()

    result = value.acquire(filing())

    assert result.error is None
    assert result.content_hash == "f893bb160163454b3ddc55a5c6ab2fcf580182aff687b575bfb0803c155f5a51"
    assert result.temporary_content is not None
    assert result.temporary_content.content_ref == f"tmp:sha256:{result.content_hash}"
    assert result.temporary_content.state is TemporaryContentState.STAGED
    assert result.temporary_content.expires_at == NOW + timedelta(hours=24)
    assert store.values[result.temporary_content.content_ref] == DOCUMENT
    assert transport.calls == [(filing().primary_document_ref, "OrderScope ops@example.test")]
    assert limiter.calls == 1


def test_provider_failure_remains_retryable_and_stores_no_body() -> None:
    value, _, store, _ = acquirer(
        SecRequestFailure("rate_limited", True, timedelta(minutes=10))
    )

    result = value.acquire(filing())

    assert result.error is not None
    assert result.error.category == "rate_limited"
    assert result.error.retryable is True
    assert result.error.retry_after == timedelta(minutes=10)
    assert result.content_hash is None
    assert result.temporary_content is None
    assert store.values == {}
    assert not hasattr(result, "body")


def test_unknown_transport_failure_is_sanitized_and_retryable() -> None:
    value, _, store, _ = acquirer(RuntimeError("provider body with secret"))

    result = value.acquire(filing())

    assert result.error is not None
    assert result.error.category == "transport_error"
    assert result.error.retryable is True
    assert "secret" not in result.error.message
    assert store.values == {}


def test_unbounded_provider_retry_delay_does_not_cross_boundary() -> None:
    value, _, _, _ = acquirer(
        SecRequestFailure("blocked", True, timedelta(days=2))
    )

    result = value.acquire(filing())

    assert result.error is not None
    assert result.error.retryable is True
    assert result.error.retry_after is None


@pytest.mark.parametrize("body", [b"", b"x" * 11])
def test_invalid_or_oversize_document_is_nonretryable(body: bytes) -> None:
    value, _, store, _ = acquirer(body, max_content_bytes=10)

    result = value.acquire(filing())

    assert result.error is not None
    assert result.error.retryable is False
    assert store.values == {}


def test_requires_canonical_document_reference_and_utc_clock() -> None:
    value, transport, _, limiter = acquirer()
    with pytest.raises(ContractViolation, match="filing root"):
        value.acquire(filing(primary_document_ref="https://example.test/document"))
    with pytest.raises(ContractViolation, match="filing root"):
        value.acquire(
            filing(
                source_ref="https://example.test/root",
                primary_document_ref="https://example.test/root/document",
            )
        )
    assert transport.calls == []
    assert limiter.calls == 0

    value, _, _, _ = acquirer()
    with pytest.raises(ContractViolation, match="primary document"):
        value.acquire(filing(primary_document_ref=None))
    with pytest.raises(ContractViolation, match="canonical SEC metadata"):
        value.acquire(filing(cik="AMD"))
    with pytest.raises(ContractViolation, match="match its CIK"):
        value.acquire(filing(cik="0001045810"))

    value, _, _, _ = acquirer()
    value._clock = lambda: NOW.replace(tzinfo=None)
    with pytest.raises(ContractViolation, match="UTC"):
        value.acquire(filing())


def test_validates_retention_user_agent_and_size_limit() -> None:
    with pytest.raises(ContractViolation, match="contact"):
        SecFilingDocumentAcquirer(
            transport=Transport(DOCUMENT), store=Store(), user_agent="bot",
            limiter=Limiter(),
        )
    with pytest.raises(ContractViolation, match="retention"):
        acquirer(retention=timedelta(days=31))
    with pytest.raises(ContractViolation, match="size limit"):
        acquirer(max_content_bytes=0)
