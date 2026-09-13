"""Provider-neutral official feed adapter boundary for O0-002.

This module models bounded incremental discovery from official RSS or HTML index
routes without leaking site-specific payloads downstream. It preserves source
registry identity, canonical item URLs, source timestamp precision, retrieval
metadata, overlap-window semantics, and explicit partial/error state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from urllib.parse import urlparse

from orderscope_local.contracts import ContractViolation, ContentHash, SourceTimestamp

from .registry import OfficialSourceLane, get_official_source


class OfficialAcquisitionRoute(StrEnum):
    RSS = "rss"
    HTML_INDEX = "html_index"


class OfficialItemAvailability(StrEnum):
    PRESENT = "present"
    LISTING_MISSING = "listing_missing"
    CANONICAL_UNAVAILABLE = "canonical_unavailable"


class OfficialFeedStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class OfficialFeedProfile:
    source_id: str
    primary_route: OfficialAcquisitionRoute
    primary_url: str
    fallback_route: OfficialAcquisitionRoute | None = None
    fallback_url: str | None = None

    def __post_init__(self) -> None:
        source = get_official_source(self.source_id)
        _validate_official_url(self.primary_url, source.source_lane)
        if (self.fallback_route is None) != (self.fallback_url is None):
            raise ContractViolation("official feed fallback route/url must be both present or both absent")
        if self.fallback_url is not None:
            _validate_official_url(self.fallback_url, source.source_lane)
        if source.source_lane in {OfficialSourceLane.WHITE_HOUSE, OfficialSourceLane.US_TREASURY}:
            if self.primary_route is not OfficialAcquisitionRoute.HTML_INDEX:
                raise ContractViolation("White House/Treasury v0.1 primary route must be HTML index")
        if self.source_id in {"official-fed-board-press", "official-fed-board-speeches-testimony", "official-sec-agency-press", "official-sec-agency-speeches-statements"}:
            if self.primary_route is not OfficialAcquisitionRoute.RSS:
                raise ContractViolation("Fed/SEC configured incremental source must be RSS-first")


@dataclass(frozen=True, slots=True)
class OfficialDiscoveredItem:
    source_id: str
    canonical_item_url: str
    content_hash: ContentHash
    retrieved_at: datetime
    published_at: SourceTimestamp | None = None
    event_time: SourceTimestamp | None = None
    source_last_update: SourceTimestamp | None = None
    availability: OfficialItemAvailability = OfficialItemAvailability.PRESENT

    def __post_init__(self) -> None:
        source = get_official_source(self.source_id)
        _validate_official_url(self.canonical_item_url, source.source_lane, allow_query=False)
        if not isinstance(self.content_hash, ContentHash):
            raise ContractViolation("official item requires ContentHash")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() != timedelta(0):
            raise ContractViolation("official item retrieved_at must be normalized to UTC")
        for value in (self.published_at, self.event_time, self.source_last_update):
            if value is not None and not isinstance(value, SourceTimestamp):
                raise ContractViolation("official source timestamps must use SourceTimestamp")
        if not isinstance(self.availability, OfficialItemAvailability):
            raise ContractViolation("official item availability is invalid")


@dataclass(frozen=True, slots=True)
class OfficialFeedCheckpoint:
    source_id: str
    observed_at: datetime
    overlap_start: date
    latest_published: SourceTimestamp | None = None
    latest_item_identity: str | None = None
    last_successful_ref: str | None = None

    def __post_init__(self) -> None:
        get_official_source(self.source_id)
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() != timedelta(0):
            raise ContractViolation("official checkpoint observed_at must be normalized to UTC")
        if not isinstance(self.overlap_start, date):
            raise ContractViolation("official checkpoint overlap_start must be a date")
        if self.latest_published is not None and not isinstance(self.latest_published, SourceTimestamp):
            raise ContractViolation("official checkpoint latest_published is invalid")
        for field, value in (("latest_item_identity", self.latest_item_identity), ("last_successful_ref", self.last_successful_ref)):
            if value is not None and (not value.strip() or len(value) > 2048):
                raise ContractViolation(f"official checkpoint {field} must be bounded text")


@dataclass(frozen=True, slots=True)
class OfficialFeedPage:
    source_id: str
    route: OfficialAcquisitionRoute
    items: tuple[OfficialDiscoveredItem, ...]
    status: OfficialFeedStatus
    retrieved_at: datetime
    next_ref: str | None = None
    error_category: str | None = None

    def __post_init__(self) -> None:
        get_official_source(self.source_id)
        if not isinstance(self.route, OfficialAcquisitionRoute):
            raise ContractViolation("official feed route is invalid")
        if any(item.source_id != self.source_id for item in self.items):
            raise ContractViolation("official feed page contains cross-source item")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() != timedelta(0):
            raise ContractViolation("official feed page retrieved_at must be normalized to UTC")
        if not isinstance(self.status, OfficialFeedStatus):
            raise ContractViolation("official feed status is invalid")
        if self.status is OfficialFeedStatus.COMPLETE and self.error_category is not None:
            raise ContractViolation("complete official feed page cannot carry error_category")
        if self.status is not OfficialFeedStatus.COMPLETE and (self.error_category is None or not self.error_category.strip()):
            raise ContractViolation("partial/error official feed page requires error_category")
        if self.next_ref is not None and (not self.next_ref.strip() or len(self.next_ref) > 2048):
            raise ContractViolation("official feed next_ref must be bounded text")


def classify_item_change(previous: OfficialDiscoveredItem | None, current: OfficialDiscoveredItem) -> str:
    """Classify one canonical item observation without inferring deletion.

    A listing disappearance is not a deletion. Canonical unavailability remains
    an availability state and historical evidence is retained.
    """
    if previous is None:
        return "new"
    if previous.source_id != current.source_id or previous.canonical_item_url != current.canonical_item_url:
        raise ContractViolation("official item comparison requires same source and canonical URL")
    if current.availability is OfficialItemAvailability.LISTING_MISSING:
        return "listing_missing"
    if current.availability is OfficialItemAvailability.CANONICAL_UNAVAILABLE:
        return "canonical_unavailable"
    if previous.content_hash.digest == current.content_hash.digest:
        return "unchanged"
    return "changed"


def _validate_official_url(url: str, lane: OfficialSourceLane, *, allow_query: bool = True) -> None:
    if not isinstance(url, str) or not url or url != url.strip() or len(url) > 2048:
        raise ContractViolation("official feed URL must be bounded canonical text")
    parsed = urlparse(url)
    hosts = {
        OfficialSourceLane.WHITE_HOUSE: {"www.whitehouse.gov"},
        OfficialSourceLane.US_TREASURY: {"home.treasury.gov"},
        OfficialSourceLane.FED_BOARD: {"www.federalreserve.gov"},
        OfficialSourceLane.SEC_AGENCY: {"www.sec.gov"},
    }
    if parsed.scheme != "https" or parsed.hostname not in hosts[lane]:
        raise ContractViolation("official feed URL must use configured official host")
    if parsed.username or parsed.password or parsed.fragment:
        raise ContractViolation("official feed URL cannot contain credentials or fragment")
    if not allow_query and parsed.query:
        raise ContractViolation("canonical official item URL cannot contain query state")


OFFICIAL_FEED_PROFILES: tuple[OfficialFeedProfile, ...] = (
    OfficialFeedProfile("official-white-house-news", OfficialAcquisitionRoute.HTML_INDEX, "https://www.whitehouse.gov/news/"),
    OfficialFeedProfile("official-white-house-briefings", OfficialAcquisitionRoute.HTML_INDEX, "https://www.whitehouse.gov/briefings-statements/"),
    OfficialFeedProfile("official-white-house-presidential-actions", OfficialAcquisitionRoute.HTML_INDEX, "https://www.whitehouse.gov/presidential-actions/"),
    OfficialFeedProfile("official-white-house-fact-sheets", OfficialAcquisitionRoute.HTML_INDEX, "https://www.whitehouse.gov/fact-sheets/"),
    OfficialFeedProfile("official-us-treasury-press", OfficialAcquisitionRoute.HTML_INDEX, "https://home.treasury.gov/news/press-releases"),
    OfficialFeedProfile("official-us-treasury-statements", OfficialAcquisitionRoute.HTML_INDEX, "https://home.treasury.gov/news/press-releases/statements-remarks/"),
    OfficialFeedProfile("official-fed-board-press", OfficialAcquisitionRoute.RSS, "https://www.federalreserve.gov/feeds/press_all.xml", OfficialAcquisitionRoute.HTML_INDEX, "https://www.federalreserve.gov/newsevents/pressreleases.htm"),
    OfficialFeedProfile("official-fed-board-speeches-testimony", OfficialAcquisitionRoute.RSS, "https://www.federalreserve.gov/feeds/speeches_and_testimony.xml", OfficialAcquisitionRoute.HTML_INDEX, "https://www.federalreserve.gov/newsevents/speeches-testimony.htm"),
    OfficialFeedProfile("official-sec-agency-press", OfficialAcquisitionRoute.RSS, "https://www.sec.gov/news/pressreleases.rss", OfficialAcquisitionRoute.HTML_INDEX, "https://www.sec.gov/newsroom/press-releases"),
    OfficialFeedProfile("official-sec-agency-speeches-statements", OfficialAcquisitionRoute.RSS, "https://www.sec.gov/news/speeches-statements.rss", OfficialAcquisitionRoute.HTML_INDEX, "https://www.sec.gov/newsroom/speeches-statements"),
)


def get_official_feed_profile(source_id: str) -> OfficialFeedProfile:
    matches = [item for item in OFFICIAL_FEED_PROFILES if item.source_id == source_id]
    if len(matches) != 1:
        raise ContractViolation("official feed profile lookup is missing or ambiguous")
    return matches[0]
