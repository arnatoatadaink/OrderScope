"""UWBS-084 generic row normalizer for U.S. spot-Bitcoin ETF daily flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from typing import Mapping

from orderscope_local.contracts.crypto_etf_flow import BtcSpotEtfFlowObservation
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.provenance import Provenance, SourceTimestamp


_MISSING = {"", "NA", "N/A", "--", "-"}


@dataclass(frozen=True, kw_only=True)
class BtcSpotEtfFundProfile:
    source_fund_id: str
    fund_ref: str
    ticker: str

    def __post_init__(self) -> None:
        for value, field in (
            (self.source_fund_id, "source_fund_id"),
            (self.fund_ref, "fund_ref"),
            (self.ticker, "ticker"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if self.source_fund_id.lower() in {"total", "aggregate", "all"}:
            raise ContractViolation("fund profile cannot identify an aggregate row")


def normalize_btc_spot_etf_flow_row(
    *,
    row: Mapping[str, object],
    profile: BtcSpotEtfFundProfile,
    accepted_at: datetime,
    provenance: Provenance,
    date_field: str = "date",
    fund_field: str = "fund",
    flow_field: str = "net_flow_usd",
) -> BtcSpotEtfFlowObservation:
    if not isinstance(row, Mapping):
        raise ContractViolation("ETF flow row must be a mapping")
    if row.get(fund_field) != profile.source_fund_id:
        raise ContractViolation("ETF flow row does not match fund profile")

    raw_date = row.get(date_field)
    if isinstance(raw_date, datetime):
        flow_date = raw_date.date()
    elif isinstance(raw_date, date):
        flow_date = raw_date
    elif isinstance(raw_date, str):
        try:
            flow_date = date.fromisoformat(raw_date.strip())
        except ValueError as error:
            raise ContractViolation("ETF flow date must be ISO YYYY-MM-DD") from error
    else:
        raise ContractViolation("ETF flow date is missing or unsupported")

    raw_flow = row.get(flow_field)
    if isinstance(raw_flow, str):
        value = raw_flow.strip().replace(",", "")
        if value.upper() in _MISSING:
            raise ContractViolation("ETF flow value is missing")
        try:
            flow = float(value)
        except ValueError as error:
            raise ContractViolation("ETF flow value must be numeric USD") from error
    elif isinstance(raw_flow, bool) or not isinstance(raw_flow, (int, float)):
        raise ContractViolation("ETF flow value must be numeric USD")
    else:
        flow = float(raw_flow)
    if not isfinite(flow):
        raise ContractViolation("ETF flow value must be finite")

    return BtcSpotEtfFlowObservation(
        fund_ref=profile.fund_ref,
        ticker=profile.ticker,
        flow_date=SourceTimestamp.date_only(flow_date),
        net_flow_usd=flow,
        accepted_at=accepted_at,
        provenance=provenance,
    )
