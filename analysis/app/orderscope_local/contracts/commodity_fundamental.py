"""UWBS-081 provider-neutral commodity supply/fundamental observation contract.

This boundary stores directly observed petroleum supply-chain fundamentals as
Facts.  It deliberately preserves source semantics: EIA ``product supplied`` is
stored as product supplied, not silently promoted to final demand/consumption;
stocks are inventory levels, while production/import/export/input observations
are flows or rates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp


class CommodityFundamentalMeasure(StrEnum):
    COMMERCIAL_STOCKS = "commercial_stocks"
    CUSHING_STOCKS = "cushing_stocks"
    SPR_STOCKS = "spr_stocks"
    FIELD_PRODUCTION = "field_production"
    REFINERY_INPUTS = "refinery_inputs"
    REFINERY_UTILIZATION = "refinery_utilization"
    IMPORTS = "imports"
    EXPORTS = "exports"
    PRODUCT_SUPPLIED = "product_supplied"


class CommodityProduct(StrEnum):
    CRUDE_OIL = "crude_oil"
    MOTOR_GASOLINE = "motor_gasoline"
    DISTILLATE_FUEL_OIL = "distillate_fuel_oil"
    JET_FUEL = "jet_fuel"
    TOTAL_PETROLEUM_PRODUCTS = "total_petroleum_products"


class CommodityGeography(StrEnum):
    US = "US"
    PADD_1 = "PADD_1"
    PADD_2 = "PADD_2"
    PADD_3 = "PADD_3"
    PADD_4 = "PADD_4"
    PADD_5 = "PADD_5"
    CUSHING_OK = "CUSHING_OK"


class CommodityFundamentalCadence(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


_LEVEL_MEASURES = {
    CommodityFundamentalMeasure.COMMERCIAL_STOCKS,
    CommodityFundamentalMeasure.CUSHING_STOCKS,
    CommodityFundamentalMeasure.SPR_STOCKS,
}

_FLOW_MEASURES = {
    CommodityFundamentalMeasure.FIELD_PRODUCTION,
    CommodityFundamentalMeasure.REFINERY_INPUTS,
    CommodityFundamentalMeasure.IMPORTS,
    CommodityFundamentalMeasure.EXPORTS,
    CommodityFundamentalMeasure.PRODUCT_SUPPLIED,
}


@dataclass(frozen=True, kw_only=True)
class CommodityFundamentalObservation:
    """One source-observed petroleum fundamental with explicit semantics."""

    subject_ref: str
    measure: CommodityFundamentalMeasure
    product: CommodityProduct
    geography: CommodityGeography
    cadence: CommodityFundamentalCadence
    series_id: str
    value: float
    unit: str
    period_start: SourceTimestamp
    period_end: SourceTimestamp
    accepted_at: datetime
    provenance: Provenance

    def __post_init__(self) -> None:
        if not isinstance(self.measure, CommodityFundamentalMeasure):
            raise ContractViolation("measure must be CommodityFundamentalMeasure")
        if not isinstance(self.product, CommodityProduct):
            raise ContractViolation("product must be CommodityProduct")
        if not isinstance(self.geography, CommodityGeography):
            raise ContractViolation("geography must be CommodityGeography")
        if not isinstance(self.cadence, CommodityFundamentalCadence):
            raise ContractViolation("cadence must be CommodityFundamentalCadence")
        for value, field in (
            (self.subject_ref, "subject_ref"),
            (self.series_id, "series_id"),
            (self.unit, "unit"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not isfinite(float(self.value)):
            raise ContractViolation("value must be a finite numeric observation")
        if not isinstance(self.period_start, SourceTimestamp) or not isinstance(self.period_end, SourceTimestamp):
            raise ContractViolation("period_start and period_end must be SourceTimestamp")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() != timedelta(0):
            raise ContractViolation("accepted_at must be normalized to UTC")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")

        if self.measure in _LEVEL_MEASURES and self.unit != "thousand_barrels":
            raise ContractViolation("stock measures must use thousand_barrels")
        if self.measure in _FLOW_MEASURES and self.unit != "thousand_barrels_per_day":
            raise ContractViolation("flow measures must use thousand_barrels_per_day")
        if self.measure is CommodityFundamentalMeasure.REFINERY_UTILIZATION and self.unit != "percent":
            raise ContractViolation("refinery utilization must use percent")

        if self.measure is CommodityFundamentalMeasure.CUSHING_STOCKS:
            if self.product is not CommodityProduct.CRUDE_OIL:
                raise ContractViolation("Cushing stocks require crude_oil product")
            if self.geography is not CommodityGeography.CUSHING_OK:
                raise ContractViolation("Cushing stocks require CUSHING_OK geography")
        elif self.geography is CommodityGeography.CUSHING_OK:
            raise ContractViolation("CUSHING_OK geography is reserved for Cushing stocks")

        if self.measure is CommodityFundamentalMeasure.SPR_STOCKS:
            if self.product is not CommodityProduct.CRUDE_OIL:
                raise ContractViolation("SPR stocks require crude_oil product")
            if self.geography is not CommodityGeography.US:
                raise ContractViolation("SPR stocks require US geography")

        if self.measure in {
            CommodityFundamentalMeasure.FIELD_PRODUCTION,
            CommodityFundamentalMeasure.REFINERY_INPUTS,
            CommodityFundamentalMeasure.REFINERY_UTILIZATION,
        } and self.product is not CommodityProduct.CRUDE_OIL:
            raise ContractViolation(f"{self.measure.value} requires crude_oil product")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        return Fact(
            record_id=record_id,
            schema_version="commodity-fundamental-observation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type=f"commodity_fundamental.{self.measure.value}",
            value=float(self.value),
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
            unit=self.unit,
            period_start=self.period_start,
            period_end=self.period_end,
        )
