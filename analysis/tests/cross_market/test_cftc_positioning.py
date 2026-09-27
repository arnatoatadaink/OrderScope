from __future__ import annotations

from datetime import date

import pytest

from orderscope_local.contracts import ContractViolation, TimestampPrecision
from orderscope_local.cross_market.cftc_positioning import parse_cftc_tff_csv

HEADER = (
    "Market_and_Exchange_Names,Report_Date_as_MM_DD_YYYY,CFTC_Contract_Market_Code,"
    "Open_Interest_All,Asset_Mgr_Positions_Long_All,Asset_Mgr_Positions_Short_All,"
    "Asset_Mgr_Positions_Spread_All,Lev_Money_Positions_Long_All,"
    "Lev_Money_Positions_Short_All,Lev_Money_Positions_Spread_All\n"
)


def test_parses_positioning_and_computes_net_without_flow_label() -> None:
    text = HEADER + "UST 2Y NOTE - CBOT,09/08/2026,042601,4346314,2249346,628123,600071,585711,1876190,233489\n"
    rows = parse_cftc_tff_csv(text)
    assert len(rows) == 1
    row = rows[0]
    assert row.report_date.precision is TimestampPrecision.DATE_ONLY
    assert row.report_date.calendar_date == date(2026, 9, 8)
    assert row.asset_manager_net_position == 1621223
    assert row.leveraged_money_net_position == -1290479
    assert "flow" not in row.source_ref


def test_filters_contract_and_window() -> None:
    text = (
        HEADER
        + "UST 2Y NOTE - CBOT,09/01/2026,042601,100,30,20,5,40,50,5\n"
        + "EURO FX - CME,09/08/2026,099741,200,80,40,10,60,70,10\n"
    )
    rows = parse_cftc_tff_csv(
        text,
        contract_market_codes=frozenset({"099741"}),
        start=date(2026, 9, 8),
        end_exclusive=date(2026, 9, 9),
    )
    assert [row.contract_market_code for row in rows] == ["099741"]


def test_missing_required_position_column_fails_closed() -> None:
    text = HEADER.replace(",Lev_Money_Positions_Spread_All", "") + "UST 2Y NOTE - CBOT,09/08/2026,042601,100,30,20,5,40,50\n"
    with pytest.raises(ContractViolation, match="Lev_Money_Positions_Spread_All"):
        parse_cftc_tff_csv(text)


def test_negative_position_fails_closed() -> None:
    text = HEADER + "UST 2Y NOTE - CBOT,09/08/2026,042601,100,30,20,5,-1,50,5\n"
    with pytest.raises(ContractViolation, match="leveraged_money_long must be non-negative"):
        parse_cftc_tff_csv(text)
