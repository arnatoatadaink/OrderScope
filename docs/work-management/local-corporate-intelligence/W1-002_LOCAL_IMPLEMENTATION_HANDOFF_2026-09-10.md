# OrderScope — W1-002 Local Implementation Handoff

Status: **Ready for local implementation — non-live only**
Date: 2026-09-10
Task: `W1-002 — Batch Market Bar D1 persistence for shared invocation budget`
Blocks: `W1-001 Stage B`
Source blocker: `docs/work-management/local-corporate-intelligence/W1-001_STAGE_B_BLOCKER_REPORT_2026-09-10.md`

## 1. Purpose

Redesign the existing Market Bars D1 persistence path so the reviewed 100-bar fixture can execute with a bounded query count that leaves room for the already-bounded News path.

This is a persistence/query-shape optimization only. Preserve Market behavior and evidence semantics.

This handoff authorizes:

```text
local TypeScript code changes
local migration preparation if required
fixture/dry-run changes
unit/integration tests
query-count instrumentation
```

It does not authorize:

```text
remote D1 apply
Worker deploy
Cron change
Worker mode change
historical catch-up
Market correctness relaxation
```

## 2. Existing bottleneck to remove

Current execution shape:

```text
executeAcquisitionJob()
  -> for each bar
     -> D1NormalizedBarStore.accept(...)
```

Current `accept()` can perform several statements for one observation:

```text
reserve/read receipt
insert/read canonical bar
optional conflict insert
complete/read receipt
```

At 100 bars, the Stage-B fixture measured at least 300 D1 queries before News accounting.

Do not optimize only the JavaScript loop while preserving one SQL query family per bar. The acceptance target is D1 query-count reduction.

## 3. Preferred design direction

Primary candidate: **bounded JSON payload + set-based SQL using D1/SQLite JSON functions**.

Cloudflare D1 supports `json_each(?)`, so one bound JSON array can be expanded into many rows in one statement.

Conceptual shape:

```text
normalize/fingerprint bounded page in Worker memory
  -> create bounded observation batch
  -> serialize compact JSON payload
  -> statement A: reserve/load receipt state for batch
  -> statement B: insert canonical bars set-wise
  -> statement C: identify canonical matches/conflicts set-wise
  -> statement D: insert conflicts set-wise where required
  -> statement E: complete receipts set-wise
  -> reconstruct BarAcceptanceResult[] deterministically
```

The exact number of statements may differ. The implementation is acceptable if the measured query bound is met without semantic regression.

A plain `db.batch([...hundreds of statements...])` is not sufficient evidence by itself; instrument/count individual statements against the D1 query budget.

## 4. Interface change

Add a batch boundary rather than forcing `executeAcquisitionJob()` to call single-row persistence repeatedly.

Preferred contract:

```ts
type BarAcceptanceInput = {
  candidate: BarNormalizationResult;
  provenance: BarProvenance;
};

interface NormalizedBarStore {
  accept(candidate: BarNormalizationResult, provenance: BarProvenance): Promise<BarAcceptanceResult>;
  acceptBatch?(inputs: readonly BarAcceptanceInput[]): Promise<readonly BarAcceptanceResult[]>;
}
```

or a clean required batch method if all implementations/tests can migrate safely.

Requirements:

- preserve a simple in-memory/test implementation path;
- deterministic result order must match input order;
- do not make the executor depend directly on D1;
- keep D1-specific batching inside `D1NormalizedBarStore` or a tightly scoped persistence module.

`executeAcquisitionJob()` should batch at a bounded unit such as provider page or a reviewed batch-size cap.

## 5. Semantics that must remain unchanged

### 5.1 Idempotency

Same `idempotencyKey` + same observation:

```text
first acceptance -> INSERTED or prior accepted outcome
replay           -> same completed receipt semantics
provenanceAppended behavior preserved according to existing contract
```

Same `idempotencyKey` associated with a different observation must still fail closed.

### 5.2 Canonical duplicate

Different observation receipt, same canonical identity and fingerprint:

```text
MATCHED
```

Do not create a second canonical bar.

### 5.3 Conflict

Same canonical identity, different semantic fingerprint:

```text
CONFLICT
```

Retain:

```text
stored fingerprint
observed fingerprint
observed semantic content
detected timestamp
receipt linkage
```

Do not overwrite the accepted canonical row merely to reduce query count.

### 5.4 Rejected normalization

Rejected candidates still obtain deterministic acceptance receipts and reasons.

### 5.5 Atomicity / partial failure

Define and test the batch failure boundary explicitly.

Preferred behavior:

- one logical batch either yields complete deterministic acceptance results or raises before checkpoint advancement;
- do not report some observations accepted in the executor summary if their receipt state is not durably reconstructable;
- if multiple SQL statements are required, use the strongest D1-supported transactional/batch semantics compatible with the design and test failure injection between phases.

Do not claim stronger atomicity than D1 actually provides.

## 6. Query-budget target

Stage-B News measurements currently reserve approximately:

```text
normal News D1 queries = 9
worst News D1 queries  = 15
```

OrderScope combined ceiling:

```text
40 D1 queries / scheduled invocation
```

Therefore W1-002 should target:

```text
Market worst reviewed fixture <= 20 D1 queries
```

This leaves at least 5 queries of additional headroom even when the measured worst News path uses 15 queries:

```text
20 Market + 15 News = 35 <= 40
```

This `<=20` Market target is an OrderScope engineering acceptance target, not a Cloudflare platform limit.

If `<=20` is impossible without weakening semantics, stop and report the measured minimum/query decomposition rather than silently raising it.

## 7. Daily Free-tier write consideration

Query-count reduction alone is insufficient.

The prior Stage-B News projection showed up to 201 News rows written/tick in the normal two-page case. Market bar writes also consume the D1 Free daily row-write allowance.

W1-002 must therefore report:

```text
Market rows read for 100-bar fixture
Market rows written for 100-bar fixture
rows written for all-MATCHED replay
rows written for conflict fixture
```

Do not alter durable evidence only to minimize billed rows. The result is for capacity planning; if the Free daily row-write allowance is structurally incompatible with the intended cadence, report that as a separate blocker.

## 8. CPU boundary

Hashing and JSON serialization happen inside Worker CPU time.

Keep:

- one fingerprint calculation per observation;
- payload construction bounded by `maxBarsPerJob`;
- no O(n^2) cross-comparison;
- no repeated JSON stringify/parse loops per SQL phase where avoidable.

Local tests may detect algorithmic regressions but cannot certify the Cloudflare Free 10 ms Cron CPU limit. Runtime CPU remains a live-Canary observation gate.

## 9. Required fixtures

At minimum test:

1. 100 entirely new normalized bars;
2. replay of same 100 idempotency receipts;
3. 100 canonical duplicates with new receipt IDs -> MATCHED;
4. one conflict inside otherwise matching/new batch;
5. multiple conflicts in one batch;
6. rejected normalization mixed with normalized rows;
7. duplicate idempotency key with different payload -> fail closed;
8. D1 failure during first set-based phase;
9. D1 failure during later set-based phase;
10. deterministic output order;
11. checkpoint does not advance when batch persistence fails;
12. existing small single-bar behavior remains compatible;
13. Market-only worker regression remains green;
14. News-disabled regression remains green;
15. combined W1-001 Stage-B 100-bar + worst News fixture remains <= 40 D1 queries.

## 10. Instrumentation

Return an explicit query decomposition, not only a total:

```text
receipt reservation/read queries:
canonical insert/read queries:
conflict queries:
receipt completion queries:
checkpoint/attempt queries:
lease/digest queries:
Market total D1 queries:
```

If a set-based statement combines multiple logical categories, count it once at the D1 statement boundary and explain the category grouping.

## 11. Acceptance commands

Use repository scripts as authority. Return at least:

```text
focused W1-002 tests:
full TypeScript tests:
typecheck:
wrangler dry-run/build:
git diff --check:
```

Also re-run the W1-001 Stage-B combined-budget fixture after the Market batching change.

## 12. Required report back

```text
W1-002 status: Accepted | Provisional | Blocked
batch strategy:
batch size:
100-bar Market total D1 queries:
query decomposition:
100-bar rows read:
100-bar rows written:
100-bar replay rows written:
conflict fixture D1 queries:
combined worst Market + News D1 queries:
combined worst external subrequests:
Market semantic regression: pass/fail
checkpoint-on-failure regression: pass/fail
focused tests:
full tests:
typecheck:
dry-run/build:
diff check:
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
remaining blockers:
```

## 13. Stop conditions

Stop and return Blocked/Provisional if:

- Market semantics must be weakened to reach the budget;
- canonical conflict evidence is lost;
- idempotency receipt traceability is lost;
- result reconstruction becomes ambiguous;
- 100-bar Market fixture remains >20 D1 queries and no safe smaller bound is demonstrated;
- combined W1-001 fixture remains >=40 D1 queries;
- daily row-write usage appears structurally incompatible with Free plan and cannot be bounded without scope change;
- remote D1 or live Worker execution becomes necessary.

## 14. Next gate

If W1-002 is Accepted:

```text
W1-002 Accepted
  -> reclassify/re-run W1-001 Stage B
  -> if combined ceilings pass: Stage B Accepted
  -> Web prepares explicit AMD/NVDA live Canary change window
```

Do not open the live change window from Local.
