from __future__ import annotations

from pathlib import Path

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.integration import SchedulerJob, SchedulerLock, run_scheduler


def _job(name: str, sink: list[str]) -> SchedulerJob:
    return SchedulerJob(name=name, execute=lambda: sink.append(name))


def test_scheduler_executes_in_order_with_bound(tmp_path: Path) -> None:
    sink: list[str] = []
    jobs = (_job("a", sink), _job("b", sink), _job("c", sink))
    result = run_scheduler(jobs=jobs, lock_path=tmp_path / "scheduler.lock", max_jobs=2)
    assert result.selected == ("a", "b")
    assert result.completed == ("a", "b")
    assert sink == ["a", "b"]


def test_scheduler_dry_run_has_no_side_effects(tmp_path: Path) -> None:
    sink: list[str] = []
    jobs = (_job("a", sink), _job("b", sink))
    result = run_scheduler(jobs=jobs, lock_path=tmp_path / "scheduler.lock", max_jobs=2, dry_run=True)
    assert result.selected == ("a", "b")
    assert result.completed == ()
    assert sink == []
    assert not (tmp_path / "scheduler.lock").exists()


def test_scheduler_resume_starts_after_completed_job(tmp_path: Path) -> None:
    sink: list[str] = []
    jobs = (_job("a", sink), _job("b", sink), _job("c", sink))
    result = run_scheduler(
        jobs=jobs,
        lock_path=tmp_path / "scheduler.lock",
        max_jobs=10,
        resume_after="a",
    )
    assert result.selected == ("b", "c")
    assert sink == ["b", "c"]


def test_scheduler_rejects_unknown_resume_job(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation, match="resume_after job"):
        run_scheduler(jobs=(), lock_path=tmp_path / "scheduler.lock", max_jobs=1, resume_after="missing")


def test_scheduler_rejects_duplicate_job_names(tmp_path: Path) -> None:
    sink: list[str] = []
    jobs = (_job("same", sink), _job("same", sink))
    with pytest.raises(ContractViolation, match="unique"):
        run_scheduler(jobs=jobs, lock_path=tmp_path / "scheduler.lock", max_jobs=2)


def test_scheduler_rejects_invalid_bound(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation, match="max_jobs"):
        run_scheduler(jobs=(), lock_path=tmp_path / "scheduler.lock", max_jobs=0)


def test_scheduler_lock_rejects_second_instance(tmp_path: Path) -> None:
    path = tmp_path / "scheduler.lock"
    with SchedulerLock(path):
        with pytest.raises(ContractViolation, match="already running"):
            with SchedulerLock(path):
                pass
    assert not path.exists()


def test_scheduler_releases_lock_when_job_fails(tmp_path: Path) -> None:
    path = tmp_path / "scheduler.lock"

    def fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        run_scheduler(jobs=(SchedulerJob("fail", fail),), lock_path=path, max_jobs=1)
    assert not path.exists()
