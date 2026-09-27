"""UWBS-086 non-live capacity bound for the checked-in shadow scheduler.

This model applies only while WORKER_MODE=shadow and NEWS_ACQUISITION_ENABLED=false.
The shadow scheduler returns before market/news acquisition and persists one digest
per Cron invocation through D1LatestDigestStore.put().

Rows are bounded from the checked-in SQL shape and D1 billing semantics. The model
is deliberately conservative and is not a substitute for live-mode D1Result meta.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from orderscope_local.contracts.errors import ContractViolation
from .cross_asset_canary_replay import ProjectedCapacityUsage


SHADOW_INVOCATIONS_PER_DAY = 1_440
DIGEST_HISTORY_RETENTION = 96

# D1LatestDigestStore.put() executes:
# 1) latest_digest upsert: conservatively one table row + one PK index row
# 2) digest_history insert: table row + PK index row + recent secondary index row
# 3) digest_history delete after retention: table row + the same two index rows
# This intentionally overstates the steady-state latest_digest UPDATE path because
# digest_key itself is not changed by the UPDATE.
SHADOW_ROWS_WRITTEN_PER_TICK_BOUND = 8

# digest_history is bounded to at most 97 rows immediately after the insert and has
# a composite recent index on (digest_key, generated_at DESC). 400 rows/tick is a
# conservative non-live planning bound that covers indexed key probes plus scanning
# both the retained candidate set and its index entries. It is not a measured value.
SHADOW_ROWS_READ_PER_TICK_BOUND = 400


@dataclass(frozen=True, kw_only=True)
class ShadowCapacityBound:
    scheduled_invocations_per_day: int = SHADOW_INVOCATIONS_PER_DAY
    safety_multiplier: float = 1.25
    max_shadow_digest_payload_bytes: int = 8 * 1024

    def __post_init__(self) -> None:
        if not isinstance(self.scheduled_invocations_per_day, int) or isinstance(self.scheduled_invocations_per_day, bool):
            raise ContractViolation("scheduled_invocations_per_day must be an integer")
        if self.scheduled_invocations_per_day <= 0:
            raise ContractViolation("scheduled_invocations_per_day must be positive")
        if not isinstance(self.safety_multiplier, (int, float)) or isinstance(self.safety_multiplier, bool):
            raise ContractViolation("safety_multiplier must be numeric")
        if self.safety_multiplier < 1:
            raise ContractViolation("safety_multiplier must be at least 1")
        if not isinstance(self.max_shadow_digest_payload_bytes, int) or isinstance(self.max_shadow_digest_payload_bytes, bool):
            raise ContractViolation("max_shadow_digest_payload_bytes must be an integer")
        if self.max_shadow_digest_payload_bytes <= 0:
            raise ContractViolation("max_shadow_digest_payload_bytes must be positive")

    @property
    def retained_digest_rows(self) -> int:
        return DIGEST_HISTORY_RETENTION + 1  # history + latest

    @property
    def warmup_storage_growth_bound_bytes(self) -> int:
        """Conservative logical payload growth before the 96-row history is full.

        A 2x factor covers row/index/SQLite overhead for planning. After warm-up,
        digest row cardinality is bounded; this is not a claim that SQLite file
        size shrinks immediately after deletes.
        """

        return self.retained_digest_rows * self.max_shadow_digest_payload_bytes * 2

    def projected_daily_usage(self) -> ProjectedCapacityUsage:
        invocations = self.scheduled_invocations_per_day
        return ProjectedCapacityUsage(
            worker_requests_per_day=invocations,
            d1_rows_read_per_day=ceil(invocations * SHADOW_ROWS_READ_PER_TICK_BOUND * self.safety_multiplier),
            d1_rows_written_per_day=ceil(invocations * SHADOW_ROWS_WRITTEN_PER_TICK_BOUND * self.safety_multiplier),
            # Daily positive growth is bounded by initial warm-up; once retention is
            # full, logical digest cardinality no longer grows with each minute tick.
            d1_bytes_written_per_day=ceil(self.warmup_storage_growth_bound_bytes * self.safety_multiplier),
            scheduled_invocations_per_day=invocations,
        )
