"""UWBS-086 D1 billing-capacity evidence helpers.

This module consumes previously captured D1 query metadata.  It never contacts
Cloudflare or mutates a database.  The intent is to turn repository-backed
D1Result ``meta`` snapshots into deterministic daily capacity projections.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Iterable

from orderscope_local.contracts.errors import ContractViolation
from .cross_asset_canary_replay import ProjectedCapacityUsage


@dataclass(frozen=True, kw_only=True)
class D1QueryMetaObservation:
    rows_read: int
    rows_written: int
    size_after: int | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.rows_read, "rows_read"),
            (self.rows_written, "rows_written"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractViolation(f"{field} must be a non-negative integer")
        if self.size_after is not None and (
            isinstance(self.size_after, bool)
            or not isinstance(self.size_after, int)
            or self.size_after < 0
        ):
            raise ContractViolation("size_after must be a non-negative integer when supplied")


@dataclass(frozen=True, kw_only=True)
class D1InvocationCapacitySample:
    queries: tuple[D1QueryMetaObservation, ...]
    database_size_before: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.queries, tuple) or not self.queries:
            raise ContractViolation("D1 invocation sample requires at least one query meta observation")
        if self.database_size_before is not None and (
            isinstance(self.database_size_before, bool)
            or not isinstance(self.database_size_before, int)
            or self.database_size_before < 0
        ):
            raise ContractViolation("database_size_before must be a non-negative integer when supplied")

    @property
    def rows_read(self) -> int:
        return sum(item.rows_read for item in self.queries)

    @property
    def rows_written(self) -> int:
        return sum(item.rows_written for item in self.queries)

    @property
    def storage_growth_bytes(self) -> int:
        sizes = [item.size_after for item in self.queries if item.size_after is not None]
        if not sizes or self.database_size_before is None:
            return 0
        return max(0, sizes[-1] - self.database_size_before)


def parse_d1_query_meta(value: dict[str, Any]) -> D1QueryMetaObservation:
    """Parse the billing-relevant subset of one Cloudflare D1 result meta object."""

    return D1QueryMetaObservation(
        rows_read=_integer(value.get("rows_read"), "rows_read"),
        rows_written=_integer(value.get("rows_written"), "rows_written"),
        size_after=_optional_integer(value.get("size_after"), "size_after"),
    )


def build_d1_invocation_sample(
    metas: Iterable[dict[str, Any]],
    *,
    database_size_before: int | None = None,
) -> D1InvocationCapacitySample:
    queries = tuple(parse_d1_query_meta(item) for item in metas)
    return D1InvocationCapacitySample(queries=queries, database_size_before=database_size_before)


def project_daily_capacity_from_samples(
    *,
    samples: tuple[D1InvocationCapacitySample, ...],
    scheduled_invocations_per_day: int,
    worker_requests_per_day: int | None = None,
    safety_multiplier: float = 1.25,
) -> ProjectedCapacityUsage:
    """Project daily usage from the worst observed invocation with a safety margin.

    The maximum rows-read, rows-written and storage-growth values are selected
    independently across supplied samples, then scaled by the requested safety
    multiplier and scheduled invocation count.  This is intentionally
    conservative and does not assume query-count equals billing rows.
    """

    if not isinstance(samples, tuple) or not samples:
        raise ContractViolation("capacity projection requires at least one D1 invocation sample")
    if isinstance(scheduled_invocations_per_day, bool) or not isinstance(scheduled_invocations_per_day, int) or scheduled_invocations_per_day <= 0:
        raise ContractViolation("scheduled_invocations_per_day must be a positive integer")
    if isinstance(safety_multiplier, bool) or not isinstance(safety_multiplier, (int, float)) or safety_multiplier < 1:
        raise ContractViolation("safety_multiplier must be numeric and at least one")
    if worker_requests_per_day is None:
        worker_requests_per_day = scheduled_invocations_per_day
    if isinstance(worker_requests_per_day, bool) or not isinstance(worker_requests_per_day, int) or worker_requests_per_day < 0:
        raise ContractViolation("worker_requests_per_day must be a non-negative integer")

    max_rows_read = max(item.rows_read for item in samples)
    max_rows_written = max(item.rows_written for item in samples)
    max_storage_growth = max(item.storage_growth_bytes for item in samples)

    return ProjectedCapacityUsage(
        worker_requests_per_day=worker_requests_per_day,
        d1_rows_read_per_day=ceil(max_rows_read * scheduled_invocations_per_day * float(safety_multiplier)),
        d1_rows_written_per_day=ceil(max_rows_written * scheduled_invocations_per_day * float(safety_multiplier)),
        d1_bytes_written_per_day=ceil(max_storage_growth * scheduled_invocations_per_day * float(safety_multiplier)),
        scheduled_invocations_per_day=scheduled_invocations_per_day,
    )


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractViolation(f"D1 meta {field} must be a non-negative integer")
    return value


def _optional_integer(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _integer(value, field)
