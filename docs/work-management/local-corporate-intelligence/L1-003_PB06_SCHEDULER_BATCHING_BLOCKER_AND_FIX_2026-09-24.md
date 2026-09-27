# OrderScope — L1-003 PB-06 Scheduler Batching Blocker and Fix

Status: **LOCAL FIX IMPLEMENTED — acceptance pending / no remote mutation**
Date: 2026-09-24 JST
Environment: `live-canary`

## Finding

PB-06 read-only preflight passed the handoff checkpoint and retention gates, but
review of the normal scheduler execution path found a latent mismatch:

```text
planner max range       100 one-minute bars per instrument
batch helper            may merge several compatible instruments
executor maxBars        100 bars for the entire provider response
```

For the Sep23 handoff, AMD, QQQ, SPY and NVDA can share the same stock range.
A four-symbol provider response can therefore contain up to 400 bars while the
executor rejects any page/campaign exceeding 100 bars.

A second issue is that batching can reorder jobs after the fairness priority
step, so the configured oldest-first priority is not guaranteed at execution.

PB-06 must not activate this path unchanged.

## Minimal safety fix

The normal scheduled execution path now bypasses provider batching and executes
the already-prioritized single-instrument jobs directly:

```text
SchedulePolicy
  -> prioritizeAcquisitionJobs
  -> slice(maxJobsPerTick)
  -> execute single-instrument jobs
```

Unchanged:
- Universe `canary-v0.1`;
- Cron `* * * * *`;
- max jobs/tick = 2;
- max bars/job = 100;
- retention = 1,440 minutes;
- provider feed = IEX;
- News disabled;
- historical recovery disabled at baseline.

The generic batch helper is retained for future work but is not used by the
normal scheduler until an aggregate batch bar ceiling is explicitly designed.

## Frozen PB-06 opportunity expectation

Using the read-only competition snapshot and unchanged oldest-first priority,
the locally frozen expectation is:

```text
opportunity 1: AMD + QQQ
opportunity 2: SPY + BTCUSD
opportunity 3: NVDA + next eligible canary
```

NVDA's expected first handoff job remains:

```text
range       2026-09-23T13:30:00.000Z -> 2026-09-23T15:10:00.000Z
mode        INCREMENTAL
due reason  FORWARD_COVERAGE
checkpoint  v58 / 2026-09-22T20:00:00.000Z
```

The three-opportunity statement is a local planner expectation, not remote
acceptance evidence. Remote execution must still be separately authorized and
observed.

## Local acceptance

Run:

```bash
git pull --ff-only
bash scripts/l1_003_pb06_local_acceptance.sh
```

Acceptance requires the PB-06 handoff test, schedule tests, priority tests,
executor tests, TypeScript typecheck and diff check to pass.

## Authority boundary

No Worker deployment, live-mode activation, provider call, D1 mutation,
scheduler activation, Cron change, Universe change or PB-07 action is
authorized by this document.
