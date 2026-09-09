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
| X0-006 | Accepted — policy-level fixture path | External review found no boundary contradiction; F1-F4 moved to explicit post-X0 follow-ups |

Real D1 promotion remains separately gated by L1-003 and must not be conflated with fixture-path X0 development.

## 4. X0 fixture-path completion

`X0-001..006` is complete for the fixture-path integration boundary.

X0-006 acceptance basis:

- external review concluded the runbook is suitable as the policy-level procedure for the current fixture-path integration boundary;
- credentials, rate limits, stop/resume, reprocessing, deletion, backup, and incident decisions are documented;
- localhost/config/scheduler/retention/Worker-D1 boundaries were found consistent;
- four production-operations gaps are explicitly tracked rather than hidden inside X0-006.

Acceptance does **not** mean production recovery is complete and does not authorize remote D1, Worker mutation, or live-provider registration.

Review authority:

`X0-006_CANARY_OPERATIONS_RUNBOOK_REVIEW_2026-09-10.md`

## 5. Post-X0 operational follow-ups

The 2026-09-03 WBS contains adjacent contracts but no task whose completion condition fully covers the four review findings. Until the next WBS revision, the following `PX0-*` IDs are non-normative tracking IDs defined in `POST_X0_OPERATIONAL_FOLLOWUPS_2026-09-10.md`.

| Follow-up | Status | Boundary |
|---|---|---|
| PX0-001 | Not started | Reviewed operational scheduler job registration; zero-job success must not imply workload completion |
| PX0-002 | Not started | Durable scheduler run/job evidence and reproducible stale-lock recovery; do not redefine I0-003 provider checkpoints |
| PX0-003 | Not started | Operator CLI for retention backlog/overdue/delete-retry and bounded reprocessing; preserve accepted N1-005 semantics |
| PX0-004 | Not started | Reproducible backup/restore implementation, validation evidence, RPO/generations, and restore drills |

Interim limitations:

- scheduler may select zero built-in jobs;
- stale-lock clearance/resume requires manual engineering review until PX0-002;
- retention/reprocessing operator checks remain fixture/programmatic until PX0-003;
- backup/restore remains policy-level until PX0-004.

## 6. Primary integration path

The original X0 primary path is complete:

```text
X0-001 -> X0-002 -> X0-003 -> X0-004 -> X0-005 -> X0-006
                                                       Accepted
```

The next separate implementation lane remains `L1-006 — read-only import/dataset API` unless a different explicitly gated lane is selected.

## 7. Parallel/deferred lanes

- `L1-006` is Ready as a separate read-only API extension.
- `PX0-001..004` are explicit post-X0 operational/recovery follow-ups and do not reopen X0 acceptance.
- `L1-003` remains externally Blocked behind `SMOKE-007` approval.
- `N1-006` remains important for News quality.
- `A0-001` remains Provisional and `A0-002` remains separate validation work.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 8. Current restart rule

1. Treat `X0-001..006` fixture-path integration as Accepted/complete.
2. Continue with `L1-006 — read-only import/dataset API` as the next Ready implementation lane unless priorities are explicitly changed.
3. Preserve `PX0-001..004` for future operations/recovery implementation and incorporate/remap them in the next WBS revision.
4. Keep `L1-003/SMOKE-007` real-D1 work separately gated.
5. Do not implicitly open a Worker change window or register live provider jobs.

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
| X0-006 | operator/external review accepted for policy-level fixture path; F1-F4 explicitly deferred to PX0-001..004 |

## 10. Unresolved items

- `PX0-001` operational scheduler job registry.
- `PX0-002` durable scheduler run evidence / stale-lock recovery.
- `PX0-003` retention/reprocessing operator CLI.
- `PX0-004` reproducible backup/restore and restore drills.
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
