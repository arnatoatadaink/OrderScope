from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContentIdentity,
    ContractViolation,
    StableIdentity,
    SourceTimestamp,
    validate_fact_store,
)
from orderscope_local.news import (
    ALPACA_NEWS_PROVIDER_KEY,
    NEWS_DETERMINISTIC_EXTRACTOR_VERSION,
    NEWS_EVENT_TAXONOMY_VERSION,
    NewsArticleMetadata,
    NewsEventType,
    extract_headline_fact_candidates,
    headline_patterns,
)

UTC = timezone.utc
PUBLISHED = datetime(2026, 9, 9, 1, 0, tzinfo=UTC)
RETRIEVED = datetime(2026, 9, 9, 1, 1, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 9, 1, 2, tzinfo=UTC)
SUBJECT = "us-sec-0000002488-common"


def _metadata(headline: str, *, article_id: str = "123", symbols=("AMD",), url="https://example.com/news/123"):
    return NewsArticleMetadata(
        provider_key=ALPACA_NEWS_PROVIDER_KEY,
        provider_article_id=article_id,
        query_symbol="AMD",
        headline=headline,
        publisher="benzinga",
        article_url=url,
        published_at=SourceTimestamp.at(PUBLISHED),
        provider_updated_at=SourceTimestamp.at(PUBLISHED),
        author=None,
        summary=None,
        provider_symbols=tuple(symbols),
        body_capability=True,
    )


def _identity(article_id: str = "123", digest: str = "a" * 64):
    return ContentIdentity(
        StableIdentity.provider_article(ALPACA_NEWS_PROVIDER_KEY, article_id),
        ContentHash(digest),
    )


def _extract(headline: str, **kwargs):
    metadata = _metadata(headline, **kwargs)
    return extract_headline_fact_candidates(
        metadata=metadata,
        content_identity=_identity(metadata.provider_article_id),
        subject_ref=SUBJECT,
        retrieved_at=RETRIEVED,
        accepted_at=ACCEPTED,
    )


def test_pattern_registry_is_immutable_and_covers_every_event_type():
    patterns = headline_patterns()
    assert isinstance(patterns, tuple)
    assert {item.event_type for item in patterns} == set(NewsEventType)
    assert len({item.pattern_id for item in patterns}) == len(patterns)


def test_contract_headline_generates_reciprocal_fact_and_evidence():
    candidates = _extract("AMD wins government contract for accelerator systems")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.event_type is NewsEventType.CONTRACT
    assert candidate.fact.value["taxonomy_version"] == NEWS_EVENT_TAXONOMY_VERSION
    assert candidate.fact.value["extractor_version"] == NEWS_DETERMINISTIC_EXTRACTOR_VERSION
    assert candidate.fact.value["headline"] == "AMD wins government contract for accelerator systems"
    validate_fact_store((candidate.fact, candidate.evidence))


def test_financing_and_capex_are_emitted_as_separate_assertions_when_both_explicit():
    candidates = _extract(
        "AMD raises debt financing and plans to invest in a new data center facility"
    )
    assert {item.event_type for item in candidates} == {
        NewsEventType.FINANCING,
        NewsEventType.CAPEX,
    }
    assert len(candidates) == 2


def test_absent_amount_counterparty_and_event_date_are_not_invented():
    candidate = _extract("AMD wins contract for accelerator systems")[0]
    value = candidate.fact.value
    assert "amount" not in value
    assert "counterparty" not in value
    assert "event_date" not in value
    assert candidate.fact.period_start is None
    assert candidate.fact.period_end is None


def test_provider_symbol_tags_do_not_change_registry_resolved_subject():
    metadata = _metadata(
        "AMD wins contract for accelerator systems",
        symbols=("NVDA",),
    )
    candidate = extract_headline_fact_candidates(
        metadata=metadata,
        content_identity=_identity(),
        subject_ref=SUBJECT,
        retrieved_at=RETRIEVED,
        accepted_at=ACCEPTED,
    )[0]
    assert candidate.fact.subject_ref == SUBJECT
    assert "provider_symbols" not in candidate.fact.value


def test_unknown_or_speculative_headline_emits_no_fact():
    assert _extract("Analyst says AMD could benefit from future AI demand") == ()


def test_partnership_is_not_promoted_to_contract():
    candidates = _extract("AMD partners with ExampleCo on joint development")
    assert [item.event_type for item in candidates] == [NewsEventType.PARTNERSHIP]


def test_regulatory_action_and_private_lawsuit_are_distinct():
    regulatory = _extract("FTC investigates AMD over competition practices")
    legal = _extract("ExampleCo sues AMD in contract lawsuit")
    assert [item.event_type for item in regulatory] == [NewsEventType.REGULATION]
    assert NewsEventType.LEGAL in {item.event_type for item in legal}
    assert NewsEventType.REGULATION not in {item.event_type for item in legal}


def test_earnings_headline_only_creates_event_category_not_financial_values():
    candidate = _extract("AMD reports quarterly earnings results")[0]
    assert candidate.event_type is NewsEventType.EARNINGS
    assert "revenue" not in candidate.fact.value
    assert "eps" not in candidate.fact.value
    assert "gaap" not in candidate.fact.value


def test_missing_url_uses_provider_article_locator_without_body_or_secret():
    metadata = _metadata("AMD wins contract for accelerator systems", url=None)
    candidate = extract_headline_fact_candidates(
        metadata=metadata,
        content_identity=_identity(),
        subject_ref=SUBJECT,
        retrieved_at=RETRIEVED,
        accepted_at=ACCEPTED,
    )[0]
    assert candidate.evidence.locator == "alpaca-news:article:123"
    assert candidate.evidence.retention_class.value == "durable_metadata"


def test_identical_input_reproduces_identical_fact_and_evidence_ids():
    first = _extract("AMD wins contract for accelerator systems")[0]
    second = _extract("AMD wins contract for accelerator systems")[0]
    assert first.fact.record_id == second.fact.record_id
    assert first.evidence.record_id == second.evidence.record_id


def test_content_identity_must_match_article_and_time_order_must_be_valid():
    metadata = _metadata("AMD wins contract for accelerator systems")
    wrong_identity = _identity(article_id="999")
    with pytest.raises(ContractViolation):
        extract_headline_fact_candidates(
            metadata=metadata,
            content_identity=wrong_identity,
            subject_ref=SUBJECT,
            retrieved_at=RETRIEVED,
            accepted_at=ACCEPTED,
        )
    with pytest.raises(ContractViolation):
        extract_headline_fact_candidates(
            metadata=metadata,
            content_identity=_identity(),
            subject_ref=SUBJECT,
            retrieved_at=ACCEPTED,
            accepted_at=RETRIEVED,
        )
