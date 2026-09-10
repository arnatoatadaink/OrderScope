# OrderScope — W1-001 Stage B Blocker Report

Status: **Blocked — Market Bars D1 query shape exceeds shared invocation budget**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Stage: B preflight

## 1. Result

Stage B is correctly classified as **Blocked**.

The News path is within its bounded design envelope, but the existing Market Bars persistence path exceeds the OrderScope Stage-B combined D1 query ceiling before News is added.

Measured local evidence reported for the bounded Stage-B implementation:

```text
focused tests                         18/18 pass
full tests                            112/112 pass
typecheck                             pass
dry-run/build                         pass
diff check                            pass
configured News cadence               5 min
configured News overlap               15 min
configured max pages/symbol           2
configured provider page limit        50
configured max raw observations/run   200
normal market external subrequests    1
normal News external subrequests      2
normal combined external subrequests  3
worst market external subrequests     10 page cap
worst News external subrequests       <= 4 without retries
worst combined external subrequests   40 hard OrderScope ceiling
normal News D1 queries                9 for two non-empty pages
worst News D1 queries                 15 for four non-empty pages
worst Market D1 queries               >= 300 for configured 100-bar fixture
worst combined D1 queries             >= 315
News-disabled provider calls          0
News-disabled News mutations          0
dry-run mutations                     0
body scan                             clean
secret/log scan                       clean
remote D1 applied                     no
Worker deployed                       no
Cron changed                          no
Worker mode changed                   no
```

The implementation changes are currently local and uncommitted. This report does not claim review of the uncommitted code diff; it records the returned acceptance evidence and the resulting planning decision.

## 2. Root cause

The existing Market execution path accepts bars one at a time:

```text
executeAcquisitionJob()
  -> for each provider bar
     -> normalizeMarketBar(...)
     -> await bars.accept(...)
```

The existing `D1NormalizedBarStore.accept()` then performs multiple D1 statements per observation to preserve:

- idempotency receipt reservation/read;
- canonical bar insert/read;
- conflict recording when needed;
- acceptance receipt completion/read.

This is semantically safe for the previously accepted Market fixture boundary, but it is not compatible with the shared Free-plan per-invocation query budget at the configured `maxBarsPerJob = 100` scale.

The blocker is therefore **not a News correctness failure**. It is a newly exposed shared-runtime scalability constraint in the pre-existing Market persistence shape.

## 3. Why the stop was correct

The Stage-B design explicitly prohibited solving the budget problem by weakening Market guarantees.

Do not solve this blocker by:

- reducing Market correctness/idempotency/conflict detection;
- silently lowering Market coverage guarantees only to make News fit;
- treating News as successful while Market consumes an unbounded D1 share;
- raising the OrderScope 40-query engineering ceiling without a reviewed design decision;
- assuming `db.batch()` automatically makes hundreds of SQL statements count as one D1 query;
- deploying to remote D1 to discover the answer experimentally.

## 4. Cloudflare D1 design fact relevant to remediation

D1 supports SQLite JSON functions including `json_each()`. A Worker may bind one JSON array parameter and expand it into rows inside SQL. Cloudflare documents this pattern as a way to reduce application/database round trips.

This enables a stronger remediation direction than merely wrapping per-bar statements in `db.batch()`:

```text
many normalized bar observations
  -> bounded JSON payload
  -> one/few set-based SQL statements using json_each(?)
  -> deterministic per-observation result reconstruction
```

Any implementation must still respect D1's per-query SQL/row/parameter constraints and preserve the accepted Market semantics.

## 5. Decision

Create a prerequisite remediation task:

```text
W1-002 — Batch Market Bar D1 persistence for shared invocation budget
```

`W1-001 Stage B` remains Blocked until W1-002 demonstrates a bounded Market query shape that leaves room for News without weakening Market guarantees.

Dependency sequence:

```text
W1-001 Stage A Accepted
  -> W1-001 Stage B Blocked on Market D1 query shape
  -> W1-002 Market D1 persistence remediation
  -> re-run W1-001 Stage B combined-budget fixtures
  -> only then consider live AMD/NVDA Canary change window
```

## 6. W1-002 acceptance target

The goal is not a specific SQL implementation. The required observable result is:

1. Market idempotency semantics unchanged;
2. identical duplicate observation remains `MATCHED`;
3. semantic conflict remains `CONFLICT` and retains observed conflict evidence;
4. rejected normalization remains recorded;
5. accepted-bar provenance/receipt remains traceable;
6. checkpoint behavior remains unchanged;
7. 100-bar reviewed fixture no longer implies hundreds of D1 queries;
8. combined Market + News worst reviewed fixture remains below the OrderScope 40-query ceiling;
9. no remote D1 mutation is needed for acceptance;
10. existing Market regression suite remains green.

## 7. Stage-B state preserved

The following News-side work should be preserved while W1-002 is implemented:

- 5-minute configurable cadence;
- 15-minute overlap;
- 2 pages/symbol;
- provider page limit 50;
- max raw observations/run 200;
- page-cap partial checkpoint behavior;
- external-budget partial behavior;
- News D1-budget protection;
- 429/500 retryable checkpoint behavior;
- page-token loop fail-closed;
- cross-symbol identity merge;
- News-disabled regression;
- metadata-only body boundary;
- secret/log boundary.

Do not discard or broaden this accepted/preflight-compatible News design merely because the shared Market persistence layer needs remediation.

## 8. Live boundary

This blocker report authorizes no live action.

Still prohibited:

```text
remote D1 migration/application
Worker deployment
Cron registration/change
Worker Shadow -> live
historical catch-up
full-Universe News activation
```
