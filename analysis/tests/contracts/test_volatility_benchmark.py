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

UTC = timezone.utc
OBSERVED = datetime(2026, 9, 27, 14, 30, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 27, 14, 31, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("official:volatility:fixture"),
        content_hash=ContentHash("e" * 64),
        retrieved_at=ACCEPTED,
        available_at=OBSERVED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.instant_utc(OBSERVED),
    )


def observation(**overrides) -> VolatilityBenchmarkObservation:
    values = dict(
        subject_ref="volatility.us-equity.vix",
        instrument_ref="index.vix",
        instrument_kind=VolatilityInstrumentKind.PUBLISHED_INDEX,
        observation_kind=VolatilityObservationKind.LEVEL,
        value=Decimal("18.25"),
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        provenance=provenance(),
        underlying_ref="index.sp500",
        horizon_days=30,
    )
    values.update(overrides)
    return VolatilityBenchmarkObservation(**values)


def test_published_index_materializes_as_volatility_index_fact() -> None:
    fact = observation().to_fact(
        record_id="fact.volatility.vix.1",
        evidence_record_ids=("evidence.vix.official.1",),
    )
    assert fact.fact_type == "volatility_benchmark.published_index.level"
    assert fact.value["instrument_ref"] == "index.vix"
    assert fact.value["unit"] == "volatility_points"


def test_vix_index_cannot_masquerade_as_currency_price() -> None:
    with pytest.raises(ContractViolation, match="currency price"):
        observation(currency="USD")


def test_vix_index_requires_level_observation() -> None:
    with pytest.raises(ContractViolation, match="must use LEVEL"):
        observation(observation_kind=VolatilityObservationKind.MARKET_PRICE)


def test_future_requires_explicit_maturity() -> None:
    with pytest.raises(ContractViolation, match="maturity_date"):
        observation(
            instrument_ref="future.vx.front",
            instrument_kind=VolatilityInstrumentKind.FUTURE,
            observation_kind=VolatilityObservationKind.SETTLEMENT,
            horizon_days=None,
        )


def test_future_is_distinct_from_spot_index() -> None:
    item = observation(
        instrument_ref="future.vx.2026-10",
        instrument_kind=VolatilityInstrumentKind.FUTURE,
        observation_kind=VolatilityObservationKind.SETTLEMENT,
        maturity_date=date(2026, 10, 21),
        horizon_days=None,
    )
    assert item.instrument_kind is VolatilityInstrumentKind.FUTURE
    assert item.instrument_kind is not VolatilityInstrumentKind.PUBLISHED_INDEX
    assert item.unit == "volatility_points"


def test_non_future_cannot_carry_maturity() -> None:
    with pytest.raises(ContractViolation, match="reserved for futures"):
        observation(maturity_date=date(2026, 10, 21))


def test_etp_proxy_requires_currency_and_price_semantics() -> None:
    with pytest.raises(ContractViolation, match="requires currency"):
        observation(
            instrument_ref="etp.vix.proxy",
            instrument_kind=VolatilityInstrumentKind.ETP_PROXY,
            observation_kind=VolatilityObservationKind.MARKET_PRICE,
            horizon_days=None,
        )


def test_etp_proxy_is_not_volatility_points() -> None:
    item = observation(
        instrument_ref="etp.vix.proxy",
        instrument_kind=VolatilityInstrumentKind.ETP_PROXY,
        observation_kind=VolatilityObservationKind.MARKET_PRICE,
        value=Decimal("22.10"),
        horizon_days=None,
        currency="USD",
    )
    assert item.unit == "currency_USD"
    assert item.instrument_kind is not VolatilityInstrumentKind.PUBLISHED_INDEX


def test_negative_or_non_decimal_value_rejected() -> None:
    with pytest.raises(ContractViolation, match="finite Decimal"):
        observation(value=18.25)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation, match="cannot be negative"):
        observation(value=Decimal("-0.01"))


def test_acceptance_time_and_provenance_must_remain_consistent() -> None:
    with pytest.raises(ContractViolation, match="cannot precede observed_at"):
        observation(accepted_at=datetime(2026, 9, 27, 14, 29, tzinfo=UTC))
    other = datetime(2026, 9, 27, 14, 32, tzinfo=UTC)
    with pytest.raises(ContractViolation, match="must match provenance"):
        observation(accepted_at=other)
