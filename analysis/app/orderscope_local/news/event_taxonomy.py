"""Versioned News event taxonomy for N1-001.

The taxonomy names event kinds only. It does not contain extraction heuristics,
confidence thresholds, sentiment, impact, or Regime interpretation. One explicit
source assertion maps to one event type; a source establishing multiple events is
split into multiple Fact candidates downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from orderscope_local.contracts import ContractViolation


NEWS_EVENT_TAXONOMY_VERSION = "news-event-taxonomy-v0.1"


class NewsEventType(StrEnum):
    CONTRACT = "contract"
    CAPEX = "capex"
    FINANCING = "financing"
    M_AND_A = "m_and_a"
    REGULATION = "regulation"
    EARNINGS = "earnings"
    PARTNERSHIP = "partnership"
    MAJOR_CUSTOMER = "major_customer"
    PRODUCT_SERVICE = "product_service"
    SUPPLY_CHAIN = "supply_chain"
    LEADERSHIP = "leadership"
    LEGAL = "legal"


@dataclass(frozen=True, slots=True)
class EventTaxonomyEntry:
    event_type: NewsEventType
    definition: str
    boundary_note: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, NewsEventType):
            raise ContractViolation("event taxonomy entry requires a NewsEventType")
        for field, value in (("definition", self.definition), ("boundary_note", self.boundary_note)):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"event taxonomy {field} must be non-blank canonical text")
            if len(value) > 1024:
                raise ContractViolation(f"event taxonomy {field} exceeds 1024 characters")


_EVENT_TAXONOMY = (
    EventTaxonomyEntry(
        NewsEventType.CONTRACT,
        "A binding or explicitly awarded commercial or government agreement for goods or services.",
        "A non-binding memorandum or general collaboration announcement is partnership unless the source explicitly establishes a binding award or contract.",
    ),
    EventTaxonomyEntry(
        NewsEventType.CAPEX,
        "A source-established commitment, plan, or completed action to spend capital on facilities, equipment, infrastructure, or other long-lived productive assets.",
        "Financing used to fund CAPEX is a separate financing event; do not infer CAPEX merely because financing was raised.",
    ),
    EventTaxonomyEntry(
        NewsEventType.FINANCING,
        "Debt, equity, convertible, credit-facility, or other source-established capital raising or refinancing event.",
        "Do not infer financing from cash-balance commentary or from an unexecuted strategic intention without an explicit financing action/proposal.",
    ),
    EventTaxonomyEntry(
        NewsEventType.M_AND_A,
        "Acquisition, merger, divestiture, spin-off, asset purchase/sale, tender, or other source-established change in corporate control or ownership of a business/assets.",
        "Ordinary commercial partnerships and minority strategic cooperation remain partnership unless the source establishes an ownership/control transaction.",
    ),
    EventTaxonomyEntry(
        NewsEventType.REGULATION,
        "A rule, order, license, restriction, approval, investigation, enforcement action, or other formal government/regulator action affecting the subject.",
        "General political commentary or proposals without a formal regulatory action remain outside a regulation Fact unless explicitly represented as a proposal by a later contract.",
    ),
    EventTaxonomyEntry(
        NewsEventType.EARNINGS,
        "An issuer earnings release, earnings result, guidance item, or other source-established fiscal-period result relevant to the existing Earnings domain.",
        "N1 does not redefine GAAP/non-GAAP metrics or release-time semantics; use the accepted E0 contracts and evidence when promoting detailed earnings Facts.",
    ),
    EventTaxonomyEntry(
        NewsEventType.PARTNERSHIP,
        "A source-established collaboration, alliance, joint development, integration, distribution, or strategic cooperation relationship.",
        "A binding purchase/supply award is contract; an ownership/control transaction is M&A. Co-mention alone is never partnership evidence.",
    ),
    EventTaxonomyEntry(
        NewsEventType.MAJOR_CUSTOMER,
        "A source explicitly identifies a material customer relationship, customer win, deployment, purchase, or loss whose customer identity is part of the event.",
        "Provider ticker tags, analyst speculation, or unnamed demand commentary cannot establish a named major-customer event.",
    ),
    EventTaxonomyEntry(
        NewsEventType.PRODUCT_SERVICE,
        "A source-established product or service launch, release, material upgrade, discontinuation, recall, or availability change.",
        "Routine marketing commentary without an explicit product/service action is not an event Fact.",
    ),
    EventTaxonomyEntry(
        NewsEventType.SUPPLY_CHAIN,
        "A source-established supplier, manufacturing, capacity, sourcing, shipment, shortage, allocation, or production disruption/change.",
        "Generic sector shortage commentary is not issuer-specific supply-chain Fact without explicit subject linkage.",
    ),
    EventTaxonomyEntry(
        NewsEventType.LEADERSHIP,
        "A source-established appointment, resignation, removal, succession, or material role change involving directors or senior executives.",
        "Commentary by an executive is not a leadership event unless the role/status itself changes.",
    ),
    EventTaxonomyEntry(
        NewsEventType.LEGAL,
        "A source-established lawsuit, judgment, settlement, material legal claim, or non-regulatory legal proceeding affecting the subject.",
        "Government/regulator enforcement belongs to regulation; ordinary commercial disputes are legal when a formal proceeding or settlement is established.",
    ),
)


def news_event_taxonomy() -> tuple[EventTaxonomyEntry, ...]:
    """Return the immutable v0.1 taxonomy in stable canonical order."""

    _validate_taxonomy(_EVENT_TAXONOMY)
    return _EVENT_TAXONOMY


def event_taxonomy_entry(event_type: NewsEventType) -> EventTaxonomyEntry:
    if not isinstance(event_type, NewsEventType):
        raise ContractViolation("event_type must be a NewsEventType")
    for entry in news_event_taxonomy():
        if entry.event_type is event_type:
            return entry
    raise ContractViolation("event_type is not registered in the active taxonomy")


def _validate_taxonomy(entries: tuple[EventTaxonomyEntry, ...]) -> None:
    if not isinstance(entries, tuple) or not entries:
        raise ContractViolation("event taxonomy must be a non-empty immutable tuple")
    if any(not isinstance(entry, EventTaxonomyEntry) for entry in entries):
        raise ContractViolation("event taxonomy contains an invalid entry")
    event_types = tuple(entry.event_type for entry in entries)
    if len(event_types) != len(set(event_types)):
        raise ContractViolation("event taxonomy cannot contain duplicate event types")
    if set(event_types) != set(NewsEventType):
        raise ContractViolation("event taxonomy must define every NewsEventType exactly once")
