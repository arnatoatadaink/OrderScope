from __future__ import annotations

from datetime import date, datetime, timezone

from orderscope_local.cross_market.evaluation import evaluate_a0_002
from orderscope_local.cross_market.validation import HypothesisRating, SeriesMeasure, SeriesObservation, SeriesRole

UTC = timezone.utc


def obs(role, measure, day, value):
    t = datetime(day.year, day.month, day.day, 23, 0, tzinfo=UTC)
    return SeriesObservation(role=role, measure=measure, analysis_date=day, observed_at=t, available_at=t, value=value, source_ref=f"source:{role.value}:{measure.value}")


def fixture():
    b0, b1 = date(2026, 8, 26), date(2026, 8, 31)
    p0, p1 = date(2026, 9, 1), date(2026, 9, 4)
    rows = []
    for day, cbrs, cvol, qqq, qvol, nvda, soxx, btc, ust, jgb, fx in (
        (b0, 10, 100, 100, 1000, 100, 100, 1000, 4.0, 1.0, 160),
        (b1, 10, 100, 100, 1000, 100, 100, 1000, 4.0, 1.0, 160),
        (p0, 10, 200, 100, 1000, 100, 100, 1000, 4.0, 1.0, 160),
        (p1, 12, 220, 105, 1100, 108, 110, 1050, 3.9, 1.1, 156),
    ):
        rows += [
            obs(SeriesRole.CBRS, SeriesMeasure.PRICE, day, cbrs),
            obs(SeriesRole.CBRS, SeriesMeasure.VOLUME, day, cvol),
            obs(SeriesRole.US_MARKET, SeriesMeasure.PRICE, day, qqq),
            obs(SeriesRole.US_MARKET, SeriesMeasure.VOLUME, day, qvol),
            obs(SeriesRole.NVDA, SeriesMeasure.PRICE, day, nvda),
            obs(SeriesRole.AI_SEMICONDUCTOR_PROXY, SeriesMeasure.PRICE, day, soxx),
            obs(SeriesRole.BTC, SeriesMeasure.PRICE, day, btc),
            obs(SeriesRole.UST_10Y, SeriesMeasure.YIELD, day, ust),
            obs(SeriesRole.JGB_10Y, SeriesMeasure.YIELD, day, jgb),
            obs(SeriesRole.USDJPY, SeriesMeasure.FX_RATE, day, fx),
        ]
    return tuple(rows)


def test_computes_relative_metrics_and_hypotheses():
    metrics, results = evaluate_a0_002(
        observations=fixture(),
        baseline_start=date(2026, 8, 26),
        baseline_end=date(2026, 9, 1),
        primary_start=date(2026, 9, 1),
        primary_end=date(2026, 9, 5),
    )
    assert round(metrics.cbrs_relative_return, 6) == 0.15
    assert metrics.cbrs_relative_volume_ratio > 1
    by_id = {item.hypothesis_id: item for item in results}
    assert by_id["H1_GLOBAL_MACRO_RELIEF"].rating is HypothesisRating.SUPPORT
    assert by_id["H2_AI_THEME_FLOW"].rating is HypothesisRating.SUPPORT
    assert by_id["H3_CBRS_SPECIFIC_REPRICING"].rating is HypothesisRating.SUPPORT
    assert by_id["H4_SHORT_COVERING"].rating is HypothesisRating.UNKNOWN
    assert by_id["H5_JAPAN_TO_US_ROTATION"].rating is HypothesisRating.CONTRADICT


def test_h5_is_only_partial_when_fx_direction_supports_simple_story():
    rows = list(fixture())
    rows = [
        SeriesObservation(
            role=row.role,
            measure=row.measure,
            analysis_date=row.analysis_date,
            observed_at=row.observed_at,
            available_at=row.available_at,
            value=(165 if row.role is SeriesRole.USDJPY and row.analysis_date == date(2026, 9, 4) else row.value),
            source_ref=row.source_ref,
        )
        for row in rows
    ]
    _, results = evaluate_a0_002(
        observations=tuple(rows),
        baseline_start=date(2026, 8, 26),
        baseline_end=date(2026, 9, 1),
        primary_start=date(2026, 9, 1),
        primary_end=date(2026, 9, 5),
    )
    h5 = next(item for item in results if item.hypothesis_id == "H5_JAPAN_TO_US_ROTATION")
    assert h5.rating is HypothesisRating.PARTIAL
