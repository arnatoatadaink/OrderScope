from datetime import datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.volatility_etp_roll import (
    VolatilityEtpRollInputs,
    VolatilityEtpRollPressure,
    assess_etp_roll,
    calculate_etp_roll_metrics,
    materialize_etp_roll_metrics,
)

UTC = timezone.utc
AS_OF = datetime(2026, 9, 27, 20, 0, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 27, 20, 5, tzinfo=UTC)


def inputs(**overrides) -> VolatilityEtpRollInputs:
    values = dict(
        subject_ref="etp.vix.fixture",
        as_of=AS_OF,
        etp_start_value=Decimal("25"),
        etp_end_value=Decimal("24"),
        front_future_value=Decimal("20"),
        second_future_value=Decimal("22"),
        etp_value_record_ids=("fact.etp.start", "fact.etp.end"),
        futures_record_ids=("fact.vx.front", "fact.vx.second"),
    )
    values.update(overrides)
    return VolatilityEtpRollInputs(**values)


def test_contango_produces_negative_roll_pressure_measurement() -> None:
    result = calculate_etp_roll_metrics(inputs())
    assert result.front_second_spread == Decimal("2")
    assert result.front_second_ratio == Decimal("1.1")
    assert result.roll_pressure is VolatilityEtpRollPressure.NEGATIVE


def test_backwardation_produces_positive_roll_pressure_measurement_and_tailwind_candidate() -> None:
    result = calculate_etp_roll_metrics(inputs(front_future_value=Decimal("24"), second_future_value=Decimal("21")))
    assert result.front_second_spread == Decimal("-3")
    assert result.roll_pressure is VolatilityEtpRollPressure.POSITIVE
    interpretation = assess_etp_roll(
        subject_ref="etp.vix.fixture",
        observed_window_start=AS_OF,
        observed_window_end=ACCEPTED,
        roll_pressure=result.roll_pressure,
        etp_return_metric_refs=("metric.etp.return",),
        term_structure_metric_refs=("metric.vx.curve",),
        generated_at=ACCEPTED,
    )
    assert interpretation.interpretation_type == "volatility.roll_tailwind_candidate"


def test_flat_curve_produces_neutral_roll_pressure() -> None:
    result = calculate_etp_roll_metrics(inputs(second_future_value=Decimal("20")))
    assert result.roll_pressure is VolatilityEtpRollPressure.NEUTRAL


def test_etp_return_is_measured_separately_from_curve() -> None:
    result = calculate_etp_roll_metrics(inputs())
    assert result.etp_return == Decimal("-0.04")


def test_materialization_keeps_etp_and_futures_lineage_distinct() -> None:
    metrics = materialize_etp_roll_metrics(inputs(), record_id_prefix="metric.vix.etp", accepted_at=ACCEPTED)
    assert metrics[0].input_record_ids == ("fact.etp.start", "fact.etp.end")
    assert metrics[1].input_record_ids == ("fact.vx.front", "fact.vx.second")
    assert metrics[0].metric_name == "volatility.etp_return"


def test_input_values_must_be_positive_finite_decimals() -> None:
    with pytest.raises(ContractViolation, match="positive finite Decimal"):
        inputs(etp_start_value=Decimal("0"))
    with pytest.raises(ContractViolation, match="positive finite Decimal"):
        inputs(front_future_value=Decimal("NaN"))


def test_etp_and_futures_lineage_cannot_overlap() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse references"):
        inputs(futures_record_ids=("fact.etp.start", "fact.vx.second"))


def test_roll_assessment_requires_both_etp_and_term_structure_evidence() -> None:
    interpretation = assess_etp_roll(
        subject_ref="etp.vix.fixture",
        observed_window_start=AS_OF,
        observed_window_end=ACCEPTED,
        roll_pressure=VolatilityEtpRollPressure.NEGATIVE,
        etp_return_metric_refs=("metric.etp.return",),
        term_structure_metric_refs=("metric.vx.curve",),
        generated_at=ACCEPTED,
    )
    assert interpretation.interpretation_type == "volatility.roll_headwind_candidate"
    assert interpretation.statement["roll_pressure"] == "negative_roll_pressure"


def test_contradicting_evidence_blocks_simple_roll_explanation() -> None:
    interpretation = assess_etp_roll(
        subject_ref="etp.vix.fixture",
        observed_window_start=AS_OF,
        observed_window_end=ACCEPTED,
        roll_pressure=VolatilityEtpRollPressure.NEGATIVE,
        etp_return_metric_refs=("metric.etp.return",),
        term_structure_metric_refs=("metric.vx.curve",),
        contradicting_evidence_refs=("metric.spot.shock",),
        generated_at=ACCEPTED,
    )
    assert interpretation.interpretation_type == "volatility.move_not_explained_by_roll"


def test_roll_assessment_rejects_reused_evidence_and_bad_windows() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse references"):
        assess_etp_roll(
            subject_ref="etp.vix.fixture",
            observed_window_start=AS_OF,
            observed_window_end=ACCEPTED,
            roll_pressure=VolatilityEtpRollPressure.NEGATIVE,
            etp_return_metric_refs=("metric.shared",),
            term_structure_metric_refs=("metric.shared",),
            generated_at=ACCEPTED,
        )
    with pytest.raises(ContractViolation, match="non-empty and half-open"):
        assess_etp_roll(
            subject_ref="etp.vix.fixture",
            observed_window_start=ACCEPTED,
            observed_window_end=ACCEPTED,
            roll_pressure=VolatilityEtpRollPressure.NEGATIVE,
            etp_return_metric_refs=("metric.etp.return",),
            term_structure_metric_refs=("metric.vx.curve",),
            generated_at=ACCEPTED,
        )
