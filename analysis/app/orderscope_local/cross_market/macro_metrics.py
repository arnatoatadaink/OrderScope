"""UWBS-012 rate-curve and cross-country Derived Metrics.

The module consumes normalized UWBS-011 observations plus their Fact record IDs.
It computes deterministic spreads, deltas, and velocities only.  Causal labels such
as carry unwind or capital movement are intentionally outside this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from orderscope_local.contracts import ContractViolation, DerivedMetric, MacroMarketObservation, MacroMarketRegion, MacroMarketSeriesKind

METHOD_VERSION = "macro-derived-metrics-v0.1"


@dataclass(frozen=True, kw_only=True)
class MacroMetricInput:
    fact_record_id: str
    observation: MacroMarketObservation

    def __post_init__(self) -> None:
        if not isinstance(self.fact_record_id, str) or not self.fact_record_id.strip():
            raise ContractViolation("fact_record_id must be non-empty canonical text")
        if not isinstance(self.observation, MacroMarketObservation):
            raise ContractViolation("observation must be MacroMarketObservation")


class CurveShape(StrEnum):
    NORMAL = "NORMAL"
    INVERTED = "INVERTED"
    FLAT = "FLAT"


class CurveChange(StrEnum):
    STEEPENING = "STEEPENING"
    FLATTENING = "FLATTENING"
    UNCHANGED = "UNCHANGED"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _yield(point: MacroMetricInput, *, region: MacroMarketRegion, tenor: str) -> None:
    observation = point.observation
    if observation.series_kind is not MacroMarketSeriesKind.SOVEREIGN_YIELD:
        raise ContractViolation("rate-curve input must be a sovereign yield")
    if observation.region is not region or observation.tenor != tenor:
        raise ContractViolation(f"expected {region.value} sovereign yield tenor {tenor}")


def _same_unit(*points: MacroMetricInput) -> str:
    units = {point.observation.unit for point in points}
    if len(units) != 1:
        raise ContractViolation("macro metric inputs must use the same unit")
    return next(iter(units))


def _as_of(*points: MacroMetricInput) -> datetime:
    return max(point.observation.provenance.available_at for point in points)


def _metric(
    *,
    metric_name: str,
    value: float | str,
    unit: str | None,
    points: tuple[MacroMetricInput, ...],
    accepted_at: datetime,
) -> DerivedMetric:
    _utc(accepted_at, "accepted_at")
    as_of = _as_of(*points)
    if accepted_at < as_of:
        raise ContractViolation("accepted_at cannot precede metric as_of")
    if isinstance(value, float) and not isfinite(value):
        raise ContractViolation("derived macro metric must be finite")
    return DerivedMetric(
        record_id=f"derived:{metric_name}:{accepted_at.isoformat()}",
        schema_version="macro-derived-metric-v0.1",
        subject_ref="macro:cross-market",
        accepted_at=accepted_at,
        created_at=as_of,
        metric_name=metric_name,
        value=value,
        calculation_method="deterministic_macro_arithmetic",
        method_version=METHOD_VERSION,
        as_of=as_of,
        input_record_ids=tuple(point.fact_record_id for point in points),
        unit=unit,
    )


def curve_slope(
    *,
    short: MacroMetricInput,
    long: MacroMetricInput,
    region: MacroMarketRegion,
    short_tenor: str,
    long_tenor: str,
    accepted_at: datetime,
) -> DerivedMetric:
    _yield(short, region=region, tenor=short_tenor)
    _yield(long, region=region, tenor=long_tenor)
    unit = _same_unit(short, long)
    value = float(long.observation.value) - float(short.observation.value)
    return _metric(
        metric_name=f"{region.value.lower()}_{short_tenor.lower()}s{long_tenor.lower()}_slope",
        value=value,
        unit=unit,
        points=(short, long),
        accepted_at=accepted_at,
    )


def cross_country_spread(
    *,
    us: MacroMetricInput,
    jp: MacroMetricInput,
    tenor: str,
    accepted_at: datetime,
) -> DerivedMetric:
    _yield(us, region=MacroMarketRegion.US, tenor=tenor)
    _yield(jp, region=MacroMarketRegion.JP, tenor=tenor)
    unit = _same_unit(us, jp)
    return _metric(
        metric_name=f"us_jp_{tenor.lower()}_spread",
        value=float(us.observation.value) - float(jp.observation.value),
        unit=unit,
        points=(us, jp),
        accepted_at=accepted_at,
    )


def series_delta(
    *,
    start: MacroMetricInput,
    end: MacroMetricInput,
    accepted_at: datetime,
) -> DerivedMetric:
    left, right = start.observation, end.observation
    if (left.series_kind, left.region, left.series_id, left.tenor) != (
        right.series_kind,
        right.region,
        right.series_id,
        right.tenor,
    ):
        raise ContractViolation("series delta requires the same normalized macro series")
    unit = _same_unit(start, end)
    if right.provenance.available_at <= left.provenance.available_at:
        raise ContractViolation("series delta requires increasing availability time")
    return _metric(
        metric_name=f"{right.series_id.lower()}_delta",
        value=float(right.value) - float(left.value),
        unit=unit,
        points=(start, end),
        accepted_at=accepted_at,
    )


def series_velocity_per_day(
    *,
    start: MacroMetricInput,
    end: MacroMetricInput,
    accepted_at: datetime,
) -> DerivedMetric:
    delta = series_delta(start=start, end=end, accepted_at=accepted_at)
    elapsed = end.observation.provenance.available_at - start.observation.provenance.available_at
    days = elapsed.total_seconds() / 86400.0
    if days <= 0:
        raise ContractViolation("series velocity requires positive elapsed time")
    return DerivedMetric(
        record_id=f"derived:{end.observation.series_id.lower()}_velocity:{accepted_at.isoformat()}",
        schema_version="macro-derived-metric-v0.1",
        subject_ref="macro:cross-market",
        accepted_at=accepted_at,
        created_at=delta.as_of,
        metric_name=f"{end.observation.series_id.lower()}_velocity_per_day",
        value=float(delta.value) / days,
        calculation_method="fixed_window_delta_per_day",
        method_version=METHOD_VERSION,
        as_of=delta.as_of,
        input_record_ids=delta.input_record_ids,
        unit=f"{end.observation.unit}_per_day",
    )


def classify_curve_shape(slope: float, *, flat_tolerance: float = 0.0) -> CurveShape:
    if not isfinite(float(slope)) or flat_tolerance < 0:
        raise ContractViolation("curve shape requires finite slope and non-negative tolerance")
    if abs(float(slope)) <= flat_tolerance:
        return CurveShape.FLAT
    return CurveShape.INVERTED if slope < 0 else CurveShape.NORMAL


def classify_curve_change(previous_slope: float, current_slope: float, *, tolerance: float = 0.0) -> CurveChange:
    if not isfinite(float(previous_slope)) or not isfinite(float(current_slope)) or tolerance < 0:
        raise ContractViolation("curve change requires finite slopes and non-negative tolerance")
    change = float(current_slope) - float(previous_slope)
    if abs(change) <= tolerance:
        return CurveChange.UNCHANGED
    return CurveChange.STEEPENING if change > 0 else CurveChange.FLATTENING
