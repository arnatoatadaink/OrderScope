"""Provider-neutral SEC FilingRecord persistence.

The repository expects the ``filing_records`` table to be installed by the
versioned local migration layer.  It deliberately does not create or migrate
schema, which remains the L0-005 boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
import re
import sqlite3
from typing import Any, Mapping

from orderscope_local.contracts import AdapterItem, ContractViolation, StableIdentityKind


_PRIMARY_DOCUMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_CANARY_TICKERS = {"0000002488": "AMD", "0001045810": "NVDA"}


class FilingWriteResult(StrEnum):
    NEW = "new"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class FilingRecord:
    accession: str
    content_hash: str
    cik: str
    ticker: str
    form: str
    filed_at: date
    period_end: date | None
    primary_document_ref: str | None
    source_ref: str
    retrieved_at: datetime


@dataclass(frozen=True, slots=True)
class FilingWrite:
    result: FilingWriteResult
    record: FilingRecord


class SqliteFilingRecordRepository:
    """Store immutable filing metadata by globally stable SEC accession."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ContractViolation("filing repository requires a sqlite3 connection")
        self._connection = connection

    def put(self, item: AdapterItem, *, retrieved_at: datetime) -> FilingWrite:
        candidate = filing_record_from_adapter(item, retrieved_at=retrieved_at)
        values = _record_values(candidate)
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO filing_records (
                    accession, content_hash, cik, ticker, form, filed_at,
                    period_end, primary_document_ref, source_ref, retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(accession) DO NOTHING
                """,
                values,
            )
            stored = self.get(candidate.accession)
        if stored is None:
            raise ContractViolation("filing record was not persisted")
        if cursor.rowcount == 1:
            return FilingWrite(FilingWriteResult.NEW, stored)
        if stored.content_hash != candidate.content_hash:
            raise ContractViolation("filing accession conflicts with persisted content hash")
        return FilingWrite(FilingWriteResult.DUPLICATE, stored)

    def get(self, accession: str) -> FilingRecord | None:
        row = self._connection.execute(
            """
            SELECT accession, content_hash, cik, ticker, form, filed_at,
                   period_end, primary_document_ref, source_ref, retrieved_at
            FROM filing_records
            WHERE accession = ?
            """,
            (accession,),
        ).fetchone()
        return None if row is None else _record_from_row(row)


def filing_record_from_adapter(item: AdapterItem, *, retrieved_at: datetime) -> FilingRecord:
    """Validate an S0-002 item and convert it to durable FilingRecord metadata."""

    if not isinstance(item, AdapterItem):
        raise ContractViolation("filing persistence requires an AdapterItem")
    identity = item.content_identity.identity
    if identity.kind is not StableIdentityKind.FILING_ACCESSION:
        raise ContractViolation("filing persistence requires a filing accession identity")
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() != timedelta(0):
        raise ContractViolation("retrieved_at must be normalized to UTC")
    normalized = item.normalized
    if not isinstance(normalized, Mapping):
        raise ContractViolation("filing normalized metadata must be a mapping")

    accession = _required_text(normalized, "accession")
    if accession != identity.value:
        raise ContractViolation("normalized accession does not match stable identity")
    cik = _required_text(normalized, "cik")
    if accession[:10] != cik:
        raise ContractViolation("filing accession does not match normalized CIK")
    ticker = _required_text(normalized, "ticker")
    if _CANARY_TICKERS.get(cik) != ticker:
        raise ContractViolation("filing CIK and ticker are outside the corporate canary")
    form = _required_text(normalized, "form")
    filed_at = _required_date(normalized, "filed_on")
    period_end = _optional_date(normalized, "period_end")
    primary_document = _optional_text(normalized, "primary_document")
    if primary_document is not None and _PRIMARY_DOCUMENT.fullmatch(primary_document) is None:
        raise ContractViolation("primary_document is not a safe SEC document name")

    accession_path = accession.replace("-", "")
    filing_root = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}"
    primary_ref = None if primary_document is None else f"{filing_root}/{primary_document}"
    return FilingRecord(
        accession=accession,
        content_hash=item.content_identity.content_hash.digest,
        cik=cik,
        ticker=ticker,
        form=form,
        filed_at=filed_at,
        period_end=period_end,
        primary_document_ref=primary_ref,
        source_ref=filing_root,
        retrieved_at=retrieved_at,
    )


def _required_text(values: Mapping[str, Any], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractViolation(f"{key} must be non-blank canonical text")
    return value


def _optional_text(values: Mapping[str, Any], key: str) -> str | None:
    value = values.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractViolation(f"{key} must be null or non-blank canonical text")
    return value


def _required_date(values: Mapping[str, Any], key: str) -> date:
    value = _required_text(values, key)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation(f"{key} must be an ISO calendar date") from exc


def _optional_date(values: Mapping[str, Any], key: str) -> date | None:
    value = values.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ContractViolation(f"{key} must be null or an ISO calendar date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation(f"{key} must be null or an ISO calendar date") from exc


def _record_values(record: FilingRecord) -> tuple[str | None, ...]:
    return (
        record.accession,
        record.content_hash,
        record.cik,
        record.ticker,
        record.form,
        record.filed_at.isoformat(),
        None if record.period_end is None else record.period_end.isoformat(),
        record.primary_document_ref,
        record.source_ref,
        record.retrieved_at.isoformat(),
    )


def _record_from_row(row: tuple[Any, ...]) -> FilingRecord:
    try:
        retrieved_at = datetime.fromisoformat(row[9])
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() != timedelta(0):
            raise ValueError
        return FilingRecord(
            accession=row[0],
            content_hash=row[1],
            cik=row[2],
            ticker=row[3],
            form=row[4],
            filed_at=date.fromisoformat(row[5]),
            period_end=None if row[6] is None else date.fromisoformat(row[6]),
            primary_document_ref=row[7],
            source_ref=row[8],
            retrieved_at=retrieved_at,
        )
    except (IndexError, TypeError, ValueError) as exc:
        raise ContractViolation("persisted filing record is invalid") from exc
