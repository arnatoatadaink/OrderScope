from __future__ import annotations

from datetime import date, datetime, timezone

from orderscope_local.cross_market.official_macro import (
    parse_boj_usdjpy_html,
    parse_fred_dgs10_csv,
    parse_mof_jgb_csv,
)
from orderscope_local.cross_market.validation import SeriesMeasure, SeriesRole

UTC = timezone.utc


def test_parses_fred_dgs10_csv() -> None:
    text = "DATE,DGS10\n2026-09-03,4.77\n2026-09-04,4.78\n"
    rows = parse_fred_dgs10_csv(text, start=date(2026, 9, 3), end_exclusive=date(2026, 9, 5))
    assert [(item.analysis_date, item.value) for item in rows] == [
        (date(2026, 9, 3), 4.77),
        (date(2026, 9, 4), 4.78),
    ]
    assert all(item.role is SeriesRole.UST_10Y for item in rows)
    assert all(item.measure is SeriesMeasure.YIELD for item in rows)


def test_parses_mof_10y_and_uses_next_weekday_release() -> None:
    text = "Date,1Y,5Y,10Y,20Y\n2026/09/03,1.0,1.5,2.10,2.5\n2026/09/04,1.1,1.6,2.20,2.6\n"
    rows = parse_mof_jgb_csv(text, start=date(2026, 9, 3), end_exclusive=date(2026, 9, 5))
    friday = next(item for item in rows if item.analysis_date == date(2026, 9, 4))
    assert friday.role is SeriesRole.JGB_10Y
    assert friday.measure is SeriesMeasure.YIELD
    assert friday.value == 2.20
    assert friday.available_at == datetime(2026, 9, 7, 0, 30, tzinfo=UTC)


def test_parses_boj_1700_usdjpy_from_main_table_shape() -> None:
    html = """
    <table>
      <tr><td>2026/09/01</td><td>155.10</td><td>155.20</td></tr>
      <tr><td>2026/09/02</td><td>155.40</td><td>155.35</td></tr>
      <tr><td>2026/09/03</td><td>156.05</td><td>155.90</td></tr>
      <tr><td>2026/09/04</td><td>156.30</td><td>156.15</td></tr>
    </table>
    """
    rows = parse_boj_usdjpy_html(html, start=date(2026, 9, 1), end_exclusive=date(2026, 9, 5))
    assert [(item.analysis_date, item.value) for item in rows] == [
        (date(2026, 9, 1), 155.10),
        (date(2026, 9, 2), 155.40),
        (date(2026, 9, 3), 156.05),
        (date(2026, 9, 4), 156.30),
    ]
    assert rows[-1].available_at == datetime(2026, 9, 4, 8, 50, tzinfo=UTC)


def test_boj_skips_non_business_na_rows() -> None:
    html = "<tr><td>2026/08/29</td><td>NA</td><td>NA</td></tr><tr><td>2026/08/31</td><td>155.0</td><td>155.1</td></tr>"
    rows = parse_boj_usdjpy_html(html, start=date(2026, 8, 29), end_exclusive=date(2026, 9, 1))
    assert len(rows) == 1
    assert rows[0].analysis_date == date(2026, 8, 31)
