"""Evidence-grounded official Fact relevance linkage for O0-004.

The contract separates direct Corporate Canary instrument relevance from indirect
semiconductor-theme exposure and from mention-only/unresolved/no-link outcomes.
It never fans out a theme relation to AMD/NVIDIA without a same-evidence identity
and action/effect anchor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from orderscope_local.contracts import (
    ContractViolation,
    Evidence,
    EvidenceKind,
    EvidenceQuality,
    Provenance,
    Relationship,
    RelationshipAssertionKind,
    RelationshipDirection,
    RetentionClass,
)

AMD_INSTRUMENT_ID = "us-sec-0000002488-common"
NVDA_INSTRUMENT_ID = "us-sec-0001045810-common"
SEMICONDUCTOR_THEME_ID = "theme-semiconductor-v0.1"


class OfficialRelevanceClass(StrEnum):
    DIRECT_INSTRUMENT = "official.direct_instrument"
    THEME_EXPOSURE = "official.theme_exposure"
    MENTION_ONLY = "official.mention_only"
    UNRESOLVED = "official.unresolved"
    NO_LINK = "official.no_link"


class OfficialRelevanceTargetType(StrEnum):
    INSTRUMENT = "instrument"
    THEME = "theme"
    ENTITY_MENTION = "entity_mention"
    UNRESOLVED_CANDIDATE = "unresolved_candidate"


class IdentityBasis(StrEnum):
    REGISTRY = "registry"
    SAME_DOCUMENT_EXPLICIT = "same_document_explicit"
    UNRESOLVED = "unresolved"
    NONE = "none"


class ActionBasis(StrEnum):
    LICENSE = "license"
    REGULATION = "regulation"
    GRANT = "grant"
    CONTRACT = "contract"
    ENFORCEMENT = "enforcement"
    FORMAL_COMMITMENT = "formal_commitment"
    MEASURABLE_EFFECT = "measurable_effect"
    THEME_SCOPE = "theme_scope"
    MENTION_ONLY = "mention_only"
    UNRESOLVED = "unresolved"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class OfficialRelevanceObservation:
    classification: OfficialRelevanceClass
    subject_fact_id: str
    provenance: Provenance
    evidence_record_id: str | None
    relationship_record_id: str | None
    target_type: OfficialRelevanceTargetType | None
    target_id: str | None
    identity_basis: IdentityBasis
    action_basis: ActionBasis
    accepted_at: datetime
    review_reason: str | None = None
    rule_version: str = "official-relevance-v0.1"

    def __post_init__(self) -> None:
        for field, value, limit in (
            ("subject_fact_id", self.subject_fact_id, 256),
            ("rule_version", self.rule_version, 128),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > limit:
                raise ContractViolation(f"official relevance {field} must be bounded canonical text")
        if not isinstance(self.classification, OfficialRelevanceClass):
            raise ContractViolation("official relevance classification is invalid")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("official relevance requires accepted Provenance")
        if not isinstance(self.identity_basis, IdentityBasis):
            raise ContractViolation("official relevance identity_basis is invalid")
        if not isinstance(self.action_basis, ActionBasis):
            raise ContractViolation("official relevance action_basis is invalid")
        if not isinstance(self.accepted_at, datetime) or self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() != timedelta(0):
            raise ContractViolation("official relevance accepted_at must be normalized to UTC")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("official relevance accepted_at must match provenance")

        if self.classification is OfficialRelevanceClass.NO_LINK:
            if any(value is not None for value in (self.evidence_record_id, self.relationship_record_id, self.target_type, self.target_id, self.review_reason)):
                raise ContractViolation("no-link observation cannot fabricate a Relationship target/evidence")
            if self.identity_basis is not IdentityBasis.NONE or self.action_basis is not ActionBasis.NONE:
                raise ContractViolation("no-link observation requires NONE identity/action basis")
            return

        for field, value in (("evidence_record_id", self.evidence_record_id), ("relationship_record_id", self.relationship_record_id), ("target_id", self.target_id)):
            if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
                raise ContractViolation(f"official relevance {field} is required and must be bounded canonical text")
        if not isinstance(self.target_type, OfficialRelevanceTargetType):
            raise ContractViolation("official relevance target_type is required")

        if self.classification is OfficialRelevanceClass.DIRECT_INSTRUMENT:
            if self.target_type is not OfficialRelevanceTargetType.INSTRUMENT:
                raise ContractViolation("direct relevance must target an instrument")
            if self.target_id not in {AMD_INSTRUMENT_ID, NVDA_INSTRUMENT_ID}:
                raise ContractViolation("direct relevance target must be a Corporate Canary instrument")
            if self.identity_basis not in {IdentityBasis.REGISTRY, IdentityBasis.SAME_DOCUMENT_EXPLICIT}:
                raise ContractViolation("direct relevance requires resolved identity basis")
            if self.action_basis in {ActionBasis.THEME_SCOPE, ActionBasis.MENTION_ONLY, ActionBasis.UNRESOLVED, ActionBasis.NONE}:
                raise ContractViolation("direct relevance requires an action/effect anchor")
            if self.review_reason is not None:
                raise ContractViolation("resolved direct relevance cannot carry review_reason")
            return

        if self.classification is OfficialRelevanceClass.THEME_EXPOSURE:
            if self.target_type is not OfficialRelevanceTargetType.THEME or self.target_id != SEMICONDUCTOR_THEME_ID:
                raise ContractViolation("theme exposure must target the versioned semiconductor theme")
            if self.action_basis is not ActionBasis.THEME_SCOPE:
                raise ContractViolation("theme exposure requires explicit theme-scope evidence")
            if self.review_reason is not None:
                raise ContractViolation("resolved theme exposure cannot carry review_reason")
            return

        if self.classification is OfficialRelevanceClass.MENTION_ONLY:
            if self.target_type is not OfficialRelevanceTargetType.ENTITY_MENTION:
                raise ContractViolation("mention-only relevance must target an entity mention")
            if self.action_basis is not ActionBasis.MENTION_ONLY:
                raise ContractViolation("mention-only relevance requires mention-only basis")
            if self.review_reason is not None:
                raise ContractViolation("mention-only relevance cannot carry review_reason")
            return

        if self.classification is OfficialRelevanceClass.UNRESOLVED:
            if self.target_type is not OfficialRelevanceTargetType.UNRESOLVED_CANDIDATE:
                raise ContractViolation("unresolved relevance must target an unresolved candidate")
            if self.identity_basis is not IdentityBasis.UNRESOLVED or self.action_basis is not ActionBasis.UNRESOLVED:
                raise ContractViolation("unresolved relevance requires unresolved identity/action basis")
            if self.review_reason is None or not self.review_reason.strip() or len(self.review_reason) > 512:
                raise ContractViolation("unresolved relevance requires bounded review_reason")


@dataclass(frozen=True, slots=True)
class OfficialRelevanceBundle:
    relationship: Relationship
    evidence: Evidence

    def __post_init__(self) -> None:
        if self.evidence.record_id not in self.relationship.evidence_record_ids:
            raise ContractViolation("official relevance Relationship must link Evidence")
        if self.relationship.record_id not in self.evidence.target_record_ids:
            raise ContractViolation("official relevance Evidence must target Relationship")


def build_official_relevance(observation: OfficialRelevanceObservation) -> OfficialRelevanceBundle | None:
    if observation.classification is OfficialRelevanceClass.NO_LINK:
        return None

    assert observation.relationship_record_id is not None
    assert observation.evidence_record_id is not None
    assert observation.target_id is not None
    assert observation.target_type is not None

    relationship = Relationship(
        record_id=observation.relationship_record_id,
        schema_version=observation.rule_version,
        subject_ref=observation.subject_fact_id,
        accepted_at=observation.accepted_at,
        created_at=observation.accepted_at,
        relationship_type=observation.classification.value,
        from_ref=observation.subject_fact_id,
        to_ref=observation.target_id,
        direction=RelationshipDirection.DIRECTED,
        assertion_kind=(
            RelationshipAssertionKind.PENDING_REVIEW
            if observation.classification is OfficialRelevanceClass.UNRESOLVED
            else RelationshipAssertionKind.ASSERTION
        ),
        provenance=observation.provenance,
        evidence_record_ids=(observation.evidence_record_id,),
    )
    evidence = Evidence(
        record_id=observation.evidence_record_id,
        schema_version=observation.rule_version,
        subject_ref=observation.subject_fact_id,
        accepted_at=observation.accepted_at,
        created_at=observation.accepted_at,
        provenance=observation.provenance,
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(observation.relationship_record_id,),
        locator=observation.provenance.source_ref.value,
        quality_class=EvidenceQuality.TIER_1_OFFICIAL,
        retention_class=RetentionClass.DURABLE_METADATA,
    )
    return OfficialRelevanceBundle(relationship=relationship, evidence=evidence)


def build_official_relevances(
    observations: tuple[OfficialRelevanceObservation, ...],
) -> tuple[OfficialRelevanceBundle, ...]:
    if not isinstance(observations, tuple) or not observations:
        raise ContractViolation("official relevance extraction requires immutable non-empty observations")
    relationship_ids = [item.relationship_record_id for item in observations if item.relationship_record_id is not None]
    evidence_ids = [item.evidence_record_id for item in observations if item.evidence_record_id is not None]
    if len(relationship_ids) != len(set(relationship_ids)):
        raise ContractViolation("official relevance relationship IDs must be unique")
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ContractViolation("official relevance evidence IDs must be unique")
    bundles = [build_official_relevance(item) for item in observations]
    return tuple(item for item in bundles if item is not None)
