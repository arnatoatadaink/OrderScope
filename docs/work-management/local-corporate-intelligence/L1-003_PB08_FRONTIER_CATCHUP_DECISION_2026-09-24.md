# OrderScope — L1-003 PB-08 Frontier Catch-Up Decision

Status: **PB-08 OPEN — normal-scheduler catch-up required before entry packet freeze**
Date: 2026-09-24 JST

## Read-only finding

At the PB-08 preflight snapshot:

```text
observed now       2026-09-24T15:16:51.000Z
NVDA checkpoint    v61 / 2026-09-23T18:28:00.000Z
state              COMPLETE
missing ranges     []
blocker            null
unresolved         0
Worker             shadow
News               disabled
feed               iex
Universe           canary-v0.1 / stock-monitoring-canary-v0.1
```

The checkpoint is healthy but not current enough for a fresh pause-gap
experiment.

With 1-minute finalization lag, the snapshot Regular-session frontier is:

```text
2026-09-24T15:15:00.000Z
```

## Required unchanged normal-scheduler catch-up

The accepted SchedulePolicy freezes three NVDA jobs from v61:

```text
1  v61 -> v62
   2026-09-23T18:27:00Z -> 2026-09-23T20:00:00Z

2  v62 -> v63
   2026-09-24T13:30:00Z -> 2026-09-24T15:10:00Z

3  v63 -> v64
   2026-09-24T15:09:00Z -> 2026-09-24T15:15:00Z
```

The first job is session-close bounded. The second is the normal 100-minute
window. The third closes the remaining six-minute frontier gap while preserving
the configured one-minute overlap.

## Fairness bound

The full canary scheduler may interleave other symbols. A local simulation
with the frozen checkpoint snapshot requires three selected NVDA executions
and asserts that the frontier is reached within at most 12 unchanged Cron
opportunities.

The 12-opportunity number is a safety upper bound, not an expected runtime
count. Before any remote window it must be revalidated against a fresh
read-only checkpoint snapshot because the frontier and crypto competition move
with time.

## Consequence for PB-08

PB-08 cannot yet freeze `checkpoint_before_pause`.

Required sequence:

```text
PB-07 ACCEPTED
  -> PB-08 read-only preflight
  -> bounded unchanged normal-scheduler frontier catch-up
  -> immediate read-only frontier verification
  -> freeze checkpoint_before_pause + calendar/session identity
  -> freeze exact short pause + exact expected gap
  -> PB-08 close
  -> PB-09 separate authorization
```

No historical recovery, checkpoint jump, retention widening, Universe change,
priority change or Cron change is permitted.

## Candidate pause

A two-Cron-interval pause remains the current candidate only. It is not frozen
until catch-up completes against the then-current active Regular-session
frontier.

## Authority boundary

This decision authorizes no remote mutation or Phase B pause/resume.


## Snapshot-vs-moving-frontier clarification

The fairness-order test is a **frozen read-only snapshot simulation**. Its job
is to prove that, from the captured checkpoint state and captured frontier,
unchanged scheduler fairness can reach that frozen frontier within the bounded
Cron count.

The test must therefore keep `now` fixed at the snapshot timestamp. Advancing
`now` inside the simulation changes the target frontier while simultaneously
testing the catch-up schedule and conflates two different properties.

Operationally, the real frontier continues to move during a remote catch-up
window. Therefore the final PB-08 packet must never reuse the old frozen
frontier after the window. Instead:

```text
freeze snapshot
  -> run separately authorized bounded normal-scheduler catch-up
  -> immediately rerun read-only frontier preflight
  -> capture the then-current frontier and exact checkpoint
  -> only if sufficiently current, freeze checkpoint_before_pause
```

This clarification changes no runtime behavior and authorizes no remote
mutation.
