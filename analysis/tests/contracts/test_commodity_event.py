from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import (
    CommodityEventKind,
    CommodityEventState,
    CommoditySupplyEventObservation,
    ContentHash,
    ContractViolation,
    Provenance,
    SourceReference,
    SourceTimestamp,
)

UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 3, 0, tzinfo=UTC)
START = SourceTimestamp.date_only(date(2026, 9, 27))


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("official:commodity-event:fixture"),
        content_hash=ContentHash("c" * 64),
        retrieved_at=ACCEPTED,
        available_at=ACCEPTED,
        accepted_at=ACCEPTED,
        event_time=START,
    )


def event(**overrides) -> CommoditySupplyEventObservation:
    values = dict(
        subject_ref="commodity.event.fixture",
        event_kind=CommodityEventKind.UPSTREAM_OUTAGE,
        event_state=CommodityEventState.REPORTED,
        geography_ref="geo.us.gulf_of_mexico",
        accepted_at=ACCEPTED,
        provenance=provenance(),
        effective_start=START,
    )
    values.update(overrides)
    return CommoditySupplyEventObservation(**values)


def test_source_observed_event_materializes_as_fact() -> None:
    item = event()
    fact = item.to_fact(
        record_id="fact.commodity.event.fixture",
        evidence_record_ids=("evidence.official.1",),
    )

    assert fact.fact_type == "commodity_event.upstream_outage"
    assert fact.value["event_state"] == "reported"
    assert fact.value["geography_ref"] == "geo.us.gulf_of_mexico"


def test_pipeline_disruption_requires_asset_identity() -> None:
    with pytest.raises(ContractViolation, match="asset_ref"):
        event(event_kind=CommodityEventKind.PIPELINE_DISRUPTION)

    item = event(
        event_kind=CommodityEventKind.PIPELINE_DISRUPTION,
        asset_ref="asset.pipeline.fixture",
    )
    assert item.asset_ref == "asset.pipeline.fixture"


def test_shipping_route_disruption_requires_route_identity() -> None:
    with pytest.raises(ContractViolation, match="route_ref"):
        event(event_kind=CommodityEventKind.SHIPPING_ROUTE_DISRUPTION)

    item = event(
        event_kind=CommodityEventKind.SHIPPING_ROUTE_DISRUPTION,
        route_ref="route.strait.fixture",
    )
    assert item.route_ref == "route.strait.fixture"


def test_policy_action_requires_actor_identity() -> None:
    with pytest.raises(ContractViolation, match="actor_ref"):
        event(event_kind=CommodityEventKind.SANCTIONS_ACTION)

    item = event(
        event_kind=CommodityEventKind.SANCTIONS_ACTION,
        actor_ref="actor.government.fixture",
    )
    assert item.actor_ref == "actor.government.fixture"


def test_event_interval_cannot_run_backwards() -> None:
    with pytest.raises(ContractViolation, match="effective_start"):
        event(
            effective_start=SourceTimestamp.date_only(date(2026, 9, 28)),
            effective_end=SourceTimestamp.date_only(date(2026, 9, 27)),
        )


def test_event_state_is_source_lifecycle_not_severity() -> None:
    names = {item.value for item in CommodityEventState}
    assert names == {"reported", "announced", "active", "resolved", "cancelled"}
    assert "severe" not in names
    assert "bullish" not in names
    assert "bearish" not in names


def test_taxonomy_contains_no_price_direction_or_barrels_at_risk() -> None:
    names = {item.value for item in CommodityEventKind}
    assert "oil_up" not in names
    assert "oil_down" not in names
    assert "barrels_at_risk" not in names
    assert "risk_on" not in names
