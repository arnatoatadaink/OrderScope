from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.crypto_onchain import (
    ChainIdentity,
    ComponentKind,
    ConfirmedTransferFact,
    CryptoOnchainContractError,
    CryptoOnchainRegistry,
    ProjectIdentity,
    ProjectRelationship,
    RegistryConflictError,
    RelationshipRole,
    RelationshipStatus,
    WalletContractComponent,
)


UTC = timezone.utc
T0 = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
T1 = datetime(2026, 10, 1, 8, 1, tzinfo=UTC)
T2 = datetime(2026, 10, 1, 8, 2, tzinfo=UTC)


def _project() -> ProjectIdentity:
    return ProjectIdentity(project_id="near", display_name="NEAR Protocol", source_ref="official:near", accepted_at=T2)


def _chain() -> ChainIdentity:
    return ChainIdentity(chain_id="near-mainnet", display_name="NEAR Mainnet", source_ref="official:near-chain", accepted_at=T2)


def _component() -> WalletContractComponent:
    return WalletContractComponent(
        chain_id="near-mainnet",
        address="bridge.near",
        component_kind=ComponentKind.CONTRACT,
        source_ref="official:near-contracts",
        accepted_at=T2,
    )


def _registry() -> CryptoOnchainRegistry:
    registry = CryptoOnchainRegistry()
    registry.register_project(_project())
    registry.register_chain(_chain())
    registry.register_component(_component())
    return registry


def test_registry_identity_and_exact_duplicate_are_deterministic() -> None:
    registry = _registry()
    assert _project().registry_key == "near"
    assert _component().registry_key == ("near-mainnet", "bridge.near")
    assert registry.register_project(_project()) is registry.projects["near"]
    assert registry.register_component(_component()) is registry.components[("near-mainnet", "bridge.near")]


def test_component_requires_known_chain() -> None:
    registry = CryptoOnchainRegistry()
    with pytest.raises(RegistryConflictError, match="unknown chain_id"):
        registry.register_component(_component())


def test_same_identity_with_incompatible_fact_raises_conflict() -> None:
    registry = CryptoOnchainRegistry()
    registry.register_project(_project())
    changed = ProjectIdentity(project_id="near", display_name="Different Label", source_ref="official:near", accepted_at=T2)
    with pytest.raises(RegistryConflictError, match="conflicting fact"):
        registry.register_project(changed)


def test_relationship_preserves_unresolved_and_disputed_evidence_from_distinct_sources() -> None:
    registry = _registry()
    unresolved = ProjectRelationship(
        project_id="near", chain_id="near-mainnet", address="bridge.near",
        role=RelationshipRole.BRIDGE, status=RelationshipStatus.UNRESOLVED,
        source_ref="source:a", accepted_at=T1,
        evidence_note="Relationship observed but ownership not established.",
    )
    disputed = ProjectRelationship(
        project_id="near", chain_id="near-mainnet", address="bridge.near",
        role=RelationshipRole.BRIDGE, status=RelationshipStatus.DISPUTED,
        source_ref="source:b", accepted_at=T2,
        evidence_note="Second source disputes the ownership relationship.",
    )
    registry.register_relationship(unresolved)
    registry.register_relationship(disputed)
    evidence = registry.relationship_evidence(unresolved.logical_key)
    assert evidence == (unresolved, disputed)
    assert {fact.status for fact in evidence} == {RelationshipStatus.UNRESOLVED, RelationshipStatus.DISPUTED}


def test_same_source_relationship_revision_cannot_silently_overwrite() -> None:
    registry = _registry()
    original = ProjectRelationship(
        project_id="near", chain_id="near-mainnet", address="bridge.near",
        role=RelationshipRole.BRIDGE, status=RelationshipStatus.UNRESOLVED,
        source_ref="source:a", accepted_at=T1,
    )
    changed = ProjectRelationship(
        project_id="near", chain_id="near-mainnet", address="bridge.near",
        role=RelationshipRole.BRIDGE, status=RelationshipStatus.CONFIRMED,
        source_ref="source:a", accepted_at=T2, source_revision="rev-2",
    )
    registry.register_relationship(original)
    with pytest.raises(RegistryConflictError, match="conflicting fact"):
        registry.register_relationship(changed)


def test_confirmed_transfer_fact_enforces_timing_and_is_idempotent() -> None:
    registry = _registry()
    transfer = ConfirmedTransferFact(
        chain_id="near-mainnet", tx_hash="tx-001", transfer_index=0,
        asset_id="NEAR", amount=Decimal("1250.5"), usd_notional=Decimal("4376.75"),
        from_address="treasury.near", to_address="exchange.near", block_number=123456,
        confirmed_at=T0, available_at=T1, accepted_at=T2, source_ref="rpc:near-mainnet",
    )
    first = registry.register_transfer(transfer)
    second = registry.register_transfer(transfer)
    assert first is second
    assert transfer.registry_key == ("near-mainnet", "tx-001", 0)


def test_transfer_rejects_non_utc_or_invalid_amount() -> None:
    naive = datetime(2026, 10, 1, 8, 0)
    with pytest.raises(CryptoOnchainContractError, match="confirmed_at must be normalized to UTC"):
        ConfirmedTransferFact(
            chain_id="near-mainnet", tx_hash="tx-001", transfer_index=0, asset_id="NEAR",
            amount=Decimal("1"), from_address="a.near", confirmed_at=naive,
            available_at=T1, accepted_at=T2, source_ref="rpc:near-mainnet",
        )
    with pytest.raises(CryptoOnchainContractError, match="amount must be non-negative"):
        ConfirmedTransferFact(
            chain_id="near-mainnet", tx_hash="tx-002", transfer_index=0, asset_id="NEAR",
            amount=Decimal("-1"), to_address="b.near", confirmed_at=T0,
            available_at=T1, accepted_at=T2, source_ref="rpc:near-mainnet",
        )


def test_address_case_is_not_universally_normalized() -> None:
    upper = WalletContractComponent(
        chain_id="ethereum-mainnet", address="0xAbC", component_kind=ComponentKind.WALLET,
        source_ref="source:eth", accepted_at=T2,
    )
    lower = WalletContractComponent(
        chain_id="ethereum-mainnet", address="0xabc", component_kind=ComponentKind.WALLET,
        source_ref="source:eth", accepted_at=T2,
    )
    assert upper.registry_key != lower.registry_key


def test_transfer_fact_has_no_incident_attribution_fields() -> None:
    names = {field.name for field in fields(ConfirmedTransferFact)}
    forbidden = {"incident", "hack", "exploit", "theft", "malicious", "attribution"}
    assert names.isdisjoint(forbidden)
