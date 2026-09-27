"""UWBS-095 volatility-futures term-structure DerivedMetric boundary.

This module derives comparable curve metrics from explicit UWBS-094 futures
observations.  It does not infer ETP roll yield, trading return, or market fear
causality.  Those remain downstream interpretation boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import DerivedMetric
from orderscope_local.contracts.volatility_benchmark import (
    VolatilityBenchmarkObservation,
    VolatilityInstrumentKind,
)


class VolatilityCurveShape(StrEnum):
    CONTANGO = "contango"
    BACKWARDATION = "backwardation"
    FLAT = "flat"


@dataclass(frozen=True, kw_only=True)
class VolatilityFuturePoint:
    record_id: str
    observation: VolatilityBenchmarkObservation

    def __post_init__(self) -> None:
        _canonical(self.record_id, "record_id")
        if not isinstance(self.observation, VolatilityBenchmarkObservation):
            raise ContractViolation("observation must be VolatilityBenchmarkObservation")
        if self.observation.instrument_kind is not VolatilityInstrumentKind.FUTURE:
            raise ContractViolation("term structure accepts volatility futures only")
        if self.observation.maturity_date is None:
            raise ContractViolation("volatility future point requires maturity_date")


@dataclass(frozen=True, kw_only=True)
class VolatilityTermStructure:
    front: VolatilityFuturePoint
    second: VolatilityFuturePoint

    def __post_init__(self) -> None:
        if self.front.record_id == self.second.record_id:
            raise ContractViolation("front and second points require distinct records")
        if self.front.observation.observed_at != self.second.observation.observed_at:
            raise ContractViolation("term-structure points require the same observation timestamp")
        front_maturity = self.front.observation.maturity_date
        second_maturity = self.second.observation.maturity_date
        assert front_maturity is not None and second_maturity is not None
        if front_maturity >= second_maturity:
            raise ContractViolation("front maturity must be earlier than second maturity")

    @property
    def spread(self) -> Decimal:
        """Second-month minus front-month volatility points."""

        return self.second.observation.value - self.front.observation.value

    @property
    def ratio(self) -> Decimal | None:
        if self.front.observation.value == 0:
            return None
        return self.second.observation.value / self.front.observation.value

    @property
    def curve_shape(self) -> VolatilityCurveShape:
        if self.spread > 0:
            return VolatilityCurveShape.CONTANGO
        if self.spread < 0:
            return VolatilityCurveShape.BACKWARDATION
        return VolatilityCurveShape.FLAT


def build_front_second_term_structure(
    points: tuple[VolatilityFuturePoint, ...],
) -> VolatilityTermStructure:
    if not isinstance(points, tuple) or len(points) < 2:
        raise ContractViolation("at least two futures points are required")
    if len({point.record_id for point in points}) != len(points):
        raise ContractViolation("future point record IDs must be unique")
    for point in points:
        if not isinstance(point, VolatilityFuturePoint):
            raise ContractViolation("points must contain VolatilityFuturePoint values")
    ordered = sorted(points, key=lambda point: point.observation.maturity_date)
    return VolatilityTermStructure(front=ordered[0], second=ordered[1])


def materialize_term_structure_metrics(
    structure: VolatilityTermStructure,
    *,
    subject_ref: str,
    accepted_at: datetime,
    record_id_prefix: str,
) -> tuple[DerivedMetric, ...]:
    if not isinstance(structure, VolatilityTermStructure):
        raise ContractViolation("structure must be VolatilityTermStructure")
    _canonical(subject_ref, "subject_ref")
    _canonical(record_id_prefix, "record_id_prefix")
    _utc(accepted_at, "accepted_at")
    observed_at = structure.front.observation.observed_at
    if accepted_at < observed_at:
        raise ContractViolation("accepted_at cannot precede observed_at")

    lineage = (structure.front.record_id, structure.second.record_id)
    metrics = [
        DerivedMetric(
            record_id=f"{record_id_prefix}.front_second_spread",
            schema_version="volatility-term-structure-v0.1",
            subject_ref=subject_ref,
            accepted_at=accepted_at,
            created_at=observed_at,
            metric_name="volatility.front_second_spread",
            value=str(structure.spread),
            calculation_method="second_future_minus_front_future",
            method_version="uwbs-095-v0.1",
            as_of=observed_at,
            input_record_ids=lineage,
            unit="volatility_points",
        ),
        DerivedMetric(
            record_id=f"{record_id_prefix}.curve_shape",
            schema_version="volatility-term-structure-v0.1",
            subject_ref=subject_ref,
            accepted_at=accepted_at,
            created_at=observed_at,
            metric_name="volatility.curve_shape",
            value=structure.curve_shape.value,
            calculation_method="sign_of_front_second_spread",
            method_version="uwbs-095-v0.1",
            as_of=observed_at,
            input_record_ids=lineage,
        ),
    ]
    if structure.ratio is not None:
        metrics.append(
            DerivedMetric(
                record_id=f"{record_id_prefix}.front_second_ratio",
                schema_version="volatility-term-structure-v0.1",
                subject_ref=subject_ref,
                accepted_at=accepted_at,
                created_at=observed_at,
                metric_name="volatility.front_second_ratio",
                value=str(structure.ratio),
                calculation_method="second_future_div_front_future",
                method_version="uwbs-095-v0.1",
                as_of=observed_at,
                input_record_ids=lineage,
                unit="ratio",
            )
        )
    return tuple(metrics)


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
