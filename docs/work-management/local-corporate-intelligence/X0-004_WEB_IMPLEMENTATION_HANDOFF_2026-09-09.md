# OrderScope — X0-004 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `X0-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-006` plus existing adapter-side prerequisites

## 1. Completion boundary

X0-004 implements the local scheduler execution boundary required by the WBS:

```text
manual CLI start
single-instance lock
bounded run
resume
dry-run
```

Implemented/changed files:

- `analysis/app/orderscope_local/integration/scheduler.py`
- `analysis/app/orderscope_local/integration/__init__.py`
- `analysis/app/orderscope_local/cli.py`
- `analysis/tests/integration/test_scheduler.py`
- `analysis/tests/cli/test_cli.py`

## 2. Scheduler core

`SchedulerJob` is an explicitly injected local job with a stable name and callable execution boundary.

`run_scheduler()`:

- requires a bounded `max_jobs` value from 1 through 100;
- rejects duplicate job names;
- preserves deterministic supplied order;
- supports job-boundary resume via `resume_after`;
- rejects unknown resume names rather than guessing;
- supports dry-run selection without executing jobs or taking the runtime lock;
- does not inspect provider cursor values; provider checkpoint semantics remain owned by adapters.

## 3. Single-instance boundary

`SchedulerLock` uses exclusive lock-file creation beneath the configured local data root.

Properties:

- a second scheduler execution fails closed while the lock exists;
- lock permissions are owner-only at creation;
- normal completion removes the lock;
- exceptions from a job also release the lock;
- X0-004 does not introduce a daemon, background service, or network scheduler.

## 4. Manual CLI boundary

The application CLI now exposes:

```text
orderscope schedule run --max-jobs N [--resume-after NAME] [--dry-run]
```

The current built-in job registry is intentionally empty. X0-004 establishes scheduler semantics without fabricating provider jobs or triggering live acquisition. Owning adapter/integration tasks can inject accepted jobs later without changing the scheduler contract.

The lock path is derived from non-secret local configuration:

```text
<ORDERSCOPE_DATA_ROOT>/locks/scheduler.lock
```

No HTTP endpoint starts scheduler jobs.

## 5. Focused tests

Focused X0-004 verification comprises 10 cases:

Scheduler core (8):
1. bounded ordered execution;
2. dry-run has no side effects;
3. resume starts after the named completed job;
4. unknown resume rejection;
5. duplicate job-name rejection;
6. invalid bound rejection;
7. second-instance lock rejection;
8. lock cleanup after job failure.

CLI integration (2):
9. manual `schedule run` boundary;
10. CLI dry-run path.

## 6. Local verification boundary

Run from repository root:

```bash
uv run pytest -q analysis/tests/integration/test_scheduler.py analysis/tests/cli/test_cli.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires focused tests, full regression, compileall success, and clean diff check.

## 7. Explicit non-scope

X0-004 does not:

- start a persistent daemon;
- schedule itself from HTTP;
- invent live provider jobs;
- parse provider cursors/checkpoints;
- execute remote D1 work;
- bypass adapter-specific retry/partial-state contracts;
- change Worker runtime or mode.

## 8. Next action after acceptance

```text
X0-004 Accepted
  -> X0-005 end-to-end fixture test
```

`L1-006` remains a separately Ready read-only API extension. `L1-003` / `SMOKE-007` remains separately gated.
