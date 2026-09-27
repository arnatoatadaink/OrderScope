# OrderScope — W1-003 Local Implementation Handoff

Status: **Ready for Local / non-live**
Date: 2026-09-10
Task: `W1-003 — Bulk Coverage Checkpoint Reads and Shared D1 Budget Instrumentation`
Parent blocker: `W1-001_STAGE_B_TIERED_UNIVERSE_BLOCKER_REPORT_2026-09-10.md`
Reference authority: `stock_monitoring_v0.1_universe_spec.md`
Universe authority: `25 / 28 / 53 = 106`

## 1. Purpose

Remove the T7 blocker where full-v0.1 performs 106 point-read checkpoint queries before acquisition starts, and make Market + Prediction + News D1 query use observable and enforceable through the shared `InvocationBudget`.

Current evidence:

```text
full-v0.1 instruments               106
current bootstrap point reads       106
shared D1 engineering ceiling        40
pre-acquisition excess               66
```

This task is non-live. Do not deploy Worker, change Cron, mutate remote D1, or change Worker mode.

## 2. Required design

### 2.1 Add set-oriented checkpoint read

Extend `CoverageCheckpointPort` with a bulk read operation, for example:

```ts
getMany(coverageKeys: readonly string[]): Promise<readonly StoredCoverageCheckpoint[]>;
```

Exact naming may differ if a cleaner interface exists.

Production D1 implementation should resolve a bounded list of coverage keys with one set-oriented query where practical. Preferred forms include bound JSON + `json_each(?)` or an equivalent bounded set query. Do not replace 106 point reads with 106 statements inside `db.batch()` and call that solved.

Requirements:
- empty input performs zero D1 reads;
- duplicate requested keys do not multiply returned checkpoints;
- returned rows remain validated through the existing checkpoint row parser;
- missing keys remain absent rather than synthesized;
- corrupt rows still fail closed;
- deterministic behavior independent of SQL row order;
- input size is bounded by the reviewed Universe/profile size.

### 2.2 Use bulk read in all relevant bootstrap paths

At minimum review and repair:
- full Market Universe bootstrap in `runScheduledTick()` / `loadMarketCheckpoints()`;
- prediction Premarket checkpoint bootstrap;
- any equivalent pre-planning fan-out introduced by the same orchestration path.

Do not weaken planner semantics or omit checkpoint state merely to reduce queries.

### 2.3 Shared D1 budget instrumentation

The shared `InvocationBudget` must cover actual D1 statements in the scheduled invocation, not just News estimates.

Instrument or wrap the relevant D1 ports so the final digest can publish concrete values for:

```text
marketD1Queries
predictionD1Queries (if separately useful)
newsD1Queries
totalD1Queries
```

The exact category decomposition may differ, but `totalD1Queries` must be concrete and enforceable.

At minimum include actual statements for:
- Market checkpoint bulk read;
- Prediction checkpoint bulk read when enabled;
- lease acquire/release;
- stale-attempt operations;
- attempt record/update;
- Market bar persistence;
- Market checkpoint CAS/read used during execution;
- News checkpoint/store operations;
- digest persistence if inside the same protected invocation accounting model.

If some D1 statements are intentionally outside the engineering budget boundary, document and justify that boundary explicitly rather than leaving them uncounted.

## 3. Engineering targets

Hard acceptance target for reviewed Stage B fixture:

```text
combined D1 queries/tick < 40 preferred
combined D1 queries/tick <= 40 absolute engineering ceiling
```

Checkpoint bootstrap target:

```text
full-v0.1 106-key Market checkpoint bootstrap <= 2 D1 statements
prediction checkpoint bootstrap             <= 2 D1 statements
```

Prefer 1 each where safe.

Existing W1-002 evidence to preserve:

```text
100-bar Market persistence = 7 D1 statements
```

Do not regress this bound.

## 4. Required tests

Add focused tests that cover at least:

1. 106 unique full-v0.1 coverage keys -> bounded bulk read query count.
2. Missing checkpoint keys are omitted correctly.
3. Duplicate requested keys do not duplicate results.
4. Corrupt checkpoint row still fails closed.
5. Market planner receives semantically identical checkpoint set vs prior point-read implementation.
6. Prediction Premarket bootstrap uses bounded bulk read.
7. 100-bar persistence remains 7 statements.
8. Combined Market + News Stage-B fixture reports concrete `totalD1Queries`.
9. Combined fixture remains within the 40-query ceiling.
10. Budget exhaustion fails closed before issuing an over-ceiling D1 statement.
11. News-disabled regression remains clean.
12. Shadow/dry-run behavior remains non-mutating.

## 5. Return report

Return all of the following explicitly:

```text
W1-003 status:
full-v0.1 Market checkpoint keys:
Market checkpoint bootstrap D1 queries:
prediction checkpoint keys:
prediction checkpoint bootstrap D1 queries:
100-bar Market persistence D1 queries:
normal combined D1 queries/tick:
worst reviewed combined D1 queries/tick:
normal combined external subrequests/tick:
worst reviewed combined external subrequests/tick:
marketD1Queries digest value:
newsD1Queries digest value:
totalD1Queries digest value:
budget exhaustion fixture:
planner semantic regression:
checkpoint corruption fail-closed fixture:
focused tests:
full tests:
typecheck:
wrangler dry-run/build:
git diff --check:
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

## 6. Stop conditions

Stop and report Blocked if any of the following occurs:

- 106-key Market bootstrap cannot be safely bounded below the shared D1 ceiling;
- bulk read changes planner/checkpoint semantics;
- Prediction path still fan-outs one D1 read per instrument;
- combined D1 accounting remains partially null/estimated;
- combined reviewed invocation exceeds 40 D1 statements;
- W1-002 100-bar persistence regresses materially above 7 statements without a reviewed reason;
- fixing the issue requires remote D1 mutation, live Worker deployment, Cron change, or Worker mode change.

## 7. Dependency sequence

```text
W1-002 Accepted
  -> W1-001 Stage B T7 Blocked (106 checkpoint point reads)
  -> W1-003 bulk checkpoint read + shared D1 instrumentation
  -> rerun tiered-universe Stage B budget/write/backlog fixtures
  -> Stage B acceptance review
  -> only then explicit live Canary change-window review
```
