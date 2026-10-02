from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.crypto_derivatives import (
    ContractType,
    CryptoDerivativeContractError,
    CryptoDerivativeObservation,
    MarginType,
    aggregate_liquidation_bucket,
    estimate_position_band,
    liquidation_event,
)

UTC = timezone.utc


def _dt(minute: int, second: int = 0) -> datetime:
    return datetime(2026, 10, 1, 0, minute, second, tzinfo=UTC)


def _obs(
    minute: int,
    *,
    oi: float,
    mark: float = 100.0,
    funding: float | None = 0.0001,
    venue: str = "BINANCE",
    instrument: str = "BTCUSDT",
) -> CryptoDerivativeObservation:
    return CryptoDerivativeObservation(
        observation_id=f"{venue}:{instrument}:{minute}:{oi}",
        venue=venue,
        instrument_id=instrument,
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=_dt(minute),
        available_at=_dt(minute, 1),
        accepted_at=_dt(minute, 2),
        source_ref="test:position-map",
        open_interest_usd=oi,
        funding_rate=funding,
        mark_price=mark,
    )


def _liq_bucket(minute: int, *, long_usd: float, short_usd: float):
    events = []
    if long_usd:
        events.append(
            liquidation_event(
                event_id=f"l:{minute}",
                venue="BINANCE",
                instrument_id="BTCUSDT",
                liquidated_side="long",
                occurred_at=_dt(minute, 10),
                accepted_at=_dt(minute, 11),
                source_ref="test:liq",
                liquidation_usd=long_usd,
            )
        )
    if short_usd:
        events.append(
            liquidation_event(
                event_id=f"s:{minute}",
                venue="BINANCE",
                instrument_id="BTCUSDT",
                liquidated_side="short",
                occurred_at=_dt(minute, 20),
                accepted_at=_dt(minute, 21),
                source_ref="test:liq",
                liquidation_usd=short_usd,
            )
        )
    return aggregate_liquidation_bucket(
        events,
        bucket_start=_dt(minute),
        bucket_end=_dt(minute + 1),
        accepted_at=_dt(minute + 1, 1),
    )


def test_position_map_retains_incremental_oi() -> None:
    baseline = _obs(0, oi=1_000.0, mark=100.0)
    anchor = _obs(1, oi=1_400.0, mark=101.0)
    as_of = _obs(3, oi=1_250.0, mark=99.0)

    estimate = estimate_position_band(baseline, anchor, as_of)

    assert estimate.added_open_interest_usd == 400.0
    assert estimate.retained_open_interest_usd == 250.0
    assert estimate.retention_ratio == pytest.approx(0.625)
    assert estimate.anchor_funding_rate == 0.0001
    assert estimate.method_version == "uwbs-076-v1"


def test_position_map_caps_retention_at_original_added_oi() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=1_200.0)
    as_of = _obs(3, oi=1_500.0)

    estimate = estimate_position_band(baseline, anchor, as_of)

    assert estimate.added_open_interest_usd == 200.0
    assert estimate.retained_open_interest_usd == 200.0
    assert estimate.retention_ratio == 1.0


def test_position_map_retention_falls_to_zero_below_baseline_oi() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=1_200.0)
    as_of = _obs(3, oi=900.0)

    estimate = estimate_position_band(baseline, anchor, as_of)

    assert estimate.retained_open_interest_usd == 0.0
    assert estimate.retention_ratio == 0.0


def test_position_map_keeps_followup_liquidations_as_context() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=1_300.0)
    as_of = _obs(4, oi=1_150.0)
    long_bucket = _liq_bucket(1, long_usd=80.0, short_usd=20.0)
    short_bucket = _liq_bucket(2, long_usd=10.0, short_usd=90.0)

    estimate = estimate_position_band(
        baseline,
        anchor,
        as_of,
        liquidations=(long_bucket, short_bucket),
    )

    assert estimate.long_liquidation_usd_after_anchor == 90.0
    assert estimate.short_liquidation_usd_after_anchor == 110.0
    assert long_bucket.observation_id in estimate.input_observation_ids
    assert short_bucket.observation_id in estimate.input_observation_ids


def test_position_map_ignores_other_series_liquidation_context() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=1_300.0)
    as_of = _obs(4, oi=1_150.0)
    other = _liq_bucket(1, long_usd=80.0, short_usd=20.0)
    other = type(other)(
        observation_id=other.observation_id,
        venue=other.venue,
        instrument_id="ETHUSDT",
        bucket_start=other.bucket_start,
        bucket_end=other.bucket_end,
        accepted_at=other.accepted_at,
        source_ref=other.source_ref,
        long_liquidation_usd=other.long_liquidation_usd,
        short_liquidation_usd=other.short_liquidation_usd,
        event_count=other.event_count,
        source_revision=other.source_revision,
    )

    estimate = estimate_position_band(baseline, anchor, as_of, liquidations=(other,))

    assert estimate.long_liquidation_usd_after_anchor == 0.0
    assert estimate.short_liquidation_usd_after_anchor == 0.0


def test_position_map_rejects_non_positive_oi_anchor_delta() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=900.0)
    as_of = _obs(2, oi=950.0)

    with pytest.raises(CryptoDerivativeContractError):
        estimate_position_band(baseline, anchor, as_of)


def test_position_map_rejects_mixed_series() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=1_100.0, instrument="ETHUSDT")
    as_of = _obs(2, oi=1_050.0)

    with pytest.raises(CryptoDerivativeContractError):
        estimate_position_band(baseline, anchor, as_of)


def test_position_map_rejects_missing_oi() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=1_100.0)
    as_of = _obs(2, oi=1_050.0)
    as_of = CryptoDerivativeObservation(
        observation_id="missing-oi",
        venue=as_of.venue,
        instrument_id=as_of.instrument_id,
        contract_type=as_of.contract_type,
        margin_type=as_of.margin_type,
        quote_asset=as_of.quote_asset,
        observed_at=as_of.observed_at,
        available_at=as_of.available_at,
        accepted_at=as_of.accepted_at,
        source_ref=as_of.source_ref,
        mark_price=as_of.mark_price,
    )

    with pytest.raises(CryptoDerivativeContractError):
        estimate_position_band(baseline, anchor, as_of)


def test_position_map_requires_anchor_price() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = CryptoDerivativeObservation(
        observation_id="no-price",
        venue="BINANCE",
        instrument_id="BTCUSDT",
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=_dt(1),
        available_at=_dt(1, 1),
        accepted_at=_dt(1, 2),
        source_ref="test:position-map",
        open_interest_usd=1_200.0,
    )
    as_of = _obs(2, oi=1_100.0)

    with pytest.raises(CryptoDerivativeContractError):
        estimate_position_band(baseline, anchor, as_of)


def test_position_map_rejects_invalid_band_width() -> None:
    baseline = _obs(0, oi=1_000.0)
    anchor = _obs(1, oi=1_200.0)
    as_of = _obs(2, oi=1_100.0)

    with pytest.raises(CryptoDerivativeContractError):
        estimate_position_band(baseline, anchor, as_of, band_width_bps=0)
