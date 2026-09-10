# OrderScope — W1-001 Stage B Tiered Universe Local Handoff

Status: **Ready for local implementation/test — no live activation authorized**
Date: 2026-09-10
Depends on: `W1-001_STAGE_B_TIERED_UNIVERSE_BUDGET_REVISION_2026-09-10.md`
Reference authority: `stock_monitoring_v0.1_universe_spec.md`
Current implementation: `src/universe.ts`

## 1. Goal

Verify Stage-B budgets against the real `full-v0.1` cadence mix instead of treating all 105 instruments as 1-minute bars.

Do not change the Universe allocation unless a mismatch with the reference specification is discovered.

Expected current mapping:

```text
Tier A / 1Min  = 25
Tier B / 15Min = 28
Tier C / 1Day  = 52
Total          = 105
```

## 2. Required implementation/test work

### T1. Assert Universe/reference parity

Add tests that assert exact counts and representative symbols:

```text
1Min  = 25
15Min = 28
1Day  = 52
Total = 105
```

At minimum verify:

```text
NVDA = 1Min
AMD = 1Min
MRVL = 15Min
MU = 15Min
EWJ = 1Day
TLT = 1Day
BTCUSD = 1Min crypto
ETHUSD = 1Day crypto
```

### T2. Build a tier-aware workload estimator/fixture

Using the actual scheduler/calendar behavior, calculate per normal session day:

```text
planned bars by cadence
NEW bars
MATCHED/replayed observations
overlap observations
provider pages/attempts
D1 statements/queries
D1 rows written
```

Do not hard-code the planning estimate from the handoff as the test oracle; derive it from the real Universe and scheduler fixtures.

### T3. Measure write amplification

Separate row writes into:

```text
normalized_bar
bar_acceptance_receipt
bar_conflict
coverage/checkpoint
attempt/lease
latest digest
news_article
news_query_membership
news_checkpoint
```

Where exact per-table instrumentation is impractical, report a conservative measured total and identify unmeasured components explicitly.

### T4. Mixed full-v0.1 fixture

Add a fixture representing one normal day with the actual Tier A/B/C mix.

It must not require remote Alpaca or remote D1. Use fixture provider pages/calendar and local D1/Miniflare where applicable.

### T5. Overlap steady-state fixture

Run enough sequential ticks to expose the effect of:

```text
1Min overlap = 1 minute
15Min overlap = 15 minutes
1Day overlap = 1440 minutes
```

Measure how many duplicate observations create new acceptance receipts and how many row writes result.

### T6. Scheduler capacity/freshness

Current configured `ACQUISITION_MAX_JOBS_PER_TICK=1` must be evaluated against `full-v0.1`.

Report, by cadence:

```text
max backlog age
median backlog age if practical
whether eventual coverage completes
whether Tier A 1Min data freshness remains acceptable
```

Important: `1Min` is the data cadence. Do not assume it automatically promises one-minute end-to-end retrieval latency.

If one-job-per-tick cannot keep backlog bounded, report `Blocked` rather than increasing the setting without review.

### T7. Combined Market + News Stage-B budget

With the shared InvocationBudget instrumentation completed, report:

```text
normal total external subrequests/tick
worst reviewed external subrequests/tick
normal total D1 queries/tick
worst reviewed D1 queries/tick
```

Retain the OrderScope acceptance ceilings:

```text
external <= 40
D1 queries <= 40
```

### T8. Daily D1 write projection

Using measured steady-state fixtures, calculate:

```text
Market NEW-bar writes/day
Market MATCHED/replay writes/day
Market operational writes/day
News writes/day
combined writes/day
```

Report both:

```text
normal session day
shortened session day
```

Do not include historical catch-up in the normal-day number. Report catch-up separately.

## 3. Stop conditions

Return `Blocked` if any of the following is found:

- `src/universe.ts` materially differs from the reference Tier allocation;
- full-v0.1 scheduler backlog grows without bound at the accepted configuration;
- meeting freshness requires silently changing existing Market guarantees;
- combined external subrequests exceed 40;
- combined D1 queries exceed 40;
- projected normal-day D1 writes exceed the accepted operating envelope;
- News-disabled behavior changes Market semantics;
- tests require remote D1, live Worker, Cron mutation or credentials.

## 4. Evidence to return

```text
W1-001 Stage B tiered-universe status: Accepted | Provisional | Blocked
Universe count 1Min:
Universe count 15Min:
Universe count 1Day:
Universe total:
normal-day planned bars 1Min:
normal-day planned bars 15Min:
normal-day planned bars 1Day:
normal-day NEW bars:
normal-day MATCHED/replayed observations:
normal-day Market row writes:
normal-day News row writes:
normal-day other Worker row writes:
normal-day total D1 row writes:
shortened-day total D1 row writes:
catch-up projection (separate):
normal combined external subrequests/tick:
worst combined external subrequests/tick:
normal combined D1 queries/tick:
worst combined D1 queries/tick:
max backlog age 1Min:
max backlog age 15Min:
max backlog age 1Day:
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

## 5. Expected interpretation

A likely first-order normal-day volume is much closer to ~11.6k bars/day than 40.95k bars/day, because only Tier A is 1Min. This is a planning expectation, not a test oracle.

The decisive Stage-B numbers are the measured steady-state row-write amplification and scheduler backlog under the actual mixed cadence configuration.
