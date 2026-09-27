"""Bounded SEC Submissions adapter for the AMD/NVIDIA corporate canary.

SEC columnar response shapes are decoded in this module and never cross the
provider-neutral adapter boundary. Persistence and target-form filtering belong
to later S0 tasks.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import re
from threading import Lock
import time
from typing import Any, Protocol

from orderscope_local.contracts import (
    AdapterItem,
    AdapterPage,
    AdapterRequest,
    ContentHash,
    ContentIdentity,
    ContractViolation,
    ErrorInfo,
    ProviderRevision,
    StableIdentity,
)


SEC_DATA_ORIGIN = "https://data.sec.gov"
_CURSOR = re.compile(r"offset:([0-9]+)")
_ACCESSION = re.compile(r"[0-9]{10}-[0-9]{2}-[0-9]{6}")
_HISTORY_FILE = re.compile(r"CIK[0-9]{10}-submissions-[0-9]+\.json")


@dataclass(frozen=True, slots=True)
class SecCanaryCompany:
    ticker: str
    cik: str


CANARY_COMPANIES = {
    "amd": SecCanaryCompany("AMD", "0000002488"),
    "nvda": SecCanaryCompany("NVDA", "0001045810"),
}


class SecJsonTransport(Protocol):
    def get_json(self, url: str, *, user_agent: str) -> Mapping[str, Any]: ...


class SecRateLimiter(Protocol):
    def acquire(self) -> None: ...


class FixedIntervalSecRateLimiter:
    """Process-shared fixed-interval gate capped below SEC's public ceiling."""

    def __init__(
        self,
        *,
        requests_per_second: float = 8.0,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not 0 < requests_per_second <= 10:
            raise ContractViolation("SEC request rate must be within (0, 10] requests per second")
        self._interval = 1.0 / requests_per_second
        self._monotonic = monotonic
        self._sleep = sleep
        self._next_allowed = 0.0
        self._lock = Lock()

    def acquire(self) -> None:
        with self._lock:
            now = self._monotonic()
            delay = self._next_allowed - now
            if delay > 0:
                self._sleep(delay)
                now = self._monotonic()
            self._next_allowed = max(now, self._next_allowed) + self._interval


@dataclass(frozen=True, slots=True)
class SecRequestFailure(Exception):
    """Sanitized transport failure safe to expose through the common contract."""

    category: str
    retryable: bool
    retry_after: timedelta | None = None


class SecSubmissionsAdapter:
    """Read and normalize one bounded page of AMD or NVIDIA filing metadata."""

    def __init__(
        self,
        *,
        transport: SecJsonTransport,
        user_agent: str,
        limiter: SecRateLimiter,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(user_agent, str) or not user_agent.strip():
            raise ContractViolation("SEC User-Agent must be declared")
        if "@" not in user_agent or len(user_agent) > 256:
            raise ContractViolation("SEC User-Agent must include a bounded contact address")
        self._transport = transport
        self._user_agent = user_agent
        self._limiter = limiter
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch(self, request: AdapterRequest) -> AdapterPage:
        _validate_request(request)
        retrieved_at = self._clock()
        try:
            company = _company_for_source(request.source_key)
            offset = _decode_cursor(request.cursor)
            rows, revision = self._load_rows(company, request)
            page_rows = rows[offset : offset + request.page_size]
            next_offset = offset + len(page_rows)
            next_cursor = f"offset:{next_offset}" if next_offset < len(rows) else None
            return AdapterPage(
                items=tuple(_normalize(row, company) for row in page_rows),
                next_cursor=next_cursor,
                partial=False,
                retrieved_at=retrieved_at,
                available_at=retrieved_at,
                provider_revision=revision,
            )
        except SecRequestFailure as exc:
            return AdapterPage(
                items=(),
                next_cursor=None,
                partial=False,
                retrieved_at=retrieved_at,
                available_at=retrieved_at,
                error=ErrorInfo(exc.category, exc.retryable, "SEC request failed", exc.retry_after),
            )

    def _get(self, path: str) -> Mapping[str, Any]:
        self._limiter.acquire()
        try:
            result = self._transport.get_json(f"{SEC_DATA_ORIGIN}/{path}", user_agent=self._user_agent)
        except SecRequestFailure:
            raise
        except Exception as exc:
            raise SecRequestFailure("transport_error", True) from exc
        if not isinstance(result, Mapping):
            raise SecRequestFailure("invalid_response", False)
        return result

    def _load_rows(
        self, company: SecCanaryCompany, request: AdapterRequest
    ) -> tuple[list[dict[str, str]], ProviderRevision | None]:
        root = self._get(f"submissions/CIK{company.cik}.json")
        root_cik = root.get("cik")
        if not isinstance(root_cik, (int, str)) or str(root_cik).zfill(10) != company.cik:
            raise SecRequestFailure("invalid_response", False)
        filings = root.get("filings")
        if not isinstance(filings, Mapping):
            raise SecRequestFailure("invalid_response", False)
        rows = _decode_columns(filings.get("recent"))
        history = filings.get("files", ())
        if not isinstance(history, list):
            raise SecRequestFailure("invalid_response", False)
        for entry in history:
            if not isinstance(entry, Mapping) or not _history_intersects(entry, request):
                continue
            name = entry.get("name")
            if (
                not isinstance(name, str)
                or not _HISTORY_FILE.fullmatch(name)
                or not name.startswith(f"CIK{company.cik}-")
            ):
                raise SecRequestFailure("invalid_response", False)
            rows.extend(_decode_columns(self._get(f"submissions/{name}")))
        bounded = [row for row in rows if _in_window(row["filingDate"], request)]
        bounded.sort(key=lambda row: (row["filingDate"], row["accessionNumber"]))
        revision_value = root.get("lastModified")
        revision = ProviderRevision(revision_value) if isinstance(revision_value, str) and revision_value else None
        return bounded, revision


def _company_for_source(source_key: str) -> SecCanaryCompany:
    prefix = "sec:submissions:"
    if not isinstance(source_key, str) or not source_key.startswith(prefix):
        raise ContractViolation("SEC submissions source_key is invalid")
    company = CANARY_COMPANIES.get(source_key[len(prefix) :])
    if company is None:
        raise ContractViolation("SEC submissions source is outside the corporate canary")
    return company


def _validate_request(request: AdapterRequest) -> None:
    if not isinstance(request, AdapterRequest):
        raise ContractViolation("SEC submissions request must be an AdapterRequest")
    for field, value in (("window_start", request.window_start), ("window_end", request.window_end)):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ContractViolation(f"{field} must be normalized to UTC")
    if request.window_start >= request.window_end:
        raise ContractViolation("SEC submissions window must be non-empty and half-open")
    if not 1 <= request.page_size <= 10_000:
        raise ContractViolation("SEC submissions page_size is outside the bounded range")


def _decode_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    match = _CURSOR.fullmatch(cursor)
    if match is None:
        raise ContractViolation("SEC submissions cursor is invalid")
    return int(match.group(1))


def _decode_columns(value: object) -> list[dict[str, str]]:
    if not isinstance(value, Mapping):
        raise SecRequestFailure("invalid_response", False)
    required = ("accessionNumber", "filingDate", "reportDate", "acceptanceDateTime", "form", "primaryDocument")
    columns = {key: value.get(key) for key in required}
    if any(not isinstance(column, list) for column in columns.values()):
        raise SecRequestFailure("invalid_response", False)
    lengths = {len(column) for column in columns.values()}
    if len(lengths) != 1:
        raise SecRequestFailure("invalid_response", False)
    rows: list[dict[str, str]] = []
    for values in zip(*(columns[key] for key in required), strict=True):
        if any(not isinstance(item, str) for item in values):
            raise SecRequestFailure("invalid_response", False)
        row = dict(zip(required, values, strict=True))
        if not _ACCESSION.fullmatch(row["accessionNumber"]):
            raise SecRequestFailure("invalid_response", False)
        rows.append(row)
    return rows


def _history_intersects(entry: Mapping[str, Any], request: AdapterRequest) -> bool:
    start = entry.get("filingFrom")
    end = entry.get("filingTo")
    if not isinstance(start, str) or not isinstance(end, str):
        raise SecRequestFailure("invalid_response", False)
    try:
        return date.fromisoformat(start) < request.window_end.date() and date.fromisoformat(end) >= request.window_start.date()
    except ValueError as exc:
        raise SecRequestFailure("invalid_response", False) from exc


def _in_window(filing_date: str, request: AdapterRequest) -> bool:
    try:
        instant = datetime.combine(date.fromisoformat(filing_date), datetime.min.time(), timezone.utc)
    except ValueError as exc:
        raise SecRequestFailure("invalid_response", False) from exc
    return request.window_start <= instant < request.window_end


def _normalize(row: Mapping[str, str], company: SecCanaryCompany) -> AdapterItem:
    normalized = {
        "cik": company.cik,
        "ticker": company.ticker,
        "accession": row["accessionNumber"],
        "form": row["form"],
        "filed_on": row["filingDate"],
        "period_end": row["reportDate"] or None,
        "source_accepted_at": row["acceptanceDateTime"] or None,
        "primary_document": row["primaryDocument"] or None,
    }
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    identity = ContentIdentity(
        StableIdentity.filing_accession(row["accessionNumber"]),
        ContentHash(hashlib.sha256(canonical.encode("utf-8")).hexdigest()),
    )
    return AdapterItem(normalized=normalized, content_identity=identity)
