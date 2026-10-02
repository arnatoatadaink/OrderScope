"""UWBS-094 source-neutral volatility benchmark observation contract.

The contract keeps a published volatility index, an exchange-traded volatility
future, and an ETP proxy distinct.  A VIX-linked ETF/ETN is never treated as the
VIX index itself, and futures maturity/term-structure information remains an
explicit product attribute rather than an inferred spot observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance


class VolatilityInstrumentKind(StrEnum):
    PUBLISHED_INDEX = "published_index"
    FUTURE = "future"
    ETP_PROXY = "etp_proxy"
    IMPLIED_VOLATILITY_INDEX = "implied_volatility_index"


class VolatilityObservationKind(StrEnum):
    LEVEL = "level"
    SETTLEMENT = "settlement"
    CLOSE = "close"
    NAV = "nav"
    MARKET_PRICE = "market_price"


@dataclass(frozen=True, kw_only=True)
class VolatilityBenchmarkObservation:
    subject_ref: str
    instrument_ref: str
    instrument_kind: VolatilityInstrumentKind
    observation_kind: VolatilityObservationKind
    value: Decimal
    observed_at: datetime
    accepted_at: datetime
    provenance: Provenance
    underlying_ref: str | None = None
    horizon_days: int | None = None
    maturity_date: date | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        _canonical(self.subject_ref, "subject_ref")
        _canonical(self.instrument_ref, "instrument_ref")
        if not isinstance(self.instrument_kind, VolatilityInstrumentKind):
            raise ContractViolation("instrument_kind must be VolatilityInstrumentKind")
        if not isinstance(self.observation_kind, VolatilityObservationKind):
            raise ContractViolation("observation_kind must be VolatilityObservationKind")
        if isinstance(self.value, bool) or not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ContractViolation("value must be a finite Decimal")
        if self.value < 0:
            raise ContractViolation("volatility benchmark value cannot be negative")
        _utc(self.observed_at, "observed_at")
        _utc(self.accepted_at, "accepted_at")
        if self.accepted_at < self.observed_at:
            raise ContractViolation("accepted_at cannot precede observed_at")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")
        if self.underlying_ref is not None:
            _canonical(self.underlying_ref, "underlying_ref")
        if self.horizon_days is not None:
            if isinstance(self.horizon_days, bool) or not isinstance(self.horizon_days, int) or self.horizon_days <= 0:
                raise ContractViolation("horizon_days must be a positive integer")
        if self.currency is not None:
            _canonical(self.currency, "currency")

        if self.instrument_kind is VolatilityInstrumentKind.FUTURE:
            if self.maturity_date is None:
                raise ContractViolation("future observation requires maturity_date")
            if self.observation_kind not in {
                VolatilityObservationKind.SETTLEMENT,
                VolatilityObservationKind.CLOSE,
                VolatilityObservationKind.MARKET_PRICE,
            }:
                raise ContractViolation("future observation kind is unsupported")
        elif self.maturity_date is not None:
            raise ContractViolation("maturity_date is reserved for futures")

        if self.instrument_kind in {
            VolatilityInstrumentKind.PUBLISHED_INDEX,
            VolatilityInstrumentKind.IMPLIED_VOLATILITY_INDEX,
        }:
            if self.currency is not None:
                raise ContractViolation("volatility index level must not masquerade as currency price")
            if self.observation_kind is not VolatilityObservationKind.LEVEL:
                raise ContractViolation("volatility index observation must use LEVEL")

        if self.instrument_kind is VolatilityInstrumentKind.ETP_PROXY:
            if self.observation_kind not in {
                VolatilityObservationKind.NAV,
                VolatilityObservationKind.MARKET_PRICE,
                VolatilityObservationKind.CLOSE,
            }:
                raise ContractViolation("ETP proxy requires NAV/market-price/close observation")
            if self.currency is None:
                raise ContractViolation("ETP proxy price requires currency")

    @property
    def unit(self) -> str:
        if self.instrument_kind in {
            VolatilityInstrumentKind.PUBLISHED_INDEX,
            VolatilityInstrumentKind.IMPLIED_VOLATILITY_INDEX,
            VolatilityInstrumentKind.FUTURE,
        }:
            return "volatility_points"
        return f"currency_{self.currency}"

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        return Fact(
            record_id=record_id,
            schema_version="volatility-benchmark-observation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.observed_at,
            provenance=self.provenance,
            fact_type=f"volatility_benchmark.{self.instrument_kind.value}.{self.observation_kind.value}",
            value={
                "instrument_ref": self.instrument_ref,
                "instrument_kind": self.instrument_kind.value,
                "observation_kind": self.observation_kind.value,
                "value": str(self.value),
                "unit": self.unit,
                "observed_at": self.observed_at.isoformat(),
                "underlying_ref": self.underlying_ref,
                "horizon_days": self.horizon_days,
                "maturity_date": self.maturity_date.isoformat() if self.maturity_date else None,
            },
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
        )


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
