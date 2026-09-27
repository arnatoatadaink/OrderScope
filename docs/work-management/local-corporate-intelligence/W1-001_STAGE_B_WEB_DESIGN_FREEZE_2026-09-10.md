# OrderScope — W1-001 Stage B Web-Side Design Freeze

Status: **Ready for local implementation/test — no live activation authorized**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Predecessor: `W1-001 Stage A` Accepted
Companion handoff: `docs/work-management/local-corporate-intelligence/W1-001_STAGE_B_PREFLIGHT_HANDOFF_2026-09-10.md`
Purpose: freeze Web-side design decisions so Local only needs implementation plus measured tests

## 1. Decision

Stage B remains a **non-live preflight**.

Web-side design work is complete enough to hand Local a bounded implementation/test task. The live AMD/NVDA Canary change window is not opened by this document.

The Stage-B objective is to prove that adding News to the existing scheduled Worker preserves a bounded combined invocation budget and an independent News rollback path.

## 2. Official platform/provider constraints frozen for this stage

Rechecked from official documentation on 2026-09-10.

### Cloudflare Workers Free

Design limits:

```text
external subrequests per invocation = 50
CPU time per Cron invocation         = 10 ms
Cron wall duration                   = 15 min
Cron Triggers per account            = 5
requests per day                     = 100,000
```

### Cloudflare D1 Free

Design limits:

```text
queries per Worker invocation = 50
rows read per day              = 5,000,000
rows written per day           = 100,000
max database size              = 500 MB
account storage                = 5 GB
```

Free-tier daily D1 row limits are enforced and queries fail after the daily allowance is exceeded until reset.

### Alpaca News

Official News REST endpoint:

```text
GET https://data.alpaca.markets/v1beta1/news
```

Relevant contract:

```text
symbols         = comma-separated symbol list
limit           = 1..50 articles/page
include_content = boolean
page_token      = provider pagination token
429             = rate limited; inspect X-RateLimit-* headers
500             = retryable provider failure class
```

Stage B must keep `include_content=false` and must not persist a body even if a provider response contains content unexpectedly.

## 3. Engineering safety envelope

Cloudflare hard limits are 50 external subrequests and 50 D1 queries per invocation. Stage B must not design directly to those limits.

Freeze the reviewed **combined acceptance ceiling** at:

```text
combined external subrequests <= 40 per scheduled invocation
combined D1 queries           <= 40 per scheduled invocation
```

This is an OrderScope engineering ceiling, not a Cloudflare platform value. It reserves 20% headroom for error-path, lease, checkpoint, digest, redirect, or incidental operations.

If the existing Market Bars worst reviewed fixture alone leaves insufficient room for the minimum News budget below, Local must return `Blocked`; do not weaken Market Bars guarantees.

## 4. News request/page budget

Freeze Stage-B Canary defaults as:

```text
Canary symbols             = AMD,NVDA
News cadence               = 5 minutes
News REST page limit       = 50 articles
maxPagesPerSymbol          = 2
max raw article observations/run = 200
```

Rationale:

- per-symbol query is retained so query-symbol membership remains explicit and is not inferred from provider symbol tags;
- two symbols × two pages means at most four Alpaca News fetches per News run;
- 50 article/page is the provider maximum;
- duplicate provider IDs across AMD/NVDA must merge at durable identity, so durable unique rows can be below 200;
- hitting page 2 with another page token does not authorize page 3 during that run.

When the cap is reached with more provider data remaining:

```text
result = partial/retryable
completeThrough must not falsely advance beyond proven complete coverage
next scheduled bounded run resumes from accepted checkpoint/overlap
```

Do not skip pages or silently drop overflow to report success.

## 5. Combined subrequest budget algorithm

Stage B instrumentation must count Market and News external requests separately and in total.

Required fields:

```text
marketExternalSubrequests
newsExternalSubrequests
totalExternalSubrequests
```

Acceptance:

```text
totalExternalSubrequests <= 40
```

News planning must be fail-closed when remaining combined budget cannot safely execute the intended News unit.

Minimum normal News unit:

```text
AMD first page + NVDA first page = 2 external requests
```

Maximum Stage-B News fetch unit:

```text
AMD up to 2 pages + NVDA up to 2 pages = 4 external requests
```

Do not issue a second-page request if doing so would exceed the combined OrderScope ceiling after already observed Market usage.

Provider retries also consume the same external-request envelope. A retry policy must therefore obey the remaining invocation budget; exhausting the budget yields retryable/partial state for the next Cron tick.

## 6. D1 operation design

Required instrumentation:

```text
marketD1Queries
newsD1Queries
totalD1Queries
```

Acceptance:

```text
totalD1Queries <= 40
```

The News path must not require one or more independent D1 queries per article in a way that makes query count scale linearly to 200 and violate the invocation ceiling.

Preferred implementation characteristic:

```text
D1 query count scales with pages/batches/checkpoint transitions,
not directly with every article observation.
```

Use indexed provider-article identity and bounded batch/upsert operations where the existing repository architecture permits. Local may choose the exact statement/batch arrangement, but must return measured query counts for all required fixtures.

Required D1 fixture shapes:

1. no new article;
2. one new article;
3. same provider article returned for both AMD and NVDA;
4. update/revision;
5. two-page/symbol burst;
6. page-cap partial result.

## 7. Identity and query membership

Provider article ID remains durable primary article identity.

Required behavior:

```text
AMD query -> provider article 123
NVDA query -> provider article 123
=> one durable article identity
=> query membership contains AMD and NVDA
```

Do not use headline equality as primary identity.

Do not infer query membership from headline text.

Provider `symbols` remain source metadata and are distinct from OrderScope query-symbol membership.

## 8. Checkpoint and overlap rule

Preserve the accepted Stage-A checkpoint semantics.

Stage B must prove:

```text
successful fully exhausted bounded window -> may advance completeThrough
page-cap hit                         -> partial; no false complete advance
429/5xx                              -> retryable; no false complete advance
page-token loop/invalid token        -> fail closed; no false complete advance
missed Cron tick                     -> next bounded overlap recovers
```

The exact overlap value already implemented in Stage A remains configurable. Stage B should report the configured value rather than replace it solely for preflight.

Historical 30-day catch-up is not part of this task and remains gated by `SMOKE-007`.

## 9. Five-minute cadence semantics

The 5-minute value is an initial Canary polling configuration, not evidence of platform or provider necessity.

N1-006 showed:

```text
4/4 reference recall
0 misattribution
provider-vs-SEC signed lag median = -44826.5 s
```

That benchmark establishes provider discovery quality, not Worker polling latency.

Live Canary later measures:

```text
provider_published_at -> worker_retrieved_at
provider_published_at -> accepted_at
scheduled_at           -> run_started_at
run_started_at         -> run_finished_at
```

Only that runtime evidence may justify relaxing 5 minutes to 10/15 minutes or tightening it.

## 10. CPU boundary

Cloudflare Free Cron CPU limit is 10 ms.

No Local unit test or `tsc` run may be used to claim production CPU acceptance.

Stage B Local responsibility is limited to:

- keeping parsing/dedup bounded by page/article caps;
- avoiding unbounded in-memory scans;
- avoiding accidental repeated serialization or article-body processing;
- exposing sufficient runtime counters for Canary observation.

Production CPU acceptance remains a live-Canary observation gate with immediate News-disable rollback on repeated exceeded-resource behavior.

## 11. Required dry-run budget surface

Dry-run/test output must expose enough data to review one combined scheduled tick without mutation.

Minimum conceptual surface:

```text
market:
  plannedJobs
  externalSubrequests
  d1Queries
news:
  enabled
  cadenceMinutes
  plannedJobs
  pagesRequested
  rawArticleObservations
  externalSubrequests
  d1Queries
combined:
  externalSubrequests
  d1Queries
  externalBudgetCeiling = 40
  d1BudgetCeiling = 40
  withinBudget
```

Exact object field names may follow repository conventions. Do not expose headline, URL, body, credentials, or auth headers in this budget surface.

## 12. Mandatory Stage-B fixtures

Local must implement/run at least:

1. ordinary 5-minute boundary, Market idle/low + one-page News each symbol;
2. same boundary with Market Bars jobs due;
3. AMD/NVDA two-page News burst;
4. second-page response indicates page 3 exists -> partial at cap;
5. duplicate provider article across symbols;
6. article update/revision;
7. News 429 while Market path remains valid;
8. News 500 while Market path remains valid;
9. invalid/looping page token fail-closed;
10. existing checkpoint overlap recovery after one missed tick;
11. News disabled exact Market-only regression;
12. dry-run mutation count exactly zero;
13. worst reviewed combined external-subrequest budget fixture;
14. worst reviewed combined D1-query budget fixture;
15. body persistence and secret/log scans clean.

## 13. Acceptance values Local must return

```text
W1-001 Stage B status: Accepted | Provisional | Blocked
files changed:
focused tests:
full tests:
typecheck:
diff check:
configured cadence minutes:
configured overlap minutes:
configured max pages/symbol: 2
configured provider page limit: 50
configured max raw observations/run: 200
normal market external subrequests:
normal news external subrequests:
normal combined external subrequests:
worst market external subrequests:
worst news external subrequests:
worst combined external subrequests:
normal market D1 queries:
normal news D1 queries:
normal combined D1 queries:
worst market D1 queries:
worst news D1 queries:
worst combined D1 queries:
projected News rows read/tick:
projected News rows written/tick:
page-cap partial checkpoint behavior: pass/fail
429 retryable checkpoint behavior: pass/fail
500 retryable checkpoint behavior: pass/fail
page-token loop behavior: pass/fail
cross-symbol identity merge: pass/fail
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

## 14. Stage-B acceptance decision rule

Web review may mark Stage B `Accepted` only if all of the following are true:

```text
focused/full/typecheck/diff required checks pass
worst combined external subrequests <= 40
worst combined D1 queries <= 40
maxPagesPerSymbol = 2 or a stricter reviewed value
provider page limit <= 50
page-cap/429/500/token-loop do not falsely advance checkpoint
cross-symbol duplicate persists once with memberships preserved
News disabled restores Market-only behavior
News-disabled provider calls = 0
News-disabled News mutations = 0
dry-run mutations = 0
body scan clean
secret/log scan clean
no remote/live operation was required
```

If a stricter page cap is required to remain within budget, Local may return it with evidence. Raising above 2 pages/symbol requires a new Web review and is not authorized by this freeze.

## 15. Explicit non-goals

Do not during Stage B:

- deploy Worker;
- modify Cron Trigger registration;
- apply a D1 migration remotely;
- enable real Alpaca News from deployed infrastructure;
- change Worker Shadow/live state;
- expand beyond AMD/NVDA;
- perform historical catch-up;
- store News bodies;
- relax existing Market Bars guarantees;
- claim production CPU safety from Local timing.

## 16. Gate after Local returns Stage-B evidence

```text
Stage A Accepted
+ Stage B Local evidence satisfies this freeze
-> Web acceptance review
-> prepare explicit AMD/NVDA live Canary change-window runbook
-> user approval for live change window
-> apply only reviewed migration/config
-> AMD/NVDA metadata-only Canary
-> measure CPU/subrequests/D1/runtime News lag
-> independently disable News if regression occurs
-> evaluate 5-minute cadence from measured runtime data
```

No step after Web acceptance review is implicitly authorized by this document.

## 17. Official references snapshot

Rechecked 2026-09-10:

- Cloudflare Workers Limits: `https://developers.cloudflare.com/workers/platform/limits/`
- Cloudflare Workers Pricing: `https://developers.cloudflare.com/workers/platform/pricing/`
- Cloudflare D1 Limits: `https://developers.cloudflare.com/d1/platform/limits/`
- Cloudflare D1 free-tier enforcement changelog: `https://developers.cloudflare.com/changelog/post/2026-09-01-d1-free-tier-limit-enforcement/`
- Alpaca News articles endpoint: `https://docs.alpaca.markets/us/reference/news-3`

Recheck official values before a materially later live change window or after any plan/account change.
