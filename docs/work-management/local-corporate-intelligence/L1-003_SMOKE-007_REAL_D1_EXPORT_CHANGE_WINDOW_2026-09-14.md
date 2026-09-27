# OrderScope — L1-003 / SMOKE-007 Real D1 Export Change Window

Status: **READY FOR EXPLICIT WINDOW AUTHORIZATION — do not execute remote mutation from this document alone**
Date: 2026-09-14 JST
Branch: `docs/mermaid-conventions-v0.1`
Task: `L1-003 — Define real D1 export validation window`
Acceptance ID: `SMOKE-007`
Environment: `live-canary`

## 1. Objective

Complete the remaining L1-003 real-D1 acceptance boundary with one bounded, reviewed:

```text
pause -> export -> local custody/quality -> resume -> catch-up
```

cycle.

This is distinct from the already accepted R0-007 first bounded remote custody evidence and R0-008 first remote ACK evidence. Those prove bounded custody/lifecycle behavior; L1-003 specifically requires the operational pause/resume and fresh post-resume catch-up path.

## 2. Current prerequisites

Treat the following as established prerequisites:

- `L1-001` and `L1-002` Accepted;
- local/fixture export and custody paths Accepted;
- first bounded R0-007 remote custody evidence Accepted;
- first R0-008 custody ACK evidence Accepted;
- W1-001 confirmation/closeout Accepted on 2026-09-14;
- Cloudflare control path succeeded before/during/after that window with no recurring `7403`;
- final Worker baseline is Shadow with News disabled;
- migration `0008_scheduler_run_evidence.sql` is already applied/verified on `live-canary`;
- scheduler-evidence feature activation remains separately gated.

This document does not reopen W1-001 and does not authorize any purge.

## 3. Frozen scope

The authorized L1-003 window, when explicitly opened, must freeze all of the following before mutation:

```text
environment: live-canary
source DB: orderscope-state-live-canary
source table/window: explicit historical bounded range only
window semantics: [startInclusive, endExclusive)
Worker baseline before/after: shadow unless a separately reviewed resume step requires bounded live acquisition
News: disabled
Universe: canary-v0.1
Cron: unchanged
D1 schema: unchanged
scheduler-evidence activation: unchanged / disabled unless separately authorized
purge: forbidden in this window
```

Do not include current checkpoint/cursor/lease/schema truth as historical drain candidates.

## 4. Phase A — pre-window and bounded export/custody

Phase A may be prepared while markets are closed, but remote execution still requires explicit authorization.

Before remote mutation/export:

1. synchronize the reviewed branch and require a clean working tree;
2. record release commit and current Worker deployment/version;
3. verify `/health` reports the safe baseline;
4. verify Cloudflare identity and D1 binding;
5. verify `SELECT 1 AS control_path_ok` succeeds;
6. freeze the exact source table and half-open UTC time window;
7. record expected exclusion of control-state tables/rows;
8. record the pause mechanism and rollback/resume mechanism before invoking either.

The first L1-003 window should remain intentionally small. Reuse an already reviewed historical interval where practical rather than broadening scope.

Required export/custody evidence:

```text
source environment/database identity
source table
window start inclusive UTC
window end exclusive UTC
row count
artifact byte size
artifact SHA-256 / deterministic digest
custody manifest identity
local immutable destination
quality-check result
```

Local custody/quality must not become acquisition checkpoint truth. The remote source checkpoint remains authoritative for coverage.

## 5. Pause boundary

The pause must be explicit, bounded, reversible, and observable.

Before pausing, capture:

```text
pause start UTC/JST
current source checkpoint / complete-through state
current Worker mode
current News state
current deployment version
control_path_ok
```

Do not change Cron, Universe, News cadence, budgets, provider, schema, or symbol scope to implement the pause.

If the reviewed implementation cannot pause acquisition without an unreviewed config/code delta, stop with `BLOCKED` rather than improvising.

## 6. Export while paused

During the paused interval:

- export only the frozen table/window;
- preserve deterministic ordering/serialization required by the accepted export contract;
- record row count/hash/byte size;
- import/register local immutable custody;
- run accepted local quality validation;
- do not delete source rows;
- do not advance or reconstruct remote checkpoints from the local artifact;
- do not perform remote purge/`PURGED` transition.

If source rows change unexpectedly inside the frozen window or deterministic digest verification fails, stop and retain all source data.

## 7. Phase B — resume and fresh catch-up

This phase is the market-day acceptance portion of `SMOKE-007`.

Resume only through the reviewed normal acquisition path. Do not use manual checkpoint advancement.

Record immediately before resume:

```text
pause end / resume UTC/JST
pre-resume source checkpoint
bounded gap created by pause
control_path_ok
```

After resume, capture fresh operational evidence that the accepted acquisition path catches up the bounded gap.

Required evidence where applicable:

```text
scheduled timestamp(s)
source/session identity
planned / selected / completed / failed jobs
requested range(s)
accepted bars/records
partial/missing/conflict/rejected counts
checkpoint before
checkpoint after
complete_through before
complete_through after
external subrequests / ceiling
D1 queries / ceiling
withinBudget
Worker outcome / exception / resource indicator
```

Acceptance requires that the resume/catch-up path closes the intended bounded gap without false checkpoint advancement.

Historical replay alone is not a substitute for this fresh post-resume evidence.

## 8. Acceptance criteria

`SMOKE-007` is Accepted only when all applicable criteria pass:

1. The exact pause interval and frozen export range are recorded.
2. The bounded export is deterministic and quality-accepted locally.
3. Remote source data is not purged during this window.
4. Remote checkpoint/control truth is not replaced by local custody state.
5. Resume uses the reviewed acquisition path with no unreviewed configuration change.
6. Fresh post-resume catch-up processes the bounded gap.
7. No false checkpoint or `complete_through` advance occurs on missing/partial/failure paths.
8. Shared external/D1 ceilings remain respected.
9. Cloudflare control-path read succeeds before, during where safe, and after the window.
10. No credential/body leakage or destructive schema/data mutation occurs.
11. The final runtime returns to the reviewed safe baseline required by the window.

## 9. Hard-stop conditions

Stop and return to the safest available baseline if any of the following occurs:

- `7403`, auth loss, quota error, or persistent control-path stall;
- D1 binding/database mismatch;
- unexpected source-window mutation that invalidates the frozen digest;
- export hash/row-count verification failure;
- catch-up attempts to cross external or D1 ceilings;
- false checkpoint/coverage advancement;
- Worker repeated exception or resource failure;
- unexpected destructive D1 mutation;
- need to change Cron/Universe/cadence/budget/schema to continue;
- inability to restore/resume the reviewed acquisition path.

Do not troubleshoot by widening the window or adding a purge.

## 10. Explicit exclusions

This window does **not** authorize:

- actual D1 purge or `PURGED` transition;
- remote restore;
- destructive migration;
- new migration application;
- scheduler-evidence activation;
- continuous Worker Live mode;
- `full-v0.1` activation;
- Cron change;
- News activation or News body persistence;
- provider/page-limit/budget expansion;
- export of current control truth as purge candidates.

## 11. Final disposition

Choose exactly one:

```text
ACCEPTED
  = one bounded pause -> export -> resume -> fresh catch-up cycle passes all applicable criteria.

INCONCLUSIVE
  = no hard failure, but fresh catch-up/session evidence is insufficient.

ROLLED_BACK
  = a hard-stop condition occurs and the safe runtime state is restored.

BLOCKED
  = a new reviewed code/config/schema/authorization change is required.
```

## 12. Required return report

Create a dated L1-003 / SMOKE-007 execution report containing at least:

```text
release commit:
pre-window Worker version:
final Worker version:
window start/end UTC/JST:
source DB:
source table:
export start inclusive:
export end exclusive:
pause start:
resume time:
source row count:
artifact bytes:
artifact SHA-256:
custody manifest:
quality result:
checkpoint before pause:
checkpoint before resume:
checkpoint after catch-up:
complete_through before:
complete_through after:
catch-up jobs planned/completed/failed:
partial/missing/conflict/rejected:
max external/tick:
max D1/tick:
control-path before/during/after:
7403 observed: yes/no
false coverage advance observed: yes/no
CPU/resource failure observed: yes/no
remote purge performed: no
schema mutation performed: no
secret/body leakage observed: no
final Worker mode:
final News state:
final disposition:
reason:
```

Update the integrated Progress Tracker only after the execution result is known.

## 13. Authorization boundary

This runbook is preparation only. The operator must receive a separate explicit authorization naming `L1-003 / SMOKE-007` before performing the remote pause/export/resume portion.

Until then, only read-only preflight and local preparation are permitted.
