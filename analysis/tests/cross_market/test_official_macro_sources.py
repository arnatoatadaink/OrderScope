from __future__ import annotations

from datetime import date

import pytest

from orderscope_local.contracts import ContractViolation, MacroMarketRegion, MacroMarketSeriesKind, TimestampPrecision
from orderscope_local.cross_market.official_macro_sources import parse_treasury_par_yield_csv


def test_parses_required_treasury_tenors_without_inventing_time_precision() -> None:
    text = (
        "Date,1 Mo,2 Yr,5 Yr,10 Yr,30 Yr\n"
        "09/01/2026,3.70,4.05,4.18,4.47,4.99\n"
    )
    points = parse_treasury_par_yield_csv(text)
    assert [(point.tenor, point.value) for point in points] == [
        ("2Y", 4.05),
        ("5Y", 4.18),
        ("10Y", 4.47),
        ("30Y", 4.99),
    ]
    assert all(point.series_kind is MacroMarketSeriesKind.SOVEREIGN_YIELD for point in points)
    assert all(point.region is MacroMarketRegion.US for point in points)
    assert all(point.unit == "percent" for point in points)
    assert all(point.observed_at.precision is TimestampPrecision.DATE_ONLY for point in points)
    assert all(point.observed_at.calendar_date == date(2026, 9, 1) for point in points)


def test_treasury_window_filters_rows() -> None:
    text = (
        "Date,2 Yr,5 Yr,10 Yr,30 Yr\n"
        "09/01/2026,4.01,4.11,4.21,4.81\n"
        "09/02/2026,4.02,4.12,4.22,4.82\n"
    )
    points = parse_treasury_par_yield_csv(
        text,
        start=date(2026, 9, 2),
        end_exclusive=date(2026, 9, 3),
    )
    assert len(points) == 4
    assert all(point.observed_at.calendar_date == date(2026, 9, 2) for point in points)


def test_treasury_missing_required_tenor_fails_closed() -> None:
    text = "Date,2 Yr,5 Yr,10 Yr\n09/01/2026,4.0,4.1,4.2\n"
    with pytest.raises(ContractViolation, match="30Y"):
        parse_treasury_par_yield_csv(text)


def test_treasury_malformed_numeric_value_fails_closed() -> None:
    text = "Date,2 Yr,5 Yr,10 Yr,30 Yr\n09/01/2026,4.0,broken,4.2,4.8\n"
    with pytest.raises(ContractViolation, match="5Y yield must be numeric"):
        parse_treasury_par_yield_csv(text)
