"""CFTC Traders in Financial Futures positioning adapter for UWBS-036.

The adapter normalizes weekly positioning only.  It must not label position
changes as fund flow, capital movement, or investor identity outside the CFTC
published trader categories.
"""

from __future__ import annotations

from csv import DictReader
from dataclasses import dataclass
from datetime import date, datetime
import io

from orderscope_local.contracts import ContractViolation, SourceTimestamp

CFTC_TFF_SOURCE = "cftc:tff:futures-only"


@dataclass(frozen=True, kw_only=True, slots=True)
class CftcTffPositioningPoint:
    market_name: str
    contract_market_code: str
    report_date: SourceTimestamp
    open_interest: int
    asset_manager_long: int
    asset_manager_short: int
    asset_manager_spread: int
    leveraged_money_long: int
    leveraged_money_short: int
    leveraged_money_spread: int
    source_ref: str = CFTC_TFF_SOURCE

    def __post_init__(self) -> None:
        for value, field in (
            (self.market_name, "market_name"),
            (self.contract_market_code, "contract_market_code"),
            (self.source_ref, "source_ref"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if not isinstance(self.report_date, SourceTimestamp):
            raise ContractViolation("report_date must be SourceTimestamp")
        for value, field in (
            (self.open_interest, "open_interest"),
            (self.asset_manager_long, "asset_manager_long"),
            (self.asset_manager_short, "asset_manager_short"),
            (self.asset_manager_spread, "asset_manager_spread"),
            (self.leveraged_money_long, "leveraged_money_long"),
            (self.leveraged_money_short, "leveraged_money_short"),
            (self.leveraged_money_spread, "leveraged_money_spread"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractViolation(f"{field} must be a non-negative integer")

    @property
    def asset_manager_net_position(self) -> int:
        return self.asset_manager_long - self.asset_manager_short

    @property
    def leveraged_money_net_position(self) -> int:
        return self.leveraged_money_long - self.leveraged_money_short


def parse_cftc_tff_csv(
    text: str,
    *,
    contract_market_codes: frozenset[str] | None = None,
    start: date | None = None,
    end_exclusive: date | None = None,
) -> tuple[CftcTffPositioningPoint, ...]:
    """Parse official comma-delimited TFF Futures Only rows."""
    if (start is None) != (end_exclusive is None):
        raise ContractViolation("CFTC window requires both start and end_exclusive")
    if start is not None and start >= end_exclusive:
        raise ContractViolation("CFTC window must be non-empty")
    if contract_market_codes is not None:
        if not isinstance(contract_market_codes, frozenset) or not contract_market_codes:
            raise ContractViolation("contract_market_codes must be a non-empty frozenset")
        for code in contract_market_codes:
            if not isinstance(code, str) or not code.strip():
                raise ContractViolation("contract market code must be non-empty text")
    if not isinstance(text, str) or not text.strip():
        raise ContractViolation("CFTC TFF CSV cannot be empty")

    reader = DictReader(io.StringIO(text))
    required = {
        "Market_and_Exchange_Names",
        "Report_Date_as_MM_DD_YYYY",
        "CFTC_Contract_Market_Code",
        "Open_Interest_All",
        "Asset_Mgr_Positions_Long_All",
        "Asset_Mgr_Positions_Short_All",
        "Asset_Mgr_Positions_Spread_All",
        "Lev_Money_Positions_Long_All",
        "Lev_Money_Positions_Short_All",
        "Lev_Money_Positions_Spread_All",
    }
    if not reader.fieldnames or not required <= set(reader.fieldnames):
        missing = sorted(required - set(reader.fieldnames or ()))
        raise ContractViolation(f"CFTC TFF CSV missing required columns: {','.join(missing)}")

    output: list[CftcTffPositioningPoint] = []
    for row in reader:
        code = (row.get("CFTC_Contract_Market_Code") or "").strip().strip('"')
        if contract_market_codes is not None and code not in contract_market_codes:
            continue
        report_day = _date(row.get("Report_Date_as_MM_DD_YYYY"))
        if start is not None and not start <= report_day < end_exclusive:
            continue
        output.append(
            CftcTffPositioningPoint(
                market_name=_text(row.get("Market_and_Exchange_Names"), "market_name"),
                contract_market_code=_text(code, "contract_market_code"),
                report_date=SourceTimestamp.date_only(report_day),
                open_interest=_integer(row.get("Open_Interest_All"), "open_interest"),
                asset_manager_long=_integer(row.get("Asset_Mgr_Positions_Long_All"), "asset_manager_long"),
                asset_manager_short=_integer(row.get("Asset_Mgr_Positions_Short_All"), "asset_manager_short"),
                asset_manager_spread=_integer(row.get("Asset_Mgr_Positions_Spread_All"), "asset_manager_spread"),
                leveraged_money_long=_integer(row.get("Lev_Money_Positions_Long_All"), "leveraged_money_long"),
                leveraged_money_short=_integer(row.get("Lev_Money_Positions_Short_All"), "leveraged_money_short"),
                leveraged_money_spread=_integer(row.get("Lev_Money_Positions_Spread_All"), "leveraged_money_spread"),
            )
        )
    return tuple(output)


def _date(value: object) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation("CFTC report date is required")
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ContractViolation("CFTC report date is not recognized")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{field} must be non-empty text")
    return value.strip()


def _integer(value: object, field: str) -> int:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{field} is required")
    normalized = value.strip().replace(",", "")
    try:
        result = int(normalized)
    except ValueError as exc:
        raise ContractViolation(f"{field} must be an integer") from exc
    if result < 0:
        raise ContractViolation(f"{field} must be non-negative")
    return result
