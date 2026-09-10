# OrderScope — W1-001 Stage B Preflight Handoff

Status: **Ready for local preflight — no live activation authorized**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Predecessor: `W1-001 Stage A` Accepted
Purpose: prove one scheduled-tick budget and rollback safety before any live AMD/NVDA Canary change window

## 1. Decision

Do not open the live Worker Canary change window yet.

Stage A has been Accepted, but current Cloudflare Free-plan limits make the critical next question a **per-invocation combined budget check** because News shares the existing scheduled Worker with Market Bars.

The next bounded task is therefore Stage B preflight only:

```text
fixture/load-model + dry-run instrumentation + budget assertions + rollback verification
```

No remote deployment, Cron change, remote D1 migration, or provider call is authorized by this handoff.

## 2. Current official constraints to design against

Rechecked 2026-09-10 from official provider documentation.

### Cloudflare Workers Free

Design-relevant limits:

```text
requests/day                         100,000
external subrequests/invocation     50
Cron Triggers/account               5
CPU time/Cron invocation            10 ms
Cron wall time                      15 min
```

The important W1-001 constraint is the **single-invocation** budget, not the daily Worker request count.

### Cloudflare D1 Free

Design-relevant limits:

```text
queries per Worker invocation       50
rows read/day                       5,000,000
rows written/day                    100,000
max database size                   500 MB
account storage                     5 GB
```

Free-tier daily row limits are enforced; queries fail after the account reaches the daily read/write allowance until reset.

### Alpaca Market Data / News

Official Market Data plan documentation lists Basic historical API calls at 200/minute and the News endpoint documents 429 handling with `X-RateLimit-*` response headers. The News endpoint itself does not provide a separate fixed News-specific RPM in the endpoint reference.

Therefore W1-001 must:

- keep a conservative explicit News page/request budget;
- fail partial/retryable rather than consume unbounded pages;
- observe provider rate-limit headers where available;
- not assume that an unstated News-specific rate limit equals another endpoint's limit.

## 3. Primary preflight risk

The Worker already performs Market Bars planning/execution, checkpoint operations, leases, D1 writes and digest writes.

At each 5-minute News boundary:

```text
existing Market Bars work
+ News planning
+ Alpaca News fetch pages
+ News checkpoint reads/writes
+ article identity/upsert work
+ digest work
```

must stay inside the same invocation limits.

Passing News tests in isolation is not enough.

## 4. Required Stage-B preflight implementation

### B1. Combined scheduled-tick budget accounting

Extend dry-run/test instrumentation so one scheduled tick reports or can assert at least:

```text
marketExternalSubrequests
newsExternalSubrequests
totalExternalSubrequests
marketD1Queries
newsD1Queries
totalD1Queries
newsPagesRequested
newsArticlesAccepted
newsArticlesDuplicate
newsArticlesUpdated
```

Do not log headlines, URLs, bodies, credentials, or authentication headers merely for budgeting.

### B2. Hard safety margins

For Free-plan fixture acceptance, require hard configured ceilings below provider/platform limits.

Recommended Stage-B assertion target:

```text
total external subrequests < 50
total D1 queries           < 50
```

Do not plan exactly to the limit. Reserve headroom for lease/digest/error/checkpoint work.

A reasonable initial test target is to keep planned normal-path combined usage at or below ~70-80% of each per-invocation ceiling. This is an engineering safety target, not a Cloudflare requirement.

If existing Market Bars worst-case fixture already consumes too much headroom, stop and report rather than silently reducing Market acceptance guarantees.

### B3. News pagination cap

Freeze an explicit `maxPagesPerSymbol` / equivalent News page budget based on the combined-subrequest ceiling.

The cap must account for Market Bars fetches occurring in the same scheduled invocation.

If the cap is reached:

```text
News result = partial/retryable
checkpoint completeThrough does not falsely advance
next bounded run resumes
```

### B4. D1 query/write shape

Add or verify indexes/lookup shape so News identity and checkpoint operations do not require full scans.

Fixture/load tests should show bounded D1 operation counts for:

1. no new article;
2. one new article;
3. same article returned for AMD and NVDA;
4. update/revision;
5. multi-page burst;
6. page-budget partial result.

Daily row totals are secondary to this per-invocation bound, but record projected rows read/written per normal 5-minute News tick for later Canary monitoring.

### B5. CPU-risk acknowledgement

Cloudflare Workers Free currently allows only 10 ms CPU per Cron invocation.

Local `tsc`/unit-test success cannot prove production CPU usage. Stage B should therefore minimize synchronous work in the scheduled handler and keep parsing/dedup bounded.

Before declaring the live Canary safe, the change-window plan must include immediate observation of Worker CPU/exceeded-resource metrics and a rollback condition if News materially increases CPU-limit failures.

Do not fabricate a local CPU-equivalence threshold.

### B6. Five-minute cadence gate

Keep:

```text
NEWS cadence = 5 minutes
Canary symbols = AMD,NVDA
```

The live Canary later measures:

```text
provider_published_at -> worker_retrieved_at
provider_published_at -> accepted_at
```

No cadence relaxation is part of Stage B preflight.

### B7. Rollback test

Prove that setting News disabled returns the exact accepted Market-only orchestration behavior:

```text
News provider calls = 0
News D1 mutation     = 0
Market Bars behavior unchanged
Worker mode unchanged
```

A live rollback must be possible by configuration without deleting News data or modifying Market tables.

## 5. Required acceptance fixtures

Run at least these combined orchestration cases:

1. ordinary 5-minute boundary, low News volume;
2. 5-minute boundary with Market Bars jobs also due;
3. News multi-page burst within cap;
4. News page budget exhausted;
5. duplicate article across AMD/NVDA;
6. article update;
7. 429/5xx retryable News failure while Market path remains valid;
8. News-disabled exact regression;
9. dry-run with zero mutation;
10. worst-case reviewed fixture for combined external-subrequest and D1-query budget.

## 6. Acceptance evidence to return

```text
W1-001 Stage B preflight status: Accepted | Provisional | Blocked
focused tests:
full tests:
typecheck:
diff check:
normal combined external subrequests:
worst fixture combined external subrequests:
normal combined D1 queries:
worst fixture combined D1 queries:
News max pages/symbol:
News max articles/run:
projected News rows read/tick:
projected News rows written/tick:
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

## 7. Stop conditions

Stop and return `Blocked` or `Provisional` if:

- worst reviewed fixture reaches/exceeds 50 external subrequests;
- worst reviewed fixture reaches/exceeds 50 D1 queries;
- meeting the budget requires weakening existing Market Bars guarantees;
- News-disabled behavior differs from accepted Market-only behavior;
- body or credential material crosses durable/logging boundaries;
- a remote deploy/change is needed to complete the preflight;
- CPU safety can only be claimed by inventing a local-to-production equivalence.

## 8. Gate after Stage B preflight

Only after Stage B preflight is Accepted:

```text
Stage A Accepted
+ Stage B budget/rollback preflight Accepted
-> prepare explicit AMD/NVDA live Canary change window
-> apply reviewed migration/config only
-> keep scope AMD/NVDA metadata-only
-> observe CPU, subrequests, D1 rows, failures and runtime News lag
-> rollback News independently if limits/errors regress
-> evaluate 5-minute cadence after measured runtime evidence
```

The live change window still requires explicit authorization.

## 9. Official-source snapshot used for this preflight

Rechecked on 2026-09-10:

- Cloudflare Workers Limits, last updated 2026-09-05.
- Cloudflare Cron Triggers, last updated 2026-09-04.
- Cloudflare D1 Limits/Pricing, current 2026 documentation.
- Cloudflare D1 free-tier enforcement changelog, 2026-09-01.
- Alpaca About Market Data API.
- Alpaca News articles endpoint reference.

Re-check again if the live change window occurs materially later or provider/account plan changes.
