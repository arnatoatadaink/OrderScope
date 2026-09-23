from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, SourceTimestamp
from orderscope_local.official import (
    OFFICIAL_FEED_PROFILES,
    OfficialAcquisitionRoute,
    OfficialDiscoveredItem,
    OfficialFeedCheckpoint,
    OfficialFeedPage,
    OfficialFeedProfile,
    OfficialFeedStatus,
    OfficialItemAvailability,
    classify_item_change,
    get_official_feed_profile,
)


def _item(*, digest: str = "a", availability: OfficialItemAvailability = OfficialItemAvailability.PRESENT) -> OfficialDiscoveredItem:
    return OfficialDiscoveredItem(
        source_id="official-fed-board-press",
        canonical_item_url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20260729a.htm",
        content_hash=ContentHash(digest * 64),
        retrieved_at=datetime(2026, 9, 4, 8, 0, tzinfo=timezone.utc),
        published_at=SourceTimestamp.date_only(date(2026, 7, 29)),
        availability=availability,
    )


def test_profiles_encode_html_first_and_rss_first_routes() -> None:
    assert get_official_feed_profile("official-white-house-news").primary_route is OfficialAcquisitionRoute.HTML_INDEX
    assert get_official_feed_profile("official-us-treasury-press").primary_route is OfficialAcquisitionRoute.HTML_INDEX
    assert get_official_feed_profile("official-fed-board-press").primary_route is OfficialAcquisitionRoute.RSS
    assert get_official_feed_profile("official-sec-agency-press").primary_route is OfficialAcquisitionRoute.RSS
    assert len({profile.source_id for profile in OFFICIAL_FEED_PROFILES}) == len(OFFICIAL_FEED_PROFILES)


def test_date_only_published_time_is_preserved_without_midnight_inference() -> None:
    item = _item()
    assert item.published_at is not None
    assert item.published_at.calendar_date == date(2026, 7, 29)
    assert item.published_at.instant is None


def test_content_hash_change_is_revision_candidate_not_silent_overwrite() -> None:
    previous = _item(digest="a")
    current = _item(digest="b")
    assert classify_item_change(previous, current) == "changed"
    assert classify_item_change(previous, _item(digest="a")) == "unchanged"


def test_listing_missing_does_not_become_delete() -> None:
    previous = _item()
    current = _item(availability=OfficialItemAvailability.LISTING_MISSING)
    assert classify_item_change(previous, current) == "listing_missing"


def test_canonical_unavailable_is_distinct_from_listing_missing() -> None:
    previous = _item()
    current = _item(availability=OfficialItemAvailability.CANONICAL_UNAVAILABLE)
    assert classify_item_change(previous, current) == "canonical_unavailable"


def test_partial_page_requires_error_and_can_preserve_next_ref() -> None:
    page = OfficialFeedPage(
        source_id="official-fed-board-press",
        route=OfficialAcquisitionRoute.RSS,
        items=(_item(),),
        status=OfficialFeedStatus.PARTIAL,
        retrieved_at=datetime(2026, 9, 4, 8, 0, tzinfo=timezone.utc),
        next_ref="https://www.federalreserve.gov/newsevents/2026-press.htm",
        error_category="archive_fetch_error",
    )
    assert page.status is OfficialFeedStatus.PARTIAL
    assert page.error_category == "archive_fetch_error"


def test_checkpoint_preserves_overlap_and_latest_identity() -> None:
    checkpoint = OfficialFeedCheckpoint(
        source_id="official-sec-agency-press",
        observed_at=datetime(2026, 9, 4, 8, 0, tzinfo=timezone.utc),
        overlap_start=date(2026, 9, 1),
        latest_published=SourceTimestamp.date_only(date(2026, 9, 4)),
        latest_item_identity="https://www.sec.gov/newsroom/press-releases/example",
        last_successful_ref="https://www.sec.gov/newsroom/press-releases?page=1",
    )
    assert checkpoint.overlap_start == date(2026, 9, 1)


def test_rejects_guessed_feed_route_for_white_house_and_cross_host_item() -> None:
    with pytest.raises(ContractViolation, match="primary route must be HTML index"):
        OfficialFeedProfile(
            "official-white-house-news",
            OfficialAcquisitionRoute.RSS,
            "https://www.whitehouse.gov/news/",
        )

    with pytest.raises(ContractViolation, match="configured official host"):
        OfficialDiscoveredItem(
            source_id="official-sec-agency-press",
            canonical_item_url="https://example.com/not-official",
            content_hash=ContentHash("f" * 64),
            retrieved_at=datetime(2026, 9, 4, 8, 0, tzinfo=timezone.utc),
        )


def test_canonical_item_url_rejects_listing_query_state() -> None:
    with pytest.raises(ContractViolation, match="cannot contain query state"):
        OfficialDiscoveredItem(
            source_id="official-sec-agency-press",
            canonical_item_url="https://www.sec.gov/newsroom/press-releases?page=1",
            content_hash=ContentHash("f" * 64),
            retrieved_at=datetime(2026, 9, 4, 8, 0, tzinfo=timezone.utc),
        )
