from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, Provenance, SourceReference
from orderscope_local.crypto import BtcSpotEtfFundProfile, normalize_btc_spot_etf_flow_row


UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 3, 15, tzinfo=UTC)
PROFILE = BtcSpotEtfFundProfile(
    source_fund_id="IBIT",
    fund_ref="crypto.etf.ibit",
    ticker="IBIT",
)


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("provider:btc-etf-flow:fixture"),
        content_hash=ContentHash("f" * 64),
        retrieved_at=ACCEPTED,
        available_at=ACCEPTED,
        accepted_at=ACCEPTED,
    )


def test_normalizes_iso_date_and_signed_numeric_string() -> None:
    item = normalize_btc_spot_etf_flow_row(
        row={"date": "2026-09-25", "fund": "IBIT", "net_flow_usd": "125,000,000"},
        profile=PROFILE,
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )
    assert item.ticker == "IBIT"
    assert item.net_flow_usd == 125_000_000.0
    assert item.flow_date.calendar_date.isoformat() == "2026-09-25"


def test_normalizes_negative_outflow() -> None:
    item = normalize_btc_spot_etf_flow_row(
        row={"date": "2026-09-25", "fund": "IBIT", "net_flow_usd": -12_500_000},
        profile=PROFILE,
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )
    assert item.net_flow_usd == -12_500_000.0


def test_rejects_provider_total_profile() -> None:
    with pytest.raises(ContractViolation, match="aggregate row"):
        BtcSpotEtfFundProfile(source_fund_id="TOTAL", fund_ref="crypto.etf.aggregate", ticker="TOTAL")


def test_rejects_mismatched_fund_row() -> None:
    with pytest.raises(ContractViolation, match="does not match fund profile"):
        normalize_btc_spot_etf_flow_row(
            row={"date": "2026-09-25", "fund": "FBTC", "net_flow_usd": 1},
            profile=PROFILE,
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )


def test_rejects_missing_flow_marker_instead_of_imputing_zero() -> None:
    with pytest.raises(ContractViolation, match="value is missing"):
        normalize_btc_spot_etf_flow_row(
            row={"date": "2026-09-25", "fund": "IBIT", "net_flow_usd": "--"},
            profile=PROFILE,
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )


def test_rejects_non_iso_date() -> None:
    with pytest.raises(ContractViolation, match="ISO YYYY-MM-DD"):
        normalize_btc_spot_etf_flow_row(
            row={"date": "09/25/2026", "fund": "IBIT", "net_flow_usd": 1},
            profile=PROFILE,
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )
