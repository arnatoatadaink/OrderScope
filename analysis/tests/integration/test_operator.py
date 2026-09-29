from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.integration.operator import (
    MAX_OPERATOR_ITEMS,
    OPERATOR_CONTRACT_VERSION,
    OperatorSnapshot,
    ReplayBacklogItem,
    RetentionBacklogItem,
    WorkState,
    execute_deletions,
    execute_replay,
    inspect_retention,
    plan_bounded_replay,
    select_due_deletions,
)

UTC = timezone.utc
NOW = datetime(2026, 9, 12, 0, 0, tzinfo=UTC)


class ReplayExecutor:
    def __init__(self):
        self.calls = []

    def replay(self, **kwargs):
        self.calls.append(kwargs)
        return len(kwargs["work_ids"])


class Deleter:
    def __init__(self, *, proof="delete-proof:ok", error=None):
        self.calls = []
        self.proof = proof
        self.error = error

    def delete(self, *, content_ref):
        self.calls.append(content_ref)
        if self.error:
            raise self.error
        return self.proof


def _snapshot():
    return OperatorSnapshot(
        retention=(
            RetentionBacklogItem("temp://due", NOW, WorkState.PENDING),
            RetentionBacklogItem("temp://overdue", NOW - timedelta(minutes=1), WorkState.RETRYABLE, "DELETE_FAILED"),
            RetentionBacklogItem("temp://future", NOW + timedelta(hours=1), WorkState.PENDING),
            RetentionBacklogItem("temp://deleted", NOW - timedelta(days=1), WorkState.DELETED),
        ),
        replay=(
            ReplayBacklogItem("r1", "alpaca-news", NOW - timedelta(hours=3), NOW - timedelta(hours=2), WorkState.FAILED, "TRANSPORT"),
            ReplayBacklogItem("r2", "alpaca-news", NOW - timedelta(hours=2), NOW - timedelta(hours=1), WorkState.RETRYABLE, "TRANSPORT"),
            ReplayBacklogItem("done", "alpaca-news", NOW - timedelta(hours=1), NOW, WorkState.COMPLETE),
            ReplayBacklogItem("other", "sec", NOW - timedelta(hours=2), NOW - timedelta(hours=1), WorkState.FAILED),
        ),
    )


def test_contract_version_is_frozen():
    assert OPERATOR_CONTRACT_VERSION == "operator-bounded-replay-v0.1"


def test_retention_inspection_counts_due_overdue_and_failures():
    result = inspect_retention(snapshot=_snapshot(), now=NOW)
    assert result.pending == 3
    assert result.due == 2
    assert result.overdue == 1
    assert result.retryable_or_failed == 1
    assert result.deleted == 1


def test_replay_requires_explicit_bounded_window_and_retryable_state():
    plan = plan_bounded_replay(
        snapshot=_snapshot(), source="alpaca-news",
        start=NOW - timedelta(hours=4), end=NOW,
        max_items=10, dry_run=True,
    )
    assert plan.work_ids == ("r1", "r2")
    assert "done" not in plan.work_ids
    assert "other" not in plan.work_ids


def test_replay_rejects_unbounded_or_invalid_window():
    with pytest.raises(ContractViolation, match="31 days"):
        plan_bounded_replay(
            snapshot=_snapshot(), source="alpaca-news",
            start=NOW - timedelta(days=32), end=NOW,
            max_items=1, dry_run=True,
        )
    with pytest.raises(ContractViolation, match="start < end"):
        plan_bounded_replay(
            snapshot=_snapshot(), source="alpaca-news",
            start=NOW, end=NOW,
            max_items=1, dry_run=True,
        )


def test_replay_selection_is_deterministic_and_capped():
    plan = plan_bounded_replay(
        snapshot=_snapshot(), source="alpaca-news",
        start=NOW - timedelta(hours=4), end=NOW,
        max_items=1, dry_run=True,
    )
    assert plan.work_ids == ("r1",)
    with pytest.raises(ContractViolation, match="between 1 and 100"):
        plan_bounded_replay(
            snapshot=_snapshot(), source="alpaca-news",
            start=NOW - timedelta(hours=4), end=NOW,
            max_items=MAX_OPERATOR_ITEMS + 1, dry_run=True,
        )


def test_dry_run_never_invokes_executor_but_execute_is_bounded():
    executor = ReplayExecutor()
    dry = plan_bounded_replay(
        snapshot=_snapshot(), source="alpaca-news",
        start=NOW - timedelta(hours=4), end=NOW,
        max_items=2, dry_run=True,
    )
    assert execute_replay(plan=dry, executor=executor) == 0
    assert executor.calls == []

    live = plan_bounded_replay(
        snapshot=_snapshot(), source="alpaca-news",
        start=NOW - timedelta(hours=4), end=NOW,
        max_items=2, dry_run=False,
    )
    assert execute_replay(plan=live, executor=executor) == 2
    assert executor.calls[0]["work_ids"] == ("r1", "r2")


def test_deletion_requires_explicit_due_refs_only():
    selected = select_due_deletions(
        snapshot=_snapshot(), now=NOW,
        content_refs=("temp://due", "temp://overdue"), max_items=2,
    )
    assert tuple(item.content_ref for item in selected) == ("temp://due", "temp://overdue")

    with pytest.raises(ContractViolation, match="explicit content_refs"):
        select_due_deletions(snapshot=_snapshot(), now=NOW, content_refs=(), max_items=1)
    with pytest.raises(ContractViolation, match="not yet due"):
        select_due_deletions(snapshot=_snapshot(), now=NOW, content_refs=("temp://future",), max_items=1)
    with pytest.raises(ContractViolation, match="already-deleted"):
        select_due_deletions(snapshot=_snapshot(), now=NOW, content_refs=("temp://deleted",), max_items=1)


def test_deletion_failure_does_not_expose_raw_error_and_proof_is_sanitized():
    items = select_due_deletions(snapshot=_snapshot(), now=NOW, content_refs=("temp://due",), max_items=1)
    with pytest.raises(ContractViolation, match="operator deletion failed") as exc:
        execute_deletions(items=items, deleter=Deleter(error=OSError("/secret/local/path")))
    assert "/secret/local/path" not in str(exc.value)

    with pytest.raises(ContractViolation, match="secret-like"):
        execute_deletions(items=items, deleter=Deleter(proof="api_key=do-not-store"))
