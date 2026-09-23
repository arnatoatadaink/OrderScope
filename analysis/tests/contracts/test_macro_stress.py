from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import (
    ContractViolation,
    MacroStressAssessment,
    MacroStressInterpretationType,
    MacroStressRating,
)


START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 4, tzinfo=timezone.utc)
GENERATED = datetime(2026, 9, 4, 1, tzinfo=timezone.utc)


def assessment(**overrides):
    values = {
        "interpretation_type": MacroStressInterpretationType.CARRY_UNWIND_CANDIDATE,
        "rating": MacroStressRating.SUPPORT,
        "subject_ref": "macro:jp-us",
        "observed_window_start": START,
        "observed_window_end": END,
        "macro_metric_refs": ("derived:us_jp_2y_spread:t1", "derived:usdjpy_velocity:t1"),
        "market_stress_metric_refs": ("derived:market_breadth:t1",),
        "explicit_source_evidence_refs": (),
        "contradicting_evidence_refs": (),
        "generated_at": GENERATED,
    }
    values.update(overrides)
    return MacroStressAssessment(**values)


def test_carry_unwind_requires_independent_macro_and_market_stress_signals() -> None:
    value = assessment()
    interpretation = value.to_interpretation(
        record_id="interpretation:carry-unwind:20260904",
        accepted_at=GENERATED,
    )

    assert interpretation.interpretation_type == "carry_unwind_candidate"
    assert interpretation.statement["rating"] == "SUPPORT"
    assert interpretation.basis_record_ids == (
        "derived:us_jp_2y_spread:t1",
        "derived:usdjpy_velocity:t1",
        "derived:market_breadth:t1",
    )


def test_single_fx_or_single_news_signal_cannot_establish_carry_unwind() -> None:
    with pytest.raises(ContractViolation, match="at least two independent"):
        assessment(
            macro_metric_refs=("derived:usdjpy_velocity:t1",),
            market_stress_metric_refs=(),
        )

    with pytest.raises(ContractViolation, match="at least two independent"):
        assessment(
            macro_metric_refs=(),
            market_stress_metric_refs=(),
            explicit_source_evidence_refs=("evidence:news:carry-comment",),
        )


def test_deleveraging_also_requires_macro_and_market_stress_classes() -> None:
    with pytest.raises(ContractViolation, match="both macro and market-stress"):
        assessment(
            interpretation_type=MacroStressInterpretationType.DELEVERAGING_REGIME,
            macro_metric_refs=("derived:rate-shock:t1",),
            market_stress_metric_refs=(),
            explicit_source_evidence_refs=("evidence:position-reduction:t1",),
        )


def test_contradict_and_unknown_have_explicit_fail_closed_rules() -> None:
    contradicted = assessment(
        rating=MacroStressRating.CONTRADICT,
        macro_metric_refs=(),
        market_stress_metric_refs=(),
        contradicting_evidence_refs=("derived:market-recovery:t1",),
    )
    assert contradicted.rating is MacroStressRating.CONTRADICT

    unknown = assessment(
        rating=MacroStressRating.UNKNOWN,
        macro_metric_refs=(),
        market_stress_metric_refs=(),
    )
    with pytest.raises(ContractViolation, match="requires evidence lineage"):
        unknown.to_interpretation(
            record_id="interpretation:unknown:20260904",
            accepted_at=GENERATED,
        )


def test_evidence_classes_cannot_reuse_same_record() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse"):
        assessment(
            macro_metric_refs=("derived:same:t1",),
            market_stress_metric_refs=("derived:same:t1",),
        )
