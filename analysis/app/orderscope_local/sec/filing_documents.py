"""Temporary acquisition boundary for SEC filing primary documents."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import re
from typing import Protocol

from orderscope_local.contracts import (
    ContractViolation,
    ErrorInfo,
    RetentionClass,
    TemporaryContent,
)

from .filing_records import FilingRecord
from .submissions import SecRateLimiter, SecRequestFailure


_ACCESSION = re.compile(r"[0-9]{10}-[0-9]{2}-[0-9]{6}")
_CIK = re.compile(r"[0-9]{10}")


class SecDocumentTransport(Protocol):
    def get_bytes(self, url: str, *, user_agent: str) -> bytes: ...


class TemporaryContentStore(Protocol):
    """Write content outside durable filing metadata under a hash-derived ref."""

    def put(self, content_ref: str, content: bytes) -> None: ...


@dataclass(frozen=True, slots=True)
class FilingDocumentAcquisition:
    accession: str
    source_ref: str
    content_hash: str | None
    temporary_content: TemporaryContent | None
    retrieved_at: datetime
    error: ErrorInfo | None = None


class SecFilingDocumentAcquirer:
    """Fetch one canonical primary document and stage it in temporary storage."""

    def __init__(
        self,
        *,
        transport: SecDocumentTransport,
        store: TemporaryContentStore,
        user_agent: str,
        limiter: SecRateLimiter,
        clock: Callable[[], datetime] | None = None,
        retention: timedelta = timedelta(hours=24),
        max_content_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        if (
            not isinstance(user_agent, str)
            or not user_agent.strip()
            or "@" not in user_agent
            or len(user_agent) > 256
        ):
            raise ContractViolation("SEC User-Agent must include a contact address")
        if retention <= timedelta(0) or retention > timedelta(days=30):
            raise ContractViolation("filing-document retention must be within 30 days")
        if not 1 <= max_content_bytes <= 100 * 1024 * 1024:
            raise ContractViolation("filing-document size limit is outside the bounded range")
        self._transport = transport
        self._store = store
        self._user_agent = user_agent
        self._limiter = limiter
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._retention = retention
        self._max_content_bytes = max_content_bytes

    def acquire(self, filing: FilingRecord) -> FilingDocumentAcquisition:
        if not isinstance(filing, FilingRecord):
            raise ContractViolation("document acquisition requires a FilingRecord")
        if filing.primary_document_ref is None:
            raise ContractViolation("filing has no primary document reference")
        if _ACCESSION.fullmatch(filing.accession) is None or _CIK.fullmatch(filing.cik) is None:
            raise ContractViolation("filing identity is not canonical SEC metadata")
        if filing.accession[:10] != filing.cik:
            raise ContractViolation("filing accession does not match its CIK")
        accession_path = filing.accession.replace("-", "")
        canonical_root = (
            f"https://www.sec.gov/Archives/edgar/data/{int(filing.cik)}/{accession_path}"
        )
        if filing.source_ref != canonical_root or not filing.primary_document_ref.startswith(
            f"{canonical_root}/"
        ):
            raise ContractViolation("primary document reference is outside the filing root")

        retrieved_at = self._clock()
        _require_utc(retrieved_at)
        try:
            self._limiter.acquire()
            body = self._transport.get_bytes(
                filing.primary_document_ref, user_agent=self._user_agent
            )
            if not isinstance(body, bytes) or not body:
                raise SecRequestFailure("invalid_document", False)
            if len(body) > self._max_content_bytes:
                raise SecRequestFailure("document_too_large", False)
            digest = hashlib.sha256(body).hexdigest()
            content_ref = f"tmp:sha256:{digest}"
            self._store.put(content_ref, body)
            lifecycle = TemporaryContent(
                content_ref=content_ref,
                retention_class=RetentionClass.TEMPORARY_SUCCESS,
                captured_at=retrieved_at,
                expires_at=retrieved_at + self._retention,
            )
            return FilingDocumentAcquisition(
                accession=filing.accession,
                source_ref=filing.primary_document_ref,
                content_hash=digest,
                temporary_content=lifecycle,
                retrieved_at=retrieved_at,
            )
        except SecRequestFailure as exc:
            return FilingDocumentAcquisition(
                accession=filing.accession,
                source_ref=filing.primary_document_ref,
                content_hash=None,
                temporary_content=None,
                retrieved_at=retrieved_at,
                error=ErrorInfo(
                    exc.category,
                    exc.retryable,
                    "SEC filing document request failed",
                    _bounded_retry_after(exc.retry_after),
                ),
            )
        except Exception:
            return FilingDocumentAcquisition(
                accession=filing.accession,
                source_ref=filing.primary_document_ref,
                content_hash=None,
                temporary_content=None,
                retrieved_at=retrieved_at,
                error=ErrorInfo("transport_error", True, "SEC filing document request failed"),
            )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation("document retrieved_at must be normalized to UTC")


def _bounded_retry_after(value: timedelta | None) -> timedelta | None:
    if value is None:
        return None
    if value < timedelta(0) or value > timedelta(hours=24):
        return None
    return value
