from __future__ import annotations

from datetime import date

import pytest

from orderscope_local.contracts import ContractViolation, MacroMarketRegion, MacroMarketSeriesKind
from orderscope_local.cross_market.fred_alfred import (
    FredSeriesDescriptor,
    parse_fred_observations_json,
    parse_fred_vintage_dates_json,
)


def _descriptor() -> FredSeriesDescriptor:
    return FredSeriesDescriptor(
        series_id="DGS10",
        series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
        region=MacroMarketRegion.US,
        unit="percent",
        underlying_source_ref="federal-reserve:h15:dgs10",
        terms_ref="fred:series-terms-reviewed",
        tenor="10Y",
    )


def test_fred_observations_preserve_realtime_lineage_and_skip_missing() -> None:
    text = '''{
      "realtime_start":"2026-09-01",
      "realtime_end":"2026-09-10",
      "observations":[
        {"realtime_start":"2026-09-01","realtime_end":"2026-09-05","date":"2026-09-01","value":"4.20"},
        {"realtime_start":"2026-09-06","realtime_end":"2026-09-10","date":"2026-09-02","value":"."}
      ]
    }'''
    rows = parse_fred_observations_json(text, descriptor=_descriptor())
    assert len(rows) == 1
    row = rows[0]
    assert row.value == 4.20
    assert row.observed_at.calendar_date == date(2026, 9, 1)
    assert row.realtime_start.calendar_date == date(2026, 9, 1)
    assert row.realtime_end.calendar_date == date(2026, 9, 5)
    assert row.source_ref == "fred:DGS10"


def test_fred_descriptor_requires_explicit_source_and_terms() -> None:
    with pytest.raises(ContractViolation, match="underlying_source_ref"):
        FredSeriesDescriptor(
            series_id="DGS10",
            series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
            region=MacroMarketRegion.US,
            unit="percent",
            underlying_source_ref="",
            terms_ref="fred:terms",
            tenor="10Y",
        )


def test_fred_vintage_dates_preserve_release_dates() -> None:
    rows = parse_fred_vintage_dates_json(
        '{"vintage_dates":["2026-08-01","2026-08-15","2026-09-01"]}',
        series_id="DGS10",
    )
    assert [row.vintage_date.calendar_date for row in rows] == [
        date(2026, 8, 1),
        date(2026, 8, 15),
        date(2026, 9, 1),
    ]


def test_fred_observation_requires_realtime_lineage() -> None:
    text = '{"observations":[{"date":"2026-09-01","value":"4.2"}]}'
    with pytest.raises(ContractViolation, match="realtime_start"):
        parse_fred_observations_json(text, descriptor=_descriptor())
