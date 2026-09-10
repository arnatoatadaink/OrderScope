# OrderScope — W1-001 Live Canary Reopen Local Handoff

Status: **Ready for reviewed Local execution / live change window only after explicit approval**
Date: 2026-09-11
Task: `W1-001 — Worker/Schedule News metadata acquisition Live Canary reopen`
Depends on:
- `W1-001 Stage B` Accepted (local/non-live preflight)
- `W1-005` Accepted (multi-symbol tier scheduler)
- `W1-006` Accepted (News cadence eligibility repair)

## 1. Purpose

Resume the previously rolled-back AMD/NVDA metadata-only News Canary after the cadence eligibility defect has been repaired and locally accepted.

The previous live window established that:
- `0007_news_metadata.sql` is already applied to the isolated live-canary D1 database;
- Alpaca credentials were repaired after the first 401 and a direct calendar request returned HTTP 200;
- one resumed Market tick completed safely with `external=1/40` and `D1=21/40`;
- the remaining blocker was the exact-millisecond cadence predicate;
- final remote state was restored to `WORKER_MODE=shadow`, `NEWS_ACQUISITION_ENABLED=false`, `UNIVERSE_PROFILE=canary-v0.1`.

W1-006 replaced the exact epoch-millisecond modulo condition with UTC minute-bucket cadence eligibility. Local evidence supplied by the operator:

```text
focused news-schedule tests: 7 passed
full TypeScript suite:      128 passed
failures:                   0
diff:                       clean
live-canary dry-run vars:
  WORKER_MODE=shadow
  NEWS_ACQUISITION_ENABLED=false
  UNIVERSE_PROFILE=canary-v0.1
  NEWS_ACQUISITION_CADENCE_MINUTES=5
  NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
```

## 2. Scope of this reopen

The live experiment is limited to:

```text
environment: live-canary
Market Universe: canary-v0.1
News symbols: AMD,NVDA
News type: metadata only
News cadence: 5 minutes (provisional)
Cron: existing * * * * *
ACQUISITION_MAX_JOBS_PER_TICK: 2
combined external ceiling: 40/invocation
combined D1 ceiling: 40/invocation
```

Do not switch to `full-v0.1` during this Canary. Do not change the Cron cadence. Do not persist News bodies. Do not perform historical catch-up.

## 3. Pre-window verification

Before any live mutation, record:

```bash
git checkout docs/mermaid-conventions-v0.1
git pull --ff-only
git status --short
git rev-parse HEAD

node --test --experimental-strip-types src/news-schedule.test.ts
npm test
npm run typecheck
npm run cf-typegen
npm run deploy:check -- --env live-canary
git diff --check
```

Expected:

```text
focused: 7 passed
full: 128 passed (or higher if only reviewed tests were added afterward)
typecheck: pass
cf typegen: pass
dry-run/build: pass
diff check: pass
working tree: clean
```

If any result differs because of an unrelated new commit, stop and reconcile before opening the change window.

## 4. Remote preflight

Confirm, without exposing secret values:

- target is `live-canary`;
- D1 binding resolves to `orderscope-state-live-canary`;
- no new pending migration beyond the already-applied reviewed schema;
- required secret names exist;
- current Worker is in `shadow`;
- News is disabled;
- Universe remains `canary-v0.1`;
- Cron remains one minute;
- no unreviewed runtime variable delta exists.

Also confirm the Alpaca calendar/auth path returns a healthy result before enabling News. If authentication regresses, stop without enabling News.

## 5. Reopen sequence

### Step A — deploy reviewed W1-006 release in safe state

Deploy the reviewed release to `live-canary` while retaining:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
```

Record deployment version ID and release commit SHA.

Wait for/inspect at least one scheduled shadow invocation and verify health/log shape remains normal. Do not claim live acceptance from shadow execution.

### Step B — activate bounded Canary

Only inside the explicitly approved change window, change the reviewed activation pair to:

```text
WORKER_MODE=live
NEWS_ACQUISITION_ENABLED=true
```

Keep every other reviewed variable unchanged.

Record activation deployment/version ID and timestamp.

### Step C — verify cadence repair on first eligible bucket

The repaired planner must allow scheduler timestamps such as:

```text
HH:00:15Z
HH:05:15Z
HH:10:15Z
...
```

when their UTC minute bucket is divisible by five.

On the first expected five-minute opportunity, confirm News is actually planned. A stable non-zero seconds offset must no longer suppress News planning.

If News remains configured enabled but repeatedly plans zero jobs across an otherwise eligible session/bucket, stop and roll back. Do not alter Cron as a workaround.

## 6. Required observation window

Collect at least **12 eligible five-minute News opportunities** (nominally one hour) unless a hard-stop condition fires first.

For each eligible opportunity capture only operational metadata/counters, not News bodies or credentials.

Required fields where available:

```text
scheduledAt
runStartedAt
runFinishedAt
market jobs planned/selected/completed/failed
news jobs planned/selected/completed/failed
news pages requested
news raw article observations
news inserted/updated/duplicate/conflict counts
marketExternalSubrequests
newsExternalSubrequests
totalExternalSubrequests
marketD1Queries
newsD1Queries
totalD1Queries
withinBudget
provider published_at -> retrieved_at lag
provider published_at -> accepted_at lag
scheduler delay = runStartedAt - scheduledAt
run duration
CPU/resource exceeded indicators
```

## 7. Hard stop conditions

Immediately disable News and begin rollback if any of these occurs:

- combined external subrequests would exceed 40;
- combined D1 queries would exceed 40;
- budget fail-before-crossing behavior is violated;
- repeated Worker exceeded-resource/CPU failures;
- Market path regresses when News is enabled;
- News causes false checkpoint advancement after 429/5xx/page-cap/token-loop;
- unauthorized symbol expansion beyond AMD/NVDA;
- News body or credential/auth-header leakage;
- D1/schema corruption or unexpected destructive mutation;
- cadence repair still fails to produce eligible News jobs;
- an unreviewed technical/configuration delta is required to continue.

Do not improvise a new Cron, Universe, cadence, page limit, or budget ceiling inside the active window.

## 8. Rollback order

Preferred rollback when Market remains healthy:

1. set `NEWS_ACQUISITION_ENABLED=false`;
2. verify a subsequent invocation has zero News provider calls/mutations;
3. if further isolation is required, set `WORKER_MODE=shadow`;
4. if release-level regression remains, restore the last known-good Worker version;
5. leave additive migration `0007_news_metadata.sql` in place unless a separately reviewed destructive migration is explicitly authorized.

Always finish by recording the actual final remote state.

## 9. Acceptance checklist

Mark each item with measured evidence.

### Release / safety

- [ ] Reviewed W1-006 commit deployed
- [ ] Local focused test passed
- [ ] Full test suite passed
- [ ] Typecheck passed
- [ ] Wrangler dry-run/build passed
- [ ] Diff clean / working tree clean
- [ ] D1 binding points to live-canary DB
- [ ] No unexpected pending migration
- [ ] Secret names present without value exposure
- [ ] Universe remains `canary-v0.1`
- [ ] Cron remains `* * * * *`

### Cadence repair

- [ ] Non-zero seconds-offset five-minute bucket produced a News job
- [ ] Ineligible minute did not produce a News job
- [ ] No Cron change was needed

### Runtime budget

- [ ] Every reviewed invocation `totalExternalSubrequests <= 40`
- [ ] Every reviewed invocation `totalD1Queries <= 40`
- [ ] Budget crossing is rejected before issue
- [ ] Market remains healthy while News runs

### News correctness

- [ ] At least 12 eligible opportunities observed, unless stopped by hard condition
- [ ] AMD/NVDA only
- [ ] Metadata only / no body persistence
- [ ] Provider article identity and query memberships behave as designed
- [ ] 429 path remains retryable without false completion if encountered
- [ ] 5xx path remains retryable without false completion if encountered
- [ ] Page-cap/token-loop does not false-complete if encountered
- [ ] No secret/log leakage

### Runtime measurements

- [ ] Scheduler delay/jitter captured
- [ ] Run duration captured
- [ ] CPU/resource indicators reviewed
- [ ] Real Alpaca paging behavior captured
- [ ] News publication -> retrieval lag captured where articles exist
- [ ] News publication -> acceptance lag captured where articles exist
- [ ] D1 write-volume evidence captured sufficiently for post-Canary projection

### Final disposition

Choose exactly one:

```text
ACCEPTED       = Canary met all applicable acceptance criteria
INCONCLUSIVE   = no hard failure, but insufficient live evidence (for example no article arrivals)
ROLLED_BACK    = hard stop triggered and safe rollback completed
BLOCKED        = a new reviewed technical/config delta is required before retry
```

## 10. Required return report

Update/create the Live Canary report with at least:

```text
release commit:
pre-window Worker version:
safe deploy version:
activation version:
rollback version (if any):
window start/end UTC/JST:
final Worker mode:
final News enabled state:
final Universe profile:
final Cron:
eligible News opportunities observed:
News jobs planned/completed/failed:
first non-zero-seconds eligible timestamp:
normal external/tick:
max external/tick:
normal D1/tick:
max D1/tick:
Market regression observed: yes/no
CPU/resource failure observed: yes/no
News bodies persisted: no
secret leakage observed: no
runtime News lag summary:
scheduler jitter summary:
D1 rows/write projection evidence:
final disposition: ACCEPTED / INCONCLUSIVE / ROLLED_BACK / BLOCKED
reason:
```

Then update `LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` with the final disposition and next CP gate.

## 11. Important authorization boundary

This handoff is an execution plan, not standing authorization for unrelated live changes.

The approved window, when explicitly opened by the user/operator, covers only the reviewed `live-canary` AMD/NVDA metadata-only activation described above. It does not authorize:

- `full-v0.1` live activation;
- Cron change;
- News cadence change from 5 minutes;
- provider/page-limit/budget-ceiling expansion;
- historical catch-up / `SMOKE-007`;
- destructive D1 migration;
- News body persistence;
- expansion beyond AMD/NVDA;
- production rollout outside `live-canary`.
