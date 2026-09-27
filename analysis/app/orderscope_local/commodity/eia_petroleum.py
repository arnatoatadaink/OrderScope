"""UWBS-081 EIA petroleum row normalization boundary.

The EIA API v2 currently returns data values as strings.  This module converts
one configured petroleum row into a provider-neutral
``CommodityFundamentalObservation`` while preserving the source period and
series identity.  HTTP transport, API keys, pagination, and retry policy remain
outside this module.
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import isfinite
from typing import Mapping, Any

from orderscope_local.contracts import (
    CommodityFundamentalCadence,
    CommodityFundamentalMeasure,
    CommodityFundamentalObservation,
    CommodityGeography,
    CommodityProduct,
    ContractViolation,
    Provenance,
    SourceTimestamp,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class EiaPetroleumSeriesProfile:
    """Configured identity for one EIA petroleum series/facet selection."""

    route: str
    series_id: str
    subject_ref: str
    measure: CommodityFundamentalMeasure
    product: CommodityProduct
    geography: CommodityGeography
    cadence: CommodityFundamentalCadence
    normalized_unit: str

    def __post_init__(self) -> None:
        for value, field in (
            (self.route, "route"),
            (self.series_id, "series_id"),
            (self.subject_ref, "subject_ref"),
            (self.normalized_unit, "normalized_unit"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"EIA profile {field} must be canonical non-empty text")
        if not self.route.startswith("/v2/petroleum/") or not self.route.endswith("/data/"):
            raise ContractViolation("EIA petroleum route must be a canonical /v2/petroleum/.../data/ path")


def normalize_eia_petroleum_row(
    *,
    profile: EiaPetroleumSeriesProfile,
    row: Mapping[str, Any],
    accepted_at: datetime,
    provenance: Provenance,
) -> CommodityFundamentalObservation:
    """Normalize one EIA API v2 row without inferring missing/withheld values."""

    if not isinstance(profile, EiaPetroleumSeriesProfile):
        raise ContractViolation("profile must be EiaPetroleumSeriesProfile")
    if not isinstance(row, Mapping):
        raise ContractViolation("EIA row must be a mapping")

    if "series" in row and row["series"] != profile.series_id:
        raise ContractViolation("EIA row series does not match configured profile")

    raw_value = row.get("value")
    if isinstance(raw_value, bool) or not isinstance(raw_value, (str, int, float)):
        raise ContractViolation("EIA value must be a numeric string or number")
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as error:
        raise ContractViolation("EIA value is missing, withheld, or non-numeric") from error
    if not isfinite(value):
        raise ContractViolation("EIA value must be finite")

    source_units = row.get("units")
    if source_units is not None:
        if not isinstance(source_units, str) or not source_units.strip():
            raise ContractViolation("EIA units must be non-empty text when present")
        if _normalize_unit_text(source_units) != _normalize_unit_text(profile.normalized_unit):
            raise ContractViolation("EIA units do not match configured normalized unit")

    period = row.get("period")
    if not isinstance(period, str) or not period.strip() or period != period.strip():
        raise ContractViolation("EIA row requires canonical period text")
    period_start, period_end = _period_bounds(period, profile.cadence)

    return CommodityFundamentalObservation(
        subject_ref=profile.subject_ref,
        measure=profile.measure,
        product=profile.product,
        geography=profile.geography,
        cadence=profile.cadence,
        series_id=profile.series_id,
        value=value,
        unit=profile.normalized_unit,
        period_start=SourceTimestamp.date_only(period_start),
        period_end=SourceTimestamp.date_only(period_end),
        accepted_at=accepted_at,
        provenance=provenance,
    )


def _period_bounds(period: str, cadence: CommodityFundamentalCadence) -> tuple[date, date]:
    try:
        if cadence is CommodityFundamentalCadence.WEEKLY:
            end = date.fromisoformat(period)
            return end - timedelta(days=6), end
        if cadence is CommodityFundamentalCadence.MONTHLY:
            year_text, month_text = period.split("-", maxsplit=1)
            year = int(year_text)
            month = int(month_text)
            start = date(year, month, 1)
            return start, date(year, month, monthrange(year, month)[1])
        if cadence is CommodityFundamentalCadence.ANNUAL:
            year = int(period)
            return date(year, 1, 1), date(year, 12, 31)
    except (TypeError, ValueError) as error:
        raise ContractViolation("EIA period does not match configured cadence") from error
    raise ContractViolation("unsupported EIA cadence")


def _normalize_unit_text(value: str) -> str:
    normalized = "_".join(value.strip().lower().replace("/", " per ").replace("%", " percent ").split())
    aliases = {
        "thousand_barrels": "thousand_barrels",
        "thousand_barrels_per_day": "thousand_barrels_per_day",
        "percent": "percent",
    }
    return aliases.get(normalized, normalized)
