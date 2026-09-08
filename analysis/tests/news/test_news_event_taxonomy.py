import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.news import (
    NEWS_EVENT_TAXONOMY_VERSION,
    EventTaxonomyEntry,
    NewsEventType,
    event_taxonomy_entry,
    news_event_taxonomy,
)


def test_taxonomy_version_and_required_core_categories_are_frozen():
    assert NEWS_EVENT_TAXONOMY_VERSION == "news-event-taxonomy-v0.1"
    event_types = {entry.event_type for entry in news_event_taxonomy()}
    assert {
        NewsEventType.CONTRACT,
        NewsEventType.CAPEX,
        NewsEventType.FINANCING,
        NewsEventType.M_AND_A,
        NewsEventType.REGULATION,
        NewsEventType.EARNINGS,
        NewsEventType.PARTNERSHIP,
        NewsEventType.MAJOR_CUSTOMER,
    } <= event_types


def test_every_event_type_is_defined_exactly_once():
    entries = news_event_taxonomy()
    assert len(entries) == len(NewsEventType)
    assert len({entry.event_type for entry in entries}) == len(entries)
    assert {entry.event_type for entry in entries} == set(NewsEventType)


def test_taxonomy_order_is_deterministic_and_immutable():
    first = news_event_taxonomy()
    second = news_event_taxonomy()
    assert first == second
    assert isinstance(first, tuple)
    assert tuple(entry.event_type for entry in first) == tuple(NewsEventType)


def test_contract_and_partnership_boundaries_do_not_collapse():
    contract = event_taxonomy_entry(NewsEventType.CONTRACT)
    partnership = event_taxonomy_entry(NewsEventType.PARTNERSHIP)
    assert "binding" in contract.definition.casefold()
    assert "non-binding" in contract.boundary_note.casefold()
    assert "binding purchase" in partnership.boundary_note.casefold()


def test_capex_and_financing_are_separate_event_types():
    capex = event_taxonomy_entry(NewsEventType.CAPEX)
    financing = event_taxonomy_entry(NewsEventType.FINANCING)
    assert capex.event_type is not financing.event_type
    assert "separate financing event" in capex.boundary_note.casefold()
    assert "capital raising" in financing.definition.casefold()


def test_earnings_taxonomy_delegates_detailed_metric_semantics_to_e0():
    earnings = event_taxonomy_entry(NewsEventType.EARNINGS)
    assert "existing Earnings domain" in earnings.definition
    assert "E0 contracts" in earnings.boundary_note
    assert "GAAP/non-GAAP" in earnings.boundary_note


def test_regulation_and_legal_have_explicit_enforcement_boundary():
    regulation = event_taxonomy_entry(NewsEventType.REGULATION)
    legal = event_taxonomy_entry(NewsEventType.LEGAL)
    assert "enforcement" in regulation.definition.casefold()
    assert "government/regulator enforcement belongs to regulation" in legal.boundary_note.casefold()


def test_major_customer_does_not_accept_provider_tags_as_identity_truth():
    entry = event_taxonomy_entry(NewsEventType.MAJOR_CUSTOMER)
    assert "provider ticker tags" in entry.boundary_note.casefold()
    assert "unnamed demand commentary" in entry.boundary_note.casefold()


def test_entry_rejects_blank_or_invalid_contract_values():
    with pytest.raises(ContractViolation):
        EventTaxonomyEntry(NewsEventType.CONTRACT, "", "boundary")
    with pytest.raises(ContractViolation):
        EventTaxonomyEntry("contract", "definition", "boundary")  # type: ignore[arg-type]


def test_lookup_rejects_non_enum_values():
    with pytest.raises(ContractViolation):
        event_taxonomy_entry("earnings")  # type: ignore[arg-type]
