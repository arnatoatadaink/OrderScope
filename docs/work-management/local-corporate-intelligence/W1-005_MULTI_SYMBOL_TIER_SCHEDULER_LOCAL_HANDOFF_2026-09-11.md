# OrderScope — W1-005 Multi-Symbol Tier Scheduler Local Handoff

Status: **Ready for Local / non-live implementation**
Date: 2026-09-11
Task: `W1-005 — Batch tiered Market acquisition by provider/cadence/range while preserving per-symbol coverage semantics`
Depends on: `W1-003 Accepted`, `W1-004 Blocked`
Reference authority: `stock_monitoring_v0.1_universe_spec.md`

## 1. Why this task exists

W1-004 proved that the unchanged `ACQUISITION_MAX_JOBS_PER_TICK=1` scheduler is not sustainable for `full-v0.1`: Tier A reached 69 minutes maximum backlog age and nine 1Min jobs remained outstanding 30 minutes after a normal close.

Do not solve this by simply increasing `ACQUISITION_MAX_JOBS_PER_TICK` until the fixture passes. The current planner emits one Market job per instrument. During the regular session the authoritative Tier A contains 24 equities plus BTCUSD at 1Min cadence, so a one-symbol-per-job design requires roughly 25 due instrument-jobs per minute before Tier B, Tier C, News, retry, or catch-up work. That shape is incompatible with the reviewed shared D1/external budget unless the acquisition unit itself is batched.

Alpaca's historical stock-bars endpoint supports a comma-separated symbol list for one request. Crypto historical bars also supports a list of symbols. W1-005 therefore changes the local scheduling/acquisition unit from one-symbol job to a bounded multi-symbol job when provider route, cadence, session scope, logical variant, and requested range are compatible.

This is a local/fixture authorization only. It does not authorize Worker deployment, remote D1, Cron modification, Worker mode change, full-v0.1 live activation, or News live activation.

## 2. Frozen design direction

### 2.1 Grouping key

A Market batch may contain multiple instruments only when all of the following are identical:

- provider route;
- cadence;
- session scope;
- logical data variant/feed;
- acquisition mode;
- requested range start/end;
- calendar revision and Universe revision.

Never group jobs with different checkpoint progression windows merely to reduce request count.

### 2.2 Expected steady-state groups

For a normal equity regular-session tick, the preferred steady-state shape is approximately:

- Tier A stock 1Min: up to 24 equity symbols in one stock-bars request;
- Tier A crypto 1Min: BTCUSD in one crypto-bars request;
- Tier B stock 15Min: up to 28 equity symbols in one stock-bars request on its due boundary;
- Tier C stock 1Day: up to 52 equity symbols in one stock-bars request after daily finalization;
- Tier C crypto 1Day: ETHUSD in one crypto-bars request.

These are compatibility groups, not a mandate that every group runs every minute.

### 2.3 Provider paging

Alpaca stock-bars page limit applies to total datapoints across all requested symbols and responses are symbol-first. The implementation must therefore:

- preserve `next_page_token` handling;
- never infer that a symbol is complete merely because another symbol filled the current page;
- cap pages and total observations using reviewed acquisition limits;
- mark the affected batch partial/retryable if page or shared-budget exhaustion prevents complete traversal;
- avoid false checkpoint advancement for symbols whose requested coverage was not proven complete.

### 2.4 Per-symbol truth must remain intact

Batching HTTP work must not collapse coverage identity. Each symbol retains its own:

- coverage key;
- expected checkpoint version;
- complete-through value;
- missing ranges/blocker state;
- normalized bar identity and acceptance receipt semantics.

A batch may share one job/attempt envelope, but success/partial/conflict must be attributable per symbol where the observed data differs.

## 3. D1 requirement

Multi-symbol HTTP batching alone is insufficient if post-fetch D1 operations fan out per symbol.

Implement or reuse bounded set-oriented D1 operations for the batch path so that D1 statement count scales with pages/batches, not with `number_of_symbols × statements_per_symbol`.

At minimum review these operations:

- checkpoint bootstrap: already bulk from W1-003;
- bar persistence: W1-002 set-oriented batch semantics must accept multi-symbol rows without per-symbol statement fan-out;
- checkpoint completion/CAS: introduce a bounded batch/set-oriented equivalent or another measured shape that keeps per-symbol version semantics;
- attempt persistence: prefer one batch/job envelope unless separate per-symbol attempts are semantically required;
- lease operations: prefer batch/job-level lease identity if safe; do not silently weaken mutual exclusion;
- digest: retain measured accounting from W1-003.

Do not hide D1 work from `InvocationBudget`. Every actually issued statement remains counted exactly once.

## 4. Scheduler policy

Add a deterministic batching stage after `SchedulePolicy.plan()` and before final selection/execution, or an equivalent design with the same semantics.

Priority remains:

1. eligible missing-range repair;
2. no-checkpoint/bootstrap work;
3. forward coverage oldest-first.

Within equal due class, cadence-aware freshness may be added only as part of this reviewed local task. Recommended order for forward steady-state work:

`1Min` before `15Min` before `1Day`, while ensuring lower-frequency tiers cannot starve indefinitely.

A bounded quota/fairness rule is preferred over unconditional cadence priority. Example design target, not a required literal implementation:

- reserve capacity for due 1Min groups each tick;
- allow due 15Min group on its boundary after Tier A freshness is protected;
- allow 1Day group after daily finalization within a bounded delay;
- catch-up/reconcile work may use residual capacity and must not destroy steady-state 1Min freshness.

Do not merely increase `ACQUISITION_MAX_JOBS_PER_TICK` as the only change.

## 5. Acceptance targets

Re-run the authoritative W1-004 simulation using real production scheduling/grouping code.

Hard conditions for local acceptance:

- full-v0.1 remains `25 / 28 / 53 = 106`;
- no instrument/cadence reassignment;
- Tier A normal-session max backlog age `<= 3 minutes` as the initial engineering acceptance bound;
- Tier A outstanding 1Min jobs 30 minutes after close = `0`;
- Tier B backlog remains bounded and does not grow session-over-session; target `<= 30 minutes`;
- Tier C daily coverage completes within a reviewed same-day window; target `<= 120 minutes` after daily finalization;
- normal and worst reviewed combined external subrequests/tick `<= 40`;
- normal and worst reviewed combined D1 queries/tick `<= 40`;
- budget exhaustion rejects before issuing the crossing D1/external call;
- no false checkpoint advancement under pagination/page-cap/429/5xx/budget exhaustion;
- W1-002 INSERTED/MATCHED/CONFLICT/REJECTED semantics remain unchanged;
- W1-003 bulk checkpoint semantics remain unchanged;
- News-disabled regression remains zero News acquisition calls/mutations;
- dry-run/shadow path remains non-mutating for acquisition state.

The `<=3 minute` Tier A bound is an engineering acceptance threshold, not a claim that a 1Min source cadence guarantees one-minute end-to-end delivery. Live scheduler delay remains a later Canary measurement.

## 6. Capacity measurements to return

Return measured values for both normal 390-minute and shortened 210-minute sessions:

```text
W1-005 status: Accepted / Provisional / Blocked
batch groups emitted by cadence/provider:
normal selected groups/tick p50/p95/max:
normal Market external/tick p50/p95/max:
normal total external/tick p50/p95/max:
normal Market D1/tick p50/p95/max:
normal total D1/tick p50/p95/max:
max backlog age 1Min:
max backlog age 15Min:
max backlog age 1Day:
outstanding 1Min at close+30m:
outstanding 15Min at close+30m:
outstanding 1Day at reviewed daily deadline:
normal-day NEW bars:
normal-day MATCHED/replayed observations:
normal-day Market row writes:
normal-day News row writes:
normal-day other Worker row writes:
normal-day total D1 row writes:
shortened-day total D1 row writes:
catch-up throughput/day under steady-state freshness protection:
catch-up days required for empty 24h retention window:
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

## 7. Required fixtures

At minimum cover:

1. 24 Tier-A equities due for the same one-minute range collapse into one compatible stock batch;
2. BTCUSD remains separate from the equity stock route;
3. 28 Tier-B equities batch on a 15Min boundary;
4. Tier-C equity daily batch after finalization;
5. ETHUSD daily crypto stays route-separated;
6. differing range/mode/session/variant never batch together;
7. multi-symbol pagination where an early page contains only a subset of requested symbols does not false-complete absent symbols;
8. one symbol conflict does not overwrite another symbol's canonical bar;
9. batch checkpoint update preserves per-symbol expected-version semantics;
10. budget exhaustion midway through a multi-page batch leaves incomplete symbols partial/retryable;
11. normal full-v0.1 session meets the backlog targets;
12. shortened session meets the backlog targets;
13. empty-checkpoint catch-up is throttled behind steady-state freshness and remains convergent;
14. News combined invocation remains under both ceilings;
15. deterministic ordering/replay;
16. News-disabled, dry-run, body-storage and secret/log regressions.

## 8. Stop conditions

Stop and report rather than weakening semantics if any of the following is required:

- dropping Tier A instruments or reducing their defined source cadence;
- changing the authoritative 106-instrument Universe;
- checkpoint advancement without per-symbol proof;
- unbudgeted D1 statements or external requests;
- raising reviewed D1/external ceiling above 40;
- remote D1 mutation;
- Worker deployment;
- Cron or Worker mode change;
- News body persistence;
- treating a local fixture as equivalent to live CPU/scheduler evidence.

## 9. Stage relationship

```text
W1-003 Accepted
  -> W1-004 Blocked (one-instrument/one-job capacity)
  -> W1-005 multi-symbol tier scheduler/persistence work
  -> re-run W1-004 capacity evidence
  -> W1-001 Stage B final acceptance review
  -> explicit live Canary change-window review only after acceptance
```
