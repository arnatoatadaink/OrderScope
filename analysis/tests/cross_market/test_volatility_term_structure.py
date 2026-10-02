from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.provenance import ContentHash, Provenance, SourceReference, SourceTimestamp
from orderscope_local.contracts.volatility_benchmark import (
    VolatilityBenchmarkObservation,
    VolatilityInstrumentKind,
    VolatilityObservationKind,
)
from orderscope_local.cross_market.volatility_term_structure import (
    VolatilityCurveShape,
    VolatilityFuturePoint,
    build_front_second_term_structure,
    materialize_term_structure_metrics,
)

UTC = timezone.utc
OBSERVED = datetime(2026, 9, 27, 14, 30, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 27, 14, 31, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("official:volatility-futures:fixture"),
        content_hash=ContentHash("f" * 64),
        retrieved_at=ACCEPTED,
        available_at=OBSERVED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.at(OBSERVED),
    )


def future(*, value: str, maturity: date, instrument_ref: str) -> VolatilityBenchmarkObservation:
    return VolatilityBenchmarkObservation(
        subject_ref="volatility.us-equity.vix",
        instrument_ref=instrument_ref,
        instrument_kind=VolatilityInstrumentKind.FUTURE,
        observation_kind=VolatilityObservationKind.SETTLEMENT,
        value=Decimal(value),
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        provenance=provenance(),
        underlying_ref="index.vix",
        maturity_date=maturity,
    )


def point(record_id: str, *, value: str, maturity: date, instrument_ref: str) -> VolatilityFuturePoint:
    return VolatilityFuturePoint(
        record_id=record_id,
        observation=future(value=value, maturity=maturity, instrument_ref=instrument_ref),
    )


def test_contango_detected_from_positive_front_second_spread() -> None:
    structure = build_front_second_term_structure((
        point("fact.vx.1", value="18", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
        point("fact.vx.2", value="20", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11"),
    ))
    assert structure.spread == Decimal("2")
    assert structure.curve_shape is VolatilityCurveShape.CONTANGO


def test_backwardation_detected_from_negative_spread() -> None:
    structure = build_front_second_term_structure((
        point("fact.vx.1", value="24", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
        point("fact.vx.2", value="21", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11"),
    ))
    assert structure.spread == Decimal("-3")
    assert structure.curve_shape is VolatilityCurveShape.BACKWARDATION


def test_flat_curve_is_preserved() -> None:
    structure = build_front_second_term_structure((
        point("fact.vx.1", value="19", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
        point("fact.vx.2", value="19", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11"),
    ))
    assert structure.curve_shape is VolatilityCurveShape.FLAT


def test_points_are_sorted_by_maturity_not_input_order() -> None:
    structure = build_front_second_term_structure((
        point("fact.vx.2", value="20", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11"),
        point("fact.vx.1", value="18", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
    ))
    assert structure.front.record_id == "fact.vx.1"
    assert structure.second.record_id == "fact.vx.2"


def test_requires_at_least_two_points() -> None:
    with pytest.raises(ContractViolation, match="at least two"):
        build_front_second_term_structure((
            point("fact.vx.1", value="18", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
        ))


def test_non_future_observation_rejected() -> None:
    obs = VolatilityBenchmarkObservation(
        subject_ref="volatility.us-equity.vix",
        instrument_ref="index.vix",
        instrument_kind=VolatilityInstrumentKind.PUBLISHED_INDEX,
        observation_kind=VolatilityObservationKind.LEVEL,
        value=Decimal("18"),
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        provenance=provenance(),
        horizon_days=30,
    )
    with pytest.raises(ContractViolation, match="futures only"):
        VolatilityFuturePoint(record_id="fact.vix", observation=obs)


def test_duplicate_record_ids_rejected() -> None:
    with pytest.raises(ContractViolation, match="record IDs must be unique"):
        build_front_second_term_structure((
            point("fact.vx.1", value="18", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
            point("fact.vx.1", value="20", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11"),
        ))


def test_mismatched_observation_times_rejected() -> None:
    first = point("fact.vx.1", value="18", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10")
    later_obs = future(value="20", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11")
    later_obs = VolatilityBenchmarkObservation(
        subject_ref=later_obs.subject_ref,
        instrument_ref=later_obs.instrument_ref,
        instrument_kind=later_obs.instrument_kind,
        observation_kind=later_obs.observation_kind,
        value=later_obs.value,
        observed_at=datetime(2026, 9, 27, 14, 31, tzinfo=UTC),
        accepted_at=datetime(2026, 9, 27, 14, 32, tzinfo=UTC),
        provenance=Provenance(
            source_ref=SourceReference("official:volatility-futures:fixture-2"),
            content_hash=ContentHash("a" * 64),
            retrieved_at=datetime(2026, 9, 27, 14, 32, tzinfo=UTC),
            available_at=datetime(2026, 9, 27, 14, 31, tzinfo=UTC),
            accepted_at=datetime(2026, 9, 27, 14, 32, tzinfo=UTC),
            event_time=SourceTimestamp.at(datetime(2026, 9, 27, 14, 31, tzinfo=UTC)),
        ),
        underlying_ref="index.vix",
        maturity_date=date(2026, 11, 18),
    )
    with pytest.raises(ContractViolation, match="same observation timestamp"):
        build_front_second_term_structure((first, VolatilityFuturePoint(record_id="fact.vx.2", observation=later_obs)))


def test_materialization_preserves_lineage_and_units() -> None:
    structure = build_front_second_term_structure((
        point("fact.vx.1", value="18", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
        point("fact.vx.2", value="20", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11"),
    ))
    metrics = materialize_term_structure_metrics(
        structure,
        subject_ref="volatility.us-equity.vix",
        accepted_at=ACCEPTED,
        record_id_prefix="metric.vx.term",
    )
    by_name = {metric.metric_name: metric for metric in metrics}
    assert by_name["volatility.front_second_spread"].value == "2"
    assert by_name["volatility.front_second_spread"].unit == "volatility_points"
    assert by_name["volatility.curve_shape"].value == "contango"
    assert by_name["volatility.front_second_ratio"].unit == "ratio"
    assert by_name["volatility.front_second_spread"].input_record_ids == ("fact.vx.1", "fact.vx.2")


def test_zero_front_suppresses_ratio_but_keeps_spread_and_shape() -> None:
    structure = build_front_second_term_structure((
        point("fact.vx.1", value="0", maturity=date(2026, 10, 21), instrument_ref="future.vx.2026-10"),
        point("fact.vx.2", value="1", maturity=date(2026, 11, 18), instrument_ref="future.vx.2026-11"),
    ))
    metrics = materialize_term_structure_metrics(
        structure,
        subject_ref="volatility.us-equity.vix",
        accepted_at=ACCEPTED,
        record_id_prefix="metric.vx.term",
    )
    assert {metric.metric_name for metric in metrics} == {
        "volatility.front_second_spread",
        "volatility.curve_shape",
    }
