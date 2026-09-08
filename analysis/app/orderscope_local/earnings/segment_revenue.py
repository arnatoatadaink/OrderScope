"""Segment-revenue fallback chain for E0-005.

The chain records every attempted extraction method and its failure reason.
Missing Company Facts output never becomes a numeric zero or a claim that a
segment does not exist. Successful values remain source-grounded observations;
segment identity normalization is deferred to E0-006.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from orderscope_local.contracts import ContractViolation, Provenance
from orderscope_local.sec import XbrlFact


class SegmentRevenueMethod(StrEnum):
    COMPANY_FACTS = "company_facts"
    XBRL_DIMENSION = "xbrl_dimension"
    FILING_TABLE = "filing_table"


class SegmentRevenueStatus(StrEnum):
    SUCCESS = "success"
    NOT_APPLICABLE = "not_applicable"
    PARTIAL = "partial"
    FAILED = "failed"


class SegmentRevenueFailureReason(StrEnum):
    ENTITY_WIDE_ONLY = "entity_wide_only"
    DIMENSION_FACT_NOT_IN_COMPANYFACTS_SCOPE = "dimension_fact_not_in_companyfacts_scope"
    CUSTOM_EXTENSION_NOT_NORMALIZED = "custom_extension_not_normalized"
    CONCEPT_NOT_FOUND = "concept_not_found"
    PERIOD_MISMATCH = "period_mismatch"
    UNIT_MISMATCH = "unit_mismatch"
    CONTEXT_MEMBER_UNRESOLVED = "context_member_unresolved"
    TABLE_LAYOUT_UNRESOLVED = "table_layout_unresolved"
    TRANSPORT_ERROR = "transport_error"


@dataclass(frozen=True, slots=True)
class SegmentRevenueAttempt:
    method: SegmentRevenueMethod
    status: SegmentRevenueStatus
    failure_reason: SegmentRevenueFailureReason | None
    source_accession: str
    source_ref: str
    concept_qname: str | None = None
    axis_member: tuple[tuple[str, str], ...] = ()
    raw_label: str | None = None
    table_role: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.method, SegmentRevenueMethod):
            raise ContractViolation("segment revenue method is invalid")
        if not isinstance(self.status, SegmentRevenueStatus):
            raise ContractViolation("segment revenue status is invalid")
        if self.status is SegmentRevenueStatus.SUCCESS and self.failure_reason is not None:
            raise ContractViolation("successful segment revenue attempt cannot have failure_reason")
        if self.status is not SegmentRevenueStatus.SUCCESS and not isinstance(
            self.failure_reason, SegmentRevenueFailureReason
        ):
            raise ContractViolation("unsuccessful segment revenue attempt requires failure_reason")
        if not isinstance(self.source_accession, str) or not self.source_accession:
            raise ContractViolation("segment revenue attempt requires source_accession")
        if not isinstance(self.source_ref, str) or not self.source_ref.strip():
            raise ContractViolation("segment revenue attempt requires source_ref")
        if self.concept_qname is not None and ":" not in self.concept_qname:
            raise ContractViolation("segment revenue concept_qname must be a QName")
        if tuple(sorted(self.axis_member)) != self.axis_member:
            raise ContractViolation("segment revenue axis/member pairs must be canonical ordered")
        if len({axis for axis, _ in self.axis_member}) != len(self.axis_member):
            raise ContractViolation("segment revenue axis/member pairs cannot repeat an axis")
        for field, value in (("raw_label", self.raw_label), ("table_role", self.table_role)):
            if value is not None and (not value.strip() or len(value) > 512):
                raise ContractViolation(f"segment revenue {field} must be bounded text")


@dataclass(frozen=True, slots=True)
class SegmentRevenueObservation:
    instrument_id: str
    raw_label: str
    classification_role: str
    period_start: date
    period_end: date
    value: Decimal
    currency: str
    display_scale: int
    provenance: Provenance
    source_accession: str
    method: SegmentRevenueMethod
    concept_qname: str | None = None
    axis_member: tuple[tuple[str, str], ...] = ()
    table_role: str | None = None

    def __post_init__(self) -> None:
        if self.instrument_id not in {"AMD", "NVDA"}:
            raise ContractViolation("segment revenue observation is outside the corporate canary")
        for field, value in (("raw_label", self.raw_label), ("classification_role", self.classification_role)):
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise ContractViolation(f"segment revenue {field} must be bounded text")
        if not isinstance(self.period_start, date) or not isinstance(self.period_end, date):
            raise ContractViolation("segment revenue period must be explicit dates")
        if self.period_start > self.period_end:
            raise ContractViolation("segment revenue period_start cannot exceed period_end")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ContractViolation("segment revenue value must be a finite Decimal")
        if self.currency != "USD":
            raise ContractViolation("v0.1 segment revenue currency must be explicit USD")
        if not isinstance(self.display_scale, int) or self.display_scale < 0:
            raise ContractViolation("segment revenue display_scale must be a non-negative integer")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("segment revenue observation requires Provenance")
        if not self.source_accession:
            raise ContractViolation("segment revenue observation requires source_accession")
        if not isinstance(self.method, SegmentRevenueMethod):
            raise ContractViolation("segment revenue observation method is invalid")
        if self.method is SegmentRevenueMethod.XBRL_DIMENSION and not self.axis_member:
            raise ContractViolation("dimension extraction requires axis/member evidence")
        if self.method is SegmentRevenueMethod.FILING_TABLE and not self.table_role:
            raise ContractViolation("filing-table extraction requires table_role")


@dataclass(frozen=True, slots=True)
class SegmentRevenueResolution:
    attempts: tuple[SegmentRevenueAttempt, ...]
    observation: SegmentRevenueObservation | None

    def __post_init__(self) -> None:
        if not self.attempts:
            raise ContractViolation("segment revenue resolution requires attempts")
        methods = tuple(item.method for item in self.attempts)
        order = (
            SegmentRevenueMethod.COMPANY_FACTS,
            SegmentRevenueMethod.XBRL_DIMENSION,
            SegmentRevenueMethod.FILING_TABLE,
        )
        if methods != order[: len(methods)]:
            raise ContractViolation("segment revenue attempts must follow the fallback order")
        successes = [item for item in self.attempts if item.status is SegmentRevenueStatus.SUCCESS]
        if self.observation is None:
            if successes:
                raise ContractViolation("successful attempt requires an observation")
        else:
            if len(successes) != 1 or successes[0].method is not self.observation.method:
                raise ContractViolation("observation must match exactly one successful attempt")
            if self.attempts[-1].method is not self.observation.method:
                raise ContractViolation("fallback chain must stop at the successful method")


def resolve_segment_revenue(
    *,
    company_facts: tuple[XbrlFact, ...] = (),
    dimension_facts: tuple[XbrlFact, ...] = (),
    filing_observation: SegmentRevenueObservation | None = None,
    instrument_id: str,
    raw_label: str,
    classification_role: str,
    period_start: date,
    period_end: date,
    source_accession: str,
    expected_unit: str = "USD",
    company_facts_failure: SegmentRevenueFailureReason = SegmentRevenueFailureReason.DIMENSION_FACT_NOT_IN_COMPANYFACTS_SCOPE,
    dimension_failure: SegmentRevenueFailureReason = SegmentRevenueFailureReason.CONTEXT_MEMBER_UNRESOLVED,
    filing_failure: SegmentRevenueFailureReason = SegmentRevenueFailureReason.TABLE_LAYOUT_UNRESOLVED,
) -> SegmentRevenueResolution:
    """Resolve one segment revenue using the fixed fallback order.

    Inputs are already-normalized source observations. This function does not
    parse HTML/XBRL payloads and does not normalize segment identity by name.
    """

    if instrument_id not in {"AMD", "NVDA"}:
        raise ContractViolation("segment revenue resolution is outside the corporate canary")
    if not raw_label.strip() or not classification_role.strip():
        raise ContractViolation("segment revenue resolution requires explicit labels")
    if period_start > period_end:
        raise ContractViolation("segment revenue resolution period is invalid")
    attempts: list[SegmentRevenueAttempt] = []

    company = _select_fact(
        company_facts,
        period_start=period_start,
        period_end=period_end,
        source_accession=source_accession,
        expected_unit=expected_unit,
        require_dimensions=False,
    )
    if company is not None and company.dimensions:
        raise ContractViolation("Company Facts stage cannot masquerade as dimension-aware input")
    if company is not None:
        observation = _from_xbrl(
            fact=company,
            instrument_id=instrument_id,
            raw_label=raw_label,
            classification_role=classification_role,
            method=SegmentRevenueMethod.COMPANY_FACTS,
        )
        attempts.append(_success_attempt(observation, company))
        return SegmentRevenueResolution(tuple(attempts), observation)
    attempts.append(
        SegmentRevenueAttempt(
            method=SegmentRevenueMethod.COMPANY_FACTS,
            status=SegmentRevenueStatus.FAILED,
            failure_reason=company_facts_failure,
            source_accession=source_accession,
            source_ref="sec:companyfacts",
            raw_label=raw_label,
        )
    )

    dimension = _select_fact(
        dimension_facts,
        period_start=period_start,
        period_end=period_end,
        source_accession=source_accession,
        expected_unit=expected_unit,
        require_dimensions=True,
    )
    if dimension is not None:
        observation = _from_xbrl(
            fact=dimension,
            instrument_id=instrument_id,
            raw_label=raw_label,
            classification_role=classification_role,
            method=SegmentRevenueMethod.XBRL_DIMENSION,
        )
        attempts.append(_success_attempt(observation, dimension))
        return SegmentRevenueResolution(tuple(attempts), observation)
    attempts.append(
        SegmentRevenueAttempt(
            method=SegmentRevenueMethod.XBRL_DIMENSION,
            status=SegmentRevenueStatus.FAILED,
            failure_reason=dimension_failure,
            source_accession=source_accession,
            source_ref="sec:xbrl-instance",
            raw_label=raw_label,
        )
    )

    if filing_observation is not None:
        if filing_observation.method is not SegmentRevenueMethod.FILING_TABLE:
            raise ContractViolation("filing fallback observation must use filing_table method")
        if (
            filing_observation.instrument_id != instrument_id
            or filing_observation.raw_label != raw_label
            or filing_observation.period_start != period_start
            or filing_observation.period_end != period_end
            or filing_observation.source_accession != source_accession
        ):
            raise ContractViolation("filing fallback observation does not match requested event")
        attempts.append(
            SegmentRevenueAttempt(
                method=SegmentRevenueMethod.FILING_TABLE,
                status=SegmentRevenueStatus.SUCCESS,
                failure_reason=None,
                source_accession=source_accession,
                source_ref=filing_observation.provenance.source_ref.value,
                raw_label=raw_label,
                table_role=filing_observation.table_role,
            )
        )
        return SegmentRevenueResolution(tuple(attempts), filing_observation)

    attempts.append(
        SegmentRevenueAttempt(
            method=SegmentRevenueMethod.FILING_TABLE,
            status=SegmentRevenueStatus.FAILED,
            failure_reason=filing_failure,
            source_accession=source_accession,
            source_ref="sec:filing-table",
            raw_label=raw_label,
        )
    )
    return SegmentRevenueResolution(tuple(attempts), None)


def _select_fact(
    facts: tuple[XbrlFact, ...],
    *,
    period_start: date,
    period_end: date,
    source_accession: str,
    expected_unit: str,
    require_dimensions: bool,
) -> XbrlFact | None:
    matches = [
        fact
        for fact in facts
        if fact.source_accession == source_accession
        and fact.period.start == period_start
        and fact.period.end == period_end
        and fact.unit == expected_unit
        and bool(fact.dimensions) is require_dimensions
    ]
    if len(matches) > 1:
        raise ContractViolation("segment revenue fallback has ambiguous matching XBRL facts")
    return matches[0] if matches else None


def _from_xbrl(
    *,
    fact: XbrlFact,
    instrument_id: str,
    raw_label: str,
    classification_role: str,
    method: SegmentRevenueMethod,
) -> SegmentRevenueObservation:
    if fact.period.start is None or fact.period.end is None:
        raise ContractViolation("segment revenue requires duration XBRL facts")
    provenance = Provenance(
        source_ref=__import__("orderscope_local.contracts", fromlist=["SourceReference"]).SourceReference(fact.source_ref),
        content_hash=__import__("orderscope_local.contracts", fromlist=["ContentHash"]).ContentHash("0" * 64),
        retrieved_at=__import__("datetime", fromlist=["datetime", "timezone"]).datetime(1970, 1, 1, tzinfo=__import__("datetime", fromlist=["timezone"]).timezone.utc),
        available_at=__import__("datetime", fromlist=["datetime", "timezone"]).datetime(1970, 1, 1, tzinfo=__import__("datetime", fromlist=["timezone"]).timezone.utc),
        accepted_at=__import__("datetime", fromlist=["datetime", "timezone"]).datetime(1970, 1, 1, tzinfo=__import__("datetime", fromlist=["timezone"]).timezone.utc),
    )
    return SegmentRevenueObservation(
        instrument_id=instrument_id,
        raw_label=raw_label,
        classification_role=classification_role,
        period_start=fact.period.start,
        period_end=fact.period.end,
        value=fact.value,
        currency="USD",
        display_scale=0,
        provenance=provenance,
        source_accession=fact.source_accession,
        method=method,
        concept_qname=fact.concept,
        axis_member=tuple((item.axis, item.member) for item in fact.dimensions),
    )


def _success_attempt(observation: SegmentRevenueObservation, fact: XbrlFact) -> SegmentRevenueAttempt:
    return SegmentRevenueAttempt(
        method=observation.method,
        status=SegmentRevenueStatus.SUCCESS,
        failure_reason=None,
        source_accession=fact.source_accession,
        source_ref=fact.source_ref,
        concept_qname=fact.concept,
        axis_member=observation.axis_member,
        raw_label=observation.raw_label,
    )
