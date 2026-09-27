"""Provider-neutral stable identity and idempotency classification contracts.

The values in this module are durable metadata only: stable identifiers and
SHA-256 digests already accepted by the provenance contract.  They deliberately
exclude provider payloads, document/news bodies, credentials, persistence
implementation, and any heuristic that guesses whether a changed item is an
update.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re

from .errors import ContractViolation
from .provenance import ContentHash


_SEC_ACCESSION = re.compile(r"[0-9]{10}-[0-9]{2}-[0-9]{6}")
_CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]")
_SECRET_LIKE_VALUE = re.compile(
    r"bearer\s+|-----begin\s+|(?:api[_-]?key|api[_-]?secret|client[_-]?secret|authorization|password)\s*[:=]",
    re.IGNORECASE,
)


class StableIdentityKind(StrEnum):
    """The externally established namespace of a stable identity."""

    FILING_ACCESSION = "filing_accession"
    ARTICLE = "article"
    SIGNAL = "signal"


def _require_stable_text(value: str, field: str, *, maximum: int) -> None:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be a string")
    if not value or value != value.strip():
        raise ContractViolation(f"{field} cannot be blank or padded")
    if len(value) > maximum:
        raise ContractViolation(f"{field} exceeds {maximum} characters")
    if _CONTROL_CHARACTER.search(value):
        raise ContractViolation(f"{field} cannot contain control characters")
    if _SECRET_LIKE_VALUE.search(value):
        raise ContractViolation(f"{field} cannot contain credential-like material")


@dataclass(frozen=True)
class StableIdentity:
    """A stable external identity without provider-specific payload shape.

    SEC filing accessions are global in this contract and therefore cannot have a
    provider scope.  Article and official-signal IDs are meaningful only inside
    their provider scope; the same ID from different providers is a distinct
    identity.
    """

    kind: StableIdentityKind
    value: str
    provider_key: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, StableIdentityKind):
            raise ContractViolation("identity kind must be a StableIdentityKind")
        _require_stable_text(self.value, "stable_id", maximum=512)
        if self.kind is StableIdentityKind.FILING_ACCESSION:
            if self.provider_key is not None:
                raise ContractViolation("filing accession is global and cannot have provider scope")
            if not _SEC_ACCESSION.fullmatch(self.value):
                raise ContractViolation("filing accession must match 0000000000-00-000000")
        else:
            if self.provider_key is None:
                raise ContractViolation(f"{self.kind.value} identity requires provider scope")
            _require_stable_text(self.provider_key, "provider_key", maximum=256)

    @classmethod
    def filing_accession(cls, accession: str) -> StableIdentity:
        """Create a globally scoped SEC filing identity."""

        return cls(StableIdentityKind.FILING_ACCESSION, accession)

    @classmethod
    def provider_article(cls, provider_key: str, article_id: str) -> StableIdentity:
        """Create an article identity scoped to its provider."""

        return cls(StableIdentityKind.ARTICLE, article_id, provider_key)

    @classmethod
    def provider_signal(cls, provider_key: str, signal_id: str) -> StableIdentity:
        """Create an official-signal identity scoped to its provider."""

        return cls(StableIdentityKind.SIGNAL, signal_id, provider_key)

    def to_record(self) -> dict[str, str | None]:
        """Return the complete, metadata-only storage representation."""

        return {
            "identity_kind": self.kind.value,
            "stable_id": self.value,
            "provider_key": self.provider_key,
        }


@dataclass(frozen=True)
class ContentIdentity:
    """The idempotency comparison key: stable identity plus normalized SHA-256."""

    identity: StableIdentity
    content_hash: ContentHash

    def __post_init__(self) -> None:
        if not isinstance(self.identity, StableIdentity):
            raise ContractViolation("identity must be a StableIdentity")
        if not isinstance(self.content_hash, ContentHash):
            raise ContractViolation("content_hash must be a ContentHash")

    def to_record(self) -> dict[str, str | None]:
        """Return only durable identity and digest metadata, never source content."""

        return {**self.identity.to_record(), "content_hash": self.content_hash.digest}


@dataclass(frozen=True)
class RevisionRelationship:
    """An explicit caller-supplied assertion that one snapshot supersedes another.

    This contract does not infer revision status from timestamps, URLs, provider
    revisions, or changed content.  The predecessor and successor must share one
    stable identity and must have different content hashes.
    """

    predecessor: ContentIdentity
    successor: ContentIdentity

    def __post_init__(self) -> None:
        if not isinstance(self.predecessor, ContentIdentity):
            raise ContractViolation("revision predecessor must be a ContentIdentity")
        if not isinstance(self.successor, ContentIdentity):
            raise ContractViolation("revision successor must be a ContentIdentity")
        if self.predecessor.identity != self.successor.identity:
            raise ContractViolation("revision relationship requires the same stable identity")
        if self.predecessor.content_hash == self.successor.content_hash:
            raise ContractViolation("revision relationship requires different content hashes")


class IdempotencyClassification(StrEnum):
    """The only outcomes for comparison against one accepted content snapshot."""

    NEW = "new"
    DUPLICATE = "duplicate"
    UPDATE = "update"
    CONFLICT = "conflict"


def classify_idempotency(
    accepted: ContentIdentity,
    candidate: ContentIdentity,
    *,
    revision_relationship: RevisionRelationship | None = None,
) -> IdempotencyClassification:
    """Classify a candidate without choosing a storage engine or mutating records.

    Invariants are deliberately exact:

    * distinct stable identities are ``NEW``;
    * same identity and same hash are ``DUPLICATE``;
    * same identity and different hashes are ``UPDATE`` only when the caller
      supplies the matching predecessor-to-successor relationship; otherwise they
      are ``CONFLICT``.

    A revision relationship outside the third case is invalid rather than silently
    ignored.  This makes an update decision auditable and prevents heuristics from
    converting a contradiction into an overwrite.
    """

    if not isinstance(accepted, ContentIdentity):
        raise ContractViolation("accepted must be a ContentIdentity")
    if not isinstance(candidate, ContentIdentity):
        raise ContractViolation("candidate must be a ContentIdentity")
    if revision_relationship is not None and not isinstance(revision_relationship, RevisionRelationship):
        raise ContractViolation("revision_relationship must be a RevisionRelationship")

    same_identity = accepted.identity == candidate.identity
    same_hash = accepted.content_hash == candidate.content_hash
    if not same_identity:
        if revision_relationship is not None:
            raise ContractViolation("revision relationship requires matching stable identities under comparison")
        return IdempotencyClassification.NEW
    if same_hash:
        if revision_relationship is not None:
            raise ContractViolation("duplicate content cannot have a revision relationship")
        return IdempotencyClassification.DUPLICATE
    if revision_relationship is None:
        return IdempotencyClassification.CONFLICT
    if revision_relationship.predecessor != accepted or revision_relationship.successor != candidate:
        raise ContractViolation("revision relationship must link accepted predecessor to candidate successor")
    return IdempotencyClassification.UPDATE
