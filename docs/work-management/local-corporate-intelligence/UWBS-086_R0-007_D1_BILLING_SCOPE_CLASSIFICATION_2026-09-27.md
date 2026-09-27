# UWBS-086 — R0-007 D1 Billing Evidence Scope Classification — 2026-09-27

Status: **ACCEPTED AS SPECIFIC READ-QUERY EVIDENCE / NOT A CRON INVOCATION PROXY**
Branch: `l1-003-local-market-recovery`

## Evidence observed locally

Two existing local custody artifacts were inspected:

```text
var/d1-custody/r0-007-first-remote/pass1.json
var/d1-custody/r0-007-first-remote/pass2.json
```

Both returned the same single QQQ 1-minute canonical bar for the frozen window around `2026-09-01T16:03:00Z` and the same D1 billing metadata:

```text
results rows:   1
rows_read:      3906
rows_written:   0
size_after:     4796416
changes:        0
changed_db:     false
total_attempts: 1
```

The two passes therefore provide reproducible evidence for this particular read-only query shape.

## Scope classification

This evidence is **not** one normal scheduled Worker invocation. It is the R0-007 bounded custody/read path targeting a frozen `normalized_bar` range and returning one canonical row.

Therefore the following extrapolation is rejected:

```text
3906 rows_read * 1440 scheduled invocations/day
```

That multiplication would incorrectly assume the R0-007 custody query runs once per normal Cron tick.

Accepted use of this evidence:

- real repository/local evidence of D1 billing metadata;
- reproducible cost of this specific read-only query shape;
- evidence that a one-row result may still scan thousands of rows;
- candidate query/index efficiency follow-up.

Rejected use:

- normal Cron rows-read/day proxy;
- write-path evidence;
- storage-growth evidence;
- final UWBS-086 capacity acceptance by itself.

## Normal scheduled path findings

The live scheduled Worker wraps D1 with `InvocationBudget` and persists total D1 statement count in the operational digest. Market bootstrap, acquisition jobs, optional news work, run evidence and the final digest are included in that statement budget.

The market acquisition path currently prefers `D1NormalizedBarStore.acceptBatch()`, so provider bars for one page are processed in bulk rather than executing the single-bar store path once per bar. The batch store performs grouped receipt reservation/read, canonical insert/read, conflict insert, receipt completion and completion read operations. Billing rows can still scale with the number of bars even though D1 statement count remains bounded.

Checkpoint updates also support bulk `compareAndSetMany()` and acquisition attempts are persisted separately.

## Remaining capacity evidence

Final UWBS-086 capacity acceptance still needs:

1. actual normal scheduler configuration (`maxJobsPerTick`, `maxPagesPerJob`, `maxBarsPerJob`, enabled news/evidence features);
2. existing scheduler digest samples containing `budget.totalD1Queries` if available;
3. measured D1 `rows_read` / `rows_written` / `size_after` for a representative normal scheduled invocation, or a defensible non-live row bound;
4. fresh external capacity envelope and headroom calculation.

No Worker/Cron/D1 mutation is authorized or performed by this classification.
