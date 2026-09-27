from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts.crypto_etf_flow import (
    BtcSpotEtfFlowObservation,
    aggregate_btc_spot_etf_flow,
)
from orderscope_local.contracts import ContentHash, ContractViolation, Provenance, SourceReference, SourceTimestamp


UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 3, 0, tzinfo=UTC)
FLOW_DATE = SourceTimestamp.date_only(date(2026, 9, 25))


def provenance(seed: str = "c") -> Provenance:
    return Provenance(
        source_ref=SourceReference("provider:btc-etf-flow:fixture"),
        content_hash=ContentHash(seed * 64),
        retrieved_at=ACCEPTED,
        available_at=ACCEPTED,
        accepted_at=ACCEPTED,
        event_time=FLOW_DATE,
    )


def observation(**overrides) -> BtcSpotEtfFlowObservation:
    values = dict(
        fund_ref="crypto.etf.ibit",
        ticker="IBIT",
        flow_date=FLOW_DATE,
        net_flow_usd=125_000_000.0,
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )
    values.update(overrides)
    return BtcSpotEtfFlowObservation(**values)


def test_fund_level_flow_materializes_as_source_grounded_fact() -> None:
    fact = observation().to_fact(record_id="fact.crypto.etf.ibit.20260925", evidence_record_ids=("evidence.etf.1",))
    assert fact.fact_type == "crypto_etf.btc_spot_net_flow"
    assert fact.subject_ref == "crypto.etf.ibit"
    assert fact.value == 125_000_000.0
    assert fact.unit == "usd"


def test_signed_outflow_and_zero_flow_are_valid() -> None:
    assert observation(net_flow_usd=-42_000_000.0).net_flow_usd == -42_000_000.0
    assert observation(net_flow_usd=0.0).net_flow_usd == 0.0


def test_flow_fact_cannot_use_aggregate_identity() -> None:
    with pytest.raises(ContractViolation, match="one fund"):
        observation(fund_ref="aggregate")


def test_flow_date_must_be_date_only() -> None:
    with pytest.raises(ContractViolation, match="date-only"):
        observation(flow_date=SourceTimestamp.at(datetime(2026, 9, 25, 20, 0, tzinfo=UTC)))


def test_aggregate_is_derived_from_unique_fund_facts() -> None:
    ibit = observation().to_fact(record_id="fact.ibit", evidence_record_ids=("evidence.ibit",))
    fbtc = observation(
        fund_ref="crypto.etf.fbtc",
        ticker="FBTC",
        net_flow_usd=-25_000_000.0,
        provenance=provenance("d"),
    ).to_fact(record_id="fact.fbtc", evidence_record_ids=("evidence.fbtc",))

    metric = aggregate_btc_spot_etf_flow(
        record_id="metric.crypto.etf.total.20260925",
        flow_date=FLOW_DATE,
        accepted_at=ACCEPTED,
        fund_flow_facts=(ibit, fbtc),
    )

    assert metric.metric_name == "crypto_etf.btc_spot_aggregate_net_flow"
    assert metric.value == 100_000_000.0
    assert metric.input_record_ids == ("fact.ibit", "fact.fbtc")


def test_aggregate_rejects_duplicate_fund_subject() -> None:
    first = observation().to_fact(record_id="fact.ibit.1", evidence_record_ids=("evidence.1",))
    second = observation(net_flow_usd=10.0, provenance=provenance("e")).to_fact(
        record_id="fact.ibit.2", evidence_record_ids=("evidence.2",)
    )
    with pytest.raises(ContractViolation, match="duplicate fund"):
        aggregate_btc_spot_etf_flow(
            record_id="metric.total",
            flow_date=FLOW_DATE,
            accepted_at=ACCEPTED,
            fund_flow_facts=(first, second),
        )


def test_price_direction_or_risk_on_is_not_part_of_flow_fact() -> None:
    fact = observation().to_fact(record_id="fact.ibit", evidence_record_ids=("evidence.ibit",))
    assert "price" not in fact.fact_type
    assert "risk_on" not in fact.fact_type
