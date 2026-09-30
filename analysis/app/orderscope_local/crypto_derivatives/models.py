"""Source-neutral contracts for crypto derivatives observations.

UWBS-068 keeps observed exchange/provider fields separate from deterministic
metrics and later market-structure interpretations.  Aggregate derivatives
observations never imply trader identity, direction of net capital flow, or a
position ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite


class CryptoDerivativeContractError(ValueError):
    """Raised when a derivatives observation violates the UWBS-068 contract."""


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise CryptoDerivativeContractError(f"{field} must be non-blank and bounded")


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise CryptoDerivativeContractError(f"{field} must be normalized to UTC")


def _finite_optional(value: float | None, field: str, *, nonnegative: bool = False) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CryptoDerivativeContractError(f"{field} must be a finite number")
    if nonnegative and value < 0:
        raise CryptoDerivativeContractError(f"{field} cannot be negative")


class ContractType(StrEnum):
    PERPETUAL = "perpetual"
    FUTURE = "future"


class MarginType(StrEnum):
    LINEAR = "linear"
    INVERSE = "inverse"
    UNKNOWN = "unknown"


@dataclass(frozen=True, kw_only=True)
class CryptoDerivativeObservation:
    observation_id: str
    venue: str
    instrument_id: str
    contract_type: ContractType
    margin_type: MarginType
    quote_asset: str
    observed_at: datetime
    available_at: datetime
    accepted_at: datetime
    source_ref: str
    source_revision: str | None = None
    open_interest_contracts: float | None = None
    open_interest_base: float | None = None
    open_interest_usd: float | None = None
    funding_rate: float | None = None
    funding_interval_seconds: int | None = None
    mark_price: float | None = None
    index_price: float | None = None
    basis: float | None = None
    derivatives_volume_usd: float | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.observation_id, "observation_id"),
            (self.venue, "venue"),
            (self.instrument_id, "instrument_id"),
            (self.quote_asset, "quote_asset"),
            (self.source_ref, "source_ref"),
        ):
            _require_text(value, field)
        if not isinstance(self.contract_type, ContractType):
            raise CryptoDerivativeContractError("contract_type must be ContractType")
        if not isinstance(self.margin_type, MarginType):
            raise CryptoDerivativeContractError("margin_type must be MarginType")
        for value, field in (
            (self.observed_at, "observed_at"),
            (self.available_at, "available_at"),
            (self.accepted_at, "accepted_at"),
        ):
            _require_utc(value, field)
        if self.observed_at > self.available_at:
            raise CryptoDerivativeContractError("observed_at cannot be later than available_at")
        if self.available_at > self.accepted_at:
            raise CryptoDerivativeContractError("available_at cannot be later than accepted_at")
        if self.source_revision is not None:
            _require_text(self.source_revision, "source_revision")
        for value, field in (
            (self.open_interest_contracts, "open_interest_contracts"),
            (self.open_interest_base, "open_interest_base"),
            (self.open_interest_usd, "open_interest_usd"),
            (self.mark_price, "mark_price"),
            (self.index_price, "index_price"),
            (self.derivatives_volume_usd, "derivatives_volume_usd"),
        ):
            _finite_optional(value, field, nonnegative=True)
        _finite_optional(self.funding_rate, "funding_rate")
        _finite_optional(self.basis, "basis")
        if self.funding_interval_seconds is not None:
            if not isinstance(self.funding_interval_seconds, int) or self.funding_interval_seconds <= 0:
                raise CryptoDerivativeContractError("funding_interval_seconds must be a positive integer")
            if self.funding_rate is None:
                raise CryptoDerivativeContractError("funding interval requires funding_rate")
        if all(
            value is None
            for value in (
                self.open_interest_contracts,
                self.open_interest_base,
                self.open_interest_usd,
                self.funding_rate,
                self.mark_price,
                self.index_price,
                self.basis,
                self.derivatives_volume_usd,
            )
        ):
            raise CryptoDerivativeContractError("observation must contain at least one derivatives field")


@dataclass(frozen=True, kw_only=True)
class LiquidationObservation:
    observation_id: str
    venue: str
    instrument_id: str
    bucket_start: datetime
    bucket_end: datetime
    accepted_at: datetime
    source_ref: str
    long_liquidation_usd: float
    short_liquidation_usd: float
    event_count: int | None = None
    source_revision: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.observation_id, "observation_id"),
            (self.venue, "venue"),
            (self.instrument_id, "instrument_id"),
            (self.source_ref, "source_ref"),
        ):
            _require_text(value, field)
        for value, field in (
            (self.bucket_start, "bucket_start"),
            (self.bucket_end, "bucket_end"),
            (self.accepted_at, "accepted_at"),
        ):
            _require_utc(value, field)
        if self.bucket_start >= self.bucket_end:
            raise CryptoDerivativeContractError("bucket_start must be earlier than bucket_end")
        if self.bucket_end > self.accepted_at:
            raise CryptoDerivativeContractError("bucket_end cannot be later than accepted_at")
        _finite_optional(self.long_liquidation_usd, "long_liquidation_usd", nonnegative=True)
        _finite_optional(self.short_liquidation_usd, "short_liquidation_usd", nonnegative=True)
        if self.event_count is not None and (not isinstance(self.event_count, int) or self.event_count < 0):
            raise CryptoDerivativeContractError("event_count must be a non-negative integer")
        if self.source_revision is not None:
            _require_text(self.source_revision, "source_revision")
