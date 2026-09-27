import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.d1_capacity_evidence import (
    D1InvocationCapacitySample,
    D1QueryMetaObservation,
    build_d1_invocation_sample,
    parse_d1_query_meta,
    project_daily_capacity_from_samples,
)


def test_parse_d1_query_meta_preserves_billing_rows_and_size() -> None:
    item = parse_d1_query_meta({"rows_read": 12, "rows_written": 3, "size_after": 1000})
    assert item.rows_read == 12
    assert item.rows_written == 3
    assert item.size_after == 1000


def test_parse_d1_query_meta_rejects_missing_billing_rows() -> None:
    with pytest.raises(ContractViolation, match="rows_read"):
        parse_d1_query_meta({"rows_written": 1})


def test_invocation_sample_sums_rows() -> None:
    sample = D1InvocationCapacitySample(
        queries=(
            D1QueryMetaObservation(rows_read=10, rows_written=2),
            D1QueryMetaObservation(rows_read=5, rows_written=1),
        )
    )
    assert sample.rows_read == 15
    assert sample.rows_written == 3


def test_invocation_sample_uses_final_size_for_storage_growth() -> None:
    sample = build_d1_invocation_sample(
        [
            {"rows_read": 1, "rows_written": 1, "size_after": 1005},
            {"rows_read": 1, "rows_written": 1, "size_after": 1025},
        ],
        database_size_before=1000,
    )
    assert sample.storage_growth_bytes == 25


def test_storage_growth_never_goes_negative() -> None:
    sample = build_d1_invocation_sample(
        [{"rows_read": 1, "rows_written": 0, "size_after": 900}],
        database_size_before=1000,
    )
    assert sample.storage_growth_bytes == 0


def test_daily_projection_uses_worst_sample_independently() -> None:
    samples = (
        build_d1_invocation_sample(
            [{"rows_read": 100, "rows_written": 2, "size_after": 1010}],
            database_size_before=1000,
        ),
        build_d1_invocation_sample(
            [{"rows_read": 20, "rows_written": 10, "size_after": 1030}],
            database_size_before=1000,
        ),
    )
    projected = project_daily_capacity_from_samples(
        samples=samples,
        scheduled_invocations_per_day=10,
        safety_multiplier=1.25,
    )
    assert projected.d1_rows_read_per_day == 1250
    assert projected.d1_rows_written_per_day == 125
    assert projected.d1_bytes_written_per_day == 375
    assert projected.worker_requests_per_day == 10


def test_worker_request_projection_can_be_supplied_separately() -> None:
    sample = build_d1_invocation_sample([{"rows_read": 1, "rows_written": 1}])
    projected = project_daily_capacity_from_samples(
        samples=(sample,),
        scheduled_invocations_per_day=1440,
        worker_requests_per_day=5000,
    )
    assert projected.worker_requests_per_day == 5000


def test_projection_requires_positive_schedule() -> None:
    sample = build_d1_invocation_sample([{"rows_read": 1, "rows_written": 1}])
    with pytest.raises(ContractViolation, match="positive integer"):
        project_daily_capacity_from_samples(samples=(sample,), scheduled_invocations_per_day=0)


def test_projection_requires_at_least_one_sample() -> None:
    with pytest.raises(ContractViolation, match="at least one"):
        project_daily_capacity_from_samples(samples=(), scheduled_invocations_per_day=1440)


def test_projection_rejects_safety_multiplier_below_one() -> None:
    sample = build_d1_invocation_sample([{"rows_read": 1, "rows_written": 1}])
    with pytest.raises(ContractViolation, match="at least one"):
        project_daily_capacity_from_samples(
            samples=(sample,),
            scheduled_invocations_per_day=1440,
            safety_multiplier=0.9,
        )
