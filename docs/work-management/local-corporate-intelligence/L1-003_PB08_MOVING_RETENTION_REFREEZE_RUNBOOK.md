# OrderScope — L1-003 PB-08 Moving-Retention Re-freeze Runbook

Status: **OPERATING RUNBOOK**
Scope: L1-003 / PB-08 normal-scheduler catch-up only
Branch: `l1-003-local-market-recovery`

## Purpose

This runbook defines how to resume PB-08 when acquisition retention and the
authoritative US-equities session boundary have moved since the previous
snapshot.

PB-08 catch-up packets are intentionally short-lived. A packet must not be
reused merely because its source code still passes local tests. The active
retention floor and authoritative market session must be re-observed before
remote mutation.

This document is date-independent. Dates, versions, timestamps, and bar counts
shown in historical evidence or prior closeout documents are evidence of those
runs only; they are not reusable authorization inputs.

## What does not need to be repeated after a day boundary

Once separately accepted and recorded, the following evidence remains valid
unless a later finding explicitly invalidates it:

- PB-06 normal-scheduler handoff evidence;
- PB-07 two clean normal scheduler opportunities;
- historical local recovery evidence already accepted;
- reproducible provider-absence reproduction evidence;
- reproducible provider-absence acknowledgement implementation;
- reproducible provider-absence remote acceptance;
- schema and checkpoint semantics already covered by accepted local tests.

Do not repeat these steps merely because the calendar date changed.

## What must be refreshed before every new PB-08 remote catch-up window

The following sequence is mandatory whenever the previous PB-08 packet may have
aged, crossed a session boundary, crossed a retention boundary, or was not
executed immediately after it was frozen.

### 1. Confirm Cloudflare identity and D1 access

Verify the active Wrangler identity before interpreting remote state.

```bash
npx wrangler whoami

CLOUDFLARE_ENV=live-canary \
bash scripts/run-wrangler-with-env.sh d1 execute orderscope-state-live-canary \
  --remote \
  --command "SELECT 1 AS auth_ok;"
```

Required result:

```text
auth_ok = 1
```

Authentication failures such as Cloudflare API code 7403 are operational
failures, not checkpoint evidence. Do not re-freeze or mutate remote state until
authentication succeeds.

### 2. Take a fresh read-only remote snapshot

Run:

```bash
bash scripts/l1_003_pb08_fresh_remote_preflight.sh
```

This step must remain read-only.

Record at minimum:

- `observed_now`;
- Worker mode;
- Alpaca feed;
- News acquisition mode;
- current NVDA checkpoint and version;
- current competing canary checkpoints;
- unresolved acquisition attempts;
- recent NVDA attempts;
- latest market digest.

Required safe baseline:

```text
Worker mode = shadow
feed = iex
News acquisition = disabled
unresolved target attempts = 0
```

If any checkpoint contains an unresolved blocker, missing range, retry gate, or
unfinished attempt, stop and reconcile that state before constructing a new
frontier packet.

### 3. Recompute the moving retention floor

The logical retention floor is:

```text
retention_floor = observed_now - configured_retention
```

For the current live-canary configuration the configured retention is read from
deployment configuration; do not hard-code a calendar date into this runbook.

Treat a prior packet as stale when its required session open has moved before
the current retention floor.

Do not assume that the previous day's Regular session is still recoverable.

### 4. Select the authoritative target session

For an equity 1-minute REGULAR checkpoint:

1. inspect the authoritative market calendar used by the scheduler;
2. discard sessions that are fully before the retention floor;
3. choose the first authoritative REGULAR session that is still eligible for
   normal scheduler catch-up;
4. if the current session is still open, freeze a minimum frontier from the
   read-only snapshot;
5. if the session is already closed and fully retained, prefer the closed
   session close as the fixed frontier.

A packet must never span a closed-session gap.

### 5. Derive the new bounded NVDA catch-up packet

The packet must be derived from the fresh checkpoint, not copied from an older
document.

Freeze:

```text
entry checkpoint version
entry completeThrough
entry state
entry missingRanges
target session
target frontier
expected maximum scheduler opportunities
expected clean-attempt count or accepted range
retention guard
```

For 1-minute work, each provider request remains bounded by the configured
`maxBarsPerJob`.

Overlap semantics mean an accepted attempt may contain both inserted and
matched bars. Acceptance is based on clean coverage advancement, not inserted
count alone.

### 6. Re-freeze local tests and operational script

Update the PB-08 frozen competition test and the bounded change-window script so
they describe the same fresh packet.

The local model must cover the current competition snapshot, including the
current versions/states of competing canary symbols.

Do not keep stale constants for:

- prior session dates;
- prior session opens/closes;
- prior target checkpoint versions;
- prior exact bar-count sequence when the first retained point changed;
- prior moving frontier when the market has since closed.

### 7. Run local acceptance

Run:

```bash
bash -n scripts/l1_003_pb08_frontier_catchup_change_window.sh
bash scripts/l1_003_pb08_local_acceptance.sh
```

Required result:

```text
all PB-08 tests pass
typecheck passes
remoteMutation=false
```

A successful local run proves the frozen packet is internally consistent. It
does not authorize remote mutation.

### 8. Record remote readiness separately from authorization

Create or update the readiness evidence with:

- fresh remote snapshot identity;
- frozen entry checkpoint;
- target session/frontier;
- retention guard;
- local acceptance result;
- explicit statement that remote mutation has not yet been authorized.

Readiness and authorization are distinct states.

### 9. Require explicit authorization for each remote mutation window

A prior authorization does not automatically carry to a re-frozen packet.

Remote authorization must identify the newly frozen PB-08 change window.

PB-09, PB-10, pause/resume operations, historical recovery, retention changes,
universe changes, cron changes, and priority-policy changes remain out of scope
unless separately authorized.

## Remote change-window acceptance rules

During an authorized PB-08 normal-scheduler catch-up window:

- every target NVDA acquisition attempt must finish;
- every target NVDA attempt must be `SUCCEEDED`;
- `conflicts = 0`;
- `rejected = 0`;
- `missing = 0`;
- checkpoint state must remain `COMPLETE`;
- `missingRanges = []`;
- `blocker = null`;
- `retry_not_before = null`;
- `sourceObservedThrough = completeThrough`;
- checkpoint version progression must agree with the number of accepted clean
  NVDA attempts;
- the frozen target frontier must be reached within the bounded opportunity
  count.

If the market is still open, clean progression beyond a frozen minimum frontier
may be accepted only when the current packet explicitly defines that rule.

If the target session is closed, prefer an exact session-close frontier.

## Safe-close requirements

Regardless of success or failure, the window must return to the checked-in safe
baseline.

Verify:

```text
Worker mode = shadow
News acquisition = disabled
feed = iex
temporary control gates = closed
temporary secrets/tokens = removed
```

A failed packet that safe-closes without remote corruption is **not accepted**,
but it is a safe operational stop.

## Staleness rules

A PB-08 packet must be re-frozen when any of the following occurs before
execution:

- the retention floor passes the packet's required first retained instant;
- the target authoritative market session changes;
- the market transitions from open-session moving frontier to a closed session;
- NVDA checkpoint version or coverage changes;
- a competing canary checkpoint changes in a way that affects scheduler
  priority;
- a new unresolved attempt appears;
- a missing range, blocker, or retry gate appears;
- live-canary configuration affecting scheduling changes;
- the packet's explicit retention guard fails.

Crossing midnight by itself is not the criterion. The criterion is whether
time-dependent scheduler or retention inputs changed enough to invalidate the
frozen packet.

## Recommended local operator workflow

```text
START
  |
  v
Wrangler identity / D1 auth
  |
  v
Fresh PB-08 read-only preflight
  |
  v
Compute retention floor
  |
  v
Select authoritative retained REGULAR session
  |
  v
Freeze entry + target frontier + competition snapshot
  |
  v
Update test + bounded change-window script
  |
  v
Local acceptance
  |
  v
Record remote readiness
  |
  v
Explicit remote authorization
  |
  v
Bounded live change window
  |
  +--> failure --> safe close --> fresh preflight / reconcile
  |
  +--> success --> exact final evidence --> safe close
                                  |
                                  v
                           PB-08 closeout
                                  |
                                  v
                           PB-09 remains gated
```

## Automation improvement

The preferred follow-up improvement is to generate the PB-08 re-freeze inputs
from the fresh preflight automatically rather than manually editing dates and
versions.

A future helper should:

1. read the fresh remote checkpoint snapshot;
2. read the authoritative market calendar;
3. calculate the live retention floor;
4. select the first eligible retained REGULAR session;
5. distinguish open-session minimum-frontier mode from closed-session exact-close
   mode;
6. emit the frozen constants and expected attempt geometry;
7. refuse generation if unresolved attempts, missing ranges, blockers, or retry
   gates exist.

Such a helper should generate evidence/configuration only. It must not itself
authorize or perform the remote live mutation.

## Principle

PB-08 is governed by **fresh evidence, not calendar-date continuity**.

The safe sequence is always:

```text
observe -> re-freeze -> validate locally -> authorize explicitly -> mutate
```

Never:

```text
reuse yesterday's packet -> mutate
```
