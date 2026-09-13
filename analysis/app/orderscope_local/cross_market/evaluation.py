"""Deterministic A0-002 metrics and hypothesis ratings.

The evaluator consumes source-neutral SeriesObservation values. It computes
simple bounded-window direction/relative metrics and then rates H1..H5 without
promoting capital movement or short-covering to Fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import fmean
from typing import Iterable

from orderscope_local.contracts import ContractViolation
from .validation import HypothesisRating, HypothesisResult, SeriesMeasure, SeriesObservation, SeriesRole

RULE_VERSION = "a0-002-directional-rules-v0.1"


@dataclass(frozen=True, slots=True)
class A0DerivedMetrics:
    cbrs_return: float
    nvda_return: float
    market_return: float
    semiconductor_return: float
    btc_return: float
    cbrs_relative_return: float
    semiconductor_relative_return: float
    cbrs_volume_ratio: float
    market_volume_ratio: float
    cbrs_relative_volume_ratio: float
    ust10y_change: float
    jgb10y_change: float
    usdjpy_return: float


def evaluate_a0_002(
    *,
    observations: tuple[SeriesObservation, ...],
    baseline_start: date,
    baseline_end: date,
    primary_start: date,
    primary_end: date,
) -> tuple[A0DerivedMetrics, tuple[HypothesisResult, ...]]:
    if baseline_start >= baseline_end or primary_start >= primary_end or baseline_end > primary_start:
        raise ContractViolation("A0-002 evaluation windows must be ordered half-open ranges")
    metrics = _metrics(
        observations=observations,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        primary_start=primary_start,
        primary_end=primary_end,
    )
    return metrics, _rate(metrics)


def _metrics(*, observations, baseline_start, baseline_end, primary_start, primary_end) -> A0DerivedMetrics:
    def values(role: SeriesRole, measure: SeriesMeasure, start: date, end: date) -> list[float]:
        rows = sorted(
            (
                item for item in observations
                if item.role is role and item.measure is measure and start <= item.analysis_date < end
            ),
            key=lambda item: item.analysis_date,
        )
        if not rows:
            raise ContractViolation(f"missing A0-002 observations for {role.value}:{measure.value} in {start}..{end}")
        return [float(item.value) for item in rows]

    def ret(role: SeriesRole) -> float:
        series = values(role, SeriesMeasure.PRICE, primary_start, primary_end)
        if series[0] == 0:
            raise ContractViolation(f"zero starting price for {role.value}")
        return series[-1] / series[0] - 1.0

    def change(role: SeriesRole, measure: SeriesMeasure) -> float:
        series = values(role, measure, primary_start, primary_end)
        return series[-1] - series[0]

    def volume_ratio(role: SeriesRole) -> float:
        baseline = values(role, SeriesMeasure.VOLUME, baseline_start, baseline_end)
        primary = values(role, SeriesMeasure.VOLUME, primary_start, primary_end)
        baseline_mean = fmean(baseline)
        if baseline_mean <= 0:
            raise ContractViolation(f"baseline volume must be positive for {role.value}")
        return fmean(primary) / baseline_mean

    cbrs_return = ret(SeriesRole.CBRS)
    nvda_return = ret(SeriesRole.NVDA)
    market_return = ret(SeriesRole.US_MARKET)
    semiconductor_return = ret(SeriesRole.AI_SEMICONDUCTOR_PROXY)
    btc_return = ret(SeriesRole.BTC)
    cbrs_volume_ratio = volume_ratio(SeriesRole.CBRS)
    market_volume_ratio = volume_ratio(SeriesRole.US_MARKET)
    if market_volume_ratio <= 0:
        raise ContractViolation("market volume ratio must be positive")

    usdjpy = values(SeriesRole.USDJPY, SeriesMeasure.FX_RATE, primary_start, primary_end)
    if usdjpy[0] == 0:
        raise ContractViolation("USDJPY starting value cannot be zero")

    return A0DerivedMetrics(
        cbrs_return=cbrs_return,
        nvda_return=nvda_return,
        market_return=market_return,
        semiconductor_return=semiconductor_return,
        btc_return=btc_return,
        cbrs_relative_return=cbrs_return - market_return,
        semiconductor_relative_return=semiconductor_return - market_return,
        cbrs_volume_ratio=cbrs_volume_ratio,
        market_volume_ratio=market_volume_ratio,
        cbrs_relative_volume_ratio=cbrs_volume_ratio / market_volume_ratio,
        ust10y_change=change(SeriesRole.UST_10Y, SeriesMeasure.YIELD),
        jgb10y_change=change(SeriesRole.JGB_10Y, SeriesMeasure.YIELD),
        usdjpy_return=usdjpy[-1] / usdjpy[0] - 1.0,
    )


def _result(hypothesis_id: str, rating: HypothesisRating, rationale: str, *refs: str) -> HypothesisResult:
    return HypothesisResult(
        hypothesis_id=hypothesis_id,
        rating=rating,
        evidence_refs=tuple(refs) if rating is not HypothesisRating.UNKNOWN else (),
        rationale=rationale,
    )


def _rate(m: A0DerivedMetrics) -> tuple[HypothesisResult, ...]:
    # H1: broad risk relief is supported when the U.S. market is positive while
    # Treasury yield pressure is not rising. BTC is context, not a requirement.
    if m.market_return > 0 and m.ust10y_change <= 0:
        h1 = _result("H1_GLOBAL_MACRO_RELIEF", HypothesisRating.SUPPORT, "US market rose while UST10Y did not rise", "metric:market_return", "metric:ust10y_change")
    elif m.market_return < 0 and m.ust10y_change > 0:
        h1 = _result("H1_GLOBAL_MACRO_RELIEF", HypothesisRating.CONTRADICT, "US market fell while UST10Y rose", "metric:market_return", "metric:ust10y_change")
    else:
        h1 = _result("H1_GLOBAL_MACRO_RELIEF", HypothesisRating.PARTIAL, "macro signals are mixed", "metric:market_return", "metric:ust10y_change", "metric:btc_return")

    # H2: AI/theme flow requires both the semiconductor proxy and NVDA to beat
    # the broader U.S. market for full support.
    nvda_relative = m.nvda_return - m.market_return
    if m.semiconductor_relative_return > 0 and nvda_relative > 0:
        h2 = _result("H2_AI_THEME_FLOW", HypothesisRating.SUPPORT, "SOXX and NVDA both outperformed the U.S. market proxy", "metric:semiconductor_relative_return", "metric:nvda_relative_return")
    elif m.semiconductor_relative_return < 0 and nvda_relative < 0:
        h2 = _result("H2_AI_THEME_FLOW", HypothesisRating.CONTRADICT, "SOXX and NVDA both underperformed the U.S. market proxy", "metric:semiconductor_relative_return", "metric:nvda_relative_return")
    else:
        h2 = _result("H2_AI_THEME_FLOW", HypothesisRating.PARTIAL, "AI/theme signals are mixed", "metric:semiconductor_relative_return", "metric:nvda_relative_return")

    # H3: company-specific repricing needs both relative price strength and
    # relative volume expansion for full support.
    if m.cbrs_relative_return > 0 and m.cbrs_relative_volume_ratio > 1:
        h3 = _result("H3_CBRS_SPECIFIC_REPRICING", HypothesisRating.SUPPORT, "CBRS outperformed QQQ with relative volume expansion", "metric:cbrs_relative_return", "metric:cbrs_relative_volume_ratio")
    elif m.cbrs_relative_return <= 0 and m.cbrs_relative_volume_ratio <= 1:
        h3 = _result("H3_CBRS_SPECIFIC_REPRICING", HypothesisRating.CONTRADICT, "CBRS lacked both relative return and relative volume support", "metric:cbrs_relative_return", "metric:cbrs_relative_volume_ratio")
    else:
        h3 = _result("H3_CBRS_SPECIFIC_REPRICING", HypothesisRating.PARTIAL, "CBRS price and volume evidence are mixed", "metric:cbrs_relative_return", "metric:cbrs_relative_volume_ratio")

    # H4 intentionally stays UNKNOWN until a reviewed short/borrow series is
    # available. Price/volume alone must not be relabeled as short covering.
    h4 = _result("H4_SHORT_COVERING", HypothesisRating.UNKNOWN, "No reviewed CBRS short/borrow series is available in A0-002 v0.1")

    # H5: falling USDJPY directly contradicts the simple Japan->US new-capital
    # flow story. Rising USDJPY plus a rising U.S. market is only PARTIAL because
    # FX cannot prove capital movement by itself.
    if m.usdjpy_return < 0:
        h5 = _result("H5_JAPAN_TO_US_ROTATION", HypothesisRating.CONTRADICT, "USDJPY fell, opposite the simple JPY-sale/USD-buy direction", "metric:usdjpy_return", "metric:jgb10y_change", "metric:market_return")
    elif m.usdjpy_return > 0 and m.market_return > 0:
        h5 = _result("H5_JAPAN_TO_US_ROTATION", HypothesisRating.PARTIAL, "USDJPY and U.S. market direction are consistent, but FX alone cannot establish capital flow", "metric:usdjpy_return", "metric:jgb10y_change", "metric:market_return")
    else:
        h5 = _result("H5_JAPAN_TO_US_ROTATION", HypothesisRating.PARTIAL, "Japan-to-US rotation evidence is mixed", "metric:usdjpy_return", "metric:jgb10y_change", "metric:market_return")

    return (h1, h2, h3, h4, h5)
