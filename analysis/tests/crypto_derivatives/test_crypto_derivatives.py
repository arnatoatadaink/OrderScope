from datetime import UTC, datetime, timedelta

import pytest

from orderscope_local.crypto_derivatives import (
    ContractType,
    CryptoDerivativeContractError,
    CryptoDerivativeObservation,
    LiquidationObservation,
    MarginType,
    basis_bps,
    funding_delta,
    liquidation_imbalance,
    open_interest_delta_usd,
)


def ts(minute: int) -> datetime:
    return datetime(2026, 9, 30, 0, minute, tzinfo=UTC)


def obs(**overrides):
    values = dict(
        observation_id="binance-nearusdt-0000",
        venue="binance",
        instrument_id="NEARUSDT-PERP",
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=ts(0),
        available_at=ts(1),
        accepted_at=ts(2),
        source_ref="provider:binance:fapi",
        open_interest_usd=800_000_000.0,
        funding_rate=0.0001,
        funding_interval_seconds=28_800,
        mark_price=4.04,
        index_price=4.00,
        derivatives_volume_usd=12_000_000.0,
    )
    values.update(overrides)
    return CryptoDerivativeObservation(**values)


def test_observation_accepts_partial_source_neutral_fields():
    value = obs(mark_price=None, index_price=None, derivatives_volume_usd=None)
    assert value.open_interest_usd == 800_000_000.0
    assert value.funding_rate == 0.0001


def test_observation_rejects_non_utc_and_bad_asof_order():
    with pytest.raises(CryptoDerivativeContractError):
        obs(observed_at=datetime(2026, 9, 30, 0, 0))
    with pytest.raises(CryptoDerivativeContractError):
        obs(available_at=ts(3), accepted_at=ts(2))


def test_observation_rejects_negative_unsigned_measures_and_empty_payload():
    with pytest.raises(CryptoDerivativeContractError):
        obs(open_interest_usd=-1)
    with pytest.raises(CryptoDerivativeContractError):
        obs(
            open_interest_usd=None,
            funding_rate=None,
            funding_interval_seconds=None,
            mark_price=None,
            index_price=None,
            basis=None,
            derivatives_volume_usd=None,
        )


def test_open_interest_delta_is_deterministic_not_directional_flow_claim():
    previous = obs()
    current = obs(
        observation_id="binance-nearusdt-0005",
        observed_at=ts(5),
        available_at=ts(6),
        accepted_at=ts(7),
        open_interest_usd=850_000_000.0,
    )
    metric = open_interest_delta_usd(previous, current)
    assert metric.metric_name == "open_interest_delta_usd"
    assert metric.value == 50_000_000.0
    assert metric.unit == "usd"
    assert metric.input_observation_ids == (previous.observation_id, current.observation_id)


def test_delta_metrics_reject_cross_venue_or_non_monotonic_series():
    previous = obs()
    other_venue = obs(
        observation_id="bybit-nearusdt-0005",
        venue="bybit",
        observed_at=ts(5),
        available_at=ts(6),
        accepted_at=ts(7),
    )
    with pytest.raises(CryptoDerivativeContractError):
        open_interest_delta_usd(previous, other_venue)
    with pytest.raises(CryptoDerivativeContractError):
        funding_delta(previous, previous)


def test_funding_delta_and_basis_bps_are_explicit_calculations():
    previous = obs()
    current = obs(
        observation_id="binance-nearusdt-0005",
        observed_at=ts(5),
        available_at=ts(6),
        accepted_at=ts(7),
        funding_rate=0.0003,
        mark_price=4.08,
        index_price=4.00,
    )
    assert funding_delta(previous, current).value == pytest.approx(0.0002)
    assert basis_bps(current).value == pytest.approx(200.0)


def test_liquidation_observation_preserves_long_and_short_closures_separately():
    liquidation = LiquidationObservation(
        observation_id="near-liq-0000-0005",
        venue="binance",
        instrument_id="NEARUSDT-PERP",
        bucket_start=ts(0),
        bucket_end=ts(5),
        accepted_at=ts(6),
        source_ref="provider:binance:liquidations",
        long_liquidation_usd=5_000_000.0,
        short_liquidation_usd=1_000_000.0,
        event_count=42,
    )
    metric = liquidation_imbalance(liquidation)
    assert metric.value == pytest.approx(2 / 3)
    assert metric.input_observation_ids == (liquidation.observation_id,)


def test_zero_liquidation_bucket_has_zero_imbalance_not_missing_direction():
    liquidation = LiquidationObservation(
        observation_id="near-liq-empty",
        venue="binance",
        instrument_id="NEARUSDT-PERP",
        bucket_start=ts(0),
        bucket_end=ts(5),
        accepted_at=ts(6),
        source_ref="provider:binance:liquidations",
        long_liquidation_usd=0.0,
        short_liquidation_usd=0.0,
    )
    assert liquidation_imbalance(liquidation).value == 0.0


def test_liquidation_bucket_rejects_invalid_time_and_negative_amounts():
    with pytest.raises(CryptoDerivativeContractError):
        LiquidationObservation(
            observation_id="bad-time",
            venue="binance",
            instrument_id="NEARUSDT-PERP",
            bucket_start=ts(5),
            bucket_end=ts(0),
            accepted_at=ts(6),
            source_ref="provider:binance:liquidations",
            long_liquidation_usd=0.0,
            short_liquidation_usd=0.0,
        )
    with pytest.raises(CryptoDerivativeContractError):
        LiquidationObservation(
            observation_id="bad-amount",
            venue="binance",
            instrument_id="NEARUSDT-PERP",
            bucket_start=ts(0),
            bucket_end=ts(5),
            accepted_at=ts(6),
            source_ref="provider:binance:liquidations",
            long_liquidation_usd=-1.0,
            short_liquidation_usd=0.0,
        )
