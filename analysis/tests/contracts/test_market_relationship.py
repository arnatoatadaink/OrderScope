from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import (
    ContractViolation,
    MarketRelationshipContext,
    MarketRelationshipKind,
    RelationshipDirection,
)
from orderscope_local.contracts.provenance import SourceTimestamp


UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 14, 0, 0, tzinfo=UTC)


def test_market_relationship_kinds_remain_distinct() -> None:
    assert {kind.value for kind in MarketRelationshipKind} == {
        "market_context.leader",
        "market_context.competitor",
        "market_context.substitute",
        "market_context.sector_peer",
    }


def test_context_materializes_as_directed_fact_store_relationship() -> None:
    context = MarketRelationshipContext(
        record_id="rel-cbrs-nvda-competitor-v1",
        subject_ref="CBRS",
        related_ref="NVDA",
        relationship_kind=MarketRelationshipKind.COMPETITOR,
        accepted_at=ACCEPTED,
        created_at=ACCEPTED,
        registry_basis_ref="a0-reviewed-market-context-v0.1",
        valid_from=SourceTimestamp.at(datetime(2026, 8, 26, 0, 0, tzinfo=UTC)),
    )

    relationship = context.to_relationship()

    assert relationship.relationship_type == "market_context.competitor"
    assert relationship.from_ref == "CBRS"
    assert relationship.to_ref == "NVDA"
    assert relationship.direction is RelationshipDirection.DIRECTED
    assert relationship.registry_basis_ref == "a0-reviewed-market-context-v0.1"
    assert relationship.valid_from == context.valid_from


def test_same_pair_can_hold_different_reviewed_contexts() -> None:
    competitor = MarketRelationshipContext(
        record_id="rel-cbrs-nvda-competitor-v1",
        subject_ref="CBRS",
        related_ref="NVDA",
        relationship_kind=MarketRelationshipKind.COMPETITOR,
        accepted_at=ACCEPTED,
        created_at=ACCEPTED,
        registry_basis_ref="reviewed-context",
    ).to_relationship()
    leader = MarketRelationshipContext(
        record_id="rel-cbrs-nvda-leader-v1",
        subject_ref="CBRS",
        related_ref="NVDA",
        relationship_kind=MarketRelationshipKind.LEADER,
        accepted_at=ACCEPTED,
        created_at=ACCEPTED,
        registry_basis_ref="reviewed-context",
    ).to_relationship()

    assert competitor.relationship_type != leader.relationship_type


def test_relationship_requires_distinct_instruments() -> None:
    with pytest.raises(ContractViolation, match="distinct instruments"):
        MarketRelationshipContext(
            record_id="rel-cbrs-self",
            subject_ref="CBRS",
            related_ref="CBRS",
            relationship_kind=MarketRelationshipKind.SECTOR_PEER,
            accepted_at=ACCEPTED,
            created_at=ACCEPTED,
            registry_basis_ref="reviewed-context",
        )


def test_supersession_and_validity_are_preserved() -> None:
    context = MarketRelationshipContext(
        record_id="rel-cbrs-nvda-competitor-v2",
        subject_ref="CBRS",
        related_ref="NVDA",
        relationship_kind=MarketRelationshipKind.COMPETITOR,
        accepted_at=ACCEPTED,
        created_at=ACCEPTED,
        registry_basis_ref="reviewed-context-v2",
        supersedes_record_id="rel-cbrs-nvda-competitor-v1",
        valid_to=SourceTimestamp.at(datetime(2026, 9, 14, 0, 0, tzinfo=UTC)),
    )

    relationship = context.to_relationship()

    assert relationship.supersedes_record_id == "rel-cbrs-nvda-competitor-v1"
    assert relationship.valid_to == context.valid_to
