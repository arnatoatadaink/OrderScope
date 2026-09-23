"""Source-grounded capital-instrument lifecycle Facts for UWBS-017."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .capital_instrument_state import CapitalInstrumentKind, CapitalInstrumentState, is_allowed_capital_instrument_transition
from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
        raise ContractViolation(f"{field} must be bounded canonical text")


@dataclass(frozen=True, kw_only=True)
class CapitalInstrumentLifecycleFact:
    instrument_ref: str
    issuer_ref: str
    instrument_kind: CapitalInstrumentKind
    state: CapitalInstrumentState
    provenance: Provenance
    accepted_at: datetime
    evidence_record_ids: tuple[str, ...]
    maturity_date: SourceTimestamp | None = None
    conversion_window_start: SourceTimestamp | None = None
    previous_state: CapitalInstrumentState | None = None
    previous_state_record_id: str | None = None
    principal_amount: float | None = None
    currency: str | None = None
    conversion_discount_percent: float | None = None

    def __post_init__(self) -> None:
        _text(self.instrument_ref, "instrument_ref")
        _text(self.issuer_ref, "issuer_ref")
        if not isinstance(self.instrument_kind, CapitalInstrumentKind):
            raise ContractViolation("instrument_kind must be CapitalInstrumentKind")
        if not isinstance(self.state, CapitalInstrumentState):
            raise ContractViolation("state must be CapitalInstrumentState")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        _utc(self.accepted_at, "accepted_at")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")
        if not isinstance(self.evidence_record_ids, tuple) or not self.evidence_record_ids:
            raise ContractViolation("evidence_record_ids must be a non-empty tuple")
        if len(self.evidence_record_ids) != len(set(self.evidence_record_ids)):
            raise ContractViolation("evidence_record_ids cannot contain duplicates")
        for ref in self.evidence_record_ids:
            _text(ref, "evidence_record_ids")
        if (self.previous_state is None) != (self.previous_state_record_id is None):
            raise ContractViolation("previous state value and record id must be provided together")
        if self.previous_state is not None:
            _text(self.previous_state_record_id, "previous_state_record_id")
            if not is_allowed_capital_instrument_transition(self.previous_state, self.state):
                raise ContractViolation("capital-instrument state transition is not allowed")
        for value, field in ((self.maturity_date, "maturity_date"), (self.conversion_window_start, "conversion_window_start")):
            if value is not None and not isinstance(value, SourceTimestamp):
                raise ContractViolation(f"{field} must be SourceTimestamp")
        if self.principal_amount is not None:
            if isinstance(self.principal_amount, bool) or self.principal_amount <= 0:
                raise ContractViolation("principal_amount must be positive")
            if self.currency is None:
                raise ContractViolation("principal_amount requires currency")
        if self.currency is not None:
            _text(self.currency, "currency")
        if self.conversion_discount_percent is not None and not 0 <= self.conversion_discount_percent < 100:
            raise ContractViolation("conversion_discount_percent must be in [0, 100)")

    def to_fact(self, *, record_id: str, supersedes_record_id: str | None = None) -> Fact:
        value = {
            "issuer_ref": self.issuer_ref,
            "instrument_kind": self.instrument_kind.value,
            "state": self.state.value,
            "maturity_date": self.maturity_date.calendar_date.isoformat() if self.maturity_date and self.maturity_date.calendar_date else None,
            "conversion_window_start": self.conversion_window_start.calendar_date.isoformat() if self.conversion_window_start and self.conversion_window_start.calendar_date else None,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "previous_state_record_id": self.previous_state_record_id,
            "principal_amount": self.principal_amount,
            "currency": self.currency,
            "conversion_discount_percent": self.conversion_discount_percent,
        }
        return Fact(
            record_id=record_id,
            schema_version="capital-instrument-lifecycle-v0.1",
            subject_ref=self.instrument_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            supersedes_record_id=supersedes_record_id,
            provenance=self.provenance,
            fact_type="capital_instrument.lifecycle",
            value=value,
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=self.evidence_record_ids,
            period_start=self.provenance.event_time,
            period_end=self.provenance.event_time,
        )
