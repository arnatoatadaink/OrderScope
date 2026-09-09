# OrderScope — Local Corporate Intelligence Progress Tracker

Status: **Active integrated runtime tracker**
Date: 2026-09-10
Scope: Local Corporate Intelligence / X0 integration

This file is the sole integrated authority for Local Corporate Intelligence runtime progress after the 2026-09-05 consolidation. Detailed implementation notes remain in task-specific handoffs.

## 1. Working rules

- `Accepted` means the implementation has passed its explicitly required local acceptance evidence.
- `Provisional result` means Web-side implementation/documentation is complete but required local/operator acceptance is still pending.
- `Ready` means prerequisites are satisfied and the task can be started without another dependency decision.
- `Blocked` means an external approval, dependency, or explicitly gated task must complete first.
- Real D1 work remains separate from fixture-path development unless an approved change window explicitly opens it.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 2. Local foundation / ingestion state

| Task | Status | Reason / next action |
|---|---|---|
| L0-001 | Accepted / inherited prerequisite | Reference only |
| L0-002 | Accepted | Scaffold/Git boundary complete |
| L0-003 | Accepted | focused 9; full 441; compileall success; diff clean |
| L0-004 | Accepted | focused 11; full 418; diff clean; upstream deprecation warnings non-blocking |
| L0-005 | Accepted | focused 7; full 352; compileall success; diff clean |
| L0-006 | Accepted | focused 6; full 447; compileall success; diff clean |
| L1-001 | Accepted | focused 8; full 360; diff clean |
| L1-002 | Accepted | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-003 | Blocked | Requires separately approved `SMOKE-007` remote D1 window |
| L1-004 | Accepted — fixture path | focused 11; full 372; diff clean |
| L1-005 | Accepted — fixture path | focused 12; full 391; diff clean |
| L1-006 | Ready | L0-004 and L1-005 are Accepted; separate import/dataset API task remains |

## 3. X0 runtime state

| Task | Status | Reason / next action |
|---|---|---|
| X0-001 | Accepted | focused 7; full 398; diff clean |
| X0-002 | Accepted | focused 9; full 407; diff clean |
| X0-003 | Accepted | focused 14; full 432; compileall success; diff clean |
| X0-004 | Accepted | focused 16; full 457; compileall success; diff clean |
| X0-005 | Accepted | focused 4; full 461; compileall success; diff clean |
| X0-006 | Provisional result | Canary operations runbook drafted; operator review/acceptance pending |

Real D1 promotion remains separately gated by L1-003 and must not be conflated with fixture-path X0 development.

## 4. Current X0-005 acceptance boundary

`analysis/tests/integration/test_end_to_end_fixture.py` replays one bounded fixture across the accepted integration path.

Local acceptance evidence:

```text
focused X0-005 tests -> 4 passed
full pytest suite    -> 461 passed
compileall           -> success / no errors
git diff --check     -> clean / no findings
```

X0-005 is Accepted.

## 5. Current X0-006 documentation boundary

`docs/work-management/local-corporate-intelligence/X0-006_CANARY_OPERATIONS_RUNBOOK_2026-09-10.md` documents the v0.1 Canary operating boundary.

Covered topics:

- local credential and non-secret configuration handling;
- provider rate/access-condition verification and runtime response;
- localhost API and manual scheduler startup;
- normal stop, interrupted-run recovery, lock handling, and job-boundary resume;
- bounded/idempotent reprocessing rules;
- temporary-news retention/deletion and expiry incidents;
- WSL-native backup/restore procedure;
- incident decision table and pre/post-run checklists.

Explicit exclusions remain preserved: no remote D1 action outside L1-003/SMOKE-007, no Worker mutation, no HTTP mutation/job start, no external API bind, and no unreviewed live-provider job registration.

X0-006 is Provisional until the operator accepts the runbook as the Canary procedure.

## 6. Primary integration path

```text
X0-005 Accepted
  -> X0-006 operator review / acceptance
```

After X0-006 acceptance, the X0-001..006 fixture-path integration lane is complete. This does not complete separately gated real-D1, L1-006, N1-006, A0, or Worker work.

## 7. Parallel/deferred lanes

- `X0-006` operator review is the current primary X0 gate.
- `L1-006` is Ready as a separate read-only API extension.
- `L1-003` remains externally Blocked.
- `N1-006` remains important for News quality but is not an X0 runbook blocker.
- `A0-001` remains Provisional and `A0-002` remains separate validation work.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 8. Current restart rule

1. Review `X0-006_CANARY_OPERATIONS_RUNBOOK_2026-09-10.md`.
2. If the runbook matches the intended Canary operating procedure, promote X0-006 to Accepted.
3. After X0-006 acceptance, treat X0-001..006 fixture-path integration as complete.
4. Choose the next separate lane explicitly: `L1-006`, `L1-003/SMOKE-007`, `N1-006`, or the A0 validation backlog.
5. Do not implicitly open a real-D1 or Worker change window.

## 9. Latest acceptance evidence

| Task | Evidence |
|---|---|
| L0-003 | focused 9; full 441; compileall success; diff clean |
| L0-004 | focused 11; full 418; diff clean; dependency deprecation warnings non-blocking |
| L0-005 | focused 7; full 352; compileall success; diff clean |
| L0-006 | focused 6; full 447; compileall success; diff clean |
| L1-001 | focused 8; full 360; diff clean |
| L1-002 | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-004 fixture | focused 11; full 372; diff clean |
| L1-005 fixture | focused 12; full 391; diff clean |
| X0-001 | focused 7; full 398; diff clean |
| X0-002 | focused 9; full 407; diff clean |
| X0-003 | focused 14; full 432; compileall success; diff clean |
| X0-004 | focused 16; full 457; compileall success; diff clean |
| X0-005 | focused 4; full 461; compileall success; diff clean |

## 10. Unresolved items

- `X0-006` operator acceptance of the Canary operations runbook.
- `L1-003` / `SMOKE-007` real-D1 approval window.
- `L1-006` read-only import/dataset API remains Ready.
- `N1-006` News quality work.
- `A0-001` provisional validation.
- A0-002 AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.
- FastAPI/Starlette/AnyIO test-client deprecation warnings should be handled in dependency maintenance.

## 11. Progress-update rule

When a task changes state, update this integrated tracker in the same bounded work cycle and preserve task-specific acceptance evidence in the corresponding handoff/runbook when one exists.
