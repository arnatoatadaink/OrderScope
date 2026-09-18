from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.market_reaction import (
    MarketReactionAssessment,
    MarketReactionConfidence,
    MarketReactionInterpretationType,
)


START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 5, tzinfo=timezone.utc)
GENERATED = datetime(2026, 9, 5, 1, tzinfo=timezone.utc)
ACCEPTED = datetime(2026, 9, 5, 2, tzinfo=timezone.utc)


def assessment(**overrides) -> MarketReactionAssessment:
    values = dict(
        interpretation_type=MarketReactionInterpretationType.LATENT_POSITIVE_CATALYST,
        subject_ref="instrument:CBRS",
        observed_window_start=START,
        observed_window_end=END,
        company_positive_evidence_refs=("evidence:cbrs-positive-news",),
        macro_pressure_evidence_refs=("evidence:rate-pressure", "evidence:qqq-selloff"),
        relative_repricing_metric_refs=("metric:cbrs-relative-recovery",),
        confidence=MarketReactionConfidence.MEDIUM,
        generated_at=GENERATED,
    )
    values.update(overrides)
    return MarketReactionAssessment(**values)


def test_requires_independent_company_macro_and_repricing_evidence() -> None:
    item = assessment()
    assert item.basis_record_ids == (
        "evidence:cbrs-positive-news",
        "evidence:rate-pressure",
        "evidence:qqq-selloff",
        "metric:cbrs-relative-recovery",
    )


@pytest.mark.parametrize(
    "field",
    [
        "company_positive_evidence_refs",
        "macro_pressure_evidence_refs",
        "relative_repricing_metric_refs",
    ],
)
def test_rejects_missing_required_evidence_class(field: str) -> None:
    with pytest.raises(ContractViolation, match=field):
        assessment(**{field: ()})


def test_rejects_same_reference_reused_across_evidence_classes() -> None:
    with pytest.raises(ContractViolation, match="independent evidence classes"):
        assessment(
            company_positive_evidence_refs=("evidence:same",),
            macro_pressure_evidence_refs=("evidence:same",),
        )


def test_materializes_only_as_fact_store_interpretation() -> None:
    record = assessment().to_interpretation(record_id="interp:cbrs:latent:1", accepted_at=ACCEPTED)
    assert record.interpretation_type == "latent_positive_catalyst"
    assert record.method == "market_reaction_rule"
    assert record.statement["company_positive_evidence_count"] == 1
    assert record.statement["macro_pressure_evidence_count"] == 2
    assert record.statement["relative_repricing_metric_count"] == 1
    assert "buyer" not in record.statement
    assert "capital_flow" not in record.statement


def test_macro_pressure_dominant_uses_same_multi_evidence_boundary() -> None:
    record = assessment(
        interpretation_type=MarketReactionInterpretationType.MACRO_PRESSURE_DOMINANT,
        confidence=MarketReactionConfidence.LOW,
    ).to_interpretation(record_id="interp:cbrs:macro:1", accepted_at=ACCEPTED)
    assert record.interpretation_type == "macro_pressure_dominant"
    assert record.statement["confidence"] == "LOW"


def test_rejects_acceptance_before_generation() -> None:
    with pytest.raises(ContractViolation, match="accepted_at cannot precede"):
        assessment().to_interpretation(
            record_id="interp:cbrs:latent:2",
            accepted_at=END,
        )
