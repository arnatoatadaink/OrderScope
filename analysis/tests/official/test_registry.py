from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.official import (
    OFFICIAL_ACTORS,
    OFFICIAL_SOURCES,
    ContentActorMode,
    OfficialActor,
    OfficialActorKind,
    OfficialSource,
    OfficialSourceLane,
    OfficialSourceType,
    get_official_actor,
    get_official_source,
    validate_official_registry,
)


def test_seed_registry_has_unique_resolvable_actors_and_sources() -> None:
    validate_official_registry()

    assert len(OFFICIAL_ACTORS) == 5
    assert len(OFFICIAL_SOURCES) == 12
    assert len({actor.actor_id for actor in OFFICIAL_ACTORS}) == 5
    assert len({source.source_id for source in OFFICIAL_SOURCES}) == 12
    assert all(get_official_actor(source.owner_actor_id) for source in OFFICIAL_SOURCES)
    assert all(get_official_source(source.source_id) == source for source in OFFICIAL_SOURCES)


def test_fomc_identity_is_distinct_from_fed_board_owner() -> None:
    board = get_official_actor("actor-gov-us-fed-board")
    fomc = get_official_actor("actor-gov-us-fomc")
    press = get_official_source("official-fed-board-press")

    assert board != fomc
    assert fomc.actor_kind is OfficialActorKind.GOVERNMENT_COMMITTEE
    assert press.owner_actor_id == board.actor_id
    assert press.content_actor_mode is ContentActorMode.FED_BOARD_OR_FOMC_FROM_ITEM


def test_sec_agency_registry_does_not_contain_edgar_source() -> None:
    sec_sources = [source for source in OFFICIAL_SOURCES if source.source_lane is OfficialSourceLane.SEC_AGENCY]

    assert len(sec_sources) == 3
    assert all("edgar" not in source.source_id.casefold() for source in sec_sources)
    assert all(source.owner_actor_id == "actor-gov-us-sec" for source in sec_sources)


def test_white_house_item_actor_is_not_silently_replaced_by_site_owner() -> None:
    source = get_official_source("official-white-house-presidential-actions")

    assert source.owner_actor_id == "actor-gov-us-white-house"
    assert source.content_actor_mode is ContentActorMode.ITEM_DECLARED


def test_registry_rejects_hostname_lane_mismatch_and_query_identity() -> None:
    common = dict(
        source_id="test-source",
        source_lane=OfficialSourceLane.WHITE_HOUSE,
        owner_actor_id="actor-gov-us-white-house",
        publisher_actor_id="actor-gov-us-white-house",
        source_type=OfficialSourceType.GOVERNMENT_NEWS_ENTRY,
        content_actor_mode=ContentActorMode.ITEM_DECLARED,
        policy_valid_from=date(2026, 9, 4),
        observed_at=datetime(2026, 9, 4, 7, 44, tzinfo=timezone.utc),
        evidence_refs=("E-TEST",),
    )

    with pytest.raises(ContractViolation, match="configured official host"):
        OfficialSource(canonical_entry_url="https://home.treasury.gov/news/", **common)

    with pytest.raises(ContractViolation, match="query"):
        OfficialSource(canonical_entry_url="https://www.whitehouse.gov/news/?page=2", **common)


def test_registry_rejects_unknown_actor_reference() -> None:
    source = OfficialSource(
        source_id="test-source",
        source_lane=OfficialSourceLane.SEC_AGENCY,
        canonical_entry_url="https://www.sec.gov/newsroom",
        owner_actor_id="actor-unknown",
        publisher_actor_id="actor-gov-us-sec",
        source_type=OfficialSourceType.SEC_AGENCY_NEWSROOM_ENTRY,
        content_actor_mode=ContentActorMode.SEC_AGENCY_OR_PERSON_FROM_ITEM,
        policy_valid_from=date(2026, 9, 4),
        observed_at=datetime(2026, 9, 4, 7, 44, tzinfo=timezone.utc),
        evidence_refs=("E-TEST",),
    )

    with pytest.raises(ContractViolation, match="unknown actor"):
        validate_official_registry(OFFICIAL_ACTORS, (source,))


def test_registry_policy_date_is_adoption_date_not_external_start_date() -> None:
    assert {source.policy_valid_from for source in OFFICIAL_SOURCES} == {date(2026, 9, 4)}
    assert all(source.observed_at == datetime(2026, 9, 4, 7, 44, tzinfo=timezone.utc) for source in OFFICIAL_SOURCES)
