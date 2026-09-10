# OrderScope — W1-001 Stage A Local Implementation Handoff

Status: **Ready for local implementation — non-live only**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
WBS revision: `docs/work-management/local-corporate-intelligence/WBS_REVISION_NEWS_WORKER_2026-09-10.md`
Source design: `docs/work-management/local-corporate-intelligence/NEWS_WORKER_ACQUISITION_DESIGN_2026-09-10.md`
Predecessor: `N1-006 — Evaluate news recall` Accepted

## 1. Purpose

Implement the **non-live/fixture boundary** of Worker/Schedule News metadata acquisition for AMD/NVDA.

This handoff authorizes Stage A only:

```text
code + config + fixtures + dry-run + local tests
```

It does **not** authorize:

```text
live Worker mutation
Cron registration/change
remote D1 mutation
historical catch-up
Worker Shadow -> live change
full-Universe News activation
```

## 2. Accepted decision to preserve

N1-006 real benchmark result:

```text
645/645 candidates reviewed
matched = 51
unrelated = 594
unresolved = 0
references discovered = 4/4
recall = 1.0000
misattribution = 0
signed lag min = -357011 s
signed lag max = 14636 s
signed lag median = -44826.5 s
focused = 19 passed
full = 503 passed
compileall = success
diff check = clean
```

The signed lag above is provider publication versus SEC/IR reference availability. It is **not** Worker polling latency.

Initial W1-001 Canary cadence is therefore retained at **5 minutes**, but must remain configurable and subject to Canary runtime measurement.

## 3. Existing Worker architecture to reuse

Do not create a parallel scheduler stack.

Relevant existing files include:

```text
src/acquisition-config.ts
src/acquisition-config.test.ts
src/schedule.ts
src/schedule.test.ts
src/worker.ts
src/worker.test.ts
src/worker-orchestration.integration.test.ts
src/checkpoint.ts
src/checkpoint.test.ts
src/execution.ts
src/execution.test.ts
src/alpaca.ts
src/alpaca.test.ts
src/calendar.ts
src/calendar.test.ts
src/digest.ts
```

Observed existing boundaries:

- `SchedulePolicy` currently plans `MARKET_BARS` jobs only.
- `runScheduledTick()` in `worker.ts` already owns live scheduled orchestration, D1 checkpoints, leases, bounded jobs, digest output, and Alpaca credentials.
- `loadAcquisitionRuntimeConfig()` already owns bounded acquisition configuration and retry/page/job limits.
- D1 checkpoint/idempotency/retry behavior exists for market acquisition and should be reused conceptually rather than duplicated.

W1-001 should extend these boundaries minimally.

## 4. Recommended implementation decomposition

### A. News-specific configuration

Add explicit News configuration without overloading bar cadence types.

Recommended shape:

```text
NEWS_ACQUISITION_ENABLED
NEWS_ACQUISITION_CADENCE_MINUTES = 5
NEWS_ACQUISITION_OVERLAP_MINUTES
NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL
NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN
NEWS_ACQUISITION_CANARY_SYMBOLS = AMD,NVDA
```

Requirements:

- default/fixture path must not imply live activation;
- cadence must validate as a bounded positive integer;
- Canary symbols must normalize to exactly the reviewed Stage-A scope;
- do not reuse `Cadence = 1Min|15Min|1Day` as if News were a bar interval;
- no credential values in config diagnostics.

If existing generated `Env` typing requires wrangler binding declarations, modify only non-secret variable declarations. Do not add real secret values.

### B. News job contract

Do not silently add News semantics to the existing `AcquisitionJob` unless the type remains unambiguous.

Preferred direction:

```ts
type NewsAcquisitionJob = {
  jobId: string;
  jobKind: "NEWS_METADATA";
  createdAt: string;
  symbols: readonly ["AMD", "NVDA"] | readonly string[];
  requestedRange: TimeRange;
  mode: "INCREMENTAL" | "CATCH_UP" | "RECONCILE";
  checkpointExpectations: ...;
  maxPagesPerSymbol: number;
  maxArticlesPerRun: number;
  dueReason: ...;
};
```

The exact type location may be a new focused module if adding it to `schedule.ts` would couple News too tightly to market bars.

### C. Session-aware 5-minute planning

Use the existing U.S. market calendar/session configuration to determine whether the current scheduled tick is inside the configured observation day.

Do not hard-code Tokyo/UTC clock windows for News.

Stage-A planning rules:

1. AMD/NVDA only.
2. At most one News job per 5-minute cadence boundary.
3. Job range starts from the last accepted News checkpoint minus bounded overlap.
4. Job range ends at current eligible observation boundary.
5. A missed tick is recovered through the next bounded overlap/range.
6. No checkpoint means a bounded initial range, **not** an unbounded 30-day historical scan.
7. Outside configured observation day: no normal News job.
8. Historical catch-up remains separately gated by `SMOKE-007`.

### D. Alpaca News transport boundary

The Local N1-006 adapter proved the live Alpaca News response shape, including whitespace normalization in provider symbols. Worker Stage A must use the same normalized contract behavior.

Required metadata only:

```text
provider article ID
headline
publisher
URL
provider created/published timestamp
provider updated timestamp if supplied
provider symbols
query-symbol membership
retrieved_at
accepted_at
```

Body handling:

- request metadata-only where provider supports it;
- if provider returns a body/content member despite metadata-only request, discard it before durable normalization;
- never persist/log body content;
- normalize provider-symbol whitespace and deduplicate after normalization;
- fail closed on invalid structural fields rather than inventing values.

### E. Worker-side identity and persistence

Preserve one provider article identity across AMD/NVDA queries.

Required semantics:

```text
provider article 123 returned for AMD
provider article 123 returned for NVDA
=> one durable article identity
=> query membership = AMD + NVDA
```

Do not use headline equality as primary identity.

Reuse accepted duplicate/update concepts:

```text
new
same/duplicate
updated/revision
conflict
```

If a new D1 table/migration is required, keep it News-metadata-specific and do not mix article rows into the market bar table.

### F. Checkpoint state

Use provider/source bounded checkpoint semantics equivalent to I0-003.

Recommended coverage key shape must include enough identity to avoid collision with market bars, for example:

```text
news|alpaca|AMD,NVDA|metadata-v0.1
```

or a per-symbol key if implementation requires it. If per-symbol checkpoints are used, cross-symbol article identity must still deduplicate at persistence.

Completion state must make these distinguishable:

```text
not selected
in progress
partial
retryable failure
complete
```

Do not advance `completeThrough` on a partial/failed page sequence.

### G. Runtime timing evidence

Persist or expose sufficient non-secret metadata to later measure:

```text
provider_published_at -> worker_retrieved_at
provider_published_at -> accepted_at
scheduled_at -> run_started_at
run_started_at -> run_finished_at
```

N1-006 retrospective lag must not be reused as Worker runtime lag.

### H. Digest / observability

Extend the existing scheduler digest with a compact News section instead of creating a second operational reporting surface.

Example conceptual fields:

```text
news.mode = disabled | shadow-plan | active
news.cadenceMinutes = 5
news.plannedJobs
news.selectedJobs
news.completedJobs
news.partialJobs
news.failedJobs
news.articlesObserved
news.duplicates
news.updates
news.pages
news.nextCheckpoint
```

Do not include URLs, headlines, provider response bodies, credentials, or header values in scheduler-level logs unless explicitly needed by a separately reviewed diagnostic path.

## 5. Required Stage-A fixture acceptance

Implement tests for at least:

1. cadence boundary plans once per eligible 5-minute slot;
2. outside-session tick plans no News job;
3. no-checkpoint start is bounded;
4. existing checkpoint uses overlap;
5. missed tick is recovered by bounded next range;
6. AMD/NVDA same provider article persists once with both query memberships;
7. provider symbol whitespace normalization/dedup matches accepted N1-006 behavior;
8. multi-page NVDA completes within page budget;
9. page limit produces partial state and does not falsely advance completion;
10. 429/5xx produces sanitized retryable failure;
11. page-token loop terminates fail-closed;
12. body-bearing response does not persist body;
13. credential/header strings do not appear in stored/logged fixture output;
14. dry-run shows intended News jobs/ranges without calling provider or mutating D1;
15. existing Market Bars scheduling behavior remains unchanged when News is disabled.

## 6. Likely code locations

Minimize changes. A reasonable decomposition is:

```text
src/news-acquisition-config.ts          new, if separation helps
src/news-acquisition-config.test.ts
src/news.ts                             normalized metadata + transport boundary
src/news.test.ts
src/news-schedule.ts                    planning only
src/news-schedule.test.ts
src/news-store.ts                       D1 metadata identity/persistence, if needed
src/news-store.test.ts
src/news-execution.ts                   bounded page execution, if needed
src/news-execution.test.ts
src/worker.ts                           orchestration integration only
src/worker-orchestration.integration.test.ts
```

This is guidance, not a requirement. Prefer fewer modules if existing boundaries absorb the work cleanly without mixing bar-specific semantics.

## 7. Acceptance commands

Use the repository's existing package scripts as the authority. At minimum run the focused new/existing Worker tests and the full TypeScript test suite.

Record exact commands and results in the completion report.

Expected evidence fields:

```text
focused tests =
full tests =
typecheck/build =
diff check =
News disabled regression =
dry-run mutation count = 0
body persistence scan = clean
secret/log scan = clean
```

If Python Local tests are untouched, do not rerun the full Python 503-test suite merely to claim W1-001 TypeScript acceptance. Run only suites affected by the actual changes plus the repository's standard required checks.

## 8. Stop conditions

Stop Stage A and report instead of improvising if any of these become necessary:

- real Worker deployment;
- real D1 migration execution;
- Cron/schedule registration;
- changing `WORKER_MODE`;
- enabling News against Alpaca in deployed infrastructure;
- adding full-Universe symbols;
- performing historical catch-up;
- changing provider terms/credential scope;
- storing article bodies;
- weakening existing Market Bars acceptance to make News pass.

Code and migration files may be prepared locally, but remote application remains separately gated.

## 9. Completion report back

Return:

```text
W1-001 Stage A status: Accepted | Provisional | Blocked
files changed:
focused tests:
full tests:
typecheck/build:
diff check:
dry-run evidence:
News job cadence:
overlap:
max pages/symbol:
max articles/run:
checkpoint key strategy:
D1 schema/migration prepared: yes/no
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
remaining blockers:
next recommended gate:
```

## 10. Next gate after Stage A

If Stage A is Accepted:

```text
Stage A Accepted
-> review current Alpaca / Cloudflare terms and limits
-> review migration/change set
-> explicit Worker Canary change window
-> AMD/NVDA live Canary only
-> measure runtime publication-to-retrieval/acceptance lag
-> decide whether 5 min remains appropriate or can be relaxed
```

Do not proceed to that live gate without explicit approval.
