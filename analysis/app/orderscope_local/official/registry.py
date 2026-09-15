"""Immutable official-source registry for O0-001.

The registry separates source owner/publisher identity from per-item content actor
resolution. Hostname membership alone never establishes actor identity. SEC agency
news sources remain separate from the SEC EDGAR filing lane.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import StrEnum
from urllib.parse import urlparse

from orderscope_local.contracts import ContractViolation


class OfficialActorKind(StrEnum):
    GOVERNMENT_OFFICIAL_SOURCE = "government_official_source"
    GOVERNMENT_AGENCY = "government_agency"
    GOVERNMENT_COMMITTEE = "government_committee"


class OfficialSourceLane(StrEnum):
    WHITE_HOUSE = "white_house"
    US_TREASURY = "us_treasury"
    FED_BOARD = "fed_board"
    SEC_AGENCY = "sec_agency"


class OfficialSourceType(StrEnum):
    GOVERNMENT_NEWS_ENTRY = "government_news_entry"
    BRIEFINGS_STATEMENTS_INDEX = "briefings_statements_index"
    PRESIDENTIAL_ACTIONS_INDEX = "presidential_actions_index"
    FACT_SHEETS_INDEX = "fact_sheets_index"
    AGENCY_PRESS_RELEASE_INDEX = "agency_press_release_index"
    AGENCY_STATEMENTS_REMARKS_INDEX = "agency_statements_remarks_index"
    CENTRAL_BANK_NEWS_ENTRY = "central_bank_news_entry"
    CENTRAL_BANK_PRESS_RELEASE_INDEX = "central_bank_press_release_index"
    CENTRAL_BANK_SPEECH_TESTIMONY_INDEX = "central_bank_speech_testimony_index"
    SEC_AGENCY_NEWSROOM_ENTRY = "sec_agency_newsroom_entry"
    AGENCY_SPEECH_STATEMENT_INDEX = "agency_speech_statement_index"


class ContentActorMode(StrEnum):
    ITEM_DECLARED = "item_declared"
    ITEM_DECLARED_OR_FIXED_OWNER = "item_declared_or_fixed_owner"
    FED_BOARD_OR_FOMC_FROM_ITEM = "fed_board_or_fomc_from_item"
    SEC_AGENCY_OR_PERSON_FROM_ITEM = "sec_agency_or_person_from_item"


@dataclass(frozen=True, slots=True)
class OfficialActor:
    actor_id: str
    actor_kind: OfficialActorKind
    display_name: str

    def __post_init__(self) -> None:
        if not self.actor_id or self.actor_id != self.actor_id.strip() or len(self.actor_id) > 128:
            raise ContractViolation("official actor_id must be bounded canonical text")
        if not isinstance(self.actor_kind, OfficialActorKind):
            raise ContractViolation("official actor_kind is invalid")
        if not self.display_name or self.display_name != self.display_name.strip() or len(self.display_name) > 256:
            raise ContractViolation("official actor display_name must be bounded canonical text")


@dataclass(frozen=True, slots=True)
class OfficialSource:
    source_id: str
    source_lane: OfficialSourceLane
    canonical_entry_url: str
    owner_actor_id: str
    publisher_actor_id: str
    source_type: OfficialSourceType
    content_actor_mode: ContentActorMode
    policy_valid_from: date
    observed_at: datetime
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.source_id or self.source_id != self.source_id.strip() or len(self.source_id) > 160:
            raise ContractViolation("official source_id must be bounded canonical text")
        if not isinstance(self.source_lane, OfficialSourceLane):
            raise ContractViolation("official source_lane is invalid")
        if not isinstance(self.source_type, OfficialSourceType):
            raise ContractViolation("official source_type is invalid")
        if not isinstance(self.content_actor_mode, ContentActorMode):
            raise ContractViolation("official content_actor_mode is invalid")
        _validate_url_for_lane(self.canonical_entry_url, self.source_lane)
        for field, value in (
            ("owner_actor_id", self.owner_actor_id),
            ("publisher_actor_id", self.publisher_actor_id),
        ):
            if not value or value != value.strip() or len(value) > 128:
                raise ContractViolation(f"official {field} must be bounded canonical text")
        if not isinstance(self.policy_valid_from, date):
            raise ContractViolation("official policy_valid_from must be a date")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() != timezone.utc.utcoffset(self.observed_at):
            raise ContractViolation("official observed_at must be normalized to UTC")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise ContractViolation("official source requires evidence_refs")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ContractViolation("official source evidence_refs must be unique")
        if any(not item or item != item.strip() or len(item) > 128 for item in self.evidence_refs):
            raise ContractViolation("official source evidence_refs contain invalid values")


_ALLOWED_HOSTS: dict[OfficialSourceLane, set[str]] = {
    OfficialSourceLane.WHITE_HOUSE: {"www.whitehouse.gov"},
    OfficialSourceLane.US_TREASURY: {"home.treasury.gov"},
    OfficialSourceLane.FED_BOARD: {"www.federalreserve.gov"},
    OfficialSourceLane.SEC_AGENCY: {"www.sec.gov"},
}


def _validate_url_for_lane(url: object, lane: OfficialSourceLane) -> None:
    if not isinstance(url, str) or not url or url != url.strip() or len(url) > 2048:
        raise ContractViolation("official canonical_entry_url must be bounded canonical text")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS[lane]:
        raise ContractViolation("official canonical_entry_url must use the configured official host")
    if parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise ContractViolation("official canonical_entry_url cannot contain credentials, query, or fragment")


OBSERVED_AT = datetime(2026, 9, 4, 7, 44, tzinfo=timezone.utc)
POLICY_VALID_FROM = date(2026, 9, 4)

OFFICIAL_ACTORS: tuple[OfficialActor, ...] = (
    OfficialActor("actor-gov-us-white-house", OfficialActorKind.GOVERNMENT_OFFICIAL_SOURCE, "The White House"),
    OfficialActor("actor-gov-us-treasury", OfficialActorKind.GOVERNMENT_AGENCY, "U.S. Department of the Treasury"),
    OfficialActor("actor-gov-us-fed-board", OfficialActorKind.GOVERNMENT_AGENCY, "Board of Governors of the Federal Reserve System"),
    OfficialActor("actor-gov-us-fomc", OfficialActorKind.GOVERNMENT_COMMITTEE, "Federal Open Market Committee"),
    OfficialActor("actor-gov-us-sec", OfficialActorKind.GOVERNMENT_AGENCY, "U.S. Securities and Exchange Commission"),
)

OFFICIAL_SOURCES: tuple[OfficialSource, ...] = (
    OfficialSource(
        "official-white-house-news", OfficialSourceLane.WHITE_HOUSE,
        "https://www.whitehouse.gov/news/", "actor-gov-us-white-house", "actor-gov-us-white-house",
        OfficialSourceType.GOVERNMENT_NEWS_ENTRY, ContentActorMode.ITEM_DECLARED,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-WH-NEWS",),
    ),
    OfficialSource(
        "official-white-house-briefings", OfficialSourceLane.WHITE_HOUSE,
        "https://www.whitehouse.gov/briefings-statements/", "actor-gov-us-white-house", "actor-gov-us-white-house",
        OfficialSourceType.BRIEFINGS_STATEMENTS_INDEX, ContentActorMode.ITEM_DECLARED,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-WH-BRIEFINGS",),
    ),
    OfficialSource(
        "official-white-house-presidential-actions", OfficialSourceLane.WHITE_HOUSE,
        "https://www.whitehouse.gov/presidential-actions/", "actor-gov-us-white-house", "actor-gov-us-white-house",
        OfficialSourceType.PRESIDENTIAL_ACTIONS_INDEX, ContentActorMode.ITEM_DECLARED,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-WH-ACTIONS",),
    ),
    OfficialSource(
        "official-white-house-fact-sheets", OfficialSourceLane.WHITE_HOUSE,
        "https://www.whitehouse.gov/fact-sheets/", "actor-gov-us-white-house", "actor-gov-us-white-house",
        OfficialSourceType.FACT_SHEETS_INDEX, ContentActorMode.ITEM_DECLARED,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-WH-FACT-SHEETS",),
    ),
    OfficialSource(
        "official-us-treasury-press", OfficialSourceLane.US_TREASURY,
        "https://home.treasury.gov/news/press-releases", "actor-gov-us-treasury", "actor-gov-us-treasury",
        OfficialSourceType.AGENCY_PRESS_RELEASE_INDEX, ContentActorMode.ITEM_DECLARED_OR_FIXED_OWNER,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-TREASURY-PRESS",),
    ),
    OfficialSource(
        "official-us-treasury-statements", OfficialSourceLane.US_TREASURY,
        "https://home.treasury.gov/news/press-releases/statements-remarks/", "actor-gov-us-treasury", "actor-gov-us-treasury",
        OfficialSourceType.AGENCY_STATEMENTS_REMARKS_INDEX, ContentActorMode.ITEM_DECLARED_OR_FIXED_OWNER,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-TREASURY-STATEMENTS",),
    ),
    OfficialSource(
        "official-fed-board-news", OfficialSourceLane.FED_BOARD,
        "https://www.federalreserve.gov/newsevents.htm", "actor-gov-us-fed-board", "actor-gov-us-fed-board",
        OfficialSourceType.CENTRAL_BANK_NEWS_ENTRY, ContentActorMode.FED_BOARD_OR_FOMC_FROM_ITEM,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-FED-NEWS",),
    ),
    OfficialSource(
        "official-fed-board-press", OfficialSourceLane.FED_BOARD,
        "https://www.federalreserve.gov/newsevents/pressreleases.htm", "actor-gov-us-fed-board", "actor-gov-us-fed-board",
        OfficialSourceType.CENTRAL_BANK_PRESS_RELEASE_INDEX, ContentActorMode.FED_BOARD_OR_FOMC_FROM_ITEM,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-FED-PRESS",),
    ),
    OfficialSource(
        "official-fed-board-speeches-testimony", OfficialSourceLane.FED_BOARD,
        "https://www.federalreserve.gov/newsevents/speeches-testimony.htm", "actor-gov-us-fed-board", "actor-gov-us-fed-board",
        OfficialSourceType.CENTRAL_BANK_SPEECH_TESTIMONY_INDEX, ContentActorMode.ITEM_DECLARED,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-FED-SPEECHES",),
    ),
    OfficialSource(
        "official-sec-agency-newsroom", OfficialSourceLane.SEC_AGENCY,
        "https://www.sec.gov/newsroom", "actor-gov-us-sec", "actor-gov-us-sec",
        OfficialSourceType.SEC_AGENCY_NEWSROOM_ENTRY, ContentActorMode.SEC_AGENCY_OR_PERSON_FROM_ITEM,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-SEC-NEWSROOM",),
    ),
    OfficialSource(
        "official-sec-agency-press", OfficialSourceLane.SEC_AGENCY,
        "https://www.sec.gov/newsroom/press-releases", "actor-gov-us-sec", "actor-gov-us-sec",
        OfficialSourceType.AGENCY_PRESS_RELEASE_INDEX, ContentActorMode.ITEM_DECLARED_OR_FIXED_OWNER,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-SEC-PRESS",),
    ),
    OfficialSource(
        "official-sec-agency-speeches-statements", OfficialSourceLane.SEC_AGENCY,
        "https://www.sec.gov/newsroom/speeches-statements", "actor-gov-us-sec", "actor-gov-us-sec",
        OfficialSourceType.AGENCY_SPEECH_STATEMENT_INDEX, ContentActorMode.SEC_AGENCY_OR_PERSON_FROM_ITEM,
        POLICY_VALID_FROM, OBSERVED_AT, ("E-SEC-SPEECHES",),
    ),
)


def validate_official_registry(
    actors: tuple[OfficialActor, ...] = OFFICIAL_ACTORS,
    sources: tuple[OfficialSource, ...] = OFFICIAL_SOURCES,
) -> None:
    if len({actor.actor_id for actor in actors}) != len(actors):
        raise ContractViolation("official actor registry contains duplicate actor_id")
    if len({source.source_id for source in sources}) != len(sources):
        raise ContractViolation("official source registry contains duplicate source_id")
    actor_ids = {actor.actor_id for actor in actors}
    for source in sources:
        if source.owner_actor_id not in actor_ids or source.publisher_actor_id not in actor_ids:
            raise ContractViolation("official source registry references an unknown actor")
    if any("edgar" in source.source_id.casefold() for source in sources):
        raise ContractViolation("SEC EDGAR must remain outside the official agency signal registry")


def get_official_actor(actor_id: str) -> OfficialActor:
    matches = [actor for actor in OFFICIAL_ACTORS if actor.actor_id == actor_id]
    if len(matches) != 1:
        raise ContractViolation("official actor lookup is missing or ambiguous")
    return matches[0]


def get_official_source(source_id: str) -> OfficialSource:
    matches = [source for source in OFFICIAL_SOURCES if source.source_id == source_id]
    if len(matches) != 1:
        raise ContractViolation("official source lookup is missing or ambiguous")
    return matches[0]


validate_official_registry()
