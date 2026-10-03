"""Source-neutral on-chain Fact contracts for REL-11A / C0-001.

These models intentionally stop at evidence-backed identity, relationship and
confirmed-transfer facts. They do not encode exploit, theft, malicious intent
or incident attribution; those conclusions belong to later bounded analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum


class CryptoOnchainContractError(ValueError):
    """Raised when an on-chain Fact violates the C0-001 contract."""


def _require_text(value: str, field: str, *, max_length: int = 512) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > max_length:
        raise CryptoOnchainContractError(f"{field} must be non-blank, trimmed and bounded")


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise CryptoOnchainContractError(f"{field} must be normalized to UTC")


def _require_nonnegative_int(value: int | None, field: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CryptoOnchainContractError(f"{field} must be a non-negative integer")


def _require_decimal(value: Decimal, field: str, *, allow_zero: bool = True) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise CryptoOnchainContractError(f"{field} must be a finite Decimal")
    if value < 0 or (not allow_zero and value == 0):
        qualifier = "positive" if not allow_zero else "non-negative"
        raise CryptoOnchainContractError(f"{field} must be {qualifier}")


class ComponentKind(StrEnum):
    WALLET = "wallet"
    CONTRACT = "contract"
    UNKNOWN = "unknown"


class RelationshipRole(StrEnum):
    TREASURY = "treasury"
    BRIDGE = "bridge"
    CUSTODY = "custody"
    OPERATIONS = "operations"
    PROTOCOL_CONTRACT = "protocol_contract"
    UNKNOWN = "unknown"


class RelationshipStatus(StrEnum):
    CONFIRMED = "confirmed"
    UNRESOLVED = "unresolved"
    DISPUTED = "disputed"


@dataclass(frozen=True, kw_only=True)
class ProjectIdentity:
    project_id: str
    display_name: str
    source_ref: str
    accepted_at: datetime
    source_revision: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.project_id, "project_id"),
            (self.display_name, "display_name"),
            (self.source_ref, "source_ref"),
        ):
            _require_text(value, field)
        _require_utc(self.accepted_at, "accepted_at")
        if self.source_revision is not None:
            _require_text(self.source_revision, "source_revision")

    @property
    def registry_key(self) -> str:
        return self.project_id


@dataclass(frozen=True, kw_only=True)
class ChainIdentity:
    chain_id: str
    display_name: str
    source_ref: str
    accepted_at: datetime
    source_revision: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.chain_id, "chain_id"),
            (self.display_name, "display_name"),
            (self.source_ref, "source_ref"),
        ):
            _require_text(value, field)
        _require_utc(self.accepted_at, "accepted_at")
        if self.source_revision is not None:
            _require_text(self.source_revision, "source_revision")

    @property
    def registry_key(self) -> str:
        return self.chain_id


@dataclass(frozen=True, kw_only=True)
class WalletContractComponent:
    chain_id: str
    address: str
    component_kind: ComponentKind
    source_ref: str
    accepted_at: datetime
    source_revision: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.chain_id, "chain_id"),
            (self.address, "address"),
            (self.source_ref, "source_ref"),
        ):
            _require_text(value, field)
        if not isinstance(self.component_kind, ComponentKind):
            raise CryptoOnchainContractError("component_kind must be ComponentKind")
        _require_utc(self.accepted_at, "accepted_at")
        if self.source_revision is not None:
            _require_text(self.source_revision, "source_revision")

    @property
    def registry_key(self) -> tuple[str, str]:
        return (self.chain_id, self.address)


@dataclass(frozen=True, kw_only=True)
class ProjectRelationship:
    project_id: str
    chain_id: str
    address: str
    role: RelationshipRole
    status: RelationshipStatus
    source_ref: str
    accepted_at: datetime
    evidence_note: str | None = None
    source_revision: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.project_id, "project_id"),
            (self.chain_id, "chain_id"),
            (self.address, "address"),
            (self.source_ref, "source_ref"),
        ):
            _require_text(value, field)
        if not isinstance(self.role, RelationshipRole):
            raise CryptoOnchainContractError("role must be RelationshipRole")
        if not isinstance(self.status, RelationshipStatus):
            raise CryptoOnchainContractError("status must be RelationshipStatus")
        _require_utc(self.accepted_at, "accepted_at")
        if self.evidence_note is not None:
            _require_text(self.evidence_note, "evidence_note", max_length=2048)
        if self.source_revision is not None:
            _require_text(self.source_revision, "source_revision")

    @property
    def logical_key(self) -> tuple[str, str, str, RelationshipRole]:
        return (self.project_id, self.chain_id, self.address, self.role)

    @property
    def registry_key(self) -> tuple[str, str, str, RelationshipRole, str]:
        return (*self.logical_key, self.source_ref)


@dataclass(frozen=True, kw_only=True)
class ConfirmedTransferFact:
    chain_id: str
    tx_hash: str
    transfer_index: int
    asset_id: str
    amount: Decimal
    confirmed_at: datetime
    available_at: datetime
    accepted_at: datetime
    source_ref: str
    from_address: str | None = None
    to_address: str | None = None
    block_number: int | None = None
    usd_notional: Decimal | None = None
    source_revision: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.chain_id, "chain_id"),
            (self.tx_hash, "tx_hash"),
            (self.asset_id, "asset_id"),
            (self.source_ref, "source_ref"),
        ):
            _require_text(value, field)
        _require_nonnegative_int(self.transfer_index, "transfer_index")
        _require_nonnegative_int(self.block_number, "block_number")
        _require_decimal(self.amount, "amount")
        if self.usd_notional is not None:
            _require_decimal(self.usd_notional, "usd_notional")
        for value, field in (
            (self.confirmed_at, "confirmed_at"),
            (self.available_at, "available_at"),
            (self.accepted_at, "accepted_at"),
        ):
            _require_utc(value, field)
        if self.confirmed_at > self.available_at:
            raise CryptoOnchainContractError("confirmed_at cannot be later than available_at")
        if self.available_at > self.accepted_at:
            raise CryptoOnchainContractError("available_at cannot be later than accepted_at")
        if self.from_address is None and self.to_address is None:
            raise CryptoOnchainContractError("at least one transfer endpoint must be present")
        for value, field in ((self.from_address, "from_address"), (self.to_address, "to_address")):
            if value is not None:
                _require_text(value, field)
        if self.source_revision is not None:
            _require_text(self.source_revision, "source_revision")

    @property
    def registry_key(self) -> tuple[str, str, int]:
        return (self.chain_id, self.tx_hash, self.transfer_index)
