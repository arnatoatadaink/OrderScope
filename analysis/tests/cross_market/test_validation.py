from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.cross_market import (
    A0ValidationCase,
    A0ValidationWindows,
    HypothesisRating,
    HypothesisResult,
    SeriesObservation,
    SeriesRole,
    SeriesSpec,
    aligned_timeline,
)

UTC = timezone.utc


def _windows() -> A0ValidationWindows:
    return A0ValidationWindows(
        baseline_start=datetime(2026, 8, 26, tzinfo=UTC),
        baseline_end=datetime(2026, 9, 1, tzinfo=UTC),
        primary_start=datetime(2026, 9, 1, tzinfo=UTC),
        primary_end=datetime(2026, 9, 5, tzinfo=UTC),
    )


def _series() -> tuple[SeriesSpec, ...]:
    return tuple(
        SeriesSpec(
            role=role,
            series_id=role.value.lower(),
            source_ref=f"source:{role.value.lower()}",
            unit="index" if role not in {SeriesRole.UST_10Y, SeriesRole.JGB_10Y, SeriesRole.USDJPY} else "percent",
            timezone="UTC",
        )
        for role in SeriesRole
    )


def _hypotheses() -> tuple[HypothesisResult, ...]:
    ids = (
        "H1_GLOBAL_MACRO_RELIEF",
        "H2_AI_THEME_FLOW",
        "H3_CBRS_SPECIFIC_REPRICING",
        "H4_SHORT_COVERING",
        "H5_JAPAN_TO_US_ROTATION",
    )
    return tuple(
        HypothesisResult(
            hypothesis_id=hypothesis_id,
            rating=HypothesisRating.PARTIAL,
            evidence_refs=(f"evidence:{hypothesis_id.lower()}",),
            rationale="fixture evidence is incomplete but directionally informative",
        )
        for hypothesis_id in ids
    )


def _case() -> A0ValidationCase:
    return A0ValidationCase(windows=_windows(), series=_series(), hypotheses=_hypotheses())


def test_accepts_complete_a0_002_case() -> None:
    case = _case()
    assert len(case.series) == 8
    assert len(case.hypotheses) == 5


def test_requires_all_eight_series_roles() -> None:
    with pytest.raises(ContractViolation, match="series roles must be complete"):
        A0ValidationCase(windows=_windows(), series=_series()[:-1], hypotheses=_hypotheses())


def test_requires_h1_through_h5() -> None:
    with pytest.raises(ContractViolation, match="requires H1 through H5"):
        A0ValidationCase(windows=_windows(), series=_series(), hypotheses=_hypotheses()[:-1])


def test_unknown_hypothesis_cannot_claim_evidence() -> None:
    with pytest.raises(ContractViolation, match="UNKNOWN hypothesis result"):
        HypothesisResult(
            hypothesis_id="H5_JAPAN_TO_US_ROTATION",
            rating=HypothesisRating.UNKNOWN,
            evidence_refs=("evidence:fx",),
            rationale="data unavailable",
        )


def test_rejects_overlapping_baseline_and_primary_windows() -> None:
    with pytest.raises(ContractViolation, match="cannot overlap"):
        A0ValidationWindows(
            baseline_start=datetime(2026, 8, 26, tzinfo=UTC),
            baseline_end=datetime(2026, 9, 2, tzinfo=UTC),
            primary_start=datetime(2026, 9, 1, tzinfo=UTC),
            primary_end=datetime(2026, 9, 5, tzinfo=UTC),
        )


def test_timeline_filters_future_available_data() -> None:
    case = _case()
    day = date(2026, 9, 1)
    observed_at = datetime(2026, 9, 1, 16, 0, tzinfo=UTC)
    observations = (
        SeriesObservation(
            role=SeriesRole.CBRS,
            analysis_date=day,
            observed_at=observed_at,
            available_at=datetime(2026, 9, 1, 16, 1, tzinfo=UTC),
            value=10.0,
            source_ref="source:cbrs",
        ),
        SeriesObservation(
            role=SeriesRole.NVDA,
            analysis_date=day,
            observed_at=observed_at,
            available_at=datetime(2026, 9, 1, 16, 5, tzinfo=UTC),
            value=20.0,
            source_ref="source:nvda",
        ),
    )
    timeline = aligned_timeline(
        case=case,
        observations=observations,
        as_of=datetime(2026, 9, 1, 16, 2, tzinfo=UTC),
    )
    assert timeline[day] == {SeriesRole.CBRS: 10.0}


def test_timeline_aligns_different_source_timestamps_on_analysis_date() -> None:
    case = _case()
    day = date(2026, 9, 1)
    observations = (
        SeriesObservation(
            role=SeriesRole.JGB_10Y,
            analysis_date=day,
            observed_at=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
            available_at=datetime(2026, 9, 2, 0, 30, tzinfo=UTC),
            value=2.9,
            source_ref="source:jgb_10y",
        ),
        SeriesObservation(
            role=SeriesRole.CBRS,
            analysis_date=day,
            observed_at=datetime(2026, 9, 1, 20, 0, tzinfo=UTC),
            available_at=datetime(2026, 9, 1, 20, 1, tzinfo=UTC),
            value=190.0,
            source_ref="source:cbrs",
        ),
    )
    timeline = aligned_timeline(
        case=case,
        observations=observations,
        as_of=datetime(2026, 9, 2, 1, 0, tzinfo=UTC),
    )
    assert timeline[day] == {SeriesRole.CBRS: 190.0, SeriesRole.JGB_10Y: 2.9}


def test_timeline_does_not_forward_fill_missing_days() -> None:
    case = _case()
    day0 = date(2026, 9, 1)
    day1 = date(2026, 9, 2)
    observations = (
        SeriesObservation(
            role=SeriesRole.CBRS,
            analysis_date=day0,
            observed_at=datetime(2026, 9, 1, 20, 0, tzinfo=UTC),
            available_at=datetime(2026, 9, 1, 20, 0, tzinfo=UTC),
            value=10.0,
            source_ref="source:cbrs",
        ),
        SeriesObservation(
            role=SeriesRole.NVDA,
            analysis_date=day1,
            observed_at=datetime(2026, 9, 2, 20, 0, tzinfo=UTC),
            available_at=datetime(2026, 9, 2, 20, 0, tzinfo=UTC),
            value=20.0,
            source_ref="source:nvda",
        ),
    )
    timeline = aligned_timeline(
        case=case,
        observations=observations,
        as_of=datetime(2026, 9, 2, 21, 0, tzinfo=UTC),
    )
    assert timeline[day0] == {SeriesRole.CBRS: 10.0}
    assert timeline[day1] == {SeriesRole.NVDA: 20.0}


def test_timeline_rejects_source_ref_drift() -> None:
    case = _case()
    t0 = datetime(2026, 9, 1, 16, 0, tzinfo=UTC)
    observations = (
        SeriesObservation(
            role=SeriesRole.CBRS,
            analysis_date=date(2026, 9, 1),
            observed_at=t0,
            available_at=t0,
            value=10.0,
            source_ref="source:wrong",
        ),
    )
    with pytest.raises(ContractViolation, match="source_ref does not match"):
        aligned_timeline(case=case, observations=observations, as_of=t0)
