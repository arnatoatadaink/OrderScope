from dataclasses import FrozenInstanceError

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContentIdentity,
    ContractViolation,
    IdempotencyClassification,
    RevisionRelationship,
    StableIdentity,
    StableIdentityKind,
    assert_secret_free,
    classify_idempotency,
)


def snapshot(identity: StableIdentity, digest: str = "a") -> ContentIdentity:
    return ContentIdentity(identity, ContentHash(digest * 64))


def test_stable_identity_representations_are_provider_neutral_and_durable_metadata_only():
    filing = StableIdentity.filing_accession("0000002488-26-000121")
    article = StableIdentity.provider_article("newswire", "article-42")
    signal = StableIdentity.provider_signal("sec", "speech-101")

    assert filing.to_record() == {
        "identity_kind": "filing_accession",
        "stable_id": "0000002488-26-000121",
        "provider_key": None,
    }
    assert article.to_record()["provider_key"] == "newswire"
    assert signal.to_record()["identity_kind"] == "signal"
    assert snapshot(article).to_record() == {
        "identity_kind": "article",
        "stable_id": "article-42",
        "provider_key": "newswire",
        "content_hash": "a" * 64,
    }
    assert_secret_free(snapshot(article).to_record())


@pytest.mark.parametrize(
    "factory, match",
    [
        (lambda: StableIdentity(StableIdentityKind.FILING_ACCESSION, "accession"), "must match"),
        (lambda: StableIdentity.filing_accession("0000002488-26-000121 "), "padded"),
        (lambda: StableIdentity(StableIdentityKind.FILING_ACCESSION, "0000002488-26-000121", "sec"), "global"),
        (lambda: StableIdentity(StableIdentityKind.ARTICLE, "article-1"), "requires provider"),
        (lambda: StableIdentity(StableIdentityKind.SIGNAL, "signal-1", ""), "blank"),
        (lambda: StableIdentity.provider_article("newswire", "article\n1"), "control"),
        (lambda: StableIdentity.provider_article("newswire", "Bearer fixture-secret"), "credential"),
        (lambda: StableIdentity.provider_signal("api_key=fixture-secret", "signal-1"), "credential"),
        (lambda: StableIdentity.provider_signal("x" * 257, "signal-1"), "exceeds"),
        (lambda: StableIdentity.provider_article("newswire", "x" * 513), "exceeds"),
    ],
)
def test_stable_identity_rejects_ambiguous_or_unbounded_inputs(factory, match):
    with pytest.raises(ContractViolation, match=match):
        factory()


def test_distinct_stable_identity_is_new_even_when_hashes_match():
    accepted = snapshot(StableIdentity.provider_article("first-wire", "42"))
    candidate = snapshot(StableIdentity.provider_article("second-wire", "42"))

    assert classify_idempotency(accepted, candidate) is IdempotencyClassification.NEW


def test_same_identity_and_hash_is_duplicate():
    accepted = snapshot(StableIdentity.filing_accession("0000002488-26-000121"))
    candidate = snapshot(StableIdentity.filing_accession("0000002488-26-000121"))

    assert classify_idempotency(accepted, candidate) is IdempotencyClassification.DUPLICATE


def test_changed_content_without_explicit_revision_relationship_is_conflict():
    identity = StableIdentity.provider_signal("fed", "speech-101")

    assert classify_idempotency(snapshot(identity, "a"), snapshot(identity, "b")) is IdempotencyClassification.CONFLICT


def test_changed_content_with_matching_explicit_revision_relationship_is_update():
    identity = StableIdentity.provider_article("newswire", "article-42")
    accepted = snapshot(identity, "a")
    candidate = snapshot(identity, "b")
    revision = RevisionRelationship(predecessor=accepted, successor=candidate)

    assert classify_idempotency(accepted, candidate, revision_relationship=revision) is IdempotencyClassification.UPDATE


@pytest.mark.parametrize(
    "relationship_factory, match",
    [
        (
            lambda: RevisionRelationship(
                snapshot(StableIdentity.provider_article("one", "42"), "a"),
                snapshot(StableIdentity.provider_article("two", "42"), "b"),
            ),
            "same stable identity",
        ),
        (
            lambda: RevisionRelationship(
                snapshot(StableIdentity.provider_article("one", "42"), "a"),
                snapshot(StableIdentity.provider_article("one", "42"), "a"),
            ),
            "different content hashes",
        ),
    ],
)
def test_revision_relationship_rejects_ambiguous_update_claims(relationship_factory, match):
    with pytest.raises(ContractViolation, match=match):
        relationship_factory()


def test_classifier_rejects_mismatched_or_inapplicable_revision_relationship():
    identity = StableIdentity.provider_article("newswire", "article-42")
    accepted = snapshot(identity, "a")
    candidate = snapshot(identity, "b")
    reverse = RevisionRelationship(predecessor=candidate, successor=accepted)

    with pytest.raises(ContractViolation, match="must link"):
        classify_idempotency(accepted, candidate, revision_relationship=reverse)
    with pytest.raises(ContractViolation, match="duplicate"):
        classify_idempotency(accepted, accepted, revision_relationship=reverse)
    distinct = snapshot(StableIdentity.provider_article("other", "article-42"), "a")
    with pytest.raises(ContractViolation, match="matching stable identities"):
        classify_idempotency(accepted, distinct, revision_relationship=reverse)


def test_identity_and_classification_values_are_immutable():
    identity = StableIdentity.provider_signal("sec", "speech-101")
    content = snapshot(identity)

    with pytest.raises(FrozenInstanceError):
        identity.value = "changed"
    with pytest.raises(FrozenInstanceError):
        content.content_hash = ContentHash("b" * 64)
