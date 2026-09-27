from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import (
    CommodityFundamentalCadence,
    CommodityFundamentalMeasure,
    CommodityFundamentalObservation,
    CommodityGeography,
    CommodityProduct,
    ContentHash,
    ContractViolation,
    Provenance,
    SourceReference,
    SourceTimestamp,
)


UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 2, 0, tzinfo=UTC)
START = SourceTimestamp.date_only(date(2026, 9, 14))
END = SourceTimestamp.date_only(date(2026, 9, 18))


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("eia:petroleum:weekly:fixture"),
        content_hash=ContentHash("b" * 64),
        retrieved_at=ACCEPTED,
        available_at=datetime(2026, 9, 23, 14, 30, tzinfo=UTC),
        accepted_at=ACCEPTED,
        event_time=END,
    )


def observation(**overrides) -> CommodityFundamentalObservation:
    values = dict(
        subject_ref="commodity.us.crude.commercial_stocks",
        measure=CommodityFundamentalMeasure.COMMERCIAL_STOCKS,
        product=CommodityProduct.CRUDE_OIL,
        geography=CommodityGeography.US,
        cadence=CommodityFundamentalCadence.WEEKLY,
        series_id="fixture-commercial-crude-stocks",
        value=414000.0,
        unit="thousand_barrels",
        period_start=START,
        period_end=END,
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )
    values.update(overrides)
    return CommodityFundamentalObservation(**values)


def test_commercial_crude_stocks_materialize_as_observation_fact() -> None:
    item = observation()
    fact = item.to_fact(record_id="fact.commodity.us.crude.stocks.20260918", evidence_record_ids=("evidence.eia.1",))

    assert fact.fact_type == "commodity_fundamental.commercial_stocks"
    assert fact.value == 414000.0
    assert fact.unit == "thousand_barrels"
    assert fact.period_start == START
    assert fact.period_end == END


def test_cushing_stock_identity_requires_crude_and_cushing_geography() -> None:
    item = observation(
        subject_ref="commodity.us.cushing.crude_stocks",
        measure=CommodityFundamentalMeasure.CUSHING_STOCKS,
        geography=CommodityGeography.CUSHING_OK,
        series_id="fixture-cushing-stocks",
        value=22000.0,
    )
    assert item.geography is CommodityGeography.CUSHING_OK

    with pytest.raises(ContractViolation, match="CUSHING_OK"):
        observation(measure=CommodityFundamentalMeasure.CUSHING_STOCKS)


def test_spr_stocks_are_separate_from_commercial_stocks() -> None:
    item = observation(
        subject_ref="commodity.us.crude.spr_stocks",
        measure=CommodityFundamentalMeasure.SPR_STOCKS,
        series_id="fixture-spr-stocks",
        value=405000.0,
    )
    assert item.measure is CommodityFundamentalMeasure.SPR_STOCKS
    assert item.measure is not CommodityFundamentalMeasure.COMMERCIAL_STOCKS


def test_flow_measures_require_barrels_per_day_unit() -> None:
    with pytest.raises(ContractViolation, match="thousand_barrels_per_day"):
        observation(
            measure=CommodityFundamentalMeasure.FIELD_PRODUCTION,
            value=13600.0,
            unit="thousand_barrels",
        )


def test_refinery_utilization_requires_percent_and_crude_identity() -> None:
    item = observation(
        subject_ref="commodity.us.refinery.utilization",
        measure=CommodityFundamentalMeasure.REFINERY_UTILIZATION,
        series_id="fixture-refinery-utilization",
        value=93.4,
        unit="percent",
    )
    assert item.unit == "percent"

    with pytest.raises(ContractViolation, match="crude_oil"):
        observation(
            measure=CommodityFundamentalMeasure.REFINERY_UTILIZATION,
            product=CommodityProduct.MOTOR_GASOLINE,
            unit="percent",
        )


def test_product_supplied_is_preserved_as_proxy_not_demand_fact() -> None:
    item = observation(
        subject_ref="commodity.us.gasoline.product_supplied",
        measure=CommodityFundamentalMeasure.PRODUCT_SUPPLIED,
        product=CommodityProduct.MOTOR_GASOLINE,
        series_id="fixture-gasoline-product-supplied",
        value=9100.0,
        unit="thousand_barrels_per_day",
    )
    fact = item.to_fact(record_id="fact.commodity.us.gasoline.supplied", evidence_record_ids=())

    assert fact.fact_type == "commodity_fundamental.product_supplied"
    assert "demand" not in fact.fact_type
    assert "consumption" not in fact.fact_type


def test_product_supplied_can_represent_negative_source_observation() -> None:
    item = observation(
        subject_ref="commodity.us.distillate.product_supplied",
        measure=CommodityFundamentalMeasure.PRODUCT_SUPPLIED,
        product=CommodityProduct.DISTILLATE_FUEL_OIL,
        series_id="fixture-distillate-product-supplied",
        value=-25.0,
        unit="thousand_barrels_per_day",
    )
    assert item.value == -25.0


def test_crude_product_supplied_is_not_accepted_as_final_demand_proxy() -> None:
    with pytest.raises(ContractViolation, match="final-demand proxy"):
        observation(
            measure=CommodityFundamentalMeasure.PRODUCT_SUPPLIED,
            product=CommodityProduct.CRUDE_OIL,
            value=50.0,
            unit="thousand_barrels_per_day",
        )


def test_contract_contains_no_supply_disruption_or_oil_down_reason_classification() -> None:
    names = {item.value for item in CommodityFundamentalMeasure}
    assert "supply_disruption" not in names
    assert "oil_down_reason" not in names
    assert "demand" not in names
