from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.crypto_derivatives import (
    CryptoDerivativeContractError,
    LiquidationSide,
    aggregate_liquidation_bucket,
    liquidation_acceleration_usd,
    liquidation_directional_share,
    liquidation_event,
    liquidation_event_rate,
    liquidation_multiplier,
    liquidation_total_usd,
)

UTC = timezone.utc


def _dt(minute: int, second: int = 0) -> datetime:
    return datetime(2026, 10, 1, 0, minute, second, tzinfo=UTC)


def _event(
    ident: str,
    *,
    side: str | LiquidationSide,
    usd: float,
    minute: int = 0,
    second: int = 10,
    venue: str = "binance",
    instrument: str = "BTCUSDT",
    count: int = 1,
):
    return liquidation_event(
        event_id=ident,
        venue=venue,
        instrument_id=instrument,
        liquidated_side=side,
        occurred_at=_dt(minute, second),
        accepted_at=_dt(minute, second + 1),
        source_ref=f"test:{ident}",
        liquidation_usd=usd,
        event_count=count,
    )


def _bucket(minute: int, *, long_usd: float, short_usd: float):
    events = []
    if long_usd:
        events.append(_event(f"l-{minute}", side="long", usd=long_usd, minute=minute))
    if short_usd:
        events.append(_event(f"s-{minute}", side="short", usd=short_usd, minute=minute, second=20))
    if not events:
        events.append(_event(f"z-{minute}", side="long", usd=0.0, minute=minute))
    return aggregate_liquidation_bucket(
        events,
        bucket_start=_dt(minute),
        bucket_end=_dt(minute + 1),
        accepted_at=_dt(minute + 1, 1),
    )


def test_event_normalizes_venue_and_side() -> None:
    event = _event("e1", side="long", usd=25.0, venue="binance")
    assert event.venue == "BINANCE"
    assert event.liquidated_side is LiquidationSide.LONG


def test_event_rejects_unknown_liquidated_side() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        _event("e1", side="buy", usd=25.0)


def test_event_rejects_negative_notional() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        _event("e1", side="long", usd=-1.0)


def test_bucket_aggregates_long_short_and_event_count() -> None:
    bucket = aggregate_liquidation_bucket(
        [
            _event("a", side="long", usd=100.0, count=2),
            _event("b", side="short", usd=40.0, second=20, count=3),
        ],
        bucket_start=_dt(0),
        bucket_end=_dt(1),
        accepted_at=_dt(1, 1),
    )
    assert bucket.long_liquidation_usd == 100.0
    assert bucket.short_liquidation_usd == 40.0
    assert bucket.event_count == 5


def test_bucket_identity_is_deterministic_for_input_order() -> None:
    first = _event("a", side="long", usd=100.0)
    second = _event("b", side="short", usd=40.0, second=20)
    kwargs = dict(bucket_start=_dt(0), bucket_end=_dt(1), accepted_at=_dt(1, 1))
    left = aggregate_liquidation_bucket([first, second], **kwargs)
    right = aggregate_liquidation_bucket([second, first], **kwargs)
    assert left.observation_id == right.observation_id
    assert left.long_liquidation_usd == right.long_liquidation_usd
    assert left.short_liquidation_usd == right.short_liquidation_usd


def test_bucket_rejects_mixed_series() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        aggregate_liquidation_bucket(
            [
                _event("a", side="long", usd=1.0),
                _event("b", side="short", usd=1.0, instrument="ETHUSDT"),
            ],
            bucket_start=_dt(0),
            bucket_end=_dt(1),
            accepted_at=_dt(1, 1),
        )


def test_bucket_rejects_event_outside_half_open_window() -> None:
    outside = _event("a", side="long", usd=1.0, minute=1, second=0)
    with pytest.raises(CryptoDerivativeContractError):
        aggregate_liquidation_bucket(
            [outside],
            bucket_start=_dt(0),
            bucket_end=_dt(1),
            accepted_at=_dt(1, 1),
        )


def test_total_directional_share_and_event_rate() -> None:
    bucket = _bucket(0, long_usd=75.0, short_usd=25.0)
    assert liquidation_total_usd(bucket).value == 100.0
    assert liquidation_directional_share(bucket).value == 0.5
    assert liquidation_event_rate(bucket).value == pytest.approx(2 / 60)


def test_acceleration_and_multiplier_use_contiguous_buckets() -> None:
    previous = _bucket(0, long_usd=60.0, short_usd=40.0)
    current = _bucket(1, long_usd=200.0, short_usd=50.0)
    acceleration = liquidation_acceleration_usd(previous, current)
    multiplier = liquidation_multiplier(previous, current)
    assert acceleration.value == 150.0
    assert multiplier.value == 2.5
    assert acceleration.input_observation_ids == (previous.observation_id, current.observation_id)
    assert multiplier.method_version == "uwbs-075-v1"


def test_cascade_metrics_reject_noncontiguous_buckets() -> None:
    previous = _bucket(0, long_usd=100.0, short_usd=0.0)
    current = _bucket(2, long_usd=200.0, short_usd=0.0)
    with pytest.raises(CryptoDerivativeContractError):
        liquidation_acceleration_usd(previous, current)


def test_multiplier_rejects_zero_previous_total() -> None:
    previous = _bucket(0, long_usd=0.0, short_usd=0.0)
    current = _bucket(1, long_usd=10.0, short_usd=0.0)
    with pytest.raises(CryptoDerivativeContractError):
        liquidation_multiplier(previous, current)


def test_directional_share_is_zero_when_no_liquidation_notional() -> None:
    bucket = _bucket(0, long_usd=0.0, short_usd=0.0)
    assert liquidation_directional_share(bucket).value == 0.0
