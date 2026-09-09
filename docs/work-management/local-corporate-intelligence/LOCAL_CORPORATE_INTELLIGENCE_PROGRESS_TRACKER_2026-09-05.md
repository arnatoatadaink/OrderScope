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
| L1-006 | Accepted — fixture path | focused command 21; full 468; compileall success; diff clean |

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

## 4. Completed fixture-path boundaries

`X0-001..006` is complete for the fixture-path integration boundary.

`L1-006` is Accepted for the fixture-path market read API boundary.

L1-006 acceptance evidence:

```text
focused API command -> 21 passed
full pytest suite   -> 468 passed
compileall          -> success / no errors
git diff --check    -> clean / no findings
```

This does not complete `L1-003` real-D1 export.

## 5. Current N1-006 evaluation boundary

`N1-006 — Evaluate news recall` is the selected current non-gated WBS lane.

Dependencies are satisfied:

- `E0-007` Accepted;
- `N1-005` Accepted.

### Evaluator framework — Accepted

Measured acceptance evidence:

```text
focused evaluator tests -> 7 passed
full pytest suite        -> 475 passed
compileall               -> success / no errors
git diff --check         -> clean / no findings
```

### Benchmark manifest/report CLI — Accepted

Implemented metadata-only benchmark loading/reporting and:

```text
quality news-recall --benchmark <json>
```

Measured acceptance evidence:

```text
focused benchmark/CLI command -> 15 passed
full pytest suite              -> 482 passed
compileall                     -> success / no errors
git diff --check               -> clean / no findings
```

### Official 30-day reference seed — Complete

Added:

`N1-006_REFERENCE_SEED_2026-08-11_2026-09-10.md`

Reference window:

```text
2026-08-11T00:00:00Z <= timestamp < 2026-09-10T00:00:00Z
```

Seeded real SEC events:

- AMD financing — SEC available 2026-08-17T16:05:40Z;
- NVIDIA / SB Energy partnership — 2026-08-17T08:41:33Z;
- AMD board/leadership change — 2026-08-19T16:16:56Z;
- NVIDIA Q2 FY2027 earnings — 2026-08-26T16:21:19Z.

The seed is not evaluated as zero recall before News population.

### News candidate population — Provisional result

Added:

- concrete Alpaca News HTTP transport (`include_content=false` only);
- retrospective AMD/NVDA metadata candidate collector;
- candidate JSON writer constrained beneath `ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/`;
- `quality news-recall-candidates` manual CLI;
- 6 focused tests.

Retrospective timestamp rule:

- SEC/IR reference side uses accepted `available_at`;
- News side uses Alpaca article `created_at` normalized as provider `published_at`;
- this measures provider News availability lag, not reconstructed historical local scheduler latency.

Current transition:

```text
N1-006 evaluator              Accepted
N1-006 benchmark path         Accepted
30-day official reference     Complete
News population implementation Provisional
  -> local verification
  -> execute 30-day Alpaca metadata fetch
  -> explicit article/reference labeling
  -> final benchmark execution
  -> N1-006 Accepted
```

Synthetic fixture metrics must never substitute for final measured benchmark values.

## 6. Post-X0 operational follow-ups

The following `PX0-*` IDs remain non-normative tracking IDs defined in `POST_X0_OPERATIONAL_FOLLOWUPS_2026-09-10.md`:

| Follow-up | Status | Boundary |
|---|---|---|
| PX0-001 | Not started | Reviewed operational scheduler job registration |
| PX0-002 | Not started | Durable scheduler run/job evidence and stale-lock recovery |
| PX0-003 | Not started | Operator CLI for retention and bounded reprocessing |
| PX0-004 | Not started | Reproducible backup/restore and restore drills |

## 7. Parallel/deferred lanes

- `N1-006` candidate-population verification/execution is the current selected lane.
- `L1-003` remains externally Blocked behind `SMOKE-007` approval.
- `PX0-001..004` remain explicit post-X0 operational/recovery follow-ups.
- `A0-001` remains Provisional and `A0-002` remains separate validation work.
- WBS-unreflected task ideas are tracked in `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 8. Current restart rule

1. Treat L1-006 as Accepted with measured 21 / 468 / compileall / diff evidence.
2. Treat N1-006 evaluator as Accepted with measured 7 / 475 / compileall / diff evidence.
3. Treat N1-006 benchmark manifest/report path as Accepted with measured 15 / 482 / compileall / diff evidence.
4. Run the new candidate-population focused tests, full pytest, compileall, and diff check.
5. If clean, perform the bounded 30-day Alpaca metadata-only acquisition using local credentials.
6. Explicitly label candidate articles to the four reference IDs; do not infer matches from headline similarity.
7. Execute `quality news-recall` on the final labeled JSON and record measured recall/lag/misattribution/unresolved values.
8. Keep `L1-003/SMOKE-007`, Worker changes, and live scheduler registration separately gated.

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
| L1-006 fixture | focused command 21; full 468; compileall success; diff clean |
| N1-006 evaluator | focused 7; full 475; compileall success; diff clean |
| N1-006 benchmark path | focused command 15; full 482; compileall success; diff clean |
| X0-001 | focused 7; full 398; diff clean |
| X0-002 | focused 9; full 407; diff clean |
| X0-003 | focused 14; full 432; compileall success; diff clean |
| X0-004 | focused 16; full 457; compileall success; diff clean |
| X0-005 | focused 4; full 461; compileall success; diff clean |
| X0-006 | operator/external review accepted for policy-level fixture path; F1-F4 explicitly deferred to PX0-001..004 |

## 10. Unresolved items

- `N1-006` News candidate population local acceptance evidence.
- `N1-006` actual 30-day Alpaca metadata candidate acquisition.
- `N1-006` explicit candidate/reference labeling and final measured report.
- `PX0-001` operational scheduler job registry.
- `PX0-002` durable scheduler run evidence / stale-lock recovery.
- `PX0-003` retention/reprocessing operator CLI.
- `PX0-004` reproducible backup/restore and restore drills.
- `L1-003` / `SMOKE-007` real-D1 approval window.
- `A0-001` provisional validation.
- `A0-002` AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.
- FastAPI/Starlette/AnyIO test-client deprecation warnings should be handled in dependency maintenance.

## 11. Progress-update rule

When a task changes state, update this integrated tracker in the same bounded work cycle and preserve task-specific acceptance evidence in the corresponding handoff/runbook when one exists.
