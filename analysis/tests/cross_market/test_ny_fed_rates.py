from __future__ import annotations

from datetime import date

import pytest

from orderscope_local.contracts import ContractViolation, MacroMarketRegion, MacroMarketSeriesKind, TimestampPrecision
from orderscope_local.cross_market.ny_fed_rates import parse_ny_fed_reference_rates_json


def test_parses_effr_sofr_obfr_as_distinct_short_market_rates() -> None:
    text = '''{"refRates":[
      {"effectiveDate":"2026-09-10","type":"EFFR","percentRate":3.63,"revisionIndicator":"R"},
      {"effectiveDate":"2026-09-10","type":"SOFR","percentRate":"3.65","footnote":"1"},
      {"effectiveDate":"2026-09-10","type":"OBFR","percentRate":3.64},
      {"effectiveDate":"2026-09-10","type":"TGCR","percentRate":3.60}
    ]}'''
    points = parse_ny_fed_reference_rates_json(text)
    assert [(point.series_id, point.value) for point in points] == [
        ("US_EFFR", 3.63),
        ("US_SOFR", 3.65),
        ("US_OBFR", 3.64),
    ]
    assert all(point.series_kind is MacroMarketSeriesKind.SHORT_MARKET_RATE for point in points)
    assert all(point.region is MacroMarketRegion.US for point in points)
    assert all(point.observed_at.precision is TimestampPrecision.DATE_ONLY for point in points)
    assert points[0].revision_indicator == "R"
    assert points[1].footnote == "1"


def test_ny_fed_window_and_type_filter_are_bounded() -> None:
    text = '''{"refRates":[
      {"effectiveDate":"2026-09-09","type":"EFFR","percentRate":3.62},
      {"effectiveDate":"2026-09-10","type":"EFFR","percentRate":3.63},
      {"effectiveDate":"2026-09-10","type":"SOFR","percentRate":3.65}
    ]}'''
    points = parse_ny_fed_reference_rates_json(
        text,
        start=date(2026, 9, 10),
        end_exclusive=date(2026, 9, 11),
        include_types=frozenset({"EFFR"}),
    )
    assert len(points) == 1
    assert points[0].series_id == "US_EFFR"
    assert points[0].observed_at.calendar_date == date(2026, 9, 10)


def test_ny_fed_malformed_rate_fails_closed() -> None:
    text = '{"refRates":[{"effectiveDate":"2026-09-10","type":"EFFR","percentRate":"broken"}]}'
    with pytest.raises(ContractViolation, match="percentRate must be numeric"):
        parse_ny_fed_reference_rates_json(text)


def test_ny_fed_does_not_accept_target_range_as_reference_rate_type() -> None:
    text = '{"refRates":[]}'
    with pytest.raises(ContractViolation, match="unsupported"):
        parse_ny_fed_reference_rates_json(text, include_types=frozenset({"FOMC_TARGET"}))
