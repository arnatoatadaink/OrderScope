from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Relationship, RelationshipAssertionKind, RelationshipDirection
from .provenance import SourceTimestamp


class MarketRelationshipKind(StrEnum):
    LEADER = "market_context.leader"
    COMPETITOR = "market_context.competitor"
    SUBSTITUTE = "market_context.substitute"
    SECTOR_PEER = "market_context.sector_peer"


@dataclass(frozen=True, kw_only=True)
class MarketRelationshipContext:
    record_id: str
    subject_ref: str
    related_ref: str
    relationship_kind: MarketRelationshipKind
    accepted_at: datetime
    created_at: datetime
    registry_basis_ref: str
    valid_from: SourceTimestamp | None = None
    valid_to: SourceTimestamp | None = None
    supersedes_record_id: str | None = None

    def __post_init__(self) -> None:
        if self.subject_ref == self.related_ref:
            raise ContractViolation("market relationship requires distinct instruments")
        if not isinstance(self.relationship_kind, MarketRelationshipKind):
            raise ContractViolation("relationship_kind must be MarketRelationshipKind")
        if not self.registry_basis_ref.strip():
            raise ContractViolation("registry_basis_ref cannot be blank")

    def to_relationship(self) -> Relationship:
        return Relationship(
            record_id=self.record_id,
            schema_version="market-relationship-context-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.created_at,
            supersedes_record_id=self.supersedes_record_id,
            relationship_type=self.relationship_kind.value,
            from_ref=self.subject_ref,
            to_ref=self.related_ref,
            direction=RelationshipDirection.DIRECTED,
            assertion_kind=RelationshipAssertionKind.ASSERTION,
            registry_basis_ref=self.registry_basis_ref,
            valid_from=self.valid_from,
            valid_to=self.valid_to,
        )
