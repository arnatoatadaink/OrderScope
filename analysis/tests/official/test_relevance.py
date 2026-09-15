from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, Provenance, SourceReference
from orderscope_local.official import (
    AMD_INSTRUMENT_ID,
    NVDA_INSTRUMENT_ID,
    SEMICONDUCTOR_THEME_ID,
    ActionBasis,
    IdentityBasis,
    OfficialRelevanceClass,
    OfficialRelevanceObservation,
    OfficialRelevanceTargetType,
    build_official_relevance,
    build_official_relevances,
)

UTC = timezone.utc
NOW = datetime(2026, 9, 4, 9, 9, tzinfo=UTC)


def provenance(url: str = "https://www.whitehouse.gov/presidential-actions/example/") -> Provenance:
    return Provenance(
        source_ref=SourceReference(url),
        content_hash=ContentHash("a" * 64),
        retrieved_at=NOW,
        available_at=NOW,
        accepted_at=NOW,
    )


def observation(
    classification: OfficialRelevanceClass,
    *,
    target_type: OfficialRelevanceTargetType | None,
    target_id: str | None,
    identity_basis: IdentityBasis,
    action_basis: ActionBasis,
    suffix: str,
    review_reason: str | None = None,
    source_url: str = "https://www.whitehouse.gov/presidential-actions/example/",
) -> OfficialRelevanceObservation:
    return OfficialRelevanceObservation(
        classification=classification,
        subject_fact_id=f"fact-{suffix}",
        provenance=provenance(source_url),
        evidence_record_id=None if classification is OfficialRelevanceClass.NO_LINK else f"evidence-{suffix}",
        relationship_record_id=None if classification is OfficialRelevanceClass.NO_LINK else f"relationship-{suffix}",
        target_type=target_type,
        target_id=target_id,
        identity_basis=identity_basis,
        action_basis=action_basis,
        accepted_at=NOW,
        review_reason=review_reason,
    )


def test_amd_direct_and_semiconductor_theme_are_separate_relationships():
    direct = observation(
        OfficialRelevanceClass.DIRECT_INSTRUMENT,
        target_type=OfficialRelevanceTargetType.INSTRUMENT,
        target_id=AMD_INSTRUMENT_ID,
        identity_basis=IdentityBasis.SAME_DOCUMENT_EXPLICIT,
        action_basis=ActionBasis.LICENSE,
        suffix="amd-direct",
        source_url="https://www.sec.gov/Archives/edgar/data/2488/000000248825000039/amd-20250415.htm",
    )
    theme = observation(
        OfficialRelevanceClass.THEME_EXPOSURE,
        target_type=OfficialRelevanceTargetType.THEME,
        target_id=SEMICONDUCTOR_THEME_ID,
        identity_basis=IdentityBasis.SAME_DOCUMENT_EXPLICIT,
        action_basis=ActionBasis.THEME_SCOPE,
        suffix="amd-theme",
        source_url="https://www.sec.gov/Archives/edgar/data/2488/000000248825000039/amd-20250415.htm",
    )

    bundles = build_official_relevances((direct, theme))

    assert [item.relationship.to_ref for item in bundles] == [AMD_INSTRUMENT_ID, SEMICONDUCTOR_THEME_ID]
    assert bundles[0].relationship.relationship_type == "official.direct_instrument"
    assert bundles[1].relationship.relationship_type == "official.theme_exposure"


def test_nvidia_h20_direct_link_requires_action_anchor():
    valid = observation(
        OfficialRelevanceClass.DIRECT_INSTRUMENT,
        target_type=OfficialRelevanceTargetType.INSTRUMENT,
        target_id=NVDA_INSTRUMENT_ID,
        identity_basis=IdentityBasis.SAME_DOCUMENT_EXPLICIT,
        action_basis=ActionBasis.LICENSE,
        suffix="nvda-h20",
    )
    bundle = build_official_relevance(valid)
    assert bundle is not None
    assert bundle.relationship.to_ref == NVDA_INSTRUMENT_ID

    with pytest.raises(ContractViolation):
        observation(
            OfficialRelevanceClass.DIRECT_INSTRUMENT,
            target_type=OfficialRelevanceTargetType.INSTRUMENT,
            target_id=NVDA_INSTRUMENT_ID,
            identity_basis=IdentityBasis.SAME_DOCUMENT_EXPLICIT,
            action_basis=ActionBasis.MENTION_ONLY,
            suffix="nvda-invalid",
        )


def test_semiconductor_proclamation_does_not_fan_out_to_canary_instruments():
    theme = observation(
        OfficialRelevanceClass.THEME_EXPOSURE,
        target_type=OfficialRelevanceTargetType.THEME,
        target_id=SEMICONDUCTOR_THEME_ID,
        identity_basis=IdentityBasis.NONE,
        action_basis=ActionBasis.THEME_SCOPE,
        suffix="wh-theme",
    )
    bundle = build_official_relevance(theme)
    assert bundle is not None
    assert bundle.relationship.to_ref == SEMICONDUCTOR_THEME_ID

    with pytest.raises(ContractViolation):
        observation(
            OfficialRelevanceClass.DIRECT_INSTRUMENT,
            target_type=OfficialRelevanceTargetType.INSTRUMENT,
            target_id=AMD_INSTRUMENT_ID,
            identity_basis=IdentityBasis.NONE,
            action_basis=ActionBasis.REGULATION,
            suffix="wh-fanout",
        )


def test_mention_only_is_not_direct_instrument_relevance():
    mention = observation(
        OfficialRelevanceClass.MENTION_ONLY,
        target_type=OfficialRelevanceTargetType.ENTITY_MENTION,
        target_id="sec-cik-0001045810",
        identity_basis=IdentityBasis.REGISTRY,
        action_basis=ActionBasis.MENTION_ONLY,
        suffix="jensen-mention",
    )
    bundle = build_official_relevance(mention)
    assert bundle is not None
    assert bundle.relationship.relationship_type == "official.mention_only"
    assert bundle.relationship.to_ref != NVDA_INSTRUMENT_ID


def test_unresolved_requires_review_reason_and_pending_review_relationship():
    unresolved = observation(
        OfficialRelevanceClass.UNRESOLVED,
        target_type=OfficialRelevanceTargetType.UNRESOLVED_CANDIDATE,
        target_id="candidate-advanced-computing-product",
        identity_basis=IdentityBasis.UNRESOLVED,
        action_basis=ActionBasis.UNRESOLVED,
        suffix="unresolved",
        review_reason="product identity is not uniquely resolved to one issuer",
    )
    bundle = build_official_relevance(unresolved)
    assert bundle is not None
    assert bundle.relationship.assertion_kind.value == "pending_review"

    with pytest.raises(ContractViolation):
        observation(
            OfficialRelevanceClass.UNRESOLVED,
            target_type=OfficialRelevanceTargetType.UNRESOLVED_CANDIDATE,
            target_id="candidate-x",
            identity_basis=IdentityBasis.UNRESOLVED,
            action_basis=ActionBasis.UNRESOLVED,
            suffix="missing-review",
        )


def test_no_link_produces_no_relationship_or_evidence():
    no_link = observation(
        OfficialRelevanceClass.NO_LINK,
        target_type=None,
        target_id=None,
        identity_basis=IdentityBasis.NONE,
        action_basis=ActionBasis.NONE,
        suffix="macro-only",
    )
    assert build_official_relevance(no_link) is None


def test_direct_target_must_use_stable_canary_instrument_id_not_ticker():
    with pytest.raises(ContractViolation):
        observation(
            OfficialRelevanceClass.DIRECT_INSTRUMENT,
            target_type=OfficialRelevanceTargetType.INSTRUMENT,
            target_id="AMD",
            identity_basis=IdentityBasis.REGISTRY,
            action_basis=ActionBasis.LICENSE,
            suffix="ticker-not-id",
        )


def test_relationship_and_evidence_are_bidirectionally_linked_and_tier1():
    direct = observation(
        OfficialRelevanceClass.DIRECT_INSTRUMENT,
        target_type=OfficialRelevanceTargetType.INSTRUMENT,
        target_id=AMD_INSTRUMENT_ID,
        identity_basis=IdentityBasis.REGISTRY,
        action_basis=ActionBasis.MEASURABLE_EFFECT,
        suffix="linked",
    )
    bundle = build_official_relevance(direct)
    assert bundle is not None
    assert bundle.evidence.record_id in bundle.relationship.evidence_record_ids
    assert bundle.relationship.record_id in bundle.evidence.target_record_ids
    assert bundle.evidence.quality_class.value == "tier_1_official"


def test_duplicate_relationship_or_evidence_ids_are_rejected():
    first = observation(
        OfficialRelevanceClass.THEME_EXPOSURE,
        target_type=OfficialRelevanceTargetType.THEME,
        target_id=SEMICONDUCTOR_THEME_ID,
        identity_basis=IdentityBasis.NONE,
        action_basis=ActionBasis.THEME_SCOPE,
        suffix="dup",
    )
    second = OfficialRelevanceObservation(
        classification=OfficialRelevanceClass.MENTION_ONLY,
        subject_fact_id="fact-other",
        provenance=provenance(),
        evidence_record_id=first.evidence_record_id,
        relationship_record_id="relationship-other",
        target_type=OfficialRelevanceTargetType.ENTITY_MENTION,
        target_id="sec-cik-0001045810",
        identity_basis=IdentityBasis.REGISTRY,
        action_basis=ActionBasis.MENTION_ONLY,
        accepted_at=NOW,
    )
    with pytest.raises(ContractViolation):
        build_official_relevances((first, second))
