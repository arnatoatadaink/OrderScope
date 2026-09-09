# OrderScope — Local Corporate Intelligence Progress Tracker

Status: **Active integrated runtime tracker**
Date: 2026-09-09
Scope: Local Corporate Intelligence / X0 integration

This file is the sole integrated authority for Local Corporate Intelligence runtime progress after the 2026-09-05 consolidation. Detailed implementation notes remain in task-specific handoffs.

## 1. Working rules

- `Accepted` means the implementation has passed its explicitly required local acceptance evidence.
- `Provisional result` means Web-side implementation is complete but required local verification is still pending.
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
| L0-006 | Ready | L0-003/L0-004/L0-005 are Accepted; implement CLI entry point next |
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
| X0-004 | Blocked | Depends on adapter availability + L0-006 |
| X0-005 | Not started | Depends on X0-001..004 |
| X0-006 | Not started | Depends on X0-005 |

Real D1 promotion remains separately gated by L1-003 and must not be conflated with fixture-path X0 development.

## 4. Current L0-003 acceptance boundary

`analysis/app/orderscope_local/config.py` implements a non-secret local configuration model and an explicit credential-name boundary.

Local acceptance evidence:

```text
focused L0-003 tests -> 9 passed
full pytest suite    -> 441 passed
compileall           -> success / no errors
git diff --check     -> clean / no findings
```

L0-003 is Accepted.

## 5. Primary integration path

Scheduler work now proceeds through:

```text
L0-006 CLI entry point
  -> X0-004 local scheduler
```

`L1-006` is independently Ready because both L0-004 and L1-005 are Accepted; it can be implemented as a separate read-only import/dataset API cycle without blocking the scheduler path.

## 6. Parallel/deferred lanes

- `L0-006` is the next primary foundation task because all L0 prerequisites are Accepted.
- `L1-006` is Ready as a parallel read-only API extension.
- `L1-003` remains externally Blocked and does not invalidate fixture-path work.
- `N1-006` remains important for News quality but is not the current X0 integration blocker.
- `A0-001` remains Provisional and `A0-002` remains separate validation work.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 7. Current restart rule

1. Start `L0-006 — CLI entry point`.
2. After L0-006 acceptance, start `X0-004 — local scheduler`.
3. `L1-006` may proceed in a separate bounded API cycle.
4. Keep L1-003/SMOKE-007 real-D1 work separate.

## 8. Latest acceptance evidence

| Task | Evidence |
|---|---|
| L0-003 | focused 9; full 441; compileall success; diff clean |
| L0-004 | focused 11; full 418; diff clean; dependency deprecation warnings non-blocking |
| L0-005 | focused 7; full 352; compileall success; diff clean |
| L1-001 | focused 8; full 360; diff clean |
| L1-002 | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-004 fixture | focused 11; full 372; diff clean |
| L1-005 fixture | focused 12; full 391; diff clean |
| X0-001 | focused 7; full 398; diff clean |
| X0-002 | focused 9; full 407; diff clean |
| X0-003 | focused 14; full 432; compileall success; diff clean |

## 9. Unresolved items

- `L0-006` CLI entry point implementation and local acceptance remain pending.
- `L1-003` / `SMOKE-007` real-D1 approval window.
- `N1-006` News quality work.
- `A0-001` provisional validation.
- A0-002 AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.
- FastAPI/Starlette/AnyIO test-client deprecation warnings should be handled in dependency maintenance, not inside L0-004/X0-003 feature logic.

## 10. Progress-update rule

When a task changes state, update this integrated tracker in the same bounded work cycle and preserve task-specific acceptance evidence in the corresponding handoff when one exists.
