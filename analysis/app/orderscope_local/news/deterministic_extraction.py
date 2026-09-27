"""Deterministic headline/metadata News Fact extraction for N1-002.

This baseline deliberately uses only explicit headline/metadata language. It does
not inspect temporary article bodies, use an LLM, infer missing values, or convert
provider ticker tags into corporate identity. One matched source assertion emits
one versioned Fact with reciprocal Evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import re

from orderscope_local.contracts import (
    ContentHash,
    ContentIdentity,
    ContractViolation,
    Evidence,
    EvidenceKind,
    EvidenceQuality,
    Fact,
    FactAssertionKind,
    Provenance,
    RetentionClass,
    SourceReference,
)

from .alpaca import ALPACA_NEWS_PROVIDER_KEY, NewsArticleMetadata
from .event_taxonomy import NEWS_EVENT_TAXONOMY_VERSION, NewsEventType


NEWS_DETERMINISTIC_EXTRACTOR_VERSION = "news-deterministic-extractor-v0.1"
NEWS_EVENT_FACT_SCHEMA_VERSION = "news-event-fact-v0.1"
NEWS_EVENT_EVIDENCE_SCHEMA_VERSION = "news-event-evidence-v0.1"


@dataclass(frozen=True, slots=True)
class HeadlinePattern:
    pattern_id: str
    event_type: NewsEventType
    expression: re.Pattern[str]

    def __post_init__(self) -> None:
        if not isinstance(self.pattern_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,127}", self.pattern_id):
            raise ContractViolation("headline pattern_id must be a bounded canonical identifier")
        if not isinstance(self.event_type, NewsEventType):
            raise ContractViolation("headline pattern requires a NewsEventType")
        if not isinstance(self.expression, re.Pattern):
            raise ContractViolation("headline expression must be a compiled regex")


_PATTERNS = (
    HeadlinePattern("contract.award.v1", NewsEventType.CONTRACT, re.compile(r"\b(?:wins?|awarded?|secures?|signs?)\b.{0,80}\b(?:contract|order|deal|agreement)\b", re.I)),
    HeadlinePattern("capex.invest.v1", NewsEventType.CAPEX, re.compile(r"\b(?:invests?|to invest|plans? to invest|spend|spending)\b.{0,80}\b(?:plant|fab|factory|facility|data center|infrastructure|capacity|equipment)\b", re.I)),
    HeadlinePattern("financing.raise.v1", NewsEventType.FINANCING, re.compile(r"\b(?:raises?|prices?|launches?|issues?|offers?)\b.{0,80}\b(?:debt|notes?|bonds?|shares?|equity|convertible|credit facility|financing|offering)\b", re.I)),
    HeadlinePattern("mna.transaction.v1", NewsEventType.M_AND_A, re.compile(r"\b(?:acquires?|acquisition|merges?|merger|buys?|purchase of|sells?|sale of|divests?|spin[- ]?off|tender offer)\b", re.I)),
    HeadlinePattern("regulation.action.v1", NewsEventType.REGULATION, re.compile(r"\b(?:SEC|FTC|DOJ|regulator|government|commission|agency)\b.{0,100}\b(?:approves?|approval|investigates?|investigation|charges?|enforcement|rule|orders?|license|restricts?|ban)\b", re.I)),
    HeadlinePattern("earnings.result.v1", NewsEventType.EARNINGS, re.compile(r"\b(?:reports?|posts?|announces?)\b.{0,60}\b(?:quarterly|quarter|earnings|revenue|EPS|results?)\b", re.I)),
    HeadlinePattern("partnership.collaboration.v1", NewsEventType.PARTNERSHIP, re.compile(r"\b(?:partners? with|partnership|collaborates? with|collaboration|alliance|joint development|teams? up with|integration with)\b", re.I)),
    HeadlinePattern("major_customer.named.v1", NewsEventType.MAJOR_CUSTOMER, re.compile(r"\b(?:customer|client)\b.{0,60}\b(?:selects?|chooses?|deploys?|orders?|purchases?|adopts?)\b", re.I)),
    HeadlinePattern("product.launch.v1", NewsEventType.PRODUCT_SERVICE, re.compile(r"\b(?:launches?|releases?|unveils?|introduces?|announces availability of|recalls?|discontinues?)\b.{0,100}\b(?:product|service|platform|chip|GPU|processor|software|system)\b", re.I)),
    HeadlinePattern("supply_chain.change.v1", NewsEventType.SUPPLY_CHAIN, re.compile(r"\b(?:supplier|supply|production|manufacturing|shipment|shortage|capacity)\b.{0,80}\b(?:halts?|cuts?|expands?|resumes?|delays?|disrupts?|shortage|allocation|increase|decrease)\b", re.I)),
    HeadlinePattern("leadership.change.v1", NewsEventType.LEADERSHIP, re.compile(r"\b(?:appoints?|names?|hires?|resigns?|retires?|steps down|removes?|succeeds?)\b.{0,80}\b(?:CEO|CFO|CTO|president|chair|director|executive)\b", re.I)),
    HeadlinePattern("legal.proceeding.v1", NewsEventType.LEGAL, re.compile(r"\b(?:sues?|lawsuit|settles?|settlement|judgment|court|litigation)\b", re.I)),
)


@dataclass(frozen=True, slots=True)
class NewsFactCandidate:
    fact: Fact
    evidence: Evidence
    event_type: NewsEventType
    pattern_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.fact, Fact) or not isinstance(self.evidence, Evidence):
            raise ContractViolation("news candidate requires Fact and Evidence")
        if not isinstance(self.event_type, NewsEventType):
            raise ContractViolation("news candidate event_type is invalid")
        if self.fact.evidence_record_ids != (self.evidence.record_id,):
            raise ContractViolation("news candidate Fact/Evidence link is not reciprocal")
        if self.evidence.target_record_ids != (self.fact.record_id,):
            raise ContractViolation("news candidate Evidence/Fact link is not reciprocal")


def headline_patterns() -> tuple[HeadlinePattern, ...]:
    return _PATTERNS


def extract_headline_fact_candidates(
    *,
    metadata: NewsArticleMetadata,
    content_identity: ContentIdentity,
    subject_ref: str,
    retrieved_at: datetime,
    accepted_at: datetime,
) -> tuple[NewsFactCandidate, ...]:
    """Extract explicit headline event assertions into deterministic Fact candidates.

    Missing amounts, counterparties, event dates, accounting basis, and other
    details remain absent. Provider symbol tags never determine ``subject_ref``;
    the caller must supply a registry-resolved subject explicitly.
    """

    _validate_inputs(metadata, content_identity, subject_ref, retrieved_at, accepted_at)
    matches = [pattern for pattern in _PATTERNS if pattern.expression.search(metadata.headline)]
    candidates = tuple(
        _build_candidate(
            metadata=metadata,
            content_identity=content_identity,
            subject_ref=subject_ref,
            retrieved_at=retrieved_at,
            accepted_at=accepted_at,
            pattern=pattern,
        )
        for pattern in matches
    )
    return candidates


def _build_candidate(
    *,
    metadata: NewsArticleMetadata,
    content_identity: ContentIdentity,
    subject_ref: str,
    retrieved_at: datetime,
    accepted_at: datetime,
    pattern: HeadlinePattern,
) -> NewsFactCandidate:
    suffix = hashlib.sha256(
        f"{metadata.provider_article_id}|{pattern.pattern_id}|{subject_ref}".encode("utf-8")
    ).hexdigest()[:20]
    fact_id = f"news-fact-{suffix}"
    evidence_id = f"news-evidence-{suffix}"
    locator = metadata.article_url or f"{ALPACA_NEWS_PROVIDER_KEY}:article:{metadata.provider_article_id}"
    provenance = Provenance(
        source_ref=SourceReference(locator),
        content_hash=content_identity.content_hash,
        retrieved_at=retrieved_at,
        available_at=retrieved_at,
        accepted_at=accepted_at,
        published_at=metadata.published_at,
    )
    value = {
        "taxonomy_version": NEWS_EVENT_TAXONOMY_VERSION,
        "event_type": pattern.event_type.value,
        "extractor_version": NEWS_DETERMINISTIC_EXTRACTOR_VERSION,
        "pattern_id": pattern.pattern_id,
        "provider_key": metadata.provider_key,
        "provider_article_id": metadata.provider_article_id,
        "headline": metadata.headline,
    }
    fact = Fact(
        record_id=fact_id,
        schema_version=NEWS_EVENT_FACT_SCHEMA_VERSION,
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=accepted_at,
        provenance=provenance,
        fact_type=f"news.event.{pattern.event_type.value}",
        value=value,
        assertion_kind=FactAssertionKind.OBSERVATION,
        evidence_record_ids=(evidence_id,),
        extraction_confidence=1.0,
    )
    evidence = Evidence(
        record_id=evidence_id,
        schema_version=NEWS_EVENT_EVIDENCE_SCHEMA_VERSION,
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=accepted_at,
        provenance=provenance,
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(fact_id,),
        locator=locator,
        quality_class=EvidenceQuality.PROVIDER,
        retention_class=RetentionClass.DURABLE_METADATA,
        excerpt_hash=ContentHash(hashlib.sha256(metadata.headline.encode("utf-8")).hexdigest()),
    )
    return NewsFactCandidate(fact=fact, evidence=evidence, event_type=pattern.event_type, pattern_id=pattern.pattern_id)


def _validate_inputs(
    metadata: NewsArticleMetadata,
    content_identity: ContentIdentity,
    subject_ref: str,
    retrieved_at: datetime,
    accepted_at: datetime,
) -> None:
    if not isinstance(metadata, NewsArticleMetadata):
        raise ContractViolation("metadata must be NewsArticleMetadata")
    if not isinstance(content_identity, ContentIdentity):
        raise ContractViolation("content_identity must be ContentIdentity")
    identity = content_identity.identity
    if identity.provider_key != metadata.provider_key or identity.value != metadata.provider_article_id:
        raise ContractViolation("content identity must belong to the supplied News article")
    if not isinstance(subject_ref, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,255}", subject_ref):
        raise ContractViolation("subject_ref must be a registry-resolved bounded identifier")
    for field, value in (("retrieved_at", retrieved_at), ("accepted_at", accepted_at)):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ContractViolation(f"{field} must be normalized to UTC")
    if retrieved_at > accepted_at:
        raise ContractViolation("retrieved_at cannot be later than accepted_at")
