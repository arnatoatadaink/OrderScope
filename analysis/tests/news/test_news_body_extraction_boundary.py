from datetime import datetime, timedelta, timezone
import hashlib

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContentIdentity,
    ContractViolation,
    EvidenceKind,
    RetentionClass,
    SourceTimestamp,
    StableIdentity,
    TemporaryContent,
    TemporaryContentState,
)
from orderscope_local.news import (
    ALPACA_NEWS_PROVIDER_KEY,
    NEWS_BODY_EXTRACTOR_NAME,
    NEWS_BODY_EXTRACTOR_VERSION,
    NewsArticleMetadata,
    NewsBodyAcquisition,
    NewsEventType,
    extract_body_fact_candidates,
)

UTC = timezone.utc
CAPTURED = datetime(2026, 9, 9, 0, 0, tzinfo=UTC)
EXTRACTED = datetime(2026, 9, 9, 0, 5, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 9, 0, 6, tzinfo=UTC)
SUBJECT = "us-sec-0000002488-common"


class Reader:
    def __init__(self, body):
        self.body = body
        self.calls = []

    def read(self, *, content_ref):
        self.calls.append(content_ref)
        return self.body


def _metadata(*, article_id="12345", url="https://example.com/news/12345"):
    return NewsArticleMetadata(
        provider_key=ALPACA_NEWS_PROVIDER_KEY,
        provider_article_id=article_id,
        query_symbol="AMD",
        headline="AMD corporate update",
        publisher="benzinga",
        article_url=url,
        published_at=SourceTimestamp.at(datetime(2026, 9, 8, 23, 30, tzinfo=UTC)),
        provider_updated_at=None,
        author=None,
        summary=None,
        provider_symbols=("AMD",),
        body_capability=True,
    )


def _identity(metadata):
    return ContentIdentity(
        StableIdentity.provider_article(metadata.provider_key, metadata.provider_article_id),
        ContentHash("1" * 64),
    )


def _acquisition(body, *, article_id="12345", expires_at=None):
    digest = ContentHash(hashlib.sha256(body.encode("utf-8")).hexdigest())
    temporary = TemporaryContent(
        content_ref="temp://news/12345",
        retention_class=RetentionClass.TEMPORARY_SUCCESS,
        captured_at=CAPTURED,
        expires_at=expires_at or CAPTURED + timedelta(hours=6),
        state=TemporaryContentState.STAGED,
    )
    return NewsBodyAcquisition(article_id=article_id, content_hash=digest, temporary_content=temporary)


def _extract(body, **kwargs):
    metadata = kwargs.pop("metadata", _metadata())
    acquisition = kwargs.pop("acquisition", _acquisition(body, article_id=metadata.provider_article_id))
    reader = kwargs.pop("reader", Reader(body))
    return extract_body_fact_candidates(
        metadata=metadata,
        content_identity=kwargs.pop("content_identity", _identity(metadata)),
        acquisition=acquisition,
        reader=reader,
        subject_ref=kwargs.pop("subject_ref", SUBJECT),
        extracted_at=kwargs.pop("extracted_at", EXTRACTED),
        accepted_at=kwargs.pop("accepted_at", ACCEPTED),
        confidence=kwargs.pop("confidence", 1.0),
        **kwargs,
    )


def test_body_reader_emits_fact_evidence_with_span_and_extractor_metadata():
    body = "AMD wins a contract for accelerator systems."
    result = _extract(body)

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.event_type is NewsEventType.CONTRACT
    assert candidate.extractor_name == NEWS_BODY_EXTRACTOR_NAME
    assert candidate.extractor_version == NEWS_BODY_EXTRACTOR_VERSION
    assert candidate.fact.extraction_confidence == 1.0
    assert candidate.fact.value["span_start"] == candidate.evidence_span.start
    assert candidate.fact.value["span_end"] == candidate.evidence_span.end
    assert candidate.fact.value["source_ref"] == "https://example.com/news/12345"
    assert candidate.evidence.evidence_kind is EvidenceKind.EXTRACTION_SPAN
    assert candidate.evidence.excerpt_hash == candidate.evidence_span.excerpt_hash
    assert candidate.fact.evidence_record_ids == (candidate.evidence.record_id,)
    assert candidate.evidence.target_record_ids == (candidate.fact.record_id,)


def test_raw_body_text_is_not_stored_in_fact_or_evidence_metadata():
    body = "AMD wins a contract for a secret fixture accelerator."
    result = _extract(body)
    candidate = result.candidates[0]

    assert body not in repr(candidate.fact.value)
    assert body not in candidate.evidence.locator
    assert "secret fixture accelerator" not in repr(candidate)


def test_multiple_explicit_body_events_become_separate_candidates():
    body = "AMD raises debt financing. AMD plans to invest in a new data center facility."
    result = _extract(body)

    assert {candidate.event_type for candidate in result.candidates} == {
        NewsEventType.FINANCING,
        NewsEventType.CAPEX,
    }
    assert len({candidate.fact.record_id for candidate in result.candidates}) == 2


def test_extraction_marks_temporary_content_succeeded_without_deleting_it():
    body = "AMD partners with Example Cloud on an integration."
    result = _extract(body)

    completed = result.completed_content
    assert completed.state is TemporaryContentState.EXTRACTION_SUCCEEDED
    assert completed.retention_class is RetentionClass.TEMPORARY_SUCCESS
    assert completed.extraction_completed_at == EXTRACTED
    assert completed.deleted_at is None
    assert completed.deletion_proof is None


def test_no_event_match_still_completes_body_extraction_lifecycle():
    result = _extract("AMD published a general corporate profile with no explicit event.")

    assert result.candidates == ()
    assert result.completed_content.state is TemporaryContentState.EXTRACTION_SUCCEEDED


def test_expired_staged_content_cannot_be_extracted():
    body = "AMD wins a contract for accelerator systems."
    expired = _acquisition(body, expires_at=EXTRACTED - timedelta(seconds=1))
    with pytest.raises(ContractViolation, match="expired temporary body"):
        _extract(body, acquisition=expired)


def test_body_hash_mismatch_is_rejected_before_fact_creation():
    expected = "AMD wins a contract for accelerator systems."
    acquisition = _acquisition(expected)
    reader = Reader("tampered temporary body")

    with pytest.raises(ContractViolation, match="hash does not match"):
        _extract(expected, acquisition=acquisition, reader=reader)


def test_article_identity_and_body_article_id_must_match_metadata():
    body = "AMD wins a contract for accelerator systems."
    metadata = _metadata()
    wrong_identity = ContentIdentity(
        StableIdentity.provider_article(ALPACA_NEWS_PROVIDER_KEY, "other"),
        ContentHash("2" * 64),
    )
    with pytest.raises(ContractViolation, match="content identity"):
        _extract(body, metadata=metadata, content_identity=wrong_identity)

    wrong_acquisition = _acquisition(body, article_id="other")
    with pytest.raises(ContractViolation, match="article ID"):
        _extract(body, metadata=metadata, acquisition=wrong_acquisition)


def test_confidence_and_timestamp_boundaries_are_enforced():
    body = "AMD wins a contract for accelerator systems."
    with pytest.raises(ContractViolation, match="confidence"):
        _extract(body, confidence=1.1)
    with pytest.raises(ContractViolation, match="earlier than body capture"):
        _extract(body, extracted_at=CAPTURED - timedelta(seconds=1))
    with pytest.raises(ContractViolation, match="later than accepted_at"):
        _extract(body, accepted_at=EXTRACTED - timedelta(seconds=1))


def test_span_locator_falls_back_when_source_url_is_at_durable_limit():
    body = "AMD wins a contract for accelerator systems."
    long_url = "https://example.com/" + "a" * 2025
    assert len(long_url) <= 2048
    metadata = _metadata(url=long_url)

    result = _extract(body, metadata=metadata)
    candidate = result.candidates[0]

    assert candidate.source_ref.value == long_url
    assert candidate.evidence.locator.startswith("alpaca-news:article:12345#char=")
    assert len(candidate.evidence.locator) <= 2048


def test_identical_body_and_inputs_reproduce_candidate_ids_and_span_hashes():
    body = "AMD wins a contract for accelerator systems."
    first = _extract(body)
    second = _extract(body)

    assert first.candidates[0].fact.record_id == second.candidates[0].fact.record_id
    assert first.candidates[0].evidence.record_id == second.candidates[0].evidence.record_id
    assert first.candidates[0].evidence_span == second.candidates[0].evidence_span
