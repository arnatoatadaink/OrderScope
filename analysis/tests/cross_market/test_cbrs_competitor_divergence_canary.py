from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import (
    ContractViolation,
    MarketReactionAssessment,
    MarketReactionConfidence,
    MarketReactionInterpretationType,
    RepricingState,
    RepricingStateAssessment,
    is_allowed_repricing_transition,
)
from orderscope_local.cross_market import SeriesMeasure, SeriesObservation, SeriesRole
from orderscope_local.cross_market.relative_repricing import evaluate_relative_repricing


UTC = timezone.utc
GENERATED = datetime(2026, 9, 5, 1, tzinfo=UTC)


def _observation(role: SeriesRole, measure: SeriesMeasure, day: int, value: float) -> SeriesObservation:
    return SeriesObservation(
        role=role,
        measure=measure,
        analysis_date=date(2026, 8 if day <= 31 else 9, day if day <= 31 else day - 31),
        observed_at=datetime(2026, 8 if day <= 31 else 9, day if day <= 31 else day - 31, 20, tzinfo=UTC),
        available_at=datetime(2026, 8 if day <= 31 else 9, day if day <= 31 else day - 31, 21, tzinfo=UTC),
        value=value,
        source_ref=f"fixture:{role.value}:{measure.value}:{day}",
    )


def _fixture_observations() -> tuple[SeriesObservation, ...]:
    rows: list[SeriesObservation] = []
    prices = {
        SeriesRole.CBRS: (100.0, 76.0, 78.0, 104.0),
        SeriesRole.NVDA: (100.0, 108.0, 109.0, 112.0),
        SeriesRole.US_MARKET: (100.0, 96.0, 97.0, 99.0),
        SeriesRole.AI_SEMICONDUCTOR_PROXY: (100.0, 101.0, 102.0, 106.0),
    }
    volumes = {
        SeriesRole.CBRS: (100.0, 110.0, 180.0, 210.0),
        SeriesRole.NVDA: (100.0, 105.0, 115.0, 120.0),
        SeriesRole.US_MARKET: (100.0, 100.0, 110.0, 115.0),
        SeriesRole.AI_SEMICONDUCTOR_PROXY: (100.0, 105.0, 120.0, 125.0),
    }
    days = (26, 31, 32, 35)  # 2026-08-26, 08-31, 09-01, 09-04
    for role in prices:
        for day, value in zip(days, prices[role], strict=True):
            rows.append(_observation(role, SeriesMeasure.PRICE, day, value))
        for day, value in zip(days, volumes[role], strict=True):
            rows.append(_observation(role, SeriesMeasure.VOLUME, day, value))
    return tuple(rows)


def test_cbrs_canary_reproduces_competitor_divergence_and_relative_recovery() -> None:
    metrics = evaluate_relative_repricing(
        observations=_fixture_observations(),
        pre_start=date(2026, 8, 26),
        pivot_date=date(2026, 9, 1),
        post_end=date(2026, 9, 5),
    )

    assert metrics.target_relative_pre_vs_market < 0
    assert metrics.target_relative_pre_vs_sector < 0
    assert metrics.target_relative_pre_vs_leader < 0
    assert metrics.target_relative_recovery_vs_market > 0
    assert metrics.target_relative_recovery_vs_sector > 0
    assert metrics.target_relative_recovery_vs_leader > 0
    assert metrics.relative_volume_participation > 1


def test_cbrs_canary_allows_latent_catalyst_interpretation_only_with_independent_inputs() -> None:
    assessment = MarketReactionAssessment(
        interpretation_type=MarketReactionInterpretationType.LATENT_POSITIVE_CATALYST,
        subject_ref="instrument:CBRS",
        observed_window_start=datetime(2026, 9, 1, tzinfo=UTC),
        observed_window_end=datetime(2026, 9, 5, tzinfo=UTC),
        company_positive_evidence_refs=("evidence:cbrs-positive-catalyst",),
        macro_pressure_evidence_refs=("evidence:macro-rate-pressure",),
        relative_repricing_metric_refs=("metric:cbrs-relative-repricing",),
        confidence=MarketReactionConfidence.MEDIUM,
        generated_at=GENERATED,
    )

    interpretation = assessment.to_interpretation(
        record_id="interpretation:cbrs-latent-catalyst",
        accepted_at=GENERATED,
    )
    assert interpretation.interpretation_type == "latent_positive_catalyst"
    assert set(interpretation.basis_record_ids) == {
        "evidence:cbrs-positive-catalyst",
        "evidence:macro-rate-pressure",
        "metric:cbrs-relative-repricing",
    }

    with pytest.raises(ContractViolation, match="company_positive_evidence_refs"):
        MarketReactionAssessment(
            interpretation_type=MarketReactionInterpretationType.LATENT_POSITIVE_CATALYST,
            subject_ref="instrument:CBRS",
            observed_window_start=datetime(2026, 9, 1, tzinfo=UTC),
            observed_window_end=datetime(2026, 9, 5, tzinfo=UTC),
            company_positive_evidence_refs=(),
            macro_pressure_evidence_refs=("evidence:macro-rate-pressure",),
            relative_repricing_metric_refs=("metric:cbrs-relative-repricing",),
            confidence=MarketReactionConfidence.LOW,
            generated_at=GENERATED,
        )


def test_cbrs_canary_state_path_requires_local_equilibrium_before_confirmed_rediscovery() -> None:
    assert is_allowed_repricing_transition(
        RepricingState.RELATIVE_OVERSHOOT,
        RepricingState.RELATIVE_MEAN_REVERSION,
    )
    assert is_allowed_repricing_transition(
        RepricingState.RELATIVE_MEAN_REVERSION,
        RepricingState.REPRICING_OVERSHOOT,
    )
    assert is_allowed_repricing_transition(
        RepricingState.REPRICING_OVERSHOOT,
        RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
    )
    assert not is_allowed_repricing_transition(
        RepricingState.RELATIVE_MEAN_REVERSION,
        RepricingState.PRICE_REDISCOVERY_CONFIRMED,
    )

    local_equilibrium = RepricingStateAssessment(
        state=RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
        subject_ref="instrument:CBRS",
        observed_window_start=datetime(2026, 9, 1, tzinfo=UTC),
        observed_window_end=datetime(2026, 9, 5, tzinfo=UTC),
        metric_record_ids=("metric:cbrs-relative-repricing",),
        previous_state_record_id="interpretation:cbrs-repricing-overshoot",
        previous_state=RepricingState.REPRICING_OVERSHOOT,
        generated_at=GENERATED,
    )
    interpretation = local_equilibrium.to_interpretation(
        record_id="interpretation:cbrs-local-equilibrium",
        accepted_at=GENERATED,
    )
    assert interpretation.statement["state"] == "local_equilibrium_candidate"

    with pytest.raises(ContractViolation, match="catalyst and persistence lineage"):
        RepricingStateAssessment(
            state=RepricingState.PRICE_REDISCOVERY_CONFIRMED,
            subject_ref="instrument:CBRS",
            observed_window_start=datetime(2026, 9, 1, tzinfo=UTC),
            observed_window_end=datetime(2026, 9, 5, tzinfo=UTC),
            metric_record_ids=("metric:cbrs-relative-repricing",),
            previous_state_record_id="interpretation:cbrs-local-equilibrium",
            previous_state=RepricingState.LOCAL_EQUILIBRIUM_CANDIDATE,
            generated_at=GENERATED,
        )
