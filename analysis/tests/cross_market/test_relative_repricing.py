from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.cross_market.relative_repricing import evaluate_relative_repricing
from orderscope_local.cross_market.validation import SeriesMeasure, SeriesObservation, SeriesRole


UTC = timezone.utc


def _obs(role: SeriesRole, measure: SeriesMeasure, day: int, value: float) -> SeriesObservation:
    timestamp = datetime(2026, 9, day, 21, 0, tzinfo=UTC)
    return SeriesObservation(
        role=role,
        measure=measure,
        analysis_date=date(2026, 9, day),
        observed_at=timestamp,
        available_at=timestamp,
        value=value,
        source_ref=f"fixture:{role.value}:{measure.value}:{day}",
    )


def _fixture() -> tuple[SeriesObservation, ...]:
    rows: list[SeriesObservation] = []
    prices = {
        SeriesRole.CBRS: (100.0, 80.0, 82.0, 104.0),
        SeriesRole.US_MARKET: (100.0, 95.0, 96.0, 99.0),
        SeriesRole.AI_SEMICONDUCTOR_PROXY: (100.0, 94.0, 95.0, 101.0),
        SeriesRole.NVDA: (100.0, 105.0, 106.0, 112.0),
    }
    volumes = {
        SeriesRole.CBRS: (100.0, 100.0, 180.0, 220.0),
        SeriesRole.US_MARKET: (100.0, 100.0, 120.0, 130.0),
        SeriesRole.AI_SEMICONDUCTOR_PROXY: (100.0, 100.0, 130.0, 140.0),
        SeriesRole.NVDA: (100.0, 100.0, 140.0, 150.0),
    }
    for role, values in prices.items():
        for day, value in zip((1, 2, 3, 4), values, strict=True):
            rows.append(_obs(role, SeriesMeasure.PRICE, day, value))
    for role, values in volumes.items():
        for day, value in zip((1, 2, 3, 4), values, strict=True):
            rows.append(_obs(role, SeriesMeasure.VOLUME, day, value))
    return tuple(rows)


def test_relative_repricing_separates_pre_divergence_and_recovery() -> None:
    metrics = evaluate_relative_repricing(
        observations=_fixture(),
        pre_start=date(2026, 9, 1),
        pivot_date=date(2026, 9, 3),
        post_end=date(2026, 9, 5),
    )

    assert metrics.target_pre_return == pytest.approx(-0.20)
    assert metrics.target_relative_pre_vs_market == pytest.approx(-0.15)
    assert metrics.target_relative_pre_vs_leader == pytest.approx(-0.25)
    assert metrics.target_recovery_return == pytest.approx(104.0 / 80.0 - 1.0)
    assert metrics.target_relative_recovery_vs_market > 0
    assert metrics.target_relative_recovery_vs_sector > 0
    assert metrics.relative_volume_participation > 1


def test_metrics_do_not_emit_a_causal_or_state_label() -> None:
    metrics = evaluate_relative_repricing(
        observations=_fixture(),
        pre_start=date(2026, 9, 1),
        pivot_date=date(2026, 9, 3),
        post_end=date(2026, 9, 5),
    )

    assert not hasattr(metrics, "cause")
    assert not hasattr(metrics, "state")
    assert not hasattr(metrics, "institutional_flow")


def test_windows_must_be_ordered() -> None:
    with pytest.raises(ContractViolation, match="pre_start < pivot_date < post_end"):
        evaluate_relative_repricing(
            observations=_fixture(),
            pre_start=date(2026, 9, 3),
            pivot_date=date(2026, 9, 3),
            post_end=date(2026, 9, 5),
        )


def test_missing_required_price_or_volume_fails_closed() -> None:
    observations = tuple(
        row for row in _fixture()
        if not (row.role is SeriesRole.CBRS and row.measure is SeriesMeasure.VOLUME)
    )
    with pytest.raises(ContractViolation, match="missing relative repricing observations"):
        evaluate_relative_repricing(
            observations=observations,
            pre_start=date(2026, 9, 1),
            pivot_date=date(2026, 9, 3),
            post_end=date(2026, 9, 5),
        )
