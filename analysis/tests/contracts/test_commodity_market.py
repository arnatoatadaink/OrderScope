from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import (
    CommodityLocation,
    CommodityPriceForm,
    CommodityPriceObservation,
    CommodityVenue,
    ContentHash,
    ContractViolation,
    CrudeBenchmark,
    Provenance,
    SourceReference,
    SourceTimestamp,
)


UTC = timezone.utc
OBSERVED = datetime(2026, 9, 25, 20, 0, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 25, 20, 5, tzinfo=UTC)


def provenance(source: str = "eia:PET.RWTC.D") -> Provenance:
    return Provenance(
        source_ref=SourceReference(source),
        content_hash=ContentHash("b" * 64),
        retrieved_at=ACCEPTED,
        available_at=OBSERVED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.at(OBSERVED),
    )


def test_wti_cushing_spot_reference_materializes_as_distinct_fact() -> None:
    observation = CommodityPriceObservation(
        subject_ref="commodity.crude.wti.cushing.spot",
        benchmark=CrudeBenchmark.WTI,
        price_form=CommodityPriceForm.SPOT_REFERENCE,
        series_id="RWTC",
        value=97.25,
        unit="usd_per_barrel",
        observed_at=SourceTimestamp.at(OBSERVED),
        accepted_at=ACCEPTED,
        provenance=provenance(),
        location=CommodityLocation.CUSHING_OK,
    )

    fact = observation.to_fact(
        record_id="fact.commodity.wti.cushing.20260925",
        evidence_record_ids=("evidence.commodity.1",),
    )

    assert fact.fact_type == "commodity_price.spot_reference"
    assert fact.subject_ref == "commodity.crude.wti.cushing.spot"
    assert fact.unit == "usd_per_barrel"


def test_brent_europe_spot_reference_has_separate_identity() -> None:
    observation = CommodityPriceObservation(
        subject_ref="commodity.crude.brent.europe.spot",
        benchmark=CrudeBenchmark.BRENT,
        price_form=CommodityPriceForm.SPOT_REFERENCE,
        series_id="RBRTE",
        value=101.5,
        unit="usd_per_barrel",
        observed_at=SourceTimestamp.at(OBSERVED),
        accepted_at=ACCEPTED,
        provenance=provenance("eia:PET.RBRTE.D"),
        location=CommodityLocation.EUROPE,
    )

    assert observation.benchmark is CrudeBenchmark.BRENT
    assert observation.series_id == "RBRTE"


def test_listed_wti_future_requires_contract_identity() -> None:
    observation = CommodityPriceObservation(
        subject_ref="commodity.crude.wti.future.CLX26",
        benchmark=CrudeBenchmark.WTI,
        price_form=CommodityPriceForm.FUTURES_CONTRACT,
        series_id="CLX26",
        value=96.75,
        unit="usd_per_barrel",
        observed_at=SourceTimestamp.at(OBSERVED),
        accepted_at=ACCEPTED,
        provenance=provenance("massive:futures:CLX26"),
        venue=CommodityVenue.NYMEX,
        contract_code="CLX26",
        delivery_month="2026-11",
    )

    assert observation.contract_code == "CLX26"
    assert observation.price_form is CommodityPriceForm.FUTURES_CONTRACT


def test_listed_brent_future_requires_ice_futures_europe() -> None:
    with pytest.raises(ContractViolation, match="ICE_FUTURES_EUROPE"):
        CommodityPriceObservation(
            subject_ref="commodity.crude.brent.future.BRNZ26",
            benchmark=CrudeBenchmark.BRENT,
            price_form=CommodityPriceForm.FUTURES_CONTRACT,
            series_id="BRNZ26",
            value=99.0,
            unit="usd_per_barrel",
            observed_at=SourceTimestamp.at(OBSERVED),
            accepted_at=ACCEPTED,
            provenance=provenance("fixture:brent"),
            venue=CommodityVenue.NYMEX,
            contract_code="BRNZ26",
            delivery_month="2026-12",
        )


def test_spot_and_futures_fields_cannot_be_collapsed() -> None:
    with pytest.raises(ContractViolation, match="cannot contain futures"):
        CommodityPriceObservation(
            subject_ref="commodity.crude.wti.invalid",
            benchmark=CrudeBenchmark.WTI,
            price_form=CommodityPriceForm.SPOT_REFERENCE,
            series_id="RWTC",
            value=95.0,
            unit="usd_per_barrel",
            observed_at=SourceTimestamp.at(OBSERVED),
            accepted_at=ACCEPTED,
            provenance=provenance(),
            location=CommodityLocation.CUSHING_OK,
            venue=CommodityVenue.NYMEX,
            contract_code="CLX26",
            delivery_month="2026-11",
        )


def test_negative_crude_price_is_valid_but_nonfinite_is_not() -> None:
    observation = CommodityPriceObservation(
        subject_ref="commodity.crude.wti.future.CLJ20",
        benchmark=CrudeBenchmark.WTI,
        price_form=CommodityPriceForm.FUTURES_CONTRACT,
        series_id="CLJ20",
        value=-37.63,
        unit="usd_per_barrel",
        observed_at=SourceTimestamp.at(OBSERVED),
        accepted_at=ACCEPTED,
        provenance=provenance("fixture:historical-negative-wti"),
        venue=CommodityVenue.NYMEX,
        contract_code="CLJ20",
        delivery_month="2020-04",
    )
    assert observation.value == -37.63

    with pytest.raises(ContractViolation, match="finite"):
        CommodityPriceObservation(
            subject_ref="commodity.crude.wti.future.invalid",
            benchmark=CrudeBenchmark.WTI,
            price_form=CommodityPriceForm.FUTURES_CONTRACT,
            series_id="INVALID",
            value=float("nan"),
            unit="usd_per_barrel",
            observed_at=SourceTimestamp.at(OBSERVED),
            accepted_at=ACCEPTED,
            provenance=provenance("fixture:invalid"),
            venue=CommodityVenue.NYMEX,
            contract_code="INVALID",
            delivery_month="2026-11",
        )


def test_uso_proxy_is_not_a_crude_benchmark_or_price_form() -> None:
    assert "USO" not in {item.value for item in CrudeBenchmark}
    assert "etf_proxy" not in {item.value for item in CommodityPriceForm}
