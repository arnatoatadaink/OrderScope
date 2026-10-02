"""UWBS-100 volatility historical calibration and Canary evaluation.

This module compares candidate alert rules against repository-backed historical
windows.  It intentionally does not choose or activate a production rule.
Cloudflare capacity is evaluated through the accepted UWBS-086 capacity
contract rather than reimplemented here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from math import isfinite
from statistics import fmean, pstdev

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.cross_asset_canary import CapacityObservation
from .cross_asset_canary_replay import (
    CapacityEnvelope,
    ProjectedCapacityUsage,
    build_capacity_observation,
)


class VolatilityWindowKind(str, Enum):
    CALM = "CALM"
    CORRECTION = "CORRECTION"
    SHOCK = "SHOCK"
    RECOVERY = "RECOVERY"
    MSTR_BTC_DIVERGENCE = "MSTR_BTC_DIVERGENCE"
    CONTROL = "CONTROL"


class CalibrationMethod(str, Enum):
    ABSOLUTE_THRESHOLD = "ABSOLUTE_THRESHOLD"
    EMPIRICAL_PERCENTILE = "EMPIRICAL_PERCENTILE"
    Z_SCORE = "Z_SCORE"


@dataclass(frozen=True, kw_only=True)
class VolatilityCalibrationPoint:
    window_id: str
    window_kind: VolatilityWindowKind
    observed_at: datetime
    signal_value: Decimal
    expected_alert: bool
    event_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ContractViolation("window_id cannot be blank")
        if not isinstance(self.window_kind, VolatilityWindowKind):
            raise ContractViolation("window_kind must be VolatilityWindowKind")
        _utc(self.observed_at, "observed_at")
        if not isinstance(self.signal_value, Decimal) or not self.signal_value.is_finite():
            raise ContractViolation("signal_value must be a finite Decimal")
        if not isinstance(self.expected_alert, bool):
            raise ContractViolation("expected_alert must be boolean")
        if self.event_at is not None:
            _utc(self.event_at, "event_at")


@dataclass(frozen=True, kw_only=True)
class VolatilityCalibrationSuite:
    points: tuple[VolatilityCalibrationPoint, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.points, tuple) or not self.points:
            raise ContractViolation("volatility calibration suite requires points")
        if not all(isinstance(item, VolatilityCalibrationPoint) for item in self.points):
            raise ContractViolation("volatility calibration suite requires VolatilityCalibrationPoint values")
        if len({item.window_id for item in self.points}) != len(self.points):
            raise ContractViolation("volatility calibration window ids must be unique")

    @property
    def covered_window_kinds(self) -> frozenset[VolatilityWindowKind]:
        return frozenset(item.window_kind for item in self.points)

    @property
    def complete_window_coverage(self) -> bool:
        return self.covered_window_kinds == frozenset(VolatilityWindowKind)


@dataclass(frozen=True, kw_only=True)
class CalibrationRule:
    method: CalibrationMethod
    boundary: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.method, CalibrationMethod):
            raise ContractViolation("method must be CalibrationMethod")
        if not isinstance(self.boundary, Decimal) or not self.boundary.is_finite():
            raise ContractViolation("boundary must be a finite Decimal")
        if self.method is CalibrationMethod.EMPIRICAL_PERCENTILE and not (
            Decimal("0") < self.boundary <= Decimal("1")
        ):
            raise ContractViolation("empirical percentile boundary must be in (0, 1]")
        if self.method is CalibrationMethod.Z_SCORE and self.boundary < 0:
            raise ContractViolation("z-score boundary cannot be negative")


@dataclass(frozen=True, kw_only=True)
class CalibrationClassification:
    window_id: str
    observed_at: datetime
    expected_alert: bool
    observed_alert: bool
    event_at: datetime | None

    @property
    def timing_seconds(self) -> float | None:
        if not self.observed_alert or self.event_at is None:
            return None
        return (self.observed_at - self.event_at).total_seconds()


@dataclass(frozen=True, kw_only=True)
class CalibrationEvaluation:
    rule: CalibrationRule
    classifications: tuple[CalibrationClassification, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.rule, CalibrationRule):
            raise ContractViolation("rule must be CalibrationRule")
        if not isinstance(self.classifications, tuple) or not self.classifications:
            raise ContractViolation("calibration evaluation requires classifications")
        if len({item.window_id for item in self.classifications}) != len(self.classifications):
            raise ContractViolation("calibration classification window ids must be unique")

    @property
    def true_positive_count(self) -> int:
        return sum(item.expected_alert and item.observed_alert for item in self.classifications)

    @property
    def false_positive_count(self) -> int:
        return sum(not item.expected_alert and item.observed_alert for item in self.classifications)

    @property
    def true_negative_count(self) -> int:
        return sum(not item.expected_alert and not item.observed_alert for item in self.classifications)

    @property
    def false_negative_count(self) -> int:
        return sum(item.expected_alert and not item.observed_alert for item in self.classifications)

    @property
    def error_count(self) -> int:
        return self.false_positive_count + self.false_negative_count

    @property
    def precision(self) -> Decimal | None:
        denominator = self.true_positive_count + self.false_positive_count
        if denominator == 0:
            return None
        return Decimal(self.true_positive_count) / Decimal(denominator)

    @property
    def recall(self) -> Decimal | None:
        denominator = self.true_positive_count + self.false_negative_count
        if denominator == 0:
            return None
        return Decimal(self.true_positive_count) / Decimal(denominator)

    @property
    def timing_seconds(self) -> tuple[float, ...]:
        return tuple(
            value
            for item in self.classifications
            if (value := item.timing_seconds) is not None
        )

    @property
    def mean_timing_seconds(self) -> float | None:
        values = self.timing_seconds
        return fmean(values) if values else None


@dataclass(frozen=True, kw_only=True)
class CalibrationComparison:
    evaluations: tuple[CalibrationEvaluation, ...]
    capacity: CapacityObservation
    minimum_headroom_ratio: float

    def __post_init__(self) -> None:
        if not isinstance(self.evaluations, tuple) or not self.evaluations:
            raise ContractViolation("calibration comparison requires evaluations")
        if not isinstance(self.capacity, CapacityObservation):
            raise ContractViolation("capacity must be CapacityObservation")
        if isinstance(self.minimum_headroom_ratio, bool) or not isinstance(
            self.minimum_headroom_ratio, (int, float)
        ):
            raise ContractViolation("minimum_headroom_ratio must be numeric")
        if not isfinite(float(self.minimum_headroom_ratio)) or not 0 <= float(self.minimum_headroom_ratio) <= 1:
            raise ContractViolation("minimum_headroom_ratio must be between zero and one")

    @property
    def capacity_acceptable(self) -> bool:
        return self.capacity.headroom_ratio >= float(self.minimum_headroom_ratio)

    @property
    def ranked_evaluations(self) -> tuple[CalibrationEvaluation, ...]:
        """Return deterministic evidence ranking without promoting a live rule."""

        def score(item: CalibrationEvaluation) -> tuple[int, Decimal, Decimal, str, Decimal]:
            recall = item.recall if item.recall is not None else Decimal("-1")
            precision = item.precision if item.precision is not None else Decimal("-1")
            return (
                item.error_count,
                -recall,
                -precision,
                item.rule.method.value,
                item.rule.boundary,
            )

        return tuple(sorted(self.evaluations, key=score))


def evaluate_calibration_rule(
    *,
    suite: VolatilityCalibrationSuite,
    rule: CalibrationRule,
) -> CalibrationEvaluation:
    if not isinstance(suite, VolatilityCalibrationSuite):
        raise ContractViolation("suite must be VolatilityCalibrationSuite")
    if not isinstance(rule, CalibrationRule):
        raise ContractViolation("rule must be CalibrationRule")

    values = tuple(item.signal_value for item in suite.points)
    alerts = _classify(values=values, rule=rule)
    classifications = tuple(
        CalibrationClassification(
            window_id=point.window_id,
            observed_at=point.observed_at,
            expected_alert=point.expected_alert,
            observed_alert=alert,
            event_at=point.event_at,
        )
        for point, alert in zip(suite.points, alerts, strict=True)
    )
    return CalibrationEvaluation(rule=rule, classifications=classifications)


def compare_calibration_rules(
    *,
    suite: VolatilityCalibrationSuite,
    rules: tuple[CalibrationRule, ...],
    projected: ProjectedCapacityUsage,
    envelope: CapacityEnvelope,
    minimum_headroom_ratio: float = 0.20,
) -> CalibrationComparison:
    if not isinstance(rules, tuple) or not rules:
        raise ContractViolation("calibration comparison requires at least one rule")
    if not all(isinstance(item, CalibrationRule) for item in rules):
        raise ContractViolation("calibration comparison requires CalibrationRule values")
    evaluations = tuple(evaluate_calibration_rule(suite=suite, rule=rule) for rule in rules)
    capacity = build_capacity_observation(projected=projected, envelope=envelope)
    return CalibrationComparison(
        evaluations=evaluations,
        capacity=capacity,
        minimum_headroom_ratio=minimum_headroom_ratio,
    )


def _classify(*, values: tuple[Decimal, ...], rule: CalibrationRule) -> tuple[bool, ...]:
    if rule.method is CalibrationMethod.ABSOLUTE_THRESHOLD:
        return tuple(value >= rule.boundary for value in values)

    floats = tuple(float(value) for value in values)
    if rule.method is CalibrationMethod.EMPIRICAL_PERCENTILE:
        ordered = tuple(sorted(values))
        return tuple(
            (Decimal(sum(candidate <= value for candidate in ordered)) / Decimal(len(ordered))) >= rule.boundary
            for value in values
        )

    mean = fmean(floats)
    deviation = pstdev(floats)
    if deviation == 0:
        raise ContractViolation("z-score calibration requires non-zero signal variance")
    return tuple(((value - mean) / deviation) >= float(rule.boundary) for value in floats)


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None or value.utcoffset().total_seconds() != 0:
        raise ContractViolation(f"{field} must be timezone-aware UTC")
