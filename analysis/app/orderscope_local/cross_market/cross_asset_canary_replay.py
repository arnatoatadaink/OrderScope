"""UWBS-086 deterministic replay and capacity planning helpers.

The evaluator is intentionally infrastructure-neutral.  Historical/synthetic
scenario expectations are supplied by the caller and Cloudflare quota values are
injected as planning inputs; no live service is queried or mutated here.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from orderscope_local.contracts.cross_asset_canary import (
    CapacityObservation,
    CrossAssetCanaryAssessment,
    CrossAssetCanaryResult,
)
from orderscope_local.contracts.errors import ContractViolation


@dataclass(frozen=True, kw_only=True)
class CapacityEnvelope:
    """External capacity limits used for one planning snapshot."""

    worker_requests_per_day: int
    d1_rows_written_per_day: int
    d1_bytes_available: int
    scheduled_invocations_per_day: int | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.worker_requests_per_day, "worker_requests_per_day"),
            (self.d1_rows_written_per_day, "d1_rows_written_per_day"),
            (self.d1_bytes_available, "d1_bytes_available"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ContractViolation(f"{field} must be a positive integer")
        if self.scheduled_invocations_per_day is not None and (
            isinstance(self.scheduled_invocations_per_day, bool)
            or not isinstance(self.scheduled_invocations_per_day, int)
            or self.scheduled_invocations_per_day <= 0
        ):
            raise ContractViolation("scheduled_invocations_per_day must be a positive integer when supplied")


@dataclass(frozen=True, kw_only=True)
class ProjectedCapacityUsage:
    worker_requests_per_day: int
    d1_rows_written_per_day: int
    d1_bytes_written_per_day: int
    scheduled_invocations_per_day: int

    def __post_init__(self) -> None:
        for value, field in (
            (self.worker_requests_per_day, "worker_requests_per_day"),
            (self.d1_rows_written_per_day, "d1_rows_written_per_day"),
            (self.d1_bytes_written_per_day, "d1_bytes_written_per_day"),
            (self.scheduled_invocations_per_day, "scheduled_invocations_per_day"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractViolation(f"{field} must be a non-negative integer")


def build_capacity_observation(
    *,
    projected: ProjectedCapacityUsage,
    envelope: CapacityEnvelope,
) -> CapacityObservation:
    """Compute conservative headroom as the minimum remaining ratio.

    D1 bytes are compared with caller-supplied remaining/available storage.  Cron
    invocations are included only if the caller supplies an explicit invocation
    envelope; the platform's Cron-trigger *count* limit is a separate deployment
    constraint and must not be confused with daily invocations.
    """

    ratios = [
        _remaining_ratio(projected.worker_requests_per_day, envelope.worker_requests_per_day),
        _remaining_ratio(projected.d1_rows_written_per_day, envelope.d1_rows_written_per_day),
        _remaining_ratio(projected.d1_bytes_written_per_day, envelope.d1_bytes_available),
    ]
    if envelope.scheduled_invocations_per_day is not None:
        ratios.append(
            _remaining_ratio(
                projected.scheduled_invocations_per_day,
                envelope.scheduled_invocations_per_day,
            )
        )

    return CapacityObservation(
        worker_requests_per_day=projected.worker_requests_per_day,
        d1_rows_written_per_day=projected.d1_rows_written_per_day,
        d1_bytes_written_per_day=projected.d1_bytes_written_per_day,
        scheduled_invocations_per_day=projected.scheduled_invocations_per_day,
        headroom_ratio=min(ratios),
    )


def assess_replay(
    *,
    results: tuple[CrossAssetCanaryResult, ...],
    projected: ProjectedCapacityUsage,
    envelope: CapacityEnvelope,
    minimum_headroom_ratio: float = 0.20,
) -> CrossAssetCanaryAssessment:
    if isinstance(minimum_headroom_ratio, bool) or not isinstance(minimum_headroom_ratio, (int, float)):
        raise ContractViolation("minimum_headroom_ratio must be numeric")
    if not isfinite(float(minimum_headroom_ratio)) or not 0 <= float(minimum_headroom_ratio) <= 1:
        raise ContractViolation("minimum_headroom_ratio must be between zero and one")
    return CrossAssetCanaryAssessment(
        results=results,
        capacity=build_capacity_observation(projected=projected, envelope=envelope),
        minimum_headroom_ratio=float(minimum_headroom_ratio),
    )


def _remaining_ratio(used: int, limit: int) -> float:
    if used >= limit:
        return 0.0
    return 1.0 - (used / limit)
