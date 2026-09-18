"""Bounded manual scheduler for accepted local adapter jobs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
import os

from orderscope_local.contracts import ContractViolation


@dataclass(frozen=True, slots=True)
class SchedulerJob:
    """One explicit scheduler unit supplied by an owning adapter/integration task."""

    name: str
    execute: Callable[[], None]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ContractViolation("scheduler job name must be non-empty")
        if not callable(self.execute):
            raise ContractViolation("scheduler job execute must be callable")


@dataclass(frozen=True, slots=True)
class SchedulerRunResult:
    selected: tuple[str, ...]
    completed: tuple[str, ...]
    dry_run: bool
    resume_after: str | None


class SchedulerLock:
    """Filesystem single-instance lock using exclusive file creation."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._fd: int | None = None

    def __enter__(self) -> "SchedulerLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ContractViolation("local scheduler is already running") from exc
        os.write(self._fd, f"pid={os.getpid()}\n".encode("ascii"))
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def run_scheduler(
    *,
    jobs: Iterable[SchedulerJob],
    lock_path: str | Path,
    max_jobs: int,
    resume_after: str | None = None,
    dry_run: bool = False,
) -> SchedulerRunResult:
    """Select and optionally execute a bounded deterministic scheduler run.

    Resume is intentionally job-boundary based in X0-004. Provider cursor/checkpoint
    semantics remain owned by each adapter; this layer never parses provider cursors.
    """

    if not isinstance(max_jobs, int) or isinstance(max_jobs, bool) or not 1 <= max_jobs <= 100:
        raise ContractViolation("max_jobs must be an integer between 1 and 100")
    if resume_after is not None and (not isinstance(resume_after, str) or not resume_after.strip()):
        raise ContractViolation("resume_after must be a non-empty job name")
    if not isinstance(dry_run, bool):
        raise ContractViolation("dry_run must be bool")

    job_tuple = tuple(jobs)
    if any(not isinstance(job, SchedulerJob) for job in job_tuple):
        raise ContractViolation("jobs must contain SchedulerJob values")
    names = tuple(job.name for job in job_tuple)
    if len(names) != len(set(names)):
        raise ContractViolation("scheduler job names must be unique")

    start = 0
    if resume_after is not None:
        try:
            start = names.index(resume_after) + 1
        except ValueError as exc:
            raise ContractViolation("resume_after job is not present in the scheduler plan") from exc

    selected_jobs = job_tuple[start : start + max_jobs]
    selected = tuple(job.name for job in selected_jobs)
    if dry_run:
        return SchedulerRunResult(selected=selected, completed=(), dry_run=True, resume_after=resume_after)

    completed: list[str] = []
    with SchedulerLock(lock_path):
        for job in selected_jobs:
            job.execute()
            completed.append(job.name)

    return SchedulerRunResult(
        selected=selected,
        completed=tuple(completed),
        dry_run=False,
        resume_after=resume_after,
    )
