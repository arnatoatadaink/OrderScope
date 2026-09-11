"""Bounded operator planning for retention, retry, and replay.

This module is intentionally local/operator-only.  It never starts HTTP work and
never infers an unbounded replay range.  Concrete storage/provider adapters are
injected by later integration; this layer owns selection and safety semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol, Sequence

from orderscope_local.contracts import ContractViolation


OPERATOR_CONTRACT_VERSION = "operator-bounded-replay-v0.1"
MAX_REPLAY_WINDOW = timedelta(days=31)
MAX_OPERATOR_ITEMS = 100


class WorkState(StrEnum):
    PENDING = "PENDING"
    RETRYABLE = "RETRYABLE"
    FAILED = "FAILED"
    COMPLETE = "COMPLETE"
    DELETED = "DELETED"


@dataclass(frozen=True, slots=True)
class RetentionBacklogItem:
    content_ref: str
    due_at: datetime
    state: WorkState
    failure_category: str | None = None

    def __post_init__(self) -> None:
        _identity(self.content_ref, "content_ref")
        _utc(self.due_at, "due_at")
        if self.state not in {WorkState.PENDING, WorkState.RETRYABLE, WorkState.FAILED, WorkState.DELETED}:
            raise ContractViolation("retention state is not operator-visible")
        _optional_category(self.failure_category)


@dataclass(frozen=True, slots=True)
class ReplayBacklogItem:
    work_id: str
    source: str
    start: datetime
    end: datetime
    state: WorkState
    failure_category: str | None = None

    def __post_init__(self) -> None:
        _identity(self.work_id, "work_id")
        _identity(self.source, "source")
        _bounded_window(self.start, self.end)
        if self.state not in {WorkState.RETRYABLE, WorkState.FAILED, WorkState.COMPLETE}:
            raise ContractViolation("replay state is not operator-visible")
        _optional_category(self.failure_category)


@dataclass(frozen=True, slots=True)
class OperatorSnapshot:
    retention: tuple[RetentionBacklogItem, ...] = ()
    replay: tuple[ReplayBacklogItem, ...] = ()


@dataclass(frozen=True, slots=True)
class RetentionInspection:
    pending: int
    due: int
    overdue: int
    retryable_or_failed: int
    deleted: int


@dataclass(frozen=True, slots=True)
class ReplayPlan:
    source: str
    start: datetime
    end: datetime
    work_ids: tuple[str, ...]
    dry_run: bool


class ReplayExecutor(Protocol):
    def replay(self, *, source: str, start: datetime, end: datetime, work_ids: Sequence[str]) -> int: ...


class RetentionDeleter(Protocol):
    def delete(self, *, content_ref: str) -> str: ...


def inspect_retention(*, snapshot: OperatorSnapshot, now: datetime) -> RetentionInspection:
    _utc(now, "now")
    active = [item for item in snapshot.retention if item.state is not WorkState.DELETED]
    due = [item for item in active if item.due_at <= now]
    overdue = [item for item in active if item.due_at < now]
    failed = [item for item in active if item.state in {WorkState.RETRYABLE, WorkState.FAILED}]
    return RetentionInspection(
        pending=len(active),
        due=len(due),
        overdue=len(overdue),
        retryable_or_failed=len(failed),
        deleted=len(snapshot.retention) - len(active),
    )


def plan_bounded_replay(
    *,
    snapshot: OperatorSnapshot,
    source: str,
    start: datetime,
    end: datetime,
    max_items: int,
    dry_run: bool,
) -> ReplayPlan:
    _identity(source, "source")
    _bounded_window(start, end)
    _max_items(max_items)
    eligible = sorted(
        (
            item for item in snapshot.replay
            if item.source == source
            and item.state in {WorkState.RETRYABLE, WorkState.FAILED}
            and item.start >= start
            and item.end <= end
        ),
        key=lambda item: (item.start, item.end, item.work_id),
    )
    selected = eligible[:max_items]
    return ReplayPlan(source=source, start=start, end=end, work_ids=tuple(item.work_id for item in selected), dry_run=dry_run)


def execute_replay(*, plan: ReplayPlan, executor: ReplayExecutor) -> int:
    if plan.dry_run or not plan.work_ids:
        return 0
    completed = executor.replay(source=plan.source, start=plan.start, end=plan.end, work_ids=plan.work_ids)
    if not isinstance(completed, int) or completed < 0 or completed > len(plan.work_ids):
        raise ContractViolation("replay executor returned invalid completion count")
    return completed


def select_due_deletions(
    *,
    snapshot: OperatorSnapshot,
    now: datetime,
    content_refs: Sequence[str],
    max_items: int,
) -> tuple[RetentionBacklogItem, ...]:
    _utc(now, "now")
    _max_items(max_items)
    if not content_refs:
        raise ContractViolation("explicit content_refs are required for deletion")
    if len(content_refs) > max_items:
        raise ContractViolation("selected deletion count exceeds max_items")
    if len(set(content_refs)) != len(content_refs):
        raise ContractViolation("content_refs must be unique")
    requested = set(content_refs)
    by_ref = {item.content_ref: item for item in snapshot.retention}
    if requested - by_ref.keys():
        raise ContractViolation("selected deletion content_ref is not present in backlog")
    selected = tuple(by_ref[ref] for ref in content_refs)
    for item in selected:
        if item.state is WorkState.DELETED:
            raise ContractViolation("already-deleted content cannot be selected")
        if item.due_at > now:
            raise ContractViolation("content is not yet due for deletion")
    return selected


def execute_deletions(*, items: Sequence[RetentionBacklogItem], deleter: RetentionDeleter) -> tuple[str, ...]:
    proofs: list[str] = []
    for item in items:
        try:
            proof = deleter.delete(content_ref=item.content_ref)
        except Exception as exc:
            raise ContractViolation("operator deletion failed") from exc
        if not isinstance(proof, str) or not proof.strip() or len(proof) > 1024:
            raise ContractViolation("operator deletion proof must be bounded non-blank text")
        lowered = proof.casefold()
        if any(marker in lowered for marker in ("api_key=", "access_token=", "client_secret=", "password=")):
            raise ContractViolation("operator deletion proof must not contain secret-like values")
        proofs.append(proof)
    return tuple(proofs)


def _bounded_window(start: datetime, end: datetime) -> None:
    _utc(start, "start")
    _utc(end, "end")
    if start >= end:
        raise ContractViolation("bounded window requires start < end")
    if end - start > MAX_REPLAY_WINDOW:
        raise ContractViolation("bounded replay window exceeds 31 days")


def _max_items(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > MAX_OPERATOR_ITEMS:
        raise ContractViolation("max_items must be between 1 and 100")


def _identity(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 512:
        raise ContractViolation(f"{field} must be bounded non-blank canonical text")


def _optional_category(value: str | None) -> None:
    if value is not None:
        _identity(value, "failure_category")


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
