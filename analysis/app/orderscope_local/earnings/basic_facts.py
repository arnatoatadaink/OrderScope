"""Basic source-grounded earnings Fact extraction for E0-004.

This module converts already-observed issuer/SEC earnings metrics into the
accepted Fact Store boundary.  It does not parse raw filing bodies, infer
missing values, reconcile disagreements across sources, or manufacture fiscal
period/timestamp semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
import hashlib
import re

from orderscope_local.contracts import (
    AccountingBasis,
    ContractViolation,
    Evidence,
    EvidenceKind,
    EvidenceQuality,
    Fact,
    FactAssertionKind,
    Provenance,
    RetentionClass,
    SourceTimestamp,
    validate_fact_store,
)


_CURRENCY = re.compile(r"[A-Z]{3}")
_CANARY = {"AMD", "NVDA"}


class BasicEarningsMetricType(StrEnum):
    REVENUE = "revenue"
    NET_INCOME = "net_income"
    BASIC_EPS = "basic_eps"
    DILUTED_EPS = "diluted_eps"

    @property
    def is_per_share(self) -> bool:
        return self in (self.BASIC_EPS, self.DILUTED_EPS)


@dataclass(frozen=True, slots=True)
class ObservedEarningsMetric:
    """One explicitly observed basic earnings value from one durable source.

    All semantic values must already be established by the source or upstream
    adapter.  In particular, callers must not pass inferred fiscal labels,
    periods, currencies, values, or source timestamps.
    """

    instrument_id: str
    fiscal_year_label: str
    fiscal_quarter: str
    period_end: date
    metric_type: BasicEarningsMetricType
    value: Decimal
    currency: str
    accounting_basis: AccountingBasis
    assertion_kind: FactAssertionKind
    provenance: Provenance
    period_start: date | None = None
    extraction_confidence: float | None = None

    def __post_init__(self) -> None:
        if self.instrument_id not in _CANARY:
            raise ContractViolation("basic earnings metric is outside the corporate canary")
        for field, value in (
            ("fiscal_year_label", self.fiscal_year_label),
            ("fiscal_quarter", self.fiscal_quarter),
        ):
            if not isinstance(value, str) or not value or value != value.strip() or len(value) > 64:
                raise ContractViolation(f"earnings {field} must be bounded canonical text")
        if not isinstance(self.period_end, date):
            raise ContractViolation("earnings period_end must be a date")
        if self.period_start is not None:
            if not isinstance(self.period_start, date):
                raise ContractViolation("earnings period_start must be null or a date")
            if self.period_start > self.period_end:
                raise ContractViolation("earnings period_start cannot be later than period_end")
        if not isinstance(self.metric_type, BasicEarningsMetricType):
            raise ContractViolation("basic earnings metric_type is invalid")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ContractViolation("basic earnings value must be a finite Decimal")
        if not isinstance(self.currency, str) or _CURRENCY.fullmatch(self.currency) is None:
            raise ContractViolation("earnings currency must be an explicit uppercase ISO-style code")
        if not isinstance(self.accounting_basis, AccountingBasis):
            raise ContractViolation("earnings accounting_basis is invalid")
        if not isinstance(self.assertion_kind, FactAssertionKind):
            raise ContractViolation("earnings assertion_kind is invalid")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("basic earnings metric requires accepted provenance")
        if self.extraction_confidence is not None and not 0 <= self.extraction_confidence <= 1:
            raise ContractViolation("earnings extraction_confidence must be between zero and one")


def extract_basic_earnings_records(
    observations: tuple[ObservedEarningsMetric, ...],
) -> tuple[Fact | Evidence, ...]:
    """Create deterministic source-grounded Fact/Evidence records.

    Exact duplicate observations collapse by deterministic extraction identity.
    Different source references/hashes remain independent Fact/Evidence pairs,
    even when their semantic values match; cross-source reconciliation belongs
    to E0-007 rather than extraction.
    """

    if not isinstance(observations, tuple) or not observations:
        raise ContractViolation("basic earnings extraction requires a non-empty tuple")
    if any(not isinstance(item, ObservedEarningsMetric) for item in observations):
        raise ContractViolation("basic earnings extraction contains an invalid observation")

    unique: dict[str, ObservedEarningsMetric] = {}
    for observation in observations:
        identity = _observation_identity(observation)
        existing = unique.get(identity)
        if existing is not None and existing != observation:
            raise ContractViolation("basic earnings extraction identity has conflicting semantics")
        unique[identity] = observation

    records: list[Fact | Evidence] = []
    for identity in sorted(unique):
        observation = unique[identity]
        fact_id = f"fact:earnings:{identity}"
        evidence_id = f"evidence:earnings:{identity}"
        accepted_at = observation.provenance.accepted_at
        created_at = observation.provenance.retrieved_at
        subject_ref = f"instrument:{observation.instrument_id}"

        fact = Fact(
            record_id=fact_id,
            schema_version="earnings.basic.v0.1",
            subject_ref=subject_ref,
            accepted_at=accepted_at,
            created_at=created_at,
            provenance=observation.provenance,
            fact_type=f"earnings.{observation.metric_type.value}",
            value={
                "amount": format(observation.value, "f"),
                "currency": observation.currency,
                "accounting_basis": observation.accounting_basis.value,
                "fiscal_year_label": observation.fiscal_year_label,
                "fiscal_quarter": observation.fiscal_quarter,
            },
            assertion_kind=observation.assertion_kind,
            evidence_record_ids=(evidence_id,),
            unit=(
                f"{observation.currency}_per_share"
                if observation.metric_type.is_per_share
                else observation.currency
            ),
            period_start=(
                None
                if observation.period_start is None
                else SourceTimestamp.date_only(observation.period_start)
            ),
            period_end=SourceTimestamp.date_only(observation.period_end),
            extraction_confidence=observation.extraction_confidence,
        )
        evidence = Evidence(
            record_id=evidence_id,
            schema_version="earnings.basic.v0.1",
            subject_ref=subject_ref,
            accepted_at=accepted_at,
            created_at=created_at,
            provenance=observation.provenance,
            evidence_kind=EvidenceKind.SUPPORTING,
            target_record_ids=(fact_id,),
            locator=observation.provenance.source_ref.value,
            quality_class=EvidenceQuality.TIER_1_OFFICIAL,
            retention_class=RetentionClass.DURABLE_METADATA,
        )
        records.extend((fact, evidence))

    result = tuple(records)
    validate_fact_store(result)
    return result


def _observation_identity(observation: ObservedEarningsMetric) -> str:
    fields = (
        observation.instrument_id,
        observation.fiscal_year_label,
        observation.fiscal_quarter,
        observation.period_start.isoformat() if observation.period_start else "",
        observation.period_end.isoformat(),
        observation.metric_type.value,
        format(observation.value, "f"),
        observation.currency,
        observation.accounting_basis.value,
        observation.assertion_kind.value,
        observation.provenance.source_ref.value,
        observation.provenance.content_hash.digest,
    )
    payload = "\x1f".join(fields).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]
