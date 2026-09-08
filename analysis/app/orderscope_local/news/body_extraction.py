"""Temporary-body News extraction boundary for N1-003.

Only an injected reader may resolve an Accepted TemporaryContent reference into
raw article text. The body is checked against the N0-004 acquisition hash,
matched with the deterministic N1-002 pattern registry, and discarded from the
returned durable records. Durable output stores extractor identity, confidence,
source reference, evidence span offsets, and excerpt hash only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import re
from typing import Protocol

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
    TemporaryContent,
    TemporaryContentState,
)

from .alpaca import ALPACA_NEWS_PROVIDER_KEY, NewsArticleMetadata
from .body import NewsBodyAcquisition
from .deterministic_extraction import headline_patterns
from .event_taxonomy import NEWS_EVENT_TAXONOMY_VERSION, NewsEventType


NEWS_BODY_EXTRACTOR_NAME = "orderscope-deterministic-body"
NEWS_BODY_EXTRACTOR_VERSION = "news-body-deterministic-v0.1"
NEWS_BODY_FACT_SCHEMA_VERSION = "news-body-event-fact-v0.1"
NEWS_BODY_EVIDENCE_SCHEMA_VERSION = "news-body-event-evidence-v0.1"


class TemporaryBodyReader(Protocol):
    """Read raw body text by opaque temporary content reference."""

    def read(self, *, content_ref: str) -> str: ...


@dataclass(frozen=True, slots=True)
class BodyEvidenceSpan:
    start: int
    end: int
    excerpt_hash: ContentHash

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or isinstance(self.start, bool) or self.start < 0:
            raise ContractViolation("body evidence span start must be a non-negative integer")
        if not isinstance(self.end, int) or isinstance(self.end, bool) or self.end <= self.start:
            raise ContractViolation("body evidence span end must be greater than start")
        if not isinstance(self.excerpt_hash, ContentHash):
            raise ContractViolation("body evidence span requires ContentHash")


@dataclass(frozen=True, slots=True)
class BodyFactCandidate:
    fact: Fact
    evidence: Evidence
    event_type: NewsEventType
    pattern_id: str
    extractor_name: str
    extractor_version: str
    confidence: float
    source_ref: SourceReference
    evidence_span: BodyEvidenceSpan

    def __post_init__(self) -> None:
        if not isinstance(self.fact, Fact) or not isinstance(self.evidence, Evidence):
            raise ContractViolation("body candidate requires Fact and Evidence")
        if not isinstance(self.event_type, NewsEventType):
            raise ContractViolation("body candidate event_type is invalid")
        for field, value in (
            ("pattern_id", self.pattern_id),
            ("extractor_name", self.extractor_name),
            ("extractor_version", self.extractor_version),
        ):
            if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,255}", value):
                raise ContractViolation(f"body candidate {field} must be a bounded identifier")
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool) or not 0 <= self.confidence <= 1:
            raise ContractViolation("body candidate confidence must be between zero and one")
        if not isinstance(self.source_ref, SourceReference):
            raise ContractViolation("body candidate source_ref must be SourceReference")
        if not isinstance(self.evidence_span, BodyEvidenceSpan):
            raise ContractViolation("body candidate evidence_span is invalid")
        if self.fact.evidence_record_ids != (self.evidence.record_id,):
            raise ContractViolation("body candidate Fact/Evidence link is not reciprocal")
        if self.evidence.target_record_ids != (self.fact.record_id,):
            raise ContractViolation("body candidate Evidence/Fact link is not reciprocal")
        if self.fact.extraction_confidence != float(self.confidence):
            raise ContractViolation("body candidate Fact confidence must match extraction confidence")
        if self.evidence.excerpt_hash != self.evidence_span.excerpt_hash:
            raise ContractViolation("body candidate Evidence hash must match span hash")


@dataclass(frozen=True, slots=True)
class BodyExtractionBatch:
    candidates: tuple[BodyFactCandidate, ...]
    completed_content: TemporaryContent

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple):
            raise ContractViolation("body extraction candidates must be an immutable tuple")
        if any(not isinstance(candidate, BodyFactCandidate) for candidate in self.candidates):
            raise ContractViolation("body extraction candidates contain an invalid item")
        if not isinstance(self.completed_content, TemporaryContent):
            raise ContractViolation("body extraction requires completed TemporaryContent")
        if self.completed_content.state is not TemporaryContentState.EXTRACTION_SUCCEEDED:
            raise ContractViolation("body extraction must return extraction_succeeded content state")


def extract_body_fact_candidates(
    *,
    metadata: NewsArticleMetadata,
    content_identity: ContentIdentity,
    acquisition: NewsBodyAcquisition,
    reader: TemporaryBodyReader,
    subject_ref: str,
    extracted_at: datetime,
    accepted_at: datetime,
    confidence: float = 1.0,
) -> BodyExtractionBatch:
    """Read one staged body and emit deterministic Fact/Evidence candidates.

    The raw body is local to this call. Returned records contain only explicit
    event type, pattern/extractor versions, source reference, character offsets,
    and hashes. No LLM/model path exists in this contract.
    """

    _validate_inputs(
        metadata=metadata,
        content_identity=content_identity,
        acquisition=acquisition,
        subject_ref=subject_ref,
        extracted_at=extracted_at,
        accepted_at=accepted_at,
        confidence=confidence,
    )

    try:
        body = reader.read(content_ref=acquisition.temporary_content.content_ref)
    except Exception as exc:
        raise ContractViolation("temporary body read failed") from exc
    if not isinstance(body, str) or not body.strip():
        raise ContractViolation("temporary body reader returned no usable text")
    body_bytes = body.encode("utf-8")
    actual_hash = ContentHash(hashlib.sha256(body_bytes).hexdigest())
    if actual_hash != acquisition.content_hash:
        raise ContractViolation("temporary body hash does not match N0-004 acquisition hash")

    source_ref = SourceReference(
        metadata.article_url or f"{ALPACA_NEWS_PROVIDER_KEY}:article:{metadata.provider_article_id}"
    )
    matches: list[tuple[object, re.Match[str]]] = []
    for pattern in headline_patterns():
        match = pattern.expression.search(body)
        if match is not None:
            matches.append((pattern, match))

    candidates = tuple(
        _build_candidate(
            metadata=metadata,
            acquisition=acquisition,
            subject_ref=subject_ref,
            extracted_at=extracted_at,
            accepted_at=accepted_at,
            confidence=float(confidence),
            source_ref=source_ref,
            pattern=pattern,
            match=match,
        )
        for pattern, match in matches
    )
    completed = TemporaryContent(
        content_ref=acquisition.temporary_content.content_ref,
        retention_class=RetentionClass.TEMPORARY_SUCCESS,
        captured_at=acquisition.temporary_content.captured_at,
        expires_at=acquisition.temporary_content.expires_at,
        state=TemporaryContentState.EXTRACTION_SUCCEEDED,
        extraction_completed_at=extracted_at,
    )
    return BodyExtractionBatch(candidates=candidates, completed_content=completed)


def _build_candidate(
    *,
    metadata: NewsArticleMetadata,
    acquisition: NewsBodyAcquisition,
    subject_ref: str,
    extracted_at: datetime,
    accepted_at: datetime,
    confidence: float,
    source_ref: SourceReference,
    pattern: object,
    match: re.Match[str],
) -> BodyFactCandidate:
    pattern_id = pattern.pattern_id
    event_type = pattern.event_type
    span_text = match.group(0)
    span_hash = ContentHash(hashlib.sha256(span_text.encode("utf-8")).hexdigest())
    span = BodyEvidenceSpan(start=match.start(), end=match.end(), excerpt_hash=span_hash)
    suffix = hashlib.sha256(
        (
            f"{metadata.provider_key}|{metadata.provider_article_id}|{pattern_id}|"
            f"{subject_ref}|{span.start}|{span.end}|{span_hash.digest}"
        ).encode("utf-8")
    ).hexdigest()[:20]
    fact_id = f"news-body-fact-{suffix}"
    evidence_id = f"news-body-evidence-{suffix}"
    provenance = Provenance(
        source_ref=source_ref,
        content_hash=acquisition.content_hash,
        retrieved_at=acquisition.temporary_content.captured_at,
        available_at=acquisition.temporary_content.captured_at,
        accepted_at=accepted_at,
        published_at=metadata.published_at,
    )
    fact = Fact(
        record_id=fact_id,
        schema_version=NEWS_BODY_FACT_SCHEMA_VERSION,
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=extracted_at,
        provenance=provenance,
        fact_type=f"news.event.{event_type.value}",
        value={
            "taxonomy_version": NEWS_EVENT_TAXONOMY_VERSION,
            "event_type": event_type.value,
            "extractor_name": NEWS_BODY_EXTRACTOR_NAME,
            "extractor_version": NEWS_BODY_EXTRACTOR_VERSION,
            "pattern_id": pattern_id,
            "provider_key": metadata.provider_key,
            "provider_article_id": metadata.provider_article_id,
            "source_ref": source_ref.value,
            "span_start": span.start,
            "span_end": span.end,
        },
        assertion_kind=FactAssertionKind.OBSERVATION,
        evidence_record_ids=(evidence_id,),
        extraction_confidence=confidence,
    )
    evidence = Evidence(
        record_id=evidence_id,
        schema_version=NEWS_BODY_EVIDENCE_SCHEMA_VERSION,
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=extracted_at,
        provenance=provenance,
        evidence_kind=EvidenceKind.EXTRACTION_SPAN,
        target_record_ids=(fact_id,),
        locator=f"{source_ref.value}#char={span.start}-{span.end}",
        quality_class=EvidenceQuality.PROVIDER,
        retention_class=RetentionClass.DURABLE_METADATA,
        excerpt_hash=span_hash,
    )
    return BodyFactCandidate(
        fact=fact,
        evidence=evidence,
        event_type=event_type,
        pattern_id=pattern_id,
        extractor_name=NEWS_BODY_EXTRACTOR_NAME,
        extractor_version=NEWS_BODY_EXTRACTOR_VERSION,
        confidence=confidence,
        source_ref=source_ref,
        evidence_span=span,
    )


def _validate_inputs(
    *,
    metadata: NewsArticleMetadata,
    content_identity: ContentIdentity,
    acquisition: NewsBodyAcquisition,
    subject_ref: str,
    extracted_at: datetime,
    accepted_at: datetime,
    confidence: float,
) -> None:
    if not isinstance(metadata, NewsArticleMetadata):
        raise ContractViolation("metadata must be NewsArticleMetadata")
    if not isinstance(content_identity, ContentIdentity):
        raise ContractViolation("content_identity must be ContentIdentity")
    identity = content_identity.identity
    if identity.provider_key != metadata.provider_key or identity.value != metadata.provider_article_id:
        raise ContractViolation("content identity must belong to the supplied News article")
    if not isinstance(acquisition, NewsBodyAcquisition):
        raise ContractViolation("acquisition must be NewsBodyAcquisition")
    if acquisition.article_id != metadata.provider_article_id:
        raise ContractViolation("body acquisition article ID must match News metadata")
    temporary = acquisition.temporary_content
    if temporary.state is not TemporaryContentState.STAGED:
        raise ContractViolation("body extraction requires staged TemporaryContent")
    if temporary.retention_class is not RetentionClass.TEMPORARY_SUCCESS:
        raise ContractViolation("body extraction requires temporary_success retention")
    if not isinstance(subject_ref, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,255}", subject_ref):
        raise ContractViolation("subject_ref must be a registry-resolved bounded identifier")
    for field, value in (("extracted_at", extracted_at), ("accepted_at", accepted_at)):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ContractViolation(f"{field} must be normalized to UTC")
    if extracted_at < temporary.captured_at:
        raise ContractViolation("extracted_at cannot be earlier than body capture")
    if extracted_at > temporary.expires_at:
        raise ContractViolation("expired temporary body cannot be extracted")
    if extracted_at > accepted_at:
        raise ContractViolation("extracted_at cannot be later than accepted_at")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        raise ContractViolation("body extraction confidence must be between zero and one")
