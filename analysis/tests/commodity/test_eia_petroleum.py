from datetime import date, datetime, timezone

import pytest

from orderscope_local.commodity import EiaPetroleumSeriesProfile, normalize_eia_petroleum_row
from orderscope_local.contracts import (
    CommodityFundamentalCadence,
    CommodityFundamentalMeasure,
    CommodityGeography,
    CommodityProduct,
    ContentHash,
    ContractViolation,
    Provenance,
    SourceReference,
    SourceTimestamp,
)


UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 2, 30, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("eia-api-v2:fixture"),
        content_hash=ContentHash("c" * 64),
        retrieved_at=ACCEPTED,
        available_at=ACCEPTED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.date_only(date(2026, 9, 18)),
    )


def stock_profile() -> EiaPetroleumSeriesProfile:
    return EiaPetroleumSeriesProfile(
        route="/v2/petroleum/sum/sndw/data/",
        series_id="fixture-commercial-crude-stocks",
        subject_ref="commodity.us.crude.commercial_stocks",
        measure=CommodityFundamentalMeasure.COMMERCIAL_STOCKS,
        product=CommodityProduct.CRUDE_OIL,
        geography=CommodityGeography.US,
        cadence=CommodityFundamentalCadence.WEEKLY,
        normalized_unit="thousand_barrels",
    )


def test_weekly_eia_string_value_normalizes_to_seven_day_observation() -> None:
    item = normalize_eia_petroleum_row(
        profile=stock_profile(),
        row={
            "period": "2026-09-18",
            "series": "fixture-commercial-crude-stocks",
            "value": "426398",
            "units": "Thousand Barrels",
        },
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )

    assert item.value == 426398.0
    assert item.period_start == SourceTimestamp.date_only(date(2026, 9, 12))
    assert item.period_end == SourceTimestamp.date_only(date(2026, 9, 18))


def test_eia_nonnumeric_withheld_value_is_not_inferred() -> None:
    with pytest.raises(ContractViolation, match="missing, withheld, or non-numeric"):
        normalize_eia_petroleum_row(
            profile=stock_profile(),
            row={"period": "2026-09-18", "value": "W", "units": "Thousand Barrels"},
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )


def test_eia_unit_mismatch_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="units do not match"):
        normalize_eia_petroleum_row(
            profile=stock_profile(),
            row={"period": "2026-09-18", "value": "426398", "units": "Thousand Barrels per Day"},
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )


def test_eia_series_identity_mismatch_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="series does not match"):
        normalize_eia_petroleum_row(
            profile=stock_profile(),
            row={"period": "2026-09-18", "series": "other", "value": "426398", "units": "Thousand Barrels"},
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )


def test_monthly_period_expands_to_calendar_month() -> None:
    profile = EiaPetroleumSeriesProfile(
        route="/v2/petroleum/crd/crpdn/data/",
        series_id="fixture-monthly-production",
        subject_ref="commodity.us.crude.field_production",
        measure=CommodityFundamentalMeasure.FIELD_PRODUCTION,
        product=CommodityProduct.CRUDE_OIL,
        geography=CommodityGeography.US,
        cadence=CommodityFundamentalCadence.MONTHLY,
        normalized_unit="thousand_barrels_per_day",
    )
    item = normalize_eia_petroleum_row(
        profile=profile,
        row={"period": "2026-02", "value": "13750", "units": "Thousand Barrels per Day"},
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )

    assert item.period_start == SourceTimestamp.date_only(date(2026, 2, 1))
    assert item.period_end == SourceTimestamp.date_only(date(2026, 2, 28))


def test_annual_period_expands_to_calendar_year() -> None:
    profile = EiaPetroleumSeriesProfile(
        route="/v2/petroleum/crd/crpdn/data/",
        series_id="fixture-annual-production",
        subject_ref="commodity.us.crude.field_production",
        measure=CommodityFundamentalMeasure.FIELD_PRODUCTION,
        product=CommodityProduct.CRUDE_OIL,
        geography=CommodityGeography.US,
        cadence=CommodityFundamentalCadence.ANNUAL,
        normalized_unit="thousand_barrels_per_day",
    )
    item = normalize_eia_petroleum_row(
        profile=profile,
        row={"period": "2025", "value": "13500", "units": "Thousand Barrels per Day"},
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )

    assert item.period_start == SourceTimestamp.date_only(date(2025, 1, 1))
    assert item.period_end == SourceTimestamp.date_only(date(2025, 12, 31))


def test_profile_requires_petroleum_v2_data_route() -> None:
    with pytest.raises(ContractViolation, match="/v2/petroleum"):
        EiaPetroleumSeriesProfile(
            route="/v2/electricity/retail-sales/data/",
            series_id="fixture",
            subject_ref="commodity.us.crude.stocks",
            measure=CommodityFundamentalMeasure.COMMERCIAL_STOCKS,
            product=CommodityProduct.CRUDE_OIL,
            geography=CommodityGeography.US,
            cadence=CommodityFundamentalCadence.WEEKLY,
            normalized_unit="thousand_barrels",
        )
