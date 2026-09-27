import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.shadow_capacity_bound import (
    DIGEST_HISTORY_RETENTION,
    SHADOW_INVOCATIONS_PER_DAY,
    SHADOW_ROWS_READ_PER_TICK_BOUND,
    SHADOW_ROWS_WRITTEN_PER_TICK_BOUND,
    ShadowCapacityBound,
)


def test_checked_in_shadow_defaults_are_minute_cron() -> None:
    bound = ShadowCapacityBound()
    assert bound.scheduled_invocations_per_day == 1_440
    assert SHADOW_INVOCATIONS_PER_DAY == 1_440


def test_shadow_digest_history_retains_96_plus_latest() -> None:
    bound = ShadowCapacityBound()
    assert DIGEST_HISTORY_RETENTION == 96
    assert bound.retained_digest_rows == 97


def test_shadow_read_bound_is_conservative_and_bounded() -> None:
    assert SHADOW_ROWS_READ_PER_TICK_BOUND == 400


def test_shadow_write_bound_includes_index_rows() -> None:
    assert SHADOW_ROWS_WRITTEN_PER_TICK_BOUND == 8


def test_default_projection_includes_25_percent_safety_margin() -> None:
    projected = ShadowCapacityBound().projected_daily_usage()
    assert projected.worker_requests_per_day == 1_440
    assert projected.d1_rows_read_per_day == 720_000
    assert projected.d1_rows_written_per_day == 14_400
    assert projected.scheduled_invocations_per_day == 1_440


def test_default_warmup_storage_bound_is_small_and_finite() -> None:
    bound = ShadowCapacityBound()
    assert bound.warmup_storage_growth_bound_bytes == 97 * 8192 * 2
    assert bound.projected_daily_usage().d1_bytes_written_per_day == 1_986_560


def test_projection_accepts_more_conservative_payload_bound() -> None:
    projected = ShadowCapacityBound(max_shadow_digest_payload_bytes=16 * 1024).projected_daily_usage()
    assert projected.d1_bytes_written_per_day == 3_973_120


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"scheduled_invocations_per_day": 0}, "scheduled_invocations_per_day"),
        ({"safety_multiplier": 0.99}, "safety_multiplier"),
        ({"max_shadow_digest_payload_bytes": 0}, "max_shadow_digest_payload_bytes"),
    ],
)
def test_shadow_bound_rejects_invalid_configuration(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ContractViolation, match=message):
        ShadowCapacityBound(**kwargs)
