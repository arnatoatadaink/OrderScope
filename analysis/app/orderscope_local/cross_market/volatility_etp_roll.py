"""UWBS-096 VIX-linked ETP roll / decay boundary.

This module keeps deterministic ETP return measurements separate from term-
structure-implied roll pressure and from causal interpretation.  Contango or
backwardation may provide context, but neither is sufficient by itself to claim
that an observed ETP move was caused by roll.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import DerivedMetric, Interpretation, InterpretationAssertionKind


class VolatilityEtpRollPressure(StrEnum):
    NEGATIVE = "negative_roll_pressure"
    POSITIVE = "positive_roll_pressure"
    NEUTRAL = "neutral_roll_pressure"


class VolatilityEtpRollAssessment(StrEnum):
    ROLL_HEADWIND_CANDIDATE = "roll_headwind_candidate"
    ROLL_TAILWIND_CANDIDATE = "roll_tailwind_candidate"
    MOVE_NOT_EXPLAINED_BY_ROLL = "move_not_explained_by_roll"
    UNKNOWN = "unknown"


@dataclass(frozen=True, kw_only=True)
class VolatilityEtpRollInputs:
    subject_ref: str
    as_of: datetime
    etp_start_value: Decimal
    etp_end_value: Decimal
    front_future_value: Decimal
    second_future_value: Decimal
    etp_value_record_ids: tuple[str, ...]
    futures_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _canonical(self.subject_ref, "subject_ref")
        _utc(self.as_of, "as_of")
        for value, field in (
            (self.etp_start_value, "etp_start_value"),
            (self.etp_end_value, "etp_end_value"),
            (self.front_future_value, "front_future_value"),
            (self.second_future_value, "second_future_value"),
        ):
            _positive_decimal(value, field)
        _refs(self.etp_value_record_ids, "etp_value_record_ids")
        _refs(self.futures_record_ids, "futures_record_ids")
        if set(self.etp_value_record_ids) & set(self.futures_record_ids):
            raise ContractViolation("ETP and futures evidence cannot reuse references")


@dataclass(frozen=True, kw_only=True)
class VolatilityEtpRollMetrics:
    etp_return: Decimal
    front_second_spread: Decimal
    front_second_ratio: Decimal
    roll_pressure: VolatilityEtpRollPressure


def calculate_etp_roll_metrics(inputs: VolatilityEtpRollInputs) -> VolatilityEtpRollMetrics:
    if not isinstance(inputs, VolatilityEtpRollInputs):
        raise TypeError("inputs must be VolatilityEtpRollInputs")
    etp_return = (inputs.etp_end_value / inputs.etp_start_value) - Decimal("1")
    spread = inputs.second_future_value - inputs.front_future_value
    ratio = inputs.second_future_value / inputs.front_future_value
    if spread > 0:
        pressure = VolatilityEtpRollPressure.NEGATIVE
    elif spread < 0:
        pressure = VolatilityEtpRollPressure.POSITIVE
    else:
        pressure = VolatilityEtpRollPressure.NEUTRAL
    return VolatilityEtpRollMetrics(
        etp_return=etp_return,
        front_second_spread=spread,
        front_second_ratio=ratio,
        roll_pressure=pressure,
    )


def materialize_etp_roll_metrics(
    inputs: VolatilityEtpRollInputs,
    *,
    record_id_prefix: str,
    accepted_at: datetime,
) -> tuple[DerivedMetric, DerivedMetric, DerivedMetric]:
    _canonical(record_id_prefix, "record_id_prefix")
    _utc(accepted_at, "accepted_at")
    if accepted_at < inputs.as_of:
        raise ContractViolation("accepted_at cannot precede as_of")
    metrics = calculate_etp_roll_metrics(inputs)
    all_refs = inputs.etp_value_record_ids + inputs.futures_record_ids
    return (
        _metric(
            record_id=f"{record_id_prefix}.etp_return",
            subject_ref=inputs.subject_ref,
            accepted_at=accepted_at,
            as_of=inputs.as_of,
            metric_name="volatility.etp_return",
            value=metrics.etp_return,
            unit="ratio",
            method="end_value_div_start_value_minus_one",
            inputs=inputs.etp_value_record_ids,
        ),
        _metric(
            record_id=f"{record_id_prefix}.front_second_spread",
            subject_ref=inputs.subject_ref,
            accepted_at=accepted_at,
            as_of=inputs.as_of,
            metric_name="volatility.front_second_spread",
            value=metrics.front_second_spread,
            unit="volatility_points",
            method="second_future_minus_front_future",
            inputs=inputs.futures_record_ids,
        ),
        _metric(
            record_id=f"{record_id_prefix}.front_second_ratio",
            subject_ref=inputs.subject_ref,
            accepted_at=accepted_at,
            as_of=inputs.as_of,
            metric_name="volatility.front_second_ratio",
            value=metrics.front_second_ratio,
            unit="ratio",
            method="second_future_div_front_future",
            inputs=all_refs,
        ),
    )


def assess_etp_roll(
    *,
    subject_ref: str,
    observed_window_start: datetime,
    observed_window_end: datetime,
    etp_return_metric_refs: tuple[str, ...],
    term_structure_metric_refs: tuple[str, ...],
    contradicting_evidence_refs: tuple[str, ...] = (),
    generated_at: datetime,
) -> Interpretation:
    _canonical(subject_ref, "subject_ref")
    _utc(observed_window_start, "observed_window_start")
    _utc(observed_window_end, "observed_window_end")
    _utc(generated_at, "generated_at")
    if observed_window_start >= observed_window_end:
        raise ContractViolation("observed window must be non-empty and half-open")
    if generated_at < observed_window_end:
        raise ContractViolation("generated_at cannot precede observed_window_end")
    for values, field in (
        (etp_return_metric_refs, "etp_return_metric_refs"),
        (term_structure_metric_refs, "term_structure_metric_refs"),
        (contradicting_evidence_refs, "contradicting_evidence_refs"),
    ):
        _refs(values, field, required=False)
    groups = [set(etp_return_metric_refs), set(term_structure_metric_refs), set(contradicting_evidence_refs)]
    for i, left in enumerate(groups):
        for right in groups[i + 1 :]:
            if left & right:
                raise ContractViolation("roll assessment evidence classes cannot reuse references")

    if not etp_return_metric_refs or not term_structure_metric_refs:
        assessment = VolatilityEtpRollAssessment.UNKNOWN
    elif contradicting_evidence_refs:
        assessment = VolatilityEtpRollAssessment.MOVE_NOT_EXPLAINED_BY_ROLL
    else:
        assessment = VolatilityEtpRollAssessment.ROLL_HEADWIND_CANDIDATE

    basis = etp_return_metric_refs + term_structure_metric_refs + contradicting_evidence_refs
    if not basis:
        raise ContractViolation("roll assessment requires evidence lineage")
    return Interpretation(
        record_id=f"interpretation.{subject_ref}.volatility_etp_roll",
        schema_version="volatility-etp-roll-v0.1",
        subject_ref=subject_ref,
        accepted_at=generated_at,
        created_at=generated_at,
        interpretation_type=f"volatility.{assessment.value}",
        statement={
            "assessment": assessment.value,
            "etp_metric_count": len(etp_return_metric_refs),
            "term_structure_metric_count": len(term_structure_metric_refs),
            "contradicting_count": len(contradicting_evidence_refs),
        },
        basis_record_ids=basis,
        method="volatility_etp_roll_assessment",
        method_version="uwbs-096-v0.1",
        assertion_kind=InterpretationAssertionKind.ASSESSMENT,
    )


def _metric(*, record_id: str, subject_ref: str, accepted_at: datetime, as_of: datetime, metric_name: str, value: Decimal, unit: str, method: str, inputs: tuple[str, ...]) -> DerivedMetric:
    return DerivedMetric(
        record_id=record_id,
        schema_version="volatility-etp-roll-metric-v0.1",
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=as_of,
        metric_name=metric_name,
        value=str(value),
        calculation_method=method,
        method_version="uwbs-096-v0.1",
        as_of=as_of,
        input_record_ids=inputs,
        unit=unit,
    )


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _positive_decimal(value: Decimal, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise ContractViolation(f"{field} must be a positive finite Decimal")


def _refs(values: tuple[str, ...], field: str, *, required: bool = True) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if required and not values:
        raise ContractViolation(f"{field} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        _canonical(value, field)
