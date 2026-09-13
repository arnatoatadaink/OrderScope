"""S0-007 fixture replay acceptance for the AMD/NVIDIA SEC canary."""

from datetime import date, datetime, timedelta, timezone
import sqlite3

import pytest

from orderscope_local.contracts import AdapterRequest
from orderscope_local.sec import (
    SEC_DATA_ORIGIN,
    FilingWriteResult,
    SecCompanyFactsAdapter,
    SecFilingDocumentAcquirer,
    SecFormFamily,
    SecRequestFailure,
    SecSubmissionsAdapter,
    SqliteFilingRecordRepository,
    classify_filing_record,
)


NOW = datetime(2026, 9, 8, 4, tzinfo=timezone.utc)
WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2027, 1, 1, tzinfo=timezone.utc)
USER_AGENT = "OrderScope ops@example.test"


def _columns(*rows: tuple[str, ...]) -> dict[str, list[str]]:
    names = (
        "accessionNumber", "filingDate", "reportDate",
        "acceptanceDateTime", "form", "primaryDocument",
    )
    return {name: [row[index] for row in rows] for index, name in enumerate(names)}


AMD_FILINGS = _columns(
    ("0000002488-26-000120", "2026-08-03", "2026-06-27", "20260803160000", "10-Q", "amd-20260627.htm"),
    ("0000002488-26-000121", "2026-08-04", "2026-06-27", "20260804160000", "10-Q/A", "amd-20260627a.htm"),
)
NVDA_FILINGS = _columns(
    ("0001197647-26-000009", "2026-09-04", "", "20260904160000", "4", "xslF345X06/ownership.xml"),
)


class JsonTransport:
    def __init__(self, payloads: dict[str, object]) -> None:
        self.payloads = payloads
        self.calls: list[tuple[str, str]] = []

    def get_json(self, url: str, *, user_agent: str):
        self.calls.append((url, user_agent))
        value = self.payloads[url]
        if isinstance(value, Exception):
            raise value
        return value


class BytesTransport:
    def __init__(self, value: bytes | Exception) -> None:
        self.value = value

    def get_bytes(self, url: str, *, user_agent: str) -> bytes:
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class Limiter:
    def __init__(self) -> None:
        self.calls = 0

    def acquire(self) -> None:
        self.calls += 1


class Store:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def put(self, content_ref: str, content: bytes) -> None:
        self.values[content_ref] = content


@pytest.fixture
def repository() -> SqliteFilingRecordRepository:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE filing_records (
            accession TEXT PRIMARY KEY, content_hash TEXT NOT NULL,
            cik TEXT NOT NULL, ticker TEXT NOT NULL, form TEXT NOT NULL,
            filed_at TEXT NOT NULL, period_end TEXT,
            primary_document_ref TEXT, source_ref TEXT NOT NULL,
            retrieved_at TEXT NOT NULL
        )
        """
    )
    return SqliteFilingRecordRepository(connection)


def _submissions_payload(cik: int, recent: dict[str, list[str]]) -> dict[str, object]:
    return {
        "cik": cik,
        "lastModified": "2026-09-08T00:00:00Z",
        "filings": {"recent": recent, "files": []},
    }


def test_fixture_replay_accepts_bounded_canary_new_duplicate_and_amendment(repository) -> None:
    payloads = {
        f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488.json": _submissions_payload(2488, AMD_FILINGS),
        f"{SEC_DATA_ORIGIN}/submissions/CIK0001045810.json": _submissions_payload(1045810, NVDA_FILINGS),
    }
    transport = JsonTransport(payloads)
    limiter = Limiter()
    adapter = SecSubmissionsAdapter(
        transport=transport, user_agent=USER_AGENT, limiter=limiter, clock=lambda: NOW,
    )

    pages = [
        adapter.fetch(AdapterRequest(f"sec:submissions:{company}", WINDOW_START, WINDOW_END))
        for company in ("amd", "nvda")
    ]
    items = [item for page in pages for item in page.items]
    first_writes = [repository.put(item, retrieved_at=NOW) for item in items]
    replay_writes = [repository.put(item, retrieved_at=NOW + timedelta(minutes=1)) for item in items]

    assert [write.result for write in first_writes] == [FilingWriteResult.NEW] * 3
    assert [write.result for write in replay_writes] == [FilingWriteResult.DUPLICATE] * 3
    base, amendment = first_writes[:2]
    base_decision = classify_filing_record(base.record)
    amendment_decision = classify_filing_record(amendment.record)
    assert base.record.accession != amendment.record.accession
    assert base_decision.family is amendment_decision.family is SecFormFamily.QUARTERLY_REPORT
    assert (base_decision.is_amendment, amendment_decision.is_amendment) == (False, True)
    assert {write.record.ticker for write in first_writes} == {"AMD", "NVDA"}
    assert first_writes[2].record.source_ref.startswith(
        "https://www.sec.gov/Archives/edgar/data/1197647/"
    )
    assert limiter.calls == 2
    assert all(user_agent == USER_AGENT for _, user_agent in transport.calls)


def test_partial_submissions_document_and_company_facts_are_retryable_and_sanitized() -> None:
    failure = SecRequestFailure("rate_limited", True, timedelta(minutes=10))
    submissions = SecSubmissionsAdapter(
        transport=JsonTransport({f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488.json": failure}),
        user_agent=USER_AGENT, limiter=Limiter(), clock=lambda: NOW,
    ).fetch(AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END))

    record_item = SecSubmissionsAdapter(
        transport=JsonTransport({
            f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488.json": _submissions_payload(2488, AMD_FILINGS),
        }), user_agent=USER_AGENT, limiter=Limiter(), clock=lambda: NOW,
    ).fetch(AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END)).items[0]
    repository_connection = sqlite3.connect(":memory:")
    repository_connection.execute(
        "CREATE TABLE filing_records (accession TEXT PRIMARY KEY, content_hash TEXT NOT NULL, cik TEXT NOT NULL, ticker TEXT NOT NULL, form TEXT NOT NULL, filed_at TEXT NOT NULL, period_end TEXT, primary_document_ref TEXT, source_ref TEXT NOT NULL, retrieved_at TEXT NOT NULL)"
    )
    record = SqliteFilingRecordRepository(repository_connection).put(
        record_item, retrieved_at=NOW
    ).record
    store = Store()
    document = SecFilingDocumentAcquirer(
        transport=BytesTransport(RuntimeError("provider body secret-token")),
        store=store, user_agent=USER_AGENT, limiter=Limiter(), clock=lambda: NOW,
    ).acquire(record)
    facts_transport = JsonTransport({
        f"{SEC_DATA_ORIGIN}/api/xbrl/companyfacts/CIK0000002488.json": failure,
    })
    facts = SecCompanyFactsAdapter(
        transport=facts_transport, user_agent=USER_AGENT, limiter=Limiter(), clock=lambda: NOW,
    )
    fact_page = facts.fetch(
        source_key="sec:companyfacts:amd", window_start=date(2026, 1, 1),
        window_end=date(2027, 1, 1),
    )

    errors = (submissions.error, document.error, fact_page.error)
    assert all(error is not None and error.retryable for error in errors)
    assert submissions.error.retry_after == timedelta(minutes=10)
    assert document.temporary_content is None and store.values == {}
    assert fact_page.facts == ()
    assert all("secret-token" not in error.message for error in errors)
    assert all(not hasattr(value, "provider_body") for value in (submissions, document, fact_page))
