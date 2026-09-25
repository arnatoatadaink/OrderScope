# OrderScope — L1-003 PB-08 Fresh Snapshot Re-freeze

Status: **LOCAL LOGIC UPDATED — remote catch-up not authorized**
Date: 2026-09-25 JST

## Fresh read-only snapshot

```text
observed_now       2026-09-25T02:44:38.000Z
retention floor    2026-09-24T02:44:38.000Z
NVDA checkpoint    v61 / 2026-09-23T18:28:00.000Z
state              COMPLETE
missing ranges     []
blocker            null
unresolved         0
Worker             shadow
News               disabled
feed               IEX
Universe           canary-v0.1 / stock-monitoring-canary-v0.1
```

The prior checkpoint is older than the active 24-hour retention floor.

## Scheduler defect discovered

The previous equity cross-session logic used the stale checkpoint itself as the
session-selection anchor. When that checkpoint belonged to an expired prior
session, the scheduler could choose that expired session and then eliminate the
job because the retention-clamped start was later than that session close.

The correct retained-session rule is:

```text
session selection anchor = max(progression checkpoint, retention floor)
```

This allows an expired prior-session checkpoint to resume at the first
authoritative Regular session still inside retention, without widening
retention or jumping the checkpoint manually.

## Fresh frozen NVDA catch-up

At the captured snapshot, September 24 Regular is fully finalized and inside
retention. After the retained-session fix, the deterministic NVDA jobs are:

```text
1  v61 -> v62
   2026-09-24T13:30:00Z -> 2026-09-24T15:10:00Z

2  v62 -> v63
   2026-09-24T15:09:00Z -> 2026-09-24T16:49:00Z

3  v63 -> v64
   2026-09-24T16:48:00Z -> 2026-09-24T18:28:00Z

4  v64 -> v65
   2026-09-24T18:27:00Z -> 2026-09-24T20:00:00Z
```

The frozen frontier is:

```text
v65 / 2026-09-24T20:00:00.000Z
```

The fairness simulation uses a local upper bound of 16 unchanged Cron
opportunities and requires exactly four selected clean NVDA jobs.

## Authority boundary

The schedule fix and local tests authorize no remote deployment, provider
acquisition, D1 mutation, checkpoint movement, pause/resume, PB-09 or PB-10.

A fresh local acceptance run is required before any remote catch-up window is
prepared.
