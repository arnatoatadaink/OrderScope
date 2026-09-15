"""UWBS-011 normalized non-price macro-market Fact contract.

This boundary stores directly observed policy rates, sovereign yields, short rates,
and FX values as Facts. Carry unwind, deleveraging, and capital movement remain
Interpretation/Hypothesis layers and are intentionally absent here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp


class MacroMarketSeriesKind(StrEnum):
    POLICY_RATE = "policy_rate"
    SHORT_MARKET_RATE = "short_market_rate"
    SOVEREIGN_YIELD = "sovereign_yield"
    FX_RATE = "fx_rate"
    VOLATILITY = "volatility"
    FUND_FLOW = "fund_flow"


class MacroMarketRegion(StrEnum):
    US = "US"
    JP = "JP"
    CROSS_MARKET = "CROSS_MARKET"


@dataclass(frozen=True, kw_only=True)
class MacroMarketObservation:
    subject_ref: str
    series_kind: MacroMarketSeriesKind
    region: MacroMarketRegion
    series_id: str
    value: float
    unit: str
    observed_at: SourceTimestamp
    accepted_at: datetime
    provenance: Provenance
    tenor: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.series_kind, MacroMarketSeriesKind):
            raise ContractViolation("series_kind must be MacroMarketSeriesKind")
        if not isinstance(self.region, MacroMarketRegion):
            raise ContractViolation("region must be MacroMarketRegion")
        for value, field in (
            (self.subject_ref, "subject_ref"),
            (self.series_id, "series_id"),
            (self.unit, "unit"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not isfinite(float(self.value)):
            raise ContractViolation("value must be a finite numeric observation")
        if not isinstance(self.observed_at, SourceTimestamp):
            raise ContractViolation("observed_at must be SourceTimestamp")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() != timedelta(0):
            raise ContractViolation("accepted_at must be normalized to UTC")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")
        if self.tenor is not None and (not self.tenor.strip() or self.tenor != self.tenor.strip()):
            raise ContractViolation("tenor must be canonical non-empty text")
        if self.series_kind is MacroMarketSeriesKind.SOVEREIGN_YIELD and self.tenor is None:
            raise ContractViolation("sovereign yield requires tenor")
        if self.series_kind is MacroMarketSeriesKind.FX_RATE and self.region is not MacroMarketRegion.CROSS_MARKET:
            raise ContractViolation("FX rate must use CROSS_MARKET region")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        return Fact(
            record_id=record_id,
            schema_version="macro-market-observation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type=f"macro_market.{self.series_kind.value}",
            value=float(self.value),
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
            unit=self.unit,
            period_start=self.observed_at,
            period_end=self.observed_at,
        )
