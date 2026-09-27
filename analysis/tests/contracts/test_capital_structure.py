from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.capital_instrument_state import CapitalInstrumentKind, CapitalInstrumentState
from orderscope_local.contracts.capital_structure import (
    CapitalStructureAssessment,
    CapitalStructureInterpretationType,
    ResidualDilutionState,
)

UTC = timezone.utc
NOW = datetime(2026, 9, 9, 14, 0, tzinfo=UTC)


def assessment(**overrides):
    values = dict(
        interpretation_type=CapitalStructureInterpretationType.CONVERTIBLE_NOTE_OVERHANG_REMOVED,
        subject_ref="issuer:TNON",
        instrument_ref="instrument:TNON:2026-convertible-note",
        instrument_kind=CapitalInstrumentKind.CONVERTIBLE_NOTE,
        terminal_state=CapitalInstrumentState.FULLY_REPAID,
        residual_dilution_state=ResidualDilutionState.REMAINS,
        instrument_fact_record_ids=("fact:note:full-repayment",),
        resolution_evidence_record_ids=("evidence:sec:repayment",),
        residual_instrument_record_ids=("fact:warrant:series-a",),
        generated_at=NOW,
    )
    values.update(overrides)
    return CapitalStructureAssessment(**values)


def test_tnon_style_overhang_removal_keeps_residual_warrant_exposure() -> None:
    item = assessment()
    record = item.to_interpretation(record_id="interpretation:TNON:overhang", accepted_at=NOW)
    assert record.statement["residual_dilution_state"] == "remains"
    assert record.statement["all_dilution_removed"] is False
    assert "fact:warrant:series-a" in record.basis_record_ids


def test_overhang_removal_requires_terminal_instrument_state() -> None:
    with pytest.raises(ContractViolation, match="terminal instrument state"):
        assessment(terminal_state=CapitalInstrumentState.ACTIVE)


def test_residual_dilution_requires_residual_instrument_lineage() -> None:
    with pytest.raises(ContractViolation, match="residual instrument lineage"):
        assessment(residual_instrument_record_ids=())


def test_assessment_is_limited_to_convertible_note_overhang() -> None:
    with pytest.raises(ContractViolation, match="convertible-note overhang"):
        assessment(instrument_kind=CapitalInstrumentKind.WARRANT)
