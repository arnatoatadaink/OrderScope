"""Conservative canonical URL and duplicate/syndication rules for N0-003.

The module never merges records by fuzzy similarity. Same provider article IDs use
I0-004 content identity semantics; cross-ID duplicate/syndication decisions use only
explicit deterministic metadata rules and remain auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from orderscope_local.contracts import (
    AdapterItem,
    ContractViolation,
    IdempotencyClassification,
    RevisionRelationship,
    SourceTimestamp,
    classify_adapter_item,
)


_TRACKING_QUERY_NAMES = {"fbclid", "gclid", "dclid", "msclkid"}
_SPACE = re.compile(r"\s+")


class NewsArticleComparisonKind(StrEnum):
    PROVIDER_DUPLICATE = "provider_duplicate"
    UPDATED_ARTICLE = "updated_article"
    PROVIDER_CONFLICT = "provider_conflict"
    CANONICAL_URL_DUPLICATE = "canonical_url_duplicate"
    SYNDICATION_CANDIDATE = "syndication_candidate"
    DISTINCT = "distinct"


@dataclass(frozen=True, slots=True)
class NewsArticleComparison:
    kind: NewsArticleComparisonKind
    same_article: bool
    same_story_candidate: bool
    canonical_url: str | None
    reason: str
    revision_relationship: RevisionRelationship | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, NewsArticleComparisonKind):
            raise ContractViolation("news comparison kind is invalid")
        if not isinstance(self.same_article, bool) or not isinstance(self.same_story_candidate, bool):
            raise ContractViolation("news comparison booleans are invalid")
        if self.canonical_url is not None and not isinstance(self.canonical_url, str):
            raise ContractViolation("news canonical_url must be text when present")
        if not isinstance(self.reason, str) or not self.reason.strip() or self.reason != self.reason.strip() or len(self.reason) > 512:
            raise ContractViolation("news comparison reason must be bounded canonical text")
        if self.kind is NewsArticleComparisonKind.UPDATED_ARTICLE and self.revision_relationship is None:
            raise ContractViolation("updated article requires an explicit revision relationship")
        if self.kind is not NewsArticleComparisonKind.UPDATED_ARTICLE and self.revision_relationship is not None:
            raise ContractViolation("revision relationship is only valid for updated article")


def canonicalize_news_url(url: str | None) -> str | None:
    """Return a conservative canonical form without deleting semantic query params.

    Only fragments and well-known tracking parameters are removed. Other query
    parameters remain and are sorted deterministically. Scheme/host case and default
    ports are normalized; path spelling is otherwise preserved.
    """

    if url is None:
        return None
    if not isinstance(url, str) or not url.strip() or url != url.strip() or len(url) > 2048:
        raise ContractViolation("news URL must be bounded non-blank text")
    parsed = urlsplit(url)
    scheme = parsed.scheme.casefold()
    if scheme not in {"http", "https"}:
        raise ContractViolation("news URL must use http or https")
    if not parsed.hostname:
        raise ContractViolation("news URL requires a hostname")
    host = parsed.hostname.casefold()
    try:
        port = parsed.port
    except ValueError as exc:
        raise ContractViolation("news URL port is invalid") from exc
    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        key_fold = key.casefold()
        if key_fold.startswith("utm_") or key_fold in _TRACKING_QUERY_NAMES:
            continue
        query_items.append((key, value))
    query_items.sort()
    path = parsed.path or "/"
    return urlunsplit((scheme, host, path, urlencode(query_items, doseq=True), ""))


def compare_news_articles(accepted: AdapterItem, candidate: AdapterItem) -> NewsArticleComparison:
    """Classify two normalized News items with explainable, fail-closed rules."""

    _validate_news_item(accepted)
    _validate_news_item(candidate)

    if accepted.content_identity.identity == candidate.content_identity.identity:
        return _compare_same_provider_identity(accepted, candidate)

    accepted_url = canonicalize_news_url(_url(accepted))
    candidate_url = canonicalize_news_url(_url(candidate))
    if accepted_url is not None and accepted_url == candidate_url:
        return NewsArticleComparison(
            kind=NewsArticleComparisonKind.CANONICAL_URL_DUPLICATE,
            same_article=True,
            same_story_candidate=True,
            canonical_url=accepted_url,
            reason="different provider article IDs resolve to the same conservative canonical URL",
        )

    if _syndication_fingerprint_matches(accepted, candidate):
        return NewsArticleComparison(
            kind=NewsArticleComparisonKind.SYNDICATION_CANDIDATE,
            same_article=False,
            same_story_candidate=True,
            canonical_url=None,
            reason="distinct article IDs/URLs have exact normalized headline and near publication time from different publishers",
        )

    return NewsArticleComparison(
        kind=NewsArticleComparisonKind.DISTINCT,
        same_article=False,
        same_story_candidate=False,
        canonical_url=None,
        reason="no stable-identity, canonical-URL, or conservative syndication match",
    )


def _compare_same_provider_identity(accepted: AdapterItem, candidate: AdapterItem) -> NewsArticleComparison:
    base = classify_adapter_item(candidate, accepted.content_identity)
    canonical = canonicalize_news_url(_url(candidate))
    if base is IdempotencyClassification.DUPLICATE:
        return NewsArticleComparison(
            kind=NewsArticleComparisonKind.PROVIDER_DUPLICATE,
            same_article=True,
            same_story_candidate=True,
            canonical_url=canonical,
            reason="same provider article ID and same normalized metadata hash",
        )
    if base is not IdempotencyClassification.CONFLICT:
        raise ContractViolation("unexpected same-identity idempotency result")

    accepted_updated = _updated_instant(accepted)
    candidate_updated = _updated_instant(candidate)
    if accepted_updated is not None and candidate_updated is not None and candidate_updated > accepted_updated:
        relationship = RevisionRelationship(accepted.content_identity, candidate.content_identity)
        classified = classify_adapter_item(
            candidate,
            accepted.content_identity,
            revision_relationship=relationship,
        )
        if classified is not IdempotencyClassification.UPDATE:
            raise ContractViolation("explicit news revision did not classify as update")
        return NewsArticleComparison(
            kind=NewsArticleComparisonKind.UPDATED_ARTICLE,
            same_article=True,
            same_story_candidate=True,
            canonical_url=canonical,
            reason="same provider article ID changed with a strictly newer provider updated timestamp",
            revision_relationship=relationship,
        )

    return NewsArticleComparison(
        kind=NewsArticleComparisonKind.PROVIDER_CONFLICT,
        same_article=True,
        same_story_candidate=True,
        canonical_url=canonical,
        reason="same provider article ID changed without a strictly newer provider updated timestamp",
    )


def _syndication_fingerprint_matches(left: AdapterItem, right: AdapterItem) -> bool:
    if _publisher(left).casefold() == _publisher(right).casefold():
        return False
    if _headline_key(left) != _headline_key(right):
        return False
    left_time = _published_instant(left)
    right_time = _published_instant(right)
    return abs(left_time - right_time) <= timedelta(minutes=15)


def _validate_news_item(item: AdapterItem) -> None:
    if not isinstance(item, AdapterItem):
        raise ContractViolation("news comparison requires AdapterItem")
    normalized = item.normalized
    for key in ("provider_key", "provider_article_id", "headline", "publisher", "published_at"):
        if key not in normalized:
            raise ContractViolation(f"news comparison item missing {key}")
    if not isinstance(normalized["published_at"], SourceTimestamp) or normalized["published_at"].instant is None:
        raise ContractViolation("news comparison requires instant published_at")
    updated = normalized.get("provider_updated_at")
    if updated is not None and (not isinstance(updated, SourceTimestamp) or updated.instant is None):
        raise ContractViolation("news provider_updated_at must be an instant when present")


def _url(item: AdapterItem) -> str | None:
    value = item.normalized.get("article_url")
    if value is not None and not isinstance(value, str):
        raise ContractViolation("news article_url must be text when present")
    return value


def _publisher(item: AdapterItem) -> str:
    value = item.normalized["publisher"]
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation("news publisher must be non-blank text")
    return value


def _headline_key(item: AdapterItem) -> str:
    value = item.normalized["headline"]
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation("news headline must be non-blank text")
    return _SPACE.sub(" ", value.strip()).casefold()


def _published_instant(item: AdapterItem):
    value = item.normalized["published_at"]
    assert isinstance(value, SourceTimestamp) and value.instant is not None
    return value.instant


def _updated_instant(item: AdapterItem):
    value = item.normalized.get("provider_updated_at")
    if value is None:
        return None
    assert isinstance(value, SourceTimestamp) and value.instant is not None
    return value.instant
