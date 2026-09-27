from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts.capital_instrument import CapitalInstrumentLifecycleFact
from orderscope_local.contracts.capital_instrument_state import CapitalInstrumentKind, CapitalInstrumentState
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.provenance import ContentHash, Provenance, SourceReference, SourceTimestamp

UTC = timezone.utc


def _p() -> Provenance:
    now = datetime(2026, 9, 9, 13, 0, tzinfo=UTC)
    return Provenance(
        source_ref=SourceReference("sec:tnon:8-k:2026-09-09"),
        content_hash=ContentHash("a" * 64),
        retrieved_at=now,
        available_at=now,
        accepted_at=now,
        event_time=SourceTimestamp.date_only(date(2026, 9, 9)),
    )


def test_materializes_lifecycle_fact() -> None:
    p = _p()
    item = CapitalInstrumentLifecycleFact(
        instrument_ref="instrument:tnon:note",
        issuer_ref="issuer:TNON",
        instrument_kind=CapitalInstrumentKind.SENIOR_CONVERTIBLE_NOTE,
        state=CapitalInstrumentState.FULLY_REPAID,
        provenance=p,
        accepted_at=p.accepted_at,
        evidence_record_ids=("evidence:tnon:repayment",),
        maturity_date=SourceTimestamp.date_only(date(2026, 9, 11)),
        previous_state=CapitalInstrumentState.ACTIVE,
        previous_state_record_id="fact:tnon:note:active",
        principal_amount=5160000.0,
        currency="USD",
    )
    fact = item.to_fact(record_id="fact:tnon:note:repaid")
    assert fact.fact_type == "capital_instrument.lifecycle"
    assert fact.value["state"] == "fully_repaid"


def test_invalid_transition_fails_closed() -> None:
    p = _p()
    with pytest.raises(ContractViolation, match="transition is not allowed"):
        CapitalInstrumentLifecycleFact(
            instrument_ref="instrument:tnon:note",
            issuer_ref="issuer:TNON",
            instrument_kind=CapitalInstrumentKind.SENIOR_CONVERTIBLE_NOTE,
            state=CapitalInstrumentState.ACTIVE,
            provenance=p,
            accepted_at=p.accepted_at,
            evidence_record_ids=("evidence:tnon:bad",),
            previous_state=CapitalInstrumentState.FULLY_REPAID,
            previous_state_record_id="fact:tnon:note:repaid",
        )
