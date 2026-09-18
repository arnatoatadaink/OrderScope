# OrderScope — W1-006 News Cadence Eligibility Repair Local Handoff

Status: **Ready for Local / non-live implementation**
Date: 2026-09-11
Task: `W1-006 — Repair News cadence eligibility for Cron second-offset execution`
Depends on: `W1-001 Stage B Accepted`; Live Canary report `ROLLED_BACK / Blocked`

## 1. Why this task exists

The first W1-001 Live Canary change window established that the production Cron trigger may execute at a stable non-zero seconds offset. The observed sequence ended in `:15.000Z`. The current News planner requires exact millisecond alignment:

```ts
const cadenceMs = config.cadenceMinutes * 60_000;
if (nowMs % cadenceMs !== 0) return [];
```

With a five-minute cadence, `19:40:15Z` therefore never becomes eligible even though it belongs to the intended `19:40` cadence minute. The Canary produced a healthy Market tick after credential repair but zero News jobs, so the live window was correctly rolled back.

This is a local scheduler-boundary repair only. Do not reopen the live Canary, deploy a Worker, mutate remote D1, change Cron, change Worker mode, or enable News live under this task.

## 2. Frozen repair semantics

Interpret cadence eligibility by the **UTC minute bucket represented by the scheduled timestamp**, not by exact seconds/milliseconds within that minute.

For a 5-minute cadence:

```text
19:40:00Z -> eligible
19:40:15Z -> eligible
19:40:59.999Z -> eligible
19:41:00Z -> not eligible
19:44:59Z -> not eligible
19:45:15Z -> eligible
```

Recommended implementation shape:

```ts
const minuteBucket = Math.floor(nowMs / 60_000);
if (minuteBucket % config.cadenceMinutes !== 0) return [];
```

An equivalent implementation is acceptable if it has the same semantics and remains deterministic.

Do not round to the nearest cadence bucket. A timestamp in minute `19:43` must not become eligible merely because it is closer to `19:45` than `19:40`.

## 3. Window and checkpoint semantics remain unchanged

This repair must not alter:

- News observation sessions (`PREMARKET`, `REGULAR`, `AFTER_HOURS`);
- configured five-minute cadence value;
- overlap minutes;
- AMD/NVDA Canary symbol set;
- metadata-only behavior;
- provider page limit / page cap;
- News durable identity and query membership;
- checkpoint complete-through semantics;
- 429 / 5xx / invalid-token fail-closed behavior;
- shared external/D1 budget ceilings;
- Market scheduler behavior;
- multi-symbol Market batching.

The actual `requestedRange.endExclusive` may continue to use the real scheduled timestamp/session boundary. This task changes **eligibility**, not historical timestamp truth.

## 4. Required focused fixtures

At minimum add tests for:

1. exact `:00` seconds on a five-minute minute is eligible;
2. `:15` seconds on that same minute is eligible;
3. `:59.999` on that same minute is eligible;
4. a non-cadence minute with the same `:15` seconds is not eligible;
5. next five-minute bucket with `:15` seconds is eligible;
6. session-open/session-close rules remain unchanged;
7. disabled News remains ineligible regardless of bucket;
8. invalid `Date` still returns no job;
9. checkpoint already at/after boundary still returns no job;
10. deterministic job identity/range behavior remains stable for repeated identical inputs.

Also retain existing page-cap, retry, token-loop, identity, body-storage, secret/log, budget, News-disabled and Market regression suites.

## 5. Acceptance conditions

Local acceptance requires all of the following:

```text
five-minute eligible minute with :15 seconds -> one News plan when otherwise due
non-cadence minute with :15 seconds         -> zero News plans
no rounding into adjacent cadence minute
session gating                              -> unchanged
checkpoint advancement semantics            -> unchanged
News-disabled provider calls                -> 0
News-disabled News mutations                -> 0
combined external ceiling                   -> <= 40 retained
combined D1 ceiling                         -> <= 40 retained
focused tests                               -> pass
full tests                                  -> pass
typecheck                                   -> pass
Wrangler live-canary dry-run/build          -> pass
git diff --check                            -> pass
remote D1 applied                           -> no
Worker deployed                             -> no
Cron changed                                -> no
Worker mode changed                         -> no
News live enabled                           -> no
```

## 6. Stop conditions

Stop and report rather than broadening the task if any repair requires:

- changing Cron expression;
- changing the News cadence from 5 minutes;
- changing Market scheduling/batching;
- changing News checkpoint identity or durable schema;
- changing the shared 40/40 budget ceilings;
- changing the authoritative Universe;
- remote D1 mutation;
- Worker deployment;
- live activation.

## 7. Return report

Return:

```text
W1-006 status: Accepted / Provisional / Blocked
eligibility rule implemented:
:00 eligible fixture:
:15 eligible fixture:
:59.999 eligible fixture:
non-cadence :15 fixture:
session-boundary regression:
checkpoint regression:
News-disabled regression:
focused tests:
full tests:
typecheck:
Wrangler live-canary dry-run/build:
git diff --check:
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
News live enabled: no
```

## 8. Critical-path transition

```text
W1-001 Stage B Accepted
  -> Live Canary #1 ROLLED_BACK
       -> 401 credential blocker repaired
       -> cadence eligibility blocker found
  -> W1-006 cadence eligibility repair (this task)
  -> Web/local acceptance review
  -> redeploy reviewed build in shadow / News disabled under a new approved change window
  -> reopen AMD/NVDA News Live Canary
  -> collect >= 12 eligible five-minute opportunities unless a hard stop occurs
```

No live action is authorized by this handoff.
