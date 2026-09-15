from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import AdapterItem, ContentHash, ContentIdentity, ContractViolation, SourceTimestamp, StableIdentity
from orderscope_local.news import NewsArticleComparisonKind, canonicalize_news_url, compare_news_articles

UTC = timezone.utc
PUBLISHED = SourceTimestamp.at(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))
UPDATED = SourceTimestamp.at(datetime(2026, 9, 1, 12, 1, tzinfo=UTC))


def _item(
    *,
    article_id="1",
    digest="a" * 64,
    url="https://Example.com:443/story?id=7&utm_source=x#frag",
    headline="AMD Announces New Partnership",
    publisher="benzinga",
    published=PUBLISHED,
    updated=UPDATED,
):
    return AdapterItem(
        normalized={
            "provider_key": "alpaca-news",
            "provider_article_id": article_id,
            "headline": headline,
            "publisher": publisher,
            "article_url": url,
            "published_at": published,
            "provider_updated_at": updated,
        },
        content_identity=ContentIdentity(
            StableIdentity.provider_article("alpaca-news", article_id),
            ContentHash(digest),
        ),
    )


def test_canonicalize_url_is_conservative_and_deterministic():
    first = canonicalize_news_url("HTTPS://Example.COM:443/path?b=2&utm_source=x&a=1#section")
    second = canonicalize_news_url("https://example.com/path?a=1&b=2")

    assert first == "https://example.com/path?a=1&b=2"
    assert first == second


def test_semantic_query_params_are_retained():
    assert canonicalize_news_url("https://example.com/story?id=7&utm_medium=email") == "https://example.com/story?id=7"
    assert canonicalize_news_url("https://example.com/story?id=8") != "https://example.com/story?id=7"


def test_same_provider_id_and_hash_is_provider_duplicate():
    accepted = _item()
    candidate = _item()

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.PROVIDER_DUPLICATE
    assert result.same_article is True
    assert result.revision_relationship is None


def test_same_provider_id_with_newer_updated_timestamp_is_update():
    accepted = _item(digest="a" * 64, updated=SourceTimestamp.at(datetime(2026, 9, 1, 12, 1, tzinfo=UTC)))
    candidate = _item(digest="b" * 64, updated=SourceTimestamp.at(datetime(2026, 9, 1, 12, 5, tzinfo=UTC)))

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.UPDATED_ARTICLE
    assert result.same_article is True
    assert result.revision_relationship is not None


def test_same_provider_id_changed_without_newer_updated_timestamp_is_conflict():
    accepted = _item(digest="a" * 64)
    candidate = _item(digest="b" * 64)

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.PROVIDER_CONFLICT
    assert result.same_article is True


def test_different_provider_ids_same_canonical_url_are_same_article():
    accepted = _item(article_id="1", digest="a" * 64, url="https://example.com/story?id=7&utm_source=x")
    candidate = _item(article_id="2", digest="b" * 64, url="https://EXAMPLE.com:443/story?utm_campaign=y&id=7#top")

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.CANONICAL_URL_DUPLICATE
    assert result.same_article is True
    assert result.canonical_url == "https://example.com/story?id=7"


def test_exact_headline_near_time_different_publishers_is_syndication_candidate_not_merge():
    accepted = _item(article_id="1", url="https://wire-a.example/story", publisher="wire-a")
    candidate = _item(
        article_id="2",
        digest="b" * 64,
        url="https://wire-b.example/story",
        headline="  amd announces   new partnership ",
        publisher="wire-b",
        published=SourceTimestamp.at(datetime(2026, 9, 1, 12, 10, tzinfo=UTC)),
    )

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.SYNDICATION_CANDIDATE
    assert result.same_article is False
    assert result.same_story_candidate is True


def test_same_headline_same_publisher_is_not_syndication():
    accepted = _item(article_id="1", url="https://example.com/a")
    candidate = _item(article_id="2", digest="b" * 64, url="https://example.com/b")

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.DISTINCT


def test_same_headline_outside_time_window_is_distinct():
    accepted = _item(article_id="1", url="https://wire-a.example/a", publisher="wire-a")
    candidate = _item(
        article_id="2",
        digest="b" * 64,
        url="https://wire-b.example/b",
        publisher="wire-b",
        published=SourceTimestamp.at(datetime(2026, 9, 1, 12, 16, tzinfo=UTC)),
    )

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.DISTINCT


def test_missing_urls_do_not_force_duplicate_or_syndication_without_fingerprint():
    accepted = _item(article_id="1", url=None, headline="AMD item A")
    candidate = _item(article_id="2", digest="b" * 64, url=None, headline="AMD item B")

    result = compare_news_articles(accepted, candidate)

    assert result.kind is NewsArticleComparisonKind.DISTINCT


def test_non_http_url_is_rejected():
    with pytest.raises(ContractViolation):
        canonicalize_news_url("javascript:alert(1)")
