"""Provider-neutral SEC Company Facts/XBRL normalization boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from orderscope_local.contracts import ContractViolation, ErrorInfo

from .submissions import CANARY_COMPANIES, SEC_DATA_ORIGIN, SecJsonTransport, SecRateLimiter, SecRequestFailure


_CURSOR = re.compile(r"offset:([0-9]+)")
_ACCESSION = re.compile(r"[0-9]{10}-[0-9]{2}-[0-9]{6}")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9._-]*")


@dataclass(frozen=True, slots=True)
class XbrlDimension:
    axis: str
    member: str

    def __post_init__(self) -> None:
        if not _valid_qname(self.axis) or not _valid_qname(self.member):
            raise ContractViolation("XBRL dimension axis and member must be canonical QNames")


@dataclass(frozen=True, slots=True)
class XbrlPeriod:
    start: date | None = None
    end: date | None = None
    instant: date | None = None

    def __post_init__(self) -> None:
        duration = self.start is not None or self.end is not None
        if self.instant is not None:
            if duration:
                raise ContractViolation("XBRL period cannot be both instant and duration")
            return
        if self.start is None or self.end is None or self.start > self.end:
            raise ContractViolation("XBRL duration requires an ordered start and end")


@dataclass(frozen=True, slots=True)
class XbrlFact:
    concept: str
    value: Decimal
    unit: str
    period: XbrlPeriod
    dimensions: tuple[XbrlDimension, ...]
    filing_source_ref: str
    source_accession: str
    source_form: str
    filed_on: date
    source_ref: str

    def __post_init__(self) -> None:
        if not _valid_qname(self.concept):
            raise ContractViolation("XBRL concept must be a canonical QName")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ContractViolation("XBRL value must be a finite Decimal")
        if not isinstance(self.unit, str) or not self.unit or self.unit != self.unit.strip():
            raise ContractViolation("XBRL unit must be non-blank canonical text")
        if not isinstance(self.period, XbrlPeriod):
            raise ContractViolation("XBRL period must be an XbrlPeriod")
        if not isinstance(self.dimensions, tuple) or any(
            not isinstance(item, XbrlDimension) for item in self.dimensions
        ):
            raise ContractViolation("XBRL dimensions must contain XbrlDimension values")
        if tuple(sorted(self.dimensions, key=lambda item: (item.axis, item.member))) != self.dimensions:
            raise ContractViolation("XBRL dimensions must be in canonical order")
        if len({item.axis for item in self.dimensions}) != len(self.dimensions):
            raise ContractViolation("XBRL dimensions cannot repeat an axis")
        if _ACCESSION.fullmatch(self.source_accession) is None:
            raise ContractViolation("XBRL source accession is invalid")
        if (
            not isinstance(self.source_form, str)
            or not self.source_form
            or self.source_form != self.source_form.strip()
        ):
            raise ContractViolation("XBRL source form must be canonical text")
        for field, value in (
            ("filing_source_ref", self.filing_source_ref),
            ("source_ref", self.source_ref),
        ):
            if not isinstance(value, str) or not value or value != value.strip():
                raise ContractViolation(f"XBRL {field} must be a non-blank canonical reference")


@dataclass(frozen=True, slots=True)
class XbrlFactPage:
    facts: tuple[XbrlFact, ...]
    next_cursor: str | None
    retrieved_at: datetime
    source_ref: str
    error: ErrorInfo | None = None


class SecCompanyFactsAdapter:
    """Fetch a bounded page while keeping the SEC JSON shape inside this module."""

    def __init__(self, *, transport: SecJsonTransport, user_agent: str, limiter: SecRateLimiter,
                 clock: Callable[[], datetime] | None = None) -> None:
        if not isinstance(user_agent, str) or not user_agent.strip() or "@" not in user_agent or len(user_agent) > 256:
            raise ContractViolation("SEC User-Agent must include a bounded contact address")
        self._transport = transport
        self._user_agent = user_agent
        self._limiter = limiter
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch(self, *, source_key: str, window_start: date, window_end: date,
              cursor: str | None = None, page_size: int = 1000) -> XbrlFactPage:
        company = _company(source_key)
        if not isinstance(window_start, date) or not isinstance(window_end, date) or window_start >= window_end:
            raise ContractViolation("Company Facts window must be a non-empty half-open date range")
        if not 1 <= page_size <= 10_000:
            raise ContractViolation("Company Facts page_size is outside the bounded range")
        offset = _decode_cursor(cursor)
        retrieved_at = self._clock()
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() != timedelta(0):
            raise ContractViolation("Company Facts retrieved_at must be normalized to UTC")
        source_ref = f"{SEC_DATA_ORIGIN}/api/xbrl/companyfacts/CIK{company.cik}.json"
        try:
            self._limiter.acquire()
            try:
                payload = self._transport.get_json(source_ref, user_agent=self._user_agent)
            except SecRequestFailure:
                raise
            except Exception as exc:
                raise SecRequestFailure("transport_error", True) from exc
            facts = _decode_company_facts(payload, company.cik)
            facts = [fact for fact in facts if window_start <= fact.filed_on < window_end]
            facts.sort(key=lambda fact: (fact.filed_on, fact.source_accession, fact.concept, fact.unit,
                                         fact.period.start or fact.period.instant, fact.period.end or fact.period.instant))
            selected = tuple(facts[offset:offset + page_size])
            next_offset = offset + len(selected)
            return XbrlFactPage(selected, f"offset:{next_offset}" if next_offset < len(facts) else None,
                                retrieved_at, source_ref)
        except SecRequestFailure as exc:
            return XbrlFactPage((), None, retrieved_at, source_ref,
                                ErrorInfo(exc.category, exc.retryable, "SEC Company Facts request failed", exc.retry_after))
        except (ContractViolation, InvalidOperation, TypeError, ValueError):
            return XbrlFactPage((), None, retrieved_at, source_ref,
                                ErrorInfo("invalid_response", False, "SEC Company Facts request failed"))


def normalize_xbrl_fact(*, concept: str, value: object, unit: str, start: str | None,
                        end: str, dimensions: Mapping[str, str], accession: str,
                        form: str, filed: str, source_ref: str) -> XbrlFact:
    """Normalize a numeric XBRL fact without accepting a provider object downstream."""
    try:
        number = Decimal(str(value))
        end_date = date.fromisoformat(end)
        period = XbrlPeriod(instant=end_date) if start is None else XbrlPeriod(date.fromisoformat(start), end_date)
        dimension_items = tuple(sorted((XbrlDimension(axis, member) for axis, member in dimensions.items()),
                                       key=lambda item: (item.axis, item.member)))
        cik = accession[:10]
        filing_ref = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"
        return XbrlFact(concept, number, unit, period, dimension_items, filing_ref, accession,
                        form, date.fromisoformat(filed), source_ref)
    except (AttributeError, InvalidOperation, ValueError, TypeError) as exc:
        raise ContractViolation("XBRL fact contains invalid value, period, or source") from exc


def _decode_company_facts(payload: object, cik: str) -> list[XbrlFact]:
    if not isinstance(payload, Mapping) or str(payload.get("cik", "")).zfill(10) != cik:
        raise ValueError("invalid company facts root")
    taxonomies = payload.get("facts")
    if not isinstance(taxonomies, Mapping):
        raise ValueError("invalid company facts collection")
    source_ref = f"{SEC_DATA_ORIGIN}/api/xbrl/companyfacts/CIK{cik}.json"
    result: list[XbrlFact] = []
    for taxonomy, concepts in taxonomies.items():
        if not isinstance(taxonomy, str) or not _NAME.fullmatch(taxonomy) or not isinstance(concepts, Mapping):
            raise ValueError("invalid taxonomy")
        for name, concept_body in concepts.items():
            if not isinstance(name, str) or not _NAME.fullmatch(name) or not isinstance(concept_body, Mapping):
                raise ValueError("invalid concept")
            units = concept_body.get("units")
            if not isinstance(units, Mapping):
                raise ValueError("invalid units")
            for unit, observations in units.items():
                if not isinstance(unit, str) or not unit or not isinstance(observations, list):
                    raise ValueError("invalid unit observations")
                for observation in observations:
                    if not isinstance(observation, Mapping):
                        raise ValueError("invalid observation")
                    fact = normalize_xbrl_fact(
                        concept=f"{taxonomy}:{name}", value=observation.get("val"), unit=unit,
                        start=observation.get("start"), end=observation.get("end"), dimensions={},
                        accession=observation.get("accn"), form=observation.get("form"),
                        filed=observation.get("filed"), source_ref=source_ref,
                    )
                    if fact.source_accession[:10] != cik:
                        raise ValueError("Company Facts accession does not match root CIK")
                    result.append(fact)
    return result


def _company(source_key: str):
    prefix = "sec:companyfacts:"
    if not isinstance(source_key, str) or not source_key.startswith(prefix):
        raise ContractViolation("SEC Company Facts source_key is invalid")
    company = CANARY_COMPANIES.get(source_key[len(prefix):])
    if company is None:
        raise ContractViolation("SEC Company Facts source is outside the corporate canary")
    return company


def _decode_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    match = _CURSOR.fullmatch(cursor)
    if match is None:
        raise ContractViolation("SEC Company Facts cursor is invalid")
    return int(match.group(1))


def _valid_qname(value: object) -> bool:
    if not isinstance(value, str) or value.count(":") != 1:
        return False
    return all(_NAME.fullmatch(part) is not None for part in value.split(":"))
