# OrderScope — W1-001 Stage B Final Budget Instrumentation Handoff

Status: **Ready for local implementation — no live activation authorized**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Predecessor: `W1-002` Accepted

## Purpose

Close the remaining W1-001 Stage-B preflight gap by measuring and enforcing Market + News D1 use through one shared invocation budget.

The original Market persistence blocker is resolved: the synchronized 100-bar fixture persists through 7 D1 statements while preserving acceptance semantics.

The remaining issue is observability/enforcement integration. `worker.ts` still emits `marketD1Queries: null` and `totalD1Queries: null` while News D1 operations consume `InvocationBudget` directly.

## Required implementation

### 1. One shared D1 budget for scheduled invocation

Create the `InvocationBudget` before any live scheduled Market/News D1 work that belongs to the guarded acquisition path.

Market acquisition must consume the same D1 budget used by News.

At minimum account for:

```text
Market bar batch persistence statements
Market checkpoint get / compare-and-set / attempt writes that occur within acquisition execution
Market lease operations if included in the W1-001 protected invocation budget
News checkpoint operations
News article/membership batch statements
```

Digest/history persistence may either be charged to the same budget or explicitly reserved as fixed headroom. Do not silently omit it from the safety argument.

### 2. Do not estimate D1 queries from bar counts

Instrumentation must be attached to actual D1 statement execution or to an explicit wrapper/port whose accounting is one-to-one with issued statements.

Do not compute:

```text
bars * assumedQueriesPerBar
```

because W1-002 intentionally changed the statement shape.

### 3. Avoid double counting

The 7 statements issued by `D1NormalizedBarStore.acceptBatch()` should count as 7, not 7 plus a synthetic page cost.

Likewise News `acceptBatch()` should be charged according to actual statements performed. If a page contains no articles, do not charge article-store statements that were never issued.

### 4. Budget refusal semantics

Before executing an operation that would cross the configured ceiling, fail boundedly rather than issuing the D1 statement.

Required behavior:

- Market work already accepted in the current job remains durable;
- checkpoint must not falsely advance beyond unaccepted data;
- News work must become partial/retryable if remaining shared budget is insufficient;
- Market guarantees must not be weakened to make News fit.

### 5. Digest values

Replace nullable placeholders with measured values:

```text
marketD1Queries
totalD1Queries
withinBudget
blocker
```

Expected normal successful state:

```text
marketD1Queries = measured integer
newsD1Queries   = measured integer
totalD1Queries  = market + news (+ explicitly budgeted shared overhead)
withinBudget    = total <= 40 and external <= 40
blocker         = null/omitted
```

### 6. Daily D1 row projection

Using actual scheduler configuration, report a bounded projection for:

```text
normal rows read/day
normal rows written/day
worst reviewed rows read/day
worst reviewed rows written/day
```

Separate steady-state polling from catch-up/replay. Do not multiply the 100-bar catch-up fixture across every tick unless that is actually schedulable.

The purpose is to compare live Canary design against current Cloudflare Free daily limits without claiming that the 100-bar fixture represents normal traffic.

## Required fixtures

At minimum:

1. one Market 100-bar page + no News;
2. one Market 100-bar page + normal two-page News path;
3. Market + worst reviewed News pages without retries;
4. Market HTTP retry + News path uses the same external budget;
5. Market D1 + News D1 combined accounting is non-null and exact in fixture;
6. insufficient remaining D1 budget stops additional D1 statements before ceiling breach;
7. News-disabled regression remains identical to accepted Market behavior except for added observability;
8. dry-run remains mutation-free;
9. body scan clean;
10. secret/log scan clean.

## Acceptance target

Return:

```text
W1-001 Stage B final-preflight status: Accepted | Provisional | Blocked
focused tests:
full tests:
typecheck:
Wrangler dry-run/build:
diff check:
100-bar Market D1 queries:
normal Market D1 queries/tick:
normal News D1 queries/tick:
normal total D1 queries/tick:
worst reviewed Market D1 queries/tick:
worst reviewed News D1 queries/tick:
worst reviewed total D1 queries/tick:
normal external subrequests/tick:
worst reviewed external subrequests/tick:
normal rows read/day:
normal rows written/day:
worst reviewed rows read/day:
worst reviewed rows written/day:
News-disabled provider calls: 0
News-disabled News mutations: 0
dry-run mutations: 0
body scan: clean
secret/log scan: clean
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

Hard Stage-B acceptance condition remains:

```text
combined external subrequests <= 40
combined D1 queries           <= 40
```

with actual measured accounting, not nullable or inferred placeholders.

## Stop conditions

Stop if satisfying the limit requires reducing accepted Market data coverage/acceptance semantics, applying remote D1, deploying Worker, changing Cron, changing Worker mode, storing News body content, or inventing CPU equivalence from local tests.

CPU remains a live-Canary observation gate after this final preflight.
