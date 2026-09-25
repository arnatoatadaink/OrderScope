# OrderScope — L1-003 PB-07 / PB-08 Local Handoff

Status: **LOCAL HANDOFF — PB-07 accepted, PB-08 frontier catch-up prepared but not executed**
Date: 2026-09-25 JST
Branch: `l1-003-local-market-recovery`

## 1. Executive summary

PB-07 normal-scheduler stability observation is complete and accepted remotely.

PB-08 entry-packet preparation is locally accepted, including a scheduler fix
for resuming an equity checkpoint whose previous session has moved outside the
normal 1,440-minute retention window.

The next runtime operation is a bounded PB-08 normal-scheduler frontier catch-up
for NVDA. It has been explicitly authorized by the operator, but it has **not**
been executed successfully yet.

The work is being handed off to local execution. No PB-09 / PB-10 pause-resume
experiment is authorized by this handoff.

## 2. PB-07 accepted state

Final PB-07 evidence:

```text
coverage key             NVDA|1Min|REGULAR|stock:iex:raw
checkpoint               v61
complete through         2026-09-23T18:28:00.000Z
source observed through  2026-09-23T18:28:00.000Z
state                    COMPLETE
missing ranges           []
blocker                  null
retry_not_before         null
unresolved attempts      0

canonical bars           199
clean NVDA attempts      2
bad NVDA attempts        0
clean live digests       2
non-clean summaries      0
```

Accepted PB-07 live scheduler executions:

```text
2026-09-24T14:39:23Z
  2026-09-23T15:09:00Z -> 2026-09-23T16:49:00Z
  inserted=99 matched=1
  conflicts=0 rejected=0 missing=0

2026-09-24T14:40:23Z
  2026-09-23T16:48:00Z -> 2026-09-23T18:28:00Z
  inserted=99 matched=1
  conflicts=0 rejected=0 missing=0
```

Final deployment returned to the checked-in safe baseline:

```text
WORKER_MODE              shadow
PREDICTION_MODE          shadow
ALPACA_FEED              iex
UNIVERSE_PROFILE         canary-v0.1
NEWS_ACQUISITION_ENABLED false
HISTORICAL_RECOVERY_ENABLED false
Cron                     * * * * *
```

PB-07 status: **ACCEPTED**.

## 3. PB-08 local preparation

PB-08 must freeze a valid `checkpoint_before_pause` before any Phase B
pause/resume experiment.

A checkpoint that is healthy but materially behind the current Regular-session
frontier is not sufficient. A short pause from such a state would mix old
catch-up work with the fresh pause-created gap.

Therefore PB-08 requires:

```text
PB-07 accepted
  -> normal-scheduler frontier catch-up
  -> immediate read-only frontier verification
  -> freeze checkpoint_before_pause
  -> freeze calendar/session/config/Universe identity
  -> freeze exact pause duration and expected gap
  -> PB-08 close
  -> PB-09 separate authorization
```

## 4. Scheduler retention-cross-session defect found and fixed

Fresh PB-08 preflight found:

```text
observed_now       2026-09-25T03:03:11.000Z
NVDA checkpoint    v61 / 2026-09-23T18:28:00.000Z
state              COMPLETE
missing ranges     []
blocker            null
unresolved         0
Worker             shadow
News               disabled
feed               iex
Universe           stock-monitoring-canary-v0.1
```

At this point the v61 checkpoint belonged to a previous Regular session that
had moved outside the active 24-hour retention floor, while the September 24
Regular session was still retained.

The prior session-selection logic could select the expired previous session and
then eliminate the planned job after retention clamping.

The accepted fix is:

```text
session selection anchor
  = max(progression checkpoint, retention floor)
```

This lets a stale prior-session equity checkpoint resume at the first
authoritative Regular session that is still inside retention, without:
- widening retention;
- manually advancing the checkpoint;
- using historical recovery;
- changing Universe/fairness;
- changing Cron.

Relevant commits:

```text
0155ffd9e28f3ba2dcda77061703c7b01911f6f5
  retained-session equity resume regression test

25461be1afd6b69a8f4edaa46ed5ba2232fd3a71
  retained-session scheduler fix
```

## 5. PB-08 local acceptance

Latest local acceptance:

```text
tests        30
pass         30
fail         0
typecheck    PASS
remoteMutation=false
```

Accepted properties:
- retained-session equity resume regression passes;
- frozen PB-08 catch-up planning passes;
- unchanged fairness simulation passes;
- PB-07 regression coverage remains green.

Relevant commits:

```text
05cb31c438750bd82cb62d4dd551e981498c6904
  PB-08 catch-up refreeze at Sep25 snapshot

3cdf04c1358b1b9fd448e56a144fb3abbcc8b1b2
  PB-08 fairness bound refreeze

c0d315b38ed6622d52e38a6c13f56c2d905df2d1
  PB-08 local acceptance expected values

49948f9dddda1272df954b576b62c7081dccff09
  PB-08 fresh snapshot decision

0b1392ad487c796b76e74a0b38ede3e9d3090321
  PB-08 retained-session local re-acceptance

8badcd2d8bbc0e8fea3fa2ae0aca5d0694da012c
  PB-08 fresh remote preflight
```

## 6. Frozen PB-08 frontier catch-up shape

From the accepted fresh snapshot, the bounded NVDA catch-up is:

```text
entry
  v61 / 2026-09-23T18:28:00.000Z

job 1
  2026-09-24T13:30:00Z -> 2026-09-24T15:10:00Z
  expected v61 -> v62

job 2
  2026-09-24T15:09:00Z -> 2026-09-24T16:49:00Z
  expected v62 -> v63

job 3
  2026-09-24T16:48:00Z -> 2026-09-24T18:28:00Z
  expected v63 -> v64

job 4
  2026-09-24T18:27:00Z -> 2026-09-24T20:00:00Z
  expected v64 -> v65
```

Final target:

```text
NVDA checkpoint          v65 / 2026-09-24T20:00:00.000Z
canonical Regular bars   390
clean NVDA attempts      4
bad/unresolved attempts  0
maximum Cron opportunities 16
```

The 16-opportunity count is a hard safety bound for unchanged canary fairness,
not a target runtime duration.

## 7. Required live acceptance / stop conditions

Accept the PB-08 catch-up only if all are true:

- exact entry is still v61 / Sep23 18:28Z;
- September 24 Regular open is still inside normal retention;
- safe baseline is Shadow / News-disabled / IEX;
- historical-recovery control endpoint remains closed;
- every observed live scheduler digest is within budget;
- every selected market summary is SUCCEEDED;
- exactly four clean NVDA attempts occur;
- each NVDA attempt has zero conflicts, rejected and missing;
- checkpoint versions advance sequentially v62 -> v63 -> v64 -> v65;
- final checkpoint is COMPLETE / gap-free / blocker-free / retry-free;
- September 24 contains exactly 390 canonical NVDA Regular one-minute bars;
- checked-in Shadow deployment is restored on exit.

Stop and restore Shadow on any mismatch.

## 8. Local execution handoff

A complete local change-window script was generated outside GitHub after the
GitHub contents API repeatedly rejected the long script write.

The repository currently contains an earlier **incomplete skeleton** at:

```text
scripts/l1_003_pb08_frontier_catchup_change_window.sh
```

Do not execute that skeleton.

For local continuation:
1. replace the skeleton with the complete locally supplied script;
2. run `bash -n` against the completed script;
3. re-run `scripts/l1_003_pb08_local_acceptance.sh`;
4. run the complete PB-08 frontier catch-up script;
5. capture full stdout/stderr;
6. verify final Shadow baseline;
7. write a PB-08 remote acceptance record only after evidence matches.

The operator has explicitly authorized only this bounded PB-08 frontier
catch-up change-window.

## 9. Authority boundary

Authorized:
- bounded PB-08 normal-scheduler frontier catch-up only.

Not authorized:
- PB-09;
- PB-10;
- Phase B pause/resume;
- retention widening;
- Universe changes;
- fairness/priority changes;
- Cron changes;
- manual checkpoint movement;
- historical-recovery use;
- News activation.

## 10. Critical path state

```text
PB-04  COMPLETE
PB-05  ACCEPTED
PB-06  ACCEPTED
PB-07  ACCEPTED
PB-08  LOCAL ACCEPTED / frontier catch-up AUTHORIZED, not yet executed
PB-09  GATED
PB-10  NOT AUTHORIZED
```

Immediate next action: local execution of the completed PB-08 frontier catch-up
change-window, followed by evidence review.
