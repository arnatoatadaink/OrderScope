from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.cross_market import (
    CrossMarketHypothesis,
    FxDirectionConsistency,
    HypothesisConfidence,
    ProposedFlowDirection,
)
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import Interpretation


START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 5, tzinfo=timezone.utc)
GENERATED = datetime(2026, 9, 5, 1, tzinfo=timezone.utc)


def _hypothesis(**overrides: object) -> CrossMarketHypothesis:
    values: dict[str, object] = {
        "hypothesis_type": "japan_to_us_capital_rotation",
        "source_region": "JP",
        "destination_region": "US",
        "proposed_direction": ProposedFlowDirection.SOURCE_TO_DESTINATION,
        "observed_window_start": START,
        "observed_window_end": END,
        "supporting_evidence_refs": ("evidence.market.us", "evidence.yield.us"),
        "contradicting_evidence_refs": ("evidence.fx.usdjpy",),
        "fx_direction_consistency": FxDirectionConsistency.CONTRADICT,
        "confidence": HypothesisConfidence.LOW,
        "generated_at": GENERATED,
        "model_or_rule_version": "a0-001-v0.1",
    }
    values.update(overrides)
    return CrossMarketHypothesis(**values)  # type: ignore[arg-type]


def test_materializes_only_as_interpretation() -> None:
    record = _hypothesis().to_interpretation(
        record_id="interpretation.a0.h5.1",
        subject_ref="theme.cross-market",
        accepted_at=datetime(2026, 9, 5, 2, tzinfo=timezone.utc),
    )
    assert isinstance(record, Interpretation)
    assert record.interpretation_type == "cross_market_capital_movement_hypothesis"
    assert record.statement["fx_direction_consistency"] == "CONTRADICT"
    assert record.statement["confidence"] == "LOW"
    assert record.basis_record_ids == (
        "evidence.market.us",
        "evidence.yield.us",
        "evidence.fx.usdjpy",
    )


def test_fx_contradiction_blocks_high_confidence() -> None:
    with pytest.raises(ContractViolation, match="blocks HIGH"):
        _hypothesis(confidence=HypothesisConfidence.HIGH)


def test_missing_evidence_requires_unknown_confidence() -> None:
    with pytest.raises(ContractViolation, match="UNKNOWN"):
        _hypothesis(
            supporting_evidence_refs=(),
            contradicting_evidence_refs=(),
            fx_direction_consistency=FxDirectionConsistency.UNKNOWN,
            confidence=HypothesisConfidence.LOW,
        )


def test_unknown_confidence_is_valid_when_context_missing() -> None:
    hypothesis = _hypothesis(
        supporting_evidence_refs=(),
        contradicting_evidence_refs=(),
        fx_direction_consistency=FxDirectionConsistency.UNKNOWN,
        confidence=HypothesisConfidence.UNKNOWN,
    )
    assert hypothesis.basis_record_ids == ()


def test_evidence_cannot_be_both_support_and_contradiction() -> None:
    with pytest.raises(ContractViolation, match="both support and contradict"):
        _hypothesis(
            supporting_evidence_refs=("evidence.fx.usdjpy",),
            contradicting_evidence_refs=("evidence.fx.usdjpy",),
        )


def test_window_is_half_open_and_ordered() -> None:
    with pytest.raises(ContractViolation, match="half-open"):
        _hypothesis(observed_window_end=START)


def test_generated_at_cannot_precede_window_end() -> None:
    with pytest.raises(ContractViolation, match="generated_at"):
        _hypothesis(generated_at=datetime(2026, 9, 4, tzinfo=timezone.utc))


def test_acceptance_cannot_predate_generation() -> None:
    with pytest.raises(ContractViolation, match="accepted_at"):
        _hypothesis().to_interpretation(
            record_id="interpretation.a0.h5.2",
            subject_ref="theme.cross-market",
            accepted_at=datetime(2026, 9, 5, 0, 30, tzinfo=timezone.utc),
        )
