from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContractViolation,
    MacroMarketObservation,
    MacroMarketRegion,
    MacroMarketSeriesKind,
    Provenance,
    SourceReference,
    SourceTimestamp,
)
from orderscope_local.cross_market.macro_metrics import (
    CurveChange,
    CurveShape,
    MacroMetricInput,
    classify_curve_change,
    classify_curve_shape,
    cross_country_spread,
    curve_slope,
    series_delta,
    series_velocity_per_day,
)

UTC = timezone.utc
BASE = datetime(2026, 9, 10, 0, 0, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 12, 0, 0, tzinfo=UTC)


def point(
    record_id: str,
    series_id: str,
    value: float,
    *,
    region: MacroMarketRegion,
    tenor: str | None,
    available_at: datetime = BASE,
    kind: MacroMarketSeriesKind = MacroMarketSeriesKind.SOVEREIGN_YIELD,
    unit: str = "percent",
) -> MacroMetricInput:
    provenance = Provenance(
        source_ref=SourceReference(f"fixture:{series_id}:{available_at.isoformat()}"),
        content_hash=ContentHash("a" * 64),
        retrieved_at=available_at,
        available_at=available_at,
        accepted_at=available_at,
        event_time=SourceTimestamp.at(available_at),
    )
    observation = MacroMarketObservation(
        subject_ref=f"macro:{series_id}",
        series_kind=kind,
        region=region,
        series_id=series_id,
        value=value,
        unit=unit,
        observed_at=SourceTimestamp.at(available_at),
        accepted_at=available_at,
        provenance=provenance,
        tenor=tenor,
    )
    return MacroMetricInput(fact_record_id=record_id, observation=observation)


def test_curve_and_cross_country_spreads_preserve_fact_lineage() -> None:
    us2 = point("fact:us2", "US_TREASURY_2Y", 4.1, region=MacroMarketRegion.US, tenor="2Y")
    us10 = point("fact:us10", "US_TREASURY_10Y", 4.4, region=MacroMarketRegion.US, tenor="10Y")
    us30 = point("fact:us30", "US_TREASURY_30Y", 4.7, region=MacroMarketRegion.US, tenor="30Y")
    jp2 = point("fact:jp2", "JP_JGB_2Y", 1.0, region=MacroMarketRegion.JP, tenor="2Y")
    jp10 = point("fact:jp10", "JP_JGB_10Y", 1.7, region=MacroMarketRegion.JP, tenor="10Y")

    two_ten = curve_slope(
        short=us2,
        long=us10,
        region=MacroMarketRegion.US,
        short_tenor="2Y",
        long_tenor="10Y",
        accepted_at=ACCEPTED,
    )
    ten_thirty = curve_slope(
        short=us10,
        long=us30,
        region=MacroMarketRegion.US,
        short_tenor="10Y",
        long_tenor="30Y",
        accepted_at=ACCEPTED,
    )
    spread2 = cross_country_spread(us=us2, jp=jp2, tenor="2Y", accepted_at=ACCEPTED)
    spread10 = cross_country_spread(us=us10, jp=jp10, tenor="10Y", accepted_at=ACCEPTED)

    assert two_ten.value == pytest.approx(0.3)
    assert ten_thirty.value == pytest.approx(0.3)
    assert spread2.value == pytest.approx(3.1)
    assert spread10.value == pytest.approx(2.7)
    assert two_ten.input_record_ids == ("fact:us2", "fact:us10")
    assert spread10.input_record_ids == ("fact:us10", "fact:jp10")
    assert all(metric.unit == "percent" for metric in (two_ten, ten_thirty, spread2, spread10))


def test_fixed_window_delta_and_velocity_use_availability_time() -> None:
    start = point(
        "fact:us10:start",
        "US_TREASURY_10Y",
        4.5,
        region=MacroMarketRegion.US,
        tenor="10Y",
        available_at=BASE,
    )
    end = point(
        "fact:us10:end",
        "US_TREASURY_10Y",
        4.3,
        region=MacroMarketRegion.US,
        tenor="10Y",
        available_at=BASE + timedelta(days=2),
    )

    delta = series_delta(start=start, end=end, accepted_at=ACCEPTED)
    velocity = series_velocity_per_day(start=start, end=end, accepted_at=ACCEPTED)

    assert delta.value == pytest.approx(-0.2)
    assert velocity.value == pytest.approx(-0.1)
    assert velocity.unit == "percent_per_day"
    assert velocity.input_record_ids == ("fact:us10:start", "fact:us10:end")


def test_curve_shape_and_change_do_not_claim_causality() -> None:
    assert classify_curve_shape(0.25) is CurveShape.NORMAL
    assert classify_curve_shape(-0.01) is CurveShape.INVERTED
    assert classify_curve_shape(0.005, flat_tolerance=0.01) is CurveShape.FLAT
    assert classify_curve_change(-0.2, 0.1) is CurveChange.STEEPENING
    assert classify_curve_change(0.4, 0.1) is CurveChange.FLATTENING
    assert classify_curve_change(0.1, 0.1001, tolerance=0.001) is CurveChange.UNCHANGED


def test_metric_inputs_fail_closed_on_mismatched_series_or_units() -> None:
    us2 = point("fact:us2", "US_TREASURY_2Y", 4.1, region=MacroMarketRegion.US, tenor="2Y")
    jp2 = point("fact:jp2", "JP_JGB_2Y", 1.0, region=MacroMarketRegion.JP, tenor="2Y")
    wrong_unit = point(
        "fact:jp2:bps",
        "JP_JGB_2Y",
        100.0,
        region=MacroMarketRegion.JP,
        tenor="2Y",
        unit="basis_points",
    )
    later_other = point(
        "fact:us10",
        "US_TREASURY_10Y",
        4.3,
        region=MacroMarketRegion.US,
        tenor="10Y",
        available_at=BASE + timedelta(days=1),
    )

    with pytest.raises(ContractViolation, match="same unit"):
        cross_country_spread(us=us2, jp=wrong_unit, tenor="2Y", accepted_at=ACCEPTED)
    with pytest.raises(ContractViolation, match="same normalized macro series"):
        series_delta(start=us2, end=later_other, accepted_at=ACCEPTED)
    with pytest.raises(ContractViolation, match="expected JP"):
        cross_country_spread(us=us2, jp=us2, tenor="2Y", accepted_at=ACCEPTED)
