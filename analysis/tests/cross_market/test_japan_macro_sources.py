from __future__ import annotations

import json
from datetime import date

import pytest

from orderscope_local.contracts import ContractViolation, MacroMarketRegion, MacroMarketSeriesKind, TimestampPrecision
from orderscope_local.cross_market.japan_macro_sources import parse_boj_usdjpy_json, parse_mof_jgb_csv


def test_boj_fxerd04_daily_json() -> None:
    payload = {
        "STATUS": 200,
        "RESULTSET": [{
            "SERIES_CODE": "FXERD04",
            "UNIT": "JPY_per_USD",
            "FREQUENCY": "DAILY",
            "LAST_UPDATE": "20260911",
            "VALUES": {"SURVEY_DATES": ["20260908", "20260909"], "VALUES": [154.1, None]},
        }],
    }
    points = parse_boj_usdjpy_json(json.dumps(payload))
    assert len(points) == 1
    assert points[0].observed_at.calendar_date == date(2026, 9, 8)
    assert points[0].observed_at.precision is TimestampPrecision.DATE_ONLY
    assert points[0].series_kind is MacroMarketSeriesKind.FX_RATE
    assert points[0].region is MacroMarketRegion.CROSS_MARKET


def test_boj_failure_boundaries() -> None:
    with pytest.raises(ContractViolation):
        parse_boj_usdjpy_json(json.dumps({"STATUS": 503, "RESULTSET": []}))
    with pytest.raises(ContractViolation):
        parse_boj_usdjpy_json(json.dumps({"STATUS": 200, "RESULTSET": []}))


def test_mof_four_tenors() -> None:
    points = parse_mof_jgb_csv("Date,2Y,5Y,10Y,30Y\n2026/09/10,1.20,1.45,1.82,2.95\n")
    assert [(p.tenor, p.value) for p in points] == [("2Y", 1.2), ("5Y", 1.45), ("10Y", 1.82), ("30Y", 2.95)]
    assert all(p.series_kind is MacroMarketSeriesKind.SOVEREIGN_YIELD for p in points)
    assert all(p.region is MacroMarketRegion.JP for p in points)


def test_mof_missing_tenor_fails_closed() -> None:
    with pytest.raises(ContractViolation):
        parse_mof_jgb_csv("Date,2Y,5Y,10Y\n2026/09/10,1.20,1.45,1.82\n")
