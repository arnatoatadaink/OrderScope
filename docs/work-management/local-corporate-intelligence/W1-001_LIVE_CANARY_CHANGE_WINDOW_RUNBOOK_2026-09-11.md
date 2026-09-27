# OrderScope — W1-001 Live Canary Change-Window Runbook

Status: **Prepared — execution not authorized by this document**
Date: 2026-09-11
Task: `W1-001 — Worker/Schedule News metadata acquisition Live Canary`
Prerequisite: `W1-001 Stage B Accepted — local/non-live preflight`
Environment: `live-canary`

## 1. Purpose

This runbook defines the reviewed execution order for the first live AMD/NVDA metadata-only News Canary. It is a change-window procedure only. Creating this document does not authorize remote D1 mutation, deployment, Cron change, `WORKER_MODE` change, News activation, or full-v0.1 live acquisition.

The first live window must remain deliberately narrow:

- Worker environment: `live-canary` only;
- Universe: existing `canary-v0.1` only;
- News query symbols: `AMD,NVDA` only;
- News bodies: prohibited;
- News cadence: 5 minutes, provisional;
- Market Cron: retain existing one-minute trigger unless a separately reviewed change says otherwise;
- Market batch capacity: existing max two groups/tick;
- combined external ceiling: 40/invocation;
- combined D1 ceiling: 40/invocation.

## 2. Current reviewed baseline

Checked-in `live-canary` configuration currently has:

```text
WORKER_MODE=shadow
PREDICTION_MODE=shadow
UNIVERSE_PROFILE=canary-v0.1
ACQUISITION_MAX_JOBS_PER_TICK=2
NEWS_ACQUISITION_ENABLED=false
NEWS_ACQUISITION_CADENCE_MINUTES=5
NEWS_ACQUISITION_OVERLAP_MINUTES=15
NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL=2
NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN=200
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
```

The live change must not silently alter any other runtime variable.

## 3. Preconditions before opening the window

All of the following must be explicitly confirmed before any remote mutation:

1. Branch/commit under review is the intended release commit and includes W1-002..W1-005 accepted changes.
2. Local full tests, focused orchestration tests, typecheck, Wrangler dry-run/build, and `git diff --check` are green on that release commit.
3. `W1-001 Stage B Final Web Acceptance` remains current and no later code invalidated it.
4. `live-canary` D1 binding points only to `orderscope-state-live-canary`.
5. Required Alpaca credentials are already provisioned as secrets; they are not printed, copied into docs, committed, or exposed in logs.
6. Migration inventory is reviewed. `0007_news_metadata.sql` is the News schema change expected for the Canary. No unrelated migration is bundled into the same window.
7. Existing Worker state and current configuration are captured for rollback evidence.
8. D1 backup/export/restore responsibility is understood. This runbook does not claim PX0-004 backup/restore completion.
9. The operator has an immediate rollback path and authority to stop the Canary.
10. User approval for this exact live change window has been obtained after this runbook/checklist review.

If any precondition is false or uncertain, stop before remote mutation.

## 4. Intended configuration delta

The first live Canary should use the minimum delta necessary.

Expected live behavior delta:

```text
WORKER_MODE: shadow -> live
NEWS_ACQUISITION_ENABLED: false -> true
```

Retain:

```text
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
NEWS_ACQUISITION_CADENCE_MINUTES=5
NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL=2
NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN=200
ACQUISITION_MAX_JOBS_PER_TICK=2
```

Do not switch to `full-v0.1` in this window.

If the deployed Worker requires a different minimal delta for technical reasons, stop and review the exact difference before execution.

## 5. Change-window execution order

### CW-0 — Freeze and identify release

Record:

```text
release commit SHA
branch
operator
window start UTC/JST
current live-canary Worker version/deployment identifier
current Worker vars relevant to this task
current applied D1 migration state
```

No mutation occurs in CW-0.

### CW-1 — Remote D1 migration review/apply

Only if `0007_news_metadata.sql` is not already applied and the exact migration has been reviewed:

- inspect pending migrations for `live-canary` D1;
- verify only the expected News migration(s) are pending;
- apply only the reviewed migration set;
- verify News tables/indexes exist and existing Market tables remain intact;
- capture migration result.

Unexpected pending migration, schema drift, or migration failure => **STOP / rollback as applicable**. Do not proceed to Worker activation.

### CW-2 — Deploy reviewed build while still safe

Preferred sequencing is to deploy the reviewed code/config in a state that does not yet produce live News acquisition if the deployment system allows that separation.

Verify after deploy:

- Worker responds/starts normally;
- digest/health surface remains reachable;
- no secret/body leakage in logs;
- no unexpected News provider calls while News remains disabled;
- Market Canary behavior has not regressed.

Deployment/startup regression => rollback deployment before activation.

### CW-3 — Activate narrow Canary

Enable only the reviewed live state:

```text
WORKER_MODE=live
NEWS_ACQUISITION_ENABLED=true
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
```

Do not modify Cron cadence unless separately approved. The existing one-minute Cron drives Market scheduling; News internally selects its 5-minute cadence.

Record the exact activation timestamp.

### CW-4 — Initial observation gate

Observe the first several eligible scheduled invocations before declaring the window stable.

For each relevant invocation capture at least:

```text
scheduled_at
run_started_at
run_finished_at
marketExternalSubrequests
newsExternalSubrequests
totalExternalSubrequests
marketD1Queries
newsD1Queries
totalD1Queries
News planned/selected/completed/partial/failed jobs
News pages requested
article observations
new/duplicate/update/conflict counts
checkpoint state/complete-through progression
provider 429/5xx occurrence
Worker exceeded-resource / CPU error occurrence
```

Also capture News timing where articles exist:

```text
provider_published_at -> worker_retrieved_at
provider_published_at -> accepted_at
scheduled_at -> run_started_at
run_started_at -> run_finished_at
```

### CW-5 — Stability observation

Recommended first window evidence target:

- at least 12 eligible News cadence opportunities (approximately one hour at 5-minute cadence), **or**
- a shorter window only if a stop condition triggers.

This is an initial Canary evidence target, not a permanent production qualification period.

If no News article arrives, the window may still validate CPU/scheduler/D1/external/empty-result behavior, but it cannot establish real article-arrival lag. Record that limitation and schedule a later Canary observation instead of fabricating lag evidence.

## 6. Hard stop / rollback conditions

Immediately disable News and/or revert the Worker change if any of the following occurs:

- `totalExternalSubrequests > 40` or budget protection fails before the crossing call;
- `totalD1Queries > 40` or budget protection fails before the crossing statement;
- repeated exceeded-resource / CPU failures attributable to News or combined execution;
- Market Canary acquisition regresses materially after News activation;
- checkpoint falsely advances after page cap, 429, 5xx, invalid token, or incomplete symbol coverage;
- News body or provider response body is durably persisted;
- credential/auth material appears in logs, responses, D1, or artifacts;
- unexpected symbol expansion beyond AMD/NVDA News Canary or beyond `canary-v0.1` Market Universe;
- migration/schema corruption or incompatible D1 behavior;
- repeated News failure causes retry amplification or threatens D1/external headroom;
- operator cannot explain an unexpected runtime mutation.

A single provider 429/5xx is not by itself a rollback condition when handled as the accepted retryable/partial path and budgets remain safe.

## 7. Rollback order

Prefer the least invasive rollback that immediately removes risk.

### R1 — Independent News disable

First choice when Market remains healthy:

```text
NEWS_ACQUISITION_ENABLED=false
```

Confirm subsequent eligible ticks produce:

```text
News provider calls = 0
News acquisition mutations = 0
Market path remains operational
```

### R2 — Worker live-to-shadow rollback

If combined Worker behavior is unsafe or Market behavior cannot be trusted:

```text
WORKER_MODE=shadow
```

Confirm acquisition mutations cease according to shadow semantics.

### R3 — Deployment rollback

If the new build itself is the problem, restore the pre-window reviewed deployment/version and verify the previous digest/health behavior.

### R4 — D1 schema rollback/restore

Do not perform destructive reverse migration ad hoc. If schema restoration is required, stop and use a separately reviewed restore procedure. Preserve evidence first.

## 8. Evidence package after the window

Produce one immutable change-window report containing:

```text
release SHA
window start/end
operator approval reference
migration state before/after
deployment/version before/after
runtime variable delta
number of scheduled ticks observed
number of eligible News runs
CPU/exceeded-resource observations
external request p50/p95/max where available
D1 query p50/p95/max where available
D1 rows read/written observed/projected where available
scheduler delay/jitter distribution
News publication->retrieved/accepted lag samples
429/5xx/retry counts
partial/failure/conflict counts
checkpoint progression evidence
rollback performed: yes/no and reason
final state: News enabled/disabled; Worker live/shadow
```

Do not include credentials, auth headers, News bodies, or raw provider response bodies.

## 9. Exit states

The window must end in exactly one of these states:

- `CANARY_ACCEPTED_CONTINUE`: narrow AMD/NVDA News Canary may remain enabled under the reviewed configuration while additional runtime evidence accumulates;
- `CANARY_ACCEPTED_DISABLE`: evidence is sufficient for the window, but News is deliberately disabled pending later analysis;
- `ROLLED_BACK`: a stop condition triggered or confidence was insufficient;
- `INCONCLUSIVE`: infrastructure ran safely but required evidence (for example real article lag) was not observed.

None of these states authorizes `full-v0.1` live activation.

## 10. Post-window decisions

After evidence review, separately decide:

1. whether CPU/scheduler/D1/external behavior is acceptable;
2. whether 5-minute News cadence should remain, relax to 10/15 minutes, or require further observation;
3. whether AMD/NVDA News Canary remains enabled;
4. whether another Canary window is needed;
5. whether full-v0.1 Market/News activation should enter a new design/review gate.

Do not combine these decisions into the first change-window execution itself.
