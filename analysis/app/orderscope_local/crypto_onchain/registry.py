"""Deterministic in-memory registry semantics for REL-11A / C0-001."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar

from .models import (
    ChainIdentity,
    ConfirmedTransferFact,
    ProjectIdentity,
    ProjectRelationship,
    WalletContractComponent,
)


class RegistryConflictError(ValueError):
    """Raised when the same deterministic identity carries incompatible facts."""


T = TypeVar("T")


def _register_exact_or_conflict(store: dict[object, T], key: object, value: T) -> T:
    existing = store.get(key)
    if existing is None:
        store[key] = value
        return value
    if existing == value:
        return existing
    raise RegistryConflictError(f"conflicting fact for deterministic identity: {key!r}")


@dataclass
class CryptoOnchainRegistry:
    """Small deterministic Fact registry used by C0-001 and replay fixtures.

    The registry is intentionally provider-neutral and persistence-neutral.  It
    establishes idempotency/conflict behavior before later adapters or storage
    are introduced.
    """

    projects: dict[str, ProjectIdentity] = field(default_factory=dict)
    chains: dict[str, ChainIdentity] = field(default_factory=dict)
    components: dict[tuple[str, str], WalletContractComponent] = field(default_factory=dict)
    relationships: dict[tuple[object, ...], ProjectRelationship] = field(default_factory=dict)
    transfers: dict[tuple[str, str, int], ConfirmedTransferFact] = field(default_factory=dict)

    def register_project(self, fact: ProjectIdentity) -> ProjectIdentity:
        return _register_exact_or_conflict(self.projects, fact.registry_key, fact)

    def register_chain(self, fact: ChainIdentity) -> ChainIdentity:
        return _register_exact_or_conflict(self.chains, fact.registry_key, fact)

    def register_component(self, fact: WalletContractComponent) -> WalletContractComponent:
        if fact.chain_id not in self.chains:
            raise RegistryConflictError(f"unknown chain_id for component: {fact.chain_id}")
        return _register_exact_or_conflict(self.components, fact.registry_key, fact)

    def register_relationship(self, fact: ProjectRelationship) -> ProjectRelationship:
        if fact.project_id not in self.projects:
            raise RegistryConflictError(f"unknown project_id for relationship: {fact.project_id}")
        if fact.chain_id not in self.chains:
            raise RegistryConflictError(f"unknown chain_id for relationship: {fact.chain_id}")
        if (fact.chain_id, fact.address) not in self.components:
            raise RegistryConflictError("relationship component must be registered first")
        return _register_exact_or_conflict(self.relationships, fact.registry_key, fact)

    def register_transfer(self, fact: ConfirmedTransferFact) -> ConfirmedTransferFact:
        if fact.chain_id not in self.chains:
            raise RegistryConflictError(f"unknown chain_id for transfer: {fact.chain_id}")
        return _register_exact_or_conflict(self.transfers, fact.registry_key, fact)

    def relationship_evidence(self, logical_key: tuple[object, ...]) -> tuple[ProjectRelationship, ...]:
        facts = [fact for fact in self.relationships.values() if fact.logical_key == logical_key]
        return tuple(sorted(facts, key=lambda fact: (fact.accepted_at, fact.source_ref)))
