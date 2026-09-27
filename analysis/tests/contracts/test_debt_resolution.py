from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.capital_instrument_state import CapitalInstrumentState
from orderscope_local.contracts.debt_resolution import (
    DebtResolutionAttentionLevel,
    DebtResolutionWindowAssessment,
)

UTC = timezone.utc


def _base(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "subject_ref": "issuer:TNON",
        "instrument_ref": "instrument:TNON:convertible-note-2026-03",
        "current_state": CapitalInstrumentState.CONVERSION_WINDOW_OPEN,
        "attention_level": DebtResolutionAttentionLevel.WATCH,
        "observed_window_start": datetime(2026, 8, 31, 0, 0, tzinfo=UTC),
        "observed_window_end": datetime(2026, 9, 9, 12, 0, tzinfo=UTC),
        "instrument_fact_record_ids": ("fact:instrument",),
        "timing_metric_record_ids": ("metric:maturity-distance", "metric:conversion-distance"),
        "financing_fact_record_ids": (),
        "repayment_use_evidence_record_ids": (),
        "generated_at": datetime(2026, 9, 9, 12, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return values


def test_watch_requires_instrument_and_timing_but_does_not_predict_outcome() -> None:
    assessment = DebtResolutionWindowAssessment(**_base())
    interpretation = assessment.to_interpretation(
        record_id="interpretation:tnon:resolution-window",
        accepted_at=datetime(2026, 9, 9, 12, 2, tzinfo=UTC),
    )
    assert interpretation.statement["attention_level"] == "watch"
    assert interpretation.statement["outcome_prediction"] == "none"


def test_elevated_requires_financing_and_explicit_repayment_use_evidence() -> None:
    assessment = DebtResolutionWindowAssessment(
        **_base(
            attention_level=DebtResolutionAttentionLevel.ELEVATED,
            financing_fact_record_ids=("fact:financing-closed",),
            repayment_use_evidence_record_ids=("evidence:use-of-proceeds-debt-repayment",),
        )
    )
    assert assessment.attention_level is DebtResolutionAttentionLevel.ELEVATED

    with pytest.raises(ContractViolation, match="financing and explicit repayment-use evidence"):
        DebtResolutionWindowAssessment(
            **_base(attention_level=DebtResolutionAttentionLevel.ELEVATED)
        )


def test_terminal_instrument_cannot_enter_resolution_window() -> None:
    with pytest.raises(ContractViolation, match="resolved capital instrument"):
        DebtResolutionWindowAssessment(
            **_base(current_state=CapitalInstrumentState.FULLY_REPAID)
        )


def test_resolution_evidence_classes_cannot_reuse_record_ids() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse"):
        DebtResolutionWindowAssessment(
            **_base(financing_fact_record_ids=("metric:maturity-distance",))
        )
