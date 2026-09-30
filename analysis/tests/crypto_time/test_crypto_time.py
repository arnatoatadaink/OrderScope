from datetime import UTC, datetime, time

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.crypto_time import (
    AnalysisWindow,
    CryptoDayType,
    TraditionalBoundaryContext,
    TraditionalBoundaryType,
    classify_crypto_time,
    default_analysis_windows,
)


def dt(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def test_weekend_classification_is_utc_deterministic() -> None:
    context = classify_crypto_time(dt(2026, 9, 27, 12))
    assert context.day_type is CryptoDayType.WEEKEND
    assert context.utc_date == "2026-09-27"
    assert context.utc_hour == 12


def test_weekday_classification() -> None:
    context = classify_crypto_time(dt(2026, 9, 28, 12))
    assert context.day_type is CryptoDayType.WEEKDAY


def test_default_windows_can_overlap() -> None:
    context = classify_crypto_time(dt(2026, 9, 28, 8), windows=default_analysis_windows())
    assert context.analysis_window_ids == ("asia_clock_window", "europe_clock_window")


def test_us_window_classification() -> None:
    context = classify_crypto_time(dt(2026, 9, 28, 20), windows=default_analysis_windows())
    assert context.analysis_window_ids == ("us_clock_window",)


def test_wrapping_window_crosses_utc_midnight() -> None:
    window = AnalysisWindow("wrap", time(22), time(2))
    assert classify_crypto_time(dt(2026, 9, 28, 23), windows=(window,)).analysis_window_ids == ("wrap",)
    assert classify_crypto_time(dt(2026, 9, 29, 1), windows=(window,)).analysis_window_ids == ("wrap",)
    assert classify_crypto_time(dt(2026, 9, 29, 3), windows=(window,)).analysis_window_ids == ()


def test_boundary_context_is_explicit_and_preserved() -> None:
    boundary = TraditionalBoundaryContext(
        boundary_type=TraditionalBoundaryType.SUNDAY_TRADITIONAL_REOPEN,
        boundary_at=dt(2026, 9, 27, 22),
        source_ref="calendar.cme.btc",
        calendar_ref="cme.crypto.v1",
    )
    context = classify_crypto_time(dt(2026, 9, 27, 22, 5), boundary_contexts=(boundary,))
    assert context.boundary_contexts == (boundary,)


def test_naive_observed_at_rejected() -> None:
    with pytest.raises(ContractViolation, match="observed_at must be normalized to UTC"):
        classify_crypto_time(datetime(2026, 9, 28, 12))


def test_explicit_none_boundary_rejected() -> None:
    with pytest.raises(ContractViolation, match="cannot use NONE"):
        TraditionalBoundaryContext(
            boundary_type=TraditionalBoundaryType.NONE,
            boundary_at=dt(2026, 9, 28, 12),
            source_ref="calendar.none",
        )


def test_full_day_analysis_window_rejected() -> None:
    with pytest.raises(ContractViolation, match="cannot span exactly 24 hours"):
        AnalysisWindow("bad", time(0), time(0))


def test_region_label_has_no_participant_identity_field() -> None:
    context = classify_crypto_time(dt(2026, 9, 28, 8), windows=default_analysis_windows())
    assert not hasattr(context, "participant_region")
    assert not hasattr(context, "trader_nationality")
