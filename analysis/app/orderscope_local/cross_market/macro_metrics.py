"""UWBS-012 deterministic macro Derived Metrics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from orderscope_local.contracts import (
    ContractViolation,
    DerivedMetric,
    MacroMarketObservation,
    MacroMarketRegion,
    MacroMarketSeriesKind,
)

METHOD_VERSION = "macro-derived-metrics-v0.1"


@dataclass(frozen=True, kw_only=True)
class MacroMetricInput:
    fact_record_id: str
    observation: MacroMarketObservation

    def __post_init__(self) -> None:
        if not self.fact_record_id.strip():
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


def _stamp(value: datetime) -> str:
    _utc(value, "identifier timestamp")
    return value.strftime("%Y%m%dT%H%M%SZ")


def _yield(point: MacroMetricInput, region: MacroMarketRegion, tenor: str) -> None:
    obs = point.observation
    if obs.series_kind is not MacroMarketSeriesKind.SOVEREIGN_YIELD:
        raise ContractViolation("rate-curve input must be a sovereign yield")
    if obs.region is not region or obs.tenor != tenor:
        raise ContractViolation(f"expected {region.value} sovereign yield tenor {tenor}")


def _same_unit(*points: MacroMetricInput) -> str:
    units = {p.observation.unit for p in points}
    if len(units) != 1:
        raise ContractViolation("macro metric inputs must use the same unit")
    return next(iter(units))


def _build(name: str, value: float, unit: str, points: tuple[MacroMetricInput, ...], accepted_at: datetime, method: str = "deterministic_macro_arithmetic") -> DerivedMetric:
    _utc(accepted_at, "accepted_at")
    as_of = max(p.observation.provenance.available_at for p in points)
    if accepted_at < as_of:
        raise ContractViolation("accepted_at cannot precede metric as_of")
    if not isfinite(float(value)):
        raise ContractViolation("derived macro metric must be finite")
    return DerivedMetric(
        record_id=f"derived:{name}:{_stamp(accepted_at)}",
        schema_version="macro-derived-metric-v0.1",
        subject_ref="macro:cross-market",
        accepted_at=accepted_at,
        created_at=as_of,
        metric_name=name,
        value=float(value),
        calculation_method=method,
        method_version=METHOD_VERSION,
        as_of=as_of,
        input_record_ids=tuple(p.fact_record_id for p in points),
        unit=unit,
    )


def curve_slope(*, short: MacroMetricInput, long: MacroMetricInput, region: MacroMarketRegion, short_tenor: str, long_tenor: str, accepted_at: datetime) -> DerivedMetric:
    _yield(short, region, short_tenor)
    _yield(long, region, long_tenor)
    return _build(
        f"{region.value.lower()}_{short_tenor.lower()}s{long_tenor.lower()}_slope",
        long.observation.value - short.observation.value,
        _same_unit(short, long),
        (short, long),
        accepted_at,
    )


def cross_country_spread(*, us: MacroMetricInput, jp: MacroMetricInput, tenor: str, accepted_at: datetime) -> DerivedMetric:
    _yield(us, MacroMarketRegion.US, tenor)
    _yield(jp, MacroMarketRegion.JP, tenor)
    return _build(
        f"us_jp_{tenor.lower()}_spread",
        us.observation.value - jp.observation.value,
        _same_unit(us, jp),
        (us, jp),
        accepted_at,
    )


def series_delta(*, start: MacroMetricInput, end: MacroMetricInput, accepted_at: datetime) -> DerivedMetric:
    a, b = start.observation, end.observation
    if (a.series_kind, a.region, a.series_id, a.tenor) != (b.series_kind, b.region, b.series_id, b.tenor):
        raise ContractViolation("series delta requires the same normalized macro series")
    if b.provenance.available_at <= a.provenance.available_at:
        raise ContractViolation("series delta requires increasing availability time")
    return _build(f"{b.series_id.lower()}_delta", b.value - a.value, _same_unit(start, end), (start, end), accepted_at)


def series_velocity_per_day(*, start: MacroMetricInput, end: MacroMetricInput, accepted_at: datetime) -> DerivedMetric:
    delta = series_delta(start=start, end=end, accepted_at=accepted_at)
    days = (end.observation.provenance.available_at - start.observation.provenance.available_at).total_seconds() / 86400.0
    return _build(
        f"{end.observation.series_id.lower()}_velocity_per_day",
        float(delta.value) / days,
        f"{end.observation.unit}_per_day",
        (start, end),
        accepted_at,
        method="fixed_window_delta_per_day",
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
    change = current_slope - previous_slope
    if abs(change) <= tolerance:
        return CurveChange.UNCHANGED
    return CurveChange.STEEPENING if change > 0 else CurveChange.FLATTENING
