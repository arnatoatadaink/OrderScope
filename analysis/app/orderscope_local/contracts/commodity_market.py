"""UWBS-080 source-neutral crude-oil price observation contract.

The contract deliberately separates benchmark spot references from listed
futures contracts.  A WTI or Brent futures price is not silently interchangeable
with a physical/reference spot series, and ETF proxies such as USO are outside
this commodity-price Fact boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp


class CrudeBenchmark(StrEnum):
    WTI = "WTI"
    BRENT = "BRENT"


class CommodityPriceForm(StrEnum):
    SPOT_REFERENCE = "spot_reference"
    FUTURES_CONTRACT = "futures_contract"


class CommodityVenue(StrEnum):
    NYMEX = "NYMEX"
    ICE_FUTURES_EUROPE = "ICE_FUTURES_EUROPE"


class CommodityLocation(StrEnum):
    CUSHING_OK = "CUSHING_OK"
    EUROPE = "EUROPE"


@dataclass(frozen=True, kw_only=True)
class CommodityPriceObservation:
    """One directly observed crude-price Fact with explicit market identity.

    Negative values are intentionally permitted. Listed WTI futures traded below
    zero historically, so positivity is not a valid invariant for the generic
    observation contract.
    """

    subject_ref: str
    benchmark: CrudeBenchmark
    price_form: CommodityPriceForm
    series_id: str
    value: float
    unit: str
    observed_at: SourceTimestamp
    accepted_at: datetime
    provenance: Provenance
    location: CommodityLocation | None = None
    venue: CommodityVenue | None = None
    contract_code: str | None = None
    delivery_month: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.benchmark, CrudeBenchmark):
            raise ContractViolation("benchmark must be CrudeBenchmark")
        if not isinstance(self.price_form, CommodityPriceForm):
            raise ContractViolation("price_form must be CommodityPriceForm")
        for value, field in (
            (self.subject_ref, "subject_ref"),
            (self.series_id, "series_id"),
            (self.unit, "unit"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if self.unit != "usd_per_barrel":
            raise ContractViolation("commodity crude price unit must be usd_per_barrel")
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

        for value, field in (
            (self.contract_code, "contract_code"),
            (self.delivery_month, "delivery_month"),
        ):
            if value is not None and (
                not isinstance(value, str) or not value.strip() or value != value.strip()
            ):
                raise ContractViolation(f"{field} must be canonical non-empty text")

        if self.price_form is CommodityPriceForm.SPOT_REFERENCE:
            if self.location is None:
                raise ContractViolation("spot reference requires location")
            if self.venue is not None or self.contract_code is not None or self.delivery_month is not None:
                raise ContractViolation("spot reference cannot contain futures contract fields")
            if self.benchmark is CrudeBenchmark.WTI and self.location is not CommodityLocation.CUSHING_OK:
                raise ContractViolation("WTI spot reference must use CUSHING_OK location")
            if self.benchmark is CrudeBenchmark.BRENT and self.location is not CommodityLocation.EUROPE:
                raise ContractViolation("Brent spot reference must use EUROPE location")
        elif self.price_form is CommodityPriceForm.FUTURES_CONTRACT:
            if self.location is not None:
                raise ContractViolation("futures contract cannot use spot location")
            if self.venue is None or self.contract_code is None or self.delivery_month is None:
                raise ContractViolation("futures contract requires venue, contract_code, and delivery_month")
            if self.benchmark is CrudeBenchmark.WTI and self.venue is not CommodityVenue.NYMEX:
                raise ContractViolation("WTI futures contract must use NYMEX venue")
            if self.benchmark is CrudeBenchmark.BRENT and self.venue is not CommodityVenue.ICE_FUTURES_EUROPE:
                raise ContractViolation("Brent futures contract must use ICE_FUTURES_EUROPE venue")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        return Fact(
            record_id=record_id,
            schema_version="commodity-price-observation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type=f"commodity_price.{self.price_form.value}",
            value=float(self.value),
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
            unit=self.unit,
            period_start=self.observed_at,
            period_end=self.observed_at,
        )
