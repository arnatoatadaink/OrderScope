# OrderScope — W1-001 Stage B Code Review / Repair Handoff

Status: **Blocked — repair required before Stage B re-evaluation**
Date: 2026-09-10
Scope: Synced Stage-B News Worker code review
Related: `W1-001_STAGE_B_BLOCKER_REPORT_2026-09-10.md`, `W1-002_LOCAL_IMPLEMENTATION_HANDOFF_2026-09-10.md`

## 1. Review decision

Keep `W1-001 Stage B = Blocked`.

The reported Market D1 blocker is real: current `D1NormalizedBarStore.accept()` still performs multiple D1 statements per bar and `executeAcquisitionJob()` awaits it per normalized bar. W1-002 remains the primary prerequisite.

The synced News implementation is broadly consistent with the Stage-A/Stage-B design, but three additional repair items must be resolved before live Canary review.

## 2. Finding R1 — shared external-subrequest budget does not govern Market execution

Severity: **High**

Current `worker.ts` creates `InvocationBudget` only after all Market jobs have executed. It reconstructs Market external use from successful execution summaries by summing `summary.pages` and then consumes that count from the shared budget.

Problems:

1. Market fetches are not prevented by the shared 40-subrequest ceiling while they execute.
2. Provider retries are not represented by `summary.pages`; one page can require multiple HTTP attempts.
3. Failed Market jobs are collapsed to `{ jobId, outcome: "FAILED" }`, so their already-consumed HTTP attempts/pages are omitted from the reconstructed count.
4. News can therefore begin with more apparent remaining external budget than the invocation actually has.

Required repair:

- instantiate one `InvocationBudget` before Market execution;
- pass it into Market provider execution or otherwise account for every actual HTTP attempt through the same budget;
- make retry attempts consume external budget before each fetch attempt;
- preserve failed-attempt consumption;
- only run News from the true remaining shared budget;
- add fixtures for Market retry/failure + News due in same invocation.

Do not use `pages` as a proxy for HTTP attempts.

## 3. Finding R2 — AFTER_HOURS is omitted from News observation sessions

Severity: **Medium / design mismatch**

`SessionKind` includes `AFTER_HOURS`, but `planNewsAcquisition()` accepts only `PREMARKET` or `REGULAR` sessions. The W1-001 design calls for News polling during the configured U.S. observation day, which previously included Pre-market / Regular / After-hours.

There is also a deeper existing calendar limitation: `AlpacaMarketCalendarProvider` currently materializes REGULAR and optionally PREMARKET sessions, but does not materialize AFTER_HOURS sessions even though the type supports them.

Required decision/repair:

- either explicitly redefine W1-001 Canary observation scope as PREMARKET + REGULAR only and update design/WBS wording; or
- preferably add/derive the accepted AFTER_HOURS session boundary through the existing calendar/session configuration and include it in News planning.

Do not hard-code a separate UTC/Tokyo clock solely in `news-schedule.ts`.

Add an explicit AFTER_HOURS scheduling fixture if after-hours remains in scope.

## 4. Finding R3 — News `CONFLICT` outcome is declared but never produced

Severity: **Medium / semantic ambiguity**

`NewsAcceptance` declares `NEW | SAME | UPDATED | CONFLICT`, but `D1NewsStore.acceptBatch()` classifies every existing article whose content identity differs as `UPDATED`.

This means there is currently no path that produces `CONFLICT`, despite W1-001 inheriting I0-004 semantics that distinguish update/revision from conflict.

Required repair:

Freeze an explicit rule, for example:

- `UPDATED`: provider article ID matches and provider revision evidence permits replacement, such as a newer explicit `provider_updated_at`;
- `CONFLICT`: same provider article ID presents materially different semantic content without a valid forward revision relationship, or regresses revision timestamp/content.

Then implement and test the rule. If News conflict is intentionally out of v0.1 scope, remove `CONFLICT` from the contract and amend W1-001 semantics explicitly rather than leaving a dead outcome.

## 5. Finding R4 — 429 handling does not consume rate-limit response metadata

Severity: **Low / design deviation**

`fetchNewsPage()` retries 429/5xx with configured exponential backoff, but does not inspect `Retry-After` or Alpaca rate-limit response headers despite Stage-B design notes requiring headers to be observed where available.

Required repair before live activation:

- safely parse supported retry/rate-limit header(s) when present;
- cap any provider-supplied wait using the existing configured maximum;
- never log auth headers or arbitrary provider response bodies;
- retain fallback exponential backoff when headers are absent/invalid.

This item need not block W1-002 implementation, but should be complete before live Canary activation.

## 6. Positive review findings

The following boundaries are implemented correctly enough to preserve while repairing:

- News defaults disabled;
- Canary symbols fixed to AMD,NVDA;
- cadence 5 minutes and overlap 15 minutes are configurable and bounded;
- provider page limit is capped at 50;
- max pages/symbol is capped at 2;
- max raw observations/run is capped at 200;
- News provider request uses `include_content=false`;
- durable schema contains no News body/content column;
- provider symbols are trimmed, uppercased and deduplicated;
- article identity is provider + providerArticleId at persistence primary-key level;
- cross-symbol membership is stored separately;
- News pages are persisted in set/batch-oriented statements rather than per-article D1 loops;
- page-token loop and page/article bounds are fail-closed;
- checkpoint does not advance to the requested end after a partial/failure;
- dry-run path remains non-mutating by contract;
- Worker digest intentionally reports Market D1 as unknown and `withinBudget=false` rather than fabricating acceptance.

## 7. W1-002 interaction

Do not rewrite W1-002 around News. Its job remains Market D1 query compression while preserving Market semantics.

Recommended sequence:

```text
R1 shared external budget repair
+ W1-002 Market D1 set-based/batched persistence
+ R2/R3 News semantic/session repairs
+ R4 rate-limit-header support
-> rerun W1-001 Stage B combined preflight
```

R1 and W1-002 should be designed together because both require a true per-invocation shared resource ledger.

## 8. Re-evaluation evidence

Return at minimum:

```text
focused tests:
full tests:
typecheck:
diff check:
Market 100-bar D1 query count:
Market retry/failure actual HTTP-attempt count:
shared external budget actual-attempt accounting: pass/fail
combined worst external subrequests:
combined worst D1 queries:
AFTER_HOURS decision: included / explicitly excluded with amended design
News UPDATED fixture: pass/fail
News CONFLICT fixture or contract removal: pass/fail
429 header-aware retry fixture: pass/fail
News disabled regression: pass/fail
dry-run mutations: 0
body scan: clean
secret/log scan: clean
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

## 9. Gate

No live Worker deployment, remote migration, Cron registration/change, or Worker mode change is authorized by this repair handoff.
