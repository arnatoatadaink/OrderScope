from datetime import date, datetime, timezone
import sqlite3

import pytest

from orderscope_local.contracts import AdapterItem, ContentHash, ContentIdentity, ContractViolation, StableIdentity
from orderscope_local.sec import FilingWriteResult, SqliteFilingRecordRepository


RETRIEVED = datetime(2026, 9, 8, 1, tzinfo=timezone.utc)
ACCESSION = "0000002488-26-000121"


def repository() -> SqliteFilingRecordRepository:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE filing_records (
            accession TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            cik TEXT NOT NULL,
            ticker TEXT NOT NULL,
            form TEXT NOT NULL,
            filed_at TEXT NOT NULL,
            period_end TEXT,
            primary_document_ref TEXT,
            source_ref TEXT NOT NULL,
            retrieved_at TEXT NOT NULL
        )
        """
    )
    return SqliteFilingRecordRepository(connection)


def item(*, content_hash: str = "a" * 64, **overrides: object) -> AdapterItem:
    normalized = {
        "cik": "0000002488",
        "ticker": "AMD",
        "accession": ACCESSION,
        "form": "8-K",
        "filed_on": "2026-08-04",
        "period_end": "2026-06-27",
        "source_accepted_at": "20260804161624",
        "primary_document": "amd-20260804.htm",
        **overrides,
    }
    return AdapterItem(
        normalized=normalized,
        content_identity=ContentIdentity(
            StableIdentity.filing_accession(ACCESSION), ContentHash(content_hash)
        ),
    )


def test_persists_provider_neutral_filing_record_by_accession() -> None:
    store = repository()

    write = store.put(item(), retrieved_at=RETRIEVED)

    assert write.result is FilingWriteResult.NEW
    assert write.record.accession == ACCESSION
    assert write.record.cik == "0000002488"
    assert write.record.form == "8-K"
    assert write.record.filed_at == date(2026, 8, 4)
    assert write.record.period_end == date(2026, 6, 27)
    assert write.record.primary_document_ref == (
        "https://www.sec.gov/Archives/edgar/data/2488/000000248826000121/amd-20260804.htm"
    )
    assert write.record.source_ref == (
        "https://www.sec.gov/Archives/edgar/data/2488/000000248826000121"
    )
    assert write.record.retrieved_at == RETRIEVED
    assert store.get(ACCESSION) == write.record


def test_same_accession_and_hash_is_idempotent_and_preserves_first_retrieval() -> None:
    store = repository()
    first = store.put(item(), retrieved_at=RETRIEVED)

    duplicate = store.put(
        item(), retrieved_at=datetime(2026, 9, 8, 2, tzinfo=timezone.utc)
    )

    assert first.result is FilingWriteResult.NEW
    assert duplicate.result is FilingWriteResult.DUPLICATE
    assert duplicate.record == first.record


def test_same_accession_with_changed_hash_is_an_explicit_conflict() -> None:
    store = repository()
    store.put(item(), retrieved_at=RETRIEVED)

    with pytest.raises(ContractViolation, match="conflicts"):
        store.put(item(content_hash="b" * 64, form="8-K/A"), retrieved_at=RETRIEVED)


@pytest.mark.parametrize(
    ("candidate", "message"),
    [
        (item(accession="0001045810-26-000001"), "stable identity"),
        (item(cik="0001045810"), "CIK"),
        (item(ticker="NVDA"), "corporate canary"),
        (item(filed_on="2026/08/04"), "ISO calendar date"),
        (item(primary_document="../secret.txt"), "safe SEC document"),
    ],
)
def test_rejects_invalid_or_cross_company_metadata(candidate: AdapterItem, message: str) -> None:
    with pytest.raises(ContractViolation, match=message):
        repository().put(candidate, retrieved_at=RETRIEVED)


def test_nullable_period_and_primary_document_remain_unknown() -> None:
    write = repository().put(
        item(period_end=None, primary_document=None), retrieved_at=RETRIEVED
    )

    assert write.record.period_end is None
    assert write.record.primary_document_ref is None


def test_requires_utc_retrieval_and_preexisting_migration() -> None:
    with pytest.raises(ContractViolation, match="UTC"):
        repository().put(item(), retrieved_at=RETRIEVED.replace(tzinfo=None))

    connection = sqlite3.connect(":memory:")
    store = SqliteFilingRecordRepository(connection)
    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        store.put(item(), retrieved_at=RETRIEVED)
