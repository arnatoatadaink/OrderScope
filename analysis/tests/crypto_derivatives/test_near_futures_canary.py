from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orderscope_local.crypto_derivatives import (
    ContractType,
    CryptoDerivativeContractError,
    CryptoDerivativeObservation,
    MarginType,
    PositionBandEstimate,
    aggregate_liquidation_bucket,
    build_near_futures_position_canary,
    liquidation_event,
)

UTC = timezone.utc


def _dt(second: int = 0) -> datetime:
    return datetime(2026, 10, 1, 0, 0, second, tzinfo=UTC)


def _obs(
    venue: str,
    *,
    oi: float,
    funding: float,
    mark: float,
    second: int = 0,
    instrument: str = "NEARUSDT",
) -> CryptoDerivativeObservation:
    return CryptoDerivativeObservation(
        observation_id=f"{venue}:{instrument}:{second}",
        venue=venue,
        instrument_id=instrument,
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=_dt(second),
        available_at=_dt(second + 1),
        accepted_at=_dt(second + 2),
        source_ref="test:near-canary",
        open_interest_usd=oi,
        funding_rate=funding,
        mark_price=mark,
    )


def _band(venue: str, *, added: float, retained: float) -> PositionBandEstimate:
    return PositionBandEstimate(
        venue=venue,
        instrument_id="NEARUSDT",
        band_low=3.0,
        band_high=3.1,
        anchor_at=_dt(0),
        as_of=_dt(30),
        baseline_open_interest_usd=1_000.0,
        added_open_interest_usd=added,
        retained_open_interest_usd=retained,
        retention_ratio=retained / added,
        anchor_funding_rate=0.0001,
        long_liquidation_usd_after_anchor=0.0,
        short_liquidation_usd_after_anchor=0.0,
        input_observation_ids=(f"{venue}:baseline", f"{venue}:anchor", f"{venue}:asof"),
    )


def _liq(*, long_usd: float, short_usd: float):
    events = []
    if long_usd:
        events.append(
            liquidation_event(
                event_id="long-liq",
                venue="BINANCE",
                instrument_id="NEARUSDT",
                liquidated_side="long",
                occurred_at=_dt(10),
                accepted_at=_dt(11),
                source_ref="test:liq",
                liquidation_usd=long_usd,
            )
        )
    if short_usd:
        events.append(
            liquidation_event(
                event_id="short-liq",
                venue="BINANCE",
                instrument_id="NEARUSDT",
                liquidated_side="short",
                occurred_at=_dt(20),
                accepted_at=_dt(21),
                source_ref="test:liq",
                liquidation_usd=short_usd,
            )
        )
    return aggregate_liquidation_bucket(
        events,
        bucket_start=_dt(0),
        bucket_end=_dt(30),
        accepted_at=_dt(31),
    )


def test_build_near_canary_composes_cross_venue_metrics() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_100.0, funding=0.0002, mark=3.03, second=10),
        _obs("OKX", oi=900.0, funding=0.0000, mark=2.97, second=20),
    )

    canary = build_near_futures_position_canary(observations)

    assert canary.instrument_id == "NEARUSDT"
    assert canary.venue_count == 3
    assert canary.median_open_interest_usd == 1_000.0
    assert canary.median_funding_rate == 0.0001
    assert canary.median_mark_price == 3.00
    assert canary.method_version == "uwbs-078-v1"


def test_canary_weighted_retention_uses_added_oi_weights() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_010.0, funding=0.0001, mark=3.00, second=10),
    )
    bands = (
        _band("BINANCE", added=100.0, retained=50.0),
        _band("BYBIT", added=300.0, retained=300.0),
    )

    canary = build_near_futures_position_canary(observations, position_bands=bands)

    assert canary.weighted_position_retention_ratio == pytest.approx(350.0 / 400.0)


def test_canary_aggregates_liquidation_direction() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_010.0, funding=0.0001, mark=3.00, second=10),
    )
    bucket = _liq(long_usd=75.0, short_usd=25.0)

    canary = build_near_futures_position_canary(observations, liquidations=(bucket,))

    assert canary.long_liquidation_usd == 75.0
    assert canary.short_liquidation_usd == 25.0
    assert canary.liquidation_directional_share == 0.5
    assert bucket.observation_id in canary.input_observation_ids


def test_canary_emits_only_qa_threshold_flags() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_500.0, funding=0.0030, mark=3.30, second=10),
    )
    bands = (_band("BINANCE", added=100.0, retained=20.0),)

    canary = build_near_futures_position_canary(
        observations,
        position_bands=bands,
        oi_relative_warn=0.10,
        funding_abs_warn=0.0005,
        mark_relative_warn=0.01,
        retention_warn=0.50,
    )

    assert canary.qa_flags == (
        "oi_cross_venue_mismatch",
        "funding_cross_venue_mismatch",
        "mark_cross_venue_mismatch",
        "position_retention_below_threshold",
    )


def test_canary_rejects_non_near_instrument() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00, instrument="BTCUSDT"),
        _obs("BYBIT", oi=1_100.0, funding=0.0001, mark=3.01, second=10, instrument="BTCUSDT"),
    )

    with pytest.raises(CryptoDerivativeContractError):
        build_near_futures_position_canary(observations)


def test_canary_rejects_position_band_instrument_mismatch() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_100.0, funding=0.0001, mark=3.01, second=10),
    )
    band = _band("BINANCE", added=100.0, retained=50.0)
    band = PositionBandEstimate(
        venue=band.venue,
        instrument_id="NEARUSD",
        band_low=band.band_low,
        band_high=band.band_high,
        anchor_at=band.anchor_at,
        as_of=band.as_of,
        baseline_open_interest_usd=band.baseline_open_interest_usd,
        added_open_interest_usd=band.added_open_interest_usd,
        retained_open_interest_usd=band.retained_open_interest_usd,
        retention_ratio=band.retention_ratio,
        anchor_funding_rate=band.anchor_funding_rate,
        long_liquidation_usd_after_anchor=band.long_liquidation_usd_after_anchor,
        short_liquidation_usd_after_anchor=band.short_liquidation_usd_after_anchor,
        input_observation_ids=band.input_observation_ids,
    )

    with pytest.raises(CryptoDerivativeContractError):
        build_near_futures_position_canary(observations, position_bands=(band,))


def test_canary_rejects_liquidation_instrument_mismatch() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_100.0, funding=0.0001, mark=3.01, second=10),
    )
    bucket = _liq(long_usd=10.0, short_usd=0.0)
    bucket = type(bucket)(
        observation_id=bucket.observation_id,
        venue=bucket.venue,
        instrument_id="NEARUSD",
        bucket_start=bucket.bucket_start,
        bucket_end=bucket.bucket_end,
        accepted_at=bucket.accepted_at,
        source_ref=bucket.source_ref,
        long_liquidation_usd=bucket.long_liquidation_usd,
        short_liquidation_usd=bucket.short_liquidation_usd,
        event_count=bucket.event_count,
        source_revision=bucket.source_revision,
    )

    with pytest.raises(CryptoDerivativeContractError):
        build_near_futures_position_canary(observations, liquidations=(bucket,))


def test_canary_rejects_invalid_retention_threshold() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_100.0, funding=0.0001, mark=3.01, second=10),
    )

    with pytest.raises(CryptoDerivativeContractError):
        build_near_futures_position_canary(observations, retention_warn=1.1)


def test_canary_requires_cross_venue_inputs() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        build_near_futures_position_canary((
            _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        ))


def test_canary_lineage_is_deduplicated_stably() -> None:
    observations = (
        _obs("BINANCE", oi=1_000.0, funding=0.0001, mark=3.00),
        _obs("BYBIT", oi=1_100.0, funding=0.0001, mark=3.01, second=10),
    )
    band = _band("BINANCE", added=100.0, retained=50.0)

    canary = build_near_futures_position_canary(observations, position_bands=(band,))

    assert len(canary.input_observation_ids) == len(set(canary.input_observation_ids))
    assert canary.input_observation_ids[:2] == ("BINANCE:NEARUSDT:0", "BYBIT:NEARUSDT:10")
