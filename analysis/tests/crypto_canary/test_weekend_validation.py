from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.crypto_canary import (
    WeekendHandoffEpisode,
    WeekendValidationStatus,
    validate_weekend_rerisking,
)
from orderscope_local.crypto_time import classify_crypto_time

UTC = timezone.utc


def _ctx(year: int, month: int, day: int, hour: int = 12):
    return classify_crypto_time(datetime(year, month, day, hour, tzinfo=UTC))


def _episode(
    episode_id: str,
    *,
    weekend_day: int,
    weekday_day: int,
    btc_return: float,
    altcoin_return: float,
    breadth: float,
    lag: int,
    spot_volume: float = 0.10,
    derivatives_volume: float = 0.15,
    oi_change: float = 0.05,
    funding_change: float = 0.0001,
    liquidation_imbalance: float = 0.2,
    persistence_1h: float = 0.01,
    persistence_3h: float = 0.02,
    persistence_6h: float = 0.03,
    persistence_24h: float = 0.04,
) -> WeekendHandoffEpisode:
    return WeekendHandoffEpisode(
        episode_id=episode_id,
        weekend_context=_ctx(2026, 9, weekend_day),
        weekday_context=_ctx(2026, 9, weekday_day),
        btc_return=btc_return,
        altcoin_return=altcoin_return,
        synchronized_breadth=breadth,
        max_btc_alt_lag_minutes=lag,
        spot_volume_change=spot_volume,
        derivatives_volume_change=derivatives_volume,
        open_interest_change=oi_change,
        funding_change=funding_change,
        liquidation_imbalance=liquidation_imbalance,
        persistence_1h=persistence_1h,
        persistence_3h=persistence_3h,
        persistence_6h=persistence_6h,
        persistence_24h=persistence_24h,
        source_refs=(f"fixture:{episode_id}",),
    )


def test_single_weekend_is_insufficient_sample() -> None:
    episode = _episode(
        "w1",
        weekend_day=5,
        weekday_day=7,
        btc_return=0.03,
        altcoin_return=0.06,
        breadth=0.75,
        lag=5,
    )

    result = validate_weekend_rerisking((episode,), minimum_independent_weekends=4)

    assert result.status is WeekendValidationStatus.INSUFFICIENT_SAMPLE
    assert result.episode_count == 1
    assert result.same_direction_fraction == 1.0


def test_four_independent_weekends_reach_experimental_status() -> None:
    episodes = (
        _episode("w1", weekend_day=5, weekday_day=7, btc_return=0.03, altcoin_return=0.06, breadth=0.8, lag=5),
        _episode("w2", weekend_day=12, weekday_day=14, btc_return=-0.02, altcoin_return=-0.04, breadth=0.7, lag=10),
        _episode("w3", weekend_day=19, weekday_day=21, btc_return=0.0002, altcoin_return=0.001, breadth=0.5, lag=0),
        _episode("w4", weekend_day=26, weekday_day=28, btc_return=0.04, altcoin_return=-0.01, breadth=0.4, lag=-5),
    )

    result = validate_weekend_rerisking(episodes, minimum_independent_weekends=4)

    assert result.status is WeekendValidationStatus.EXPERIMENTAL
    assert result.positive_btc_weekends == 2
    assert result.negative_btc_weekends == 1
    assert result.flat_btc_weekends == 1
    assert result.same_direction_fraction == pytest.approx(0.75)
    assert result.median_synchronized_breadth == pytest.approx(0.6)
    assert result.median_max_btc_alt_lag_minutes == pytest.approx(2.5)


def test_summary_uses_medians_for_recurrence_features() -> None:
    episodes = (
        _episode(
            "w1",
            weekend_day=5,
            weekday_day=7,
            btc_return=0.03,
            altcoin_return=0.04,
            breadth=0.8,
            lag=5,
            spot_volume=0.10,
            derivatives_volume=0.20,
            oi_change=0.05,
            funding_change=0.0001,
            liquidation_imbalance=0.4,
            persistence_1h=0.01,
            persistence_3h=0.02,
            persistence_6h=0.03,
            persistence_24h=0.04,
        ),
        _episode(
            "w2",
            weekend_day=12,
            weekday_day=14,
            btc_return=0.02,
            altcoin_return=0.03,
            breadth=0.6,
            lag=15,
            spot_volume=0.30,
            derivatives_volume=0.40,
            oi_change=0.15,
            funding_change=0.0003,
            liquidation_imbalance=-0.2,
            persistence_1h=0.03,
            persistence_3h=0.04,
            persistence_6h=0.05,
            persistence_24h=0.06,
        ),
    )

    result = validate_weekend_rerisking(episodes, minimum_independent_weekends=2)

    assert result.median_spot_volume_change == pytest.approx(0.20)
    assert result.median_derivatives_volume_change == pytest.approx(0.30)
    assert result.median_open_interest_change == pytest.approx(0.10)
    assert result.median_funding_change == pytest.approx(0.0002)
    assert result.median_liquidation_imbalance == pytest.approx(0.1)
    assert result.median_persistence_24h == pytest.approx(0.05)


def test_episode_rejects_weekday_as_weekend_context() -> None:
    with pytest.raises(ContractViolation):
        WeekendHandoffEpisode(
            episode_id="bad",
            weekend_context=_ctx(2026, 9, 7),
            weekday_context=_ctx(2026, 9, 8),
            btc_return=0.01,
            altcoin_return=0.01,
            synchronized_breadth=0.5,
            max_btc_alt_lag_minutes=0,
            spot_volume_change=0.0,
            derivatives_volume_change=0.0,
            open_interest_change=0.0,
            funding_change=0.0,
            liquidation_imbalance=0.0,
            persistence_1h=0.0,
            persistence_3h=0.0,
            persistence_6h=0.0,
            persistence_24h=0.0,
            source_refs=("fixture:bad",),
        )


def test_episode_rejects_out_of_range_breadth() -> None:
    with pytest.raises(ContractViolation):
        _episode(
            "bad",
            weekend_day=5,
            weekday_day=7,
            btc_return=0.01,
            altcoin_return=0.01,
            breadth=1.1,
            lag=0,
        )


def test_episode_rejects_lag_outside_research_range() -> None:
    with pytest.raises(ContractViolation):
        _episode(
            "bad",
            weekend_day=5,
            weekday_day=7,
            btc_return=0.01,
            altcoin_return=0.01,
            breadth=0.5,
            lag=61,
        )


def test_validation_rejects_duplicate_episode_ids() -> None:
    first = _episode("same", weekend_day=5, weekday_day=7, btc_return=0.01, altcoin_return=0.01, breadth=0.5, lag=0)
    second = _episode("same", weekend_day=12, weekday_day=14, btc_return=0.01, altcoin_return=0.01, breadth=0.5, lag=0)

    with pytest.raises(ContractViolation):
        validate_weekend_rerisking((first, second), minimum_independent_weekends=2)


def test_validation_rejects_same_weekend_date_twice() -> None:
    first = _episode("a", weekend_day=5, weekday_day=7, btc_return=0.01, altcoin_return=0.01, breadth=0.5, lag=0)
    second = _episode("b", weekend_day=5, weekday_day=7, btc_return=-0.01, altcoin_return=-0.01, breadth=0.6, lag=5)

    with pytest.raises(ContractViolation):
        validate_weekend_rerisking((first, second), minimum_independent_weekends=2)


def test_validation_rejects_minimum_sample_below_two() -> None:
    episode = _episode("w1", weekend_day=5, weekday_day=7, btc_return=0.01, altcoin_return=0.01, breadth=0.5, lag=0)

    with pytest.raises(ContractViolation):
        validate_weekend_rerisking((episode,), minimum_independent_weekends=1)


def test_source_lineage_is_deduplicated_stably() -> None:
    first = _episode("w1", weekend_day=5, weekday_day=7, btc_return=0.01, altcoin_return=0.01, breadth=0.5, lag=0)
    second = _episode("w2", weekend_day=12, weekday_day=14, btc_return=0.02, altcoin_return=0.03, breadth=0.6, lag=5)
    second = WeekendHandoffEpisode(
        episode_id=second.episode_id,
        weekend_context=second.weekend_context,
        weekday_context=second.weekday_context,
        btc_return=second.btc_return,
        altcoin_return=second.altcoin_return,
        synchronized_breadth=second.synchronized_breadth,
        max_btc_alt_lag_minutes=second.max_btc_alt_lag_minutes,
        spot_volume_change=second.spot_volume_change,
        derivatives_volume_change=second.derivatives_volume_change,
        open_interest_change=second.open_interest_change,
        funding_change=second.funding_change,
        liquidation_imbalance=second.liquidation_imbalance,
        persistence_1h=second.persistence_1h,
        persistence_3h=second.persistence_3h,
        persistence_6h=second.persistence_6h,
        persistence_24h=second.persistence_24h,
        source_refs=("fixture:w1", "fixture:w2"),
    )

    result = validate_weekend_rerisking((first, second), minimum_independent_weekends=2)

    assert result.source_refs == ("fixture:w1", "fixture:w2")
    assert result.method_version == "uwbs-079-v1"
