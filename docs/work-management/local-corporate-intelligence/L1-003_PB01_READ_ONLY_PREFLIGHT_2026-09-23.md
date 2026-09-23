# OrderScope — L1-003 PB-01 Read-only Preflight

Status: **PASS WITH TIME-BOUND HANDOFF WINDOW**
Date: 2026-09-23 JST
Branch: `l1-003-local-market-recovery`
Parent: `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`

## 1. Authority boundary

This preflight is read-only. It authorizes no Worker deploy, Cron activation,
secret mutation, D1 write, checkpoint movement, or Phase B action.

## 2. Frozen preflight time

```text
preflight_now_utc   2026-09-23T08:19:36Z
retention_lookback  1,440 minutes
retention_floor     2026-09-22T08:19:36Z
```

## 3. Market-calendar facts

NYSE Core Trading is 09:30-16:00 America/New_York. September 22, 2026 is a
normal Tuesday and is not a listed 2026 NYSE holiday. The September 22 Regular
session therefore maps to:

```text
open   2026-09-22T13:30:00Z
close  2026-09-22T20:00:00Z
```

At the frozen preflight time, September 23 Regular trading has not opened yet,
so September 22 is the last completed Regular session.

## 4. Current remote and local states

Authoritative remote PB-04 checkpoint remains:

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
checkpoint version 18
complete through   2026-09-08T20:00:00.000Z
```

Accepted local-only provider evidence is available through September 21 close:

```text
sessions           Sep 9, 10, 11, 14, 15, 16, 17, 18, 21
provider bars      3,509
local disposition  ACCEPTED
remote mutation    none
```

## 5. PB-01 boundary calculation

Using the WBS rule:

```text
retention_floor = preflight_now - 1,440 minutes

handoff_session = earliest authoritative session whose required next range
                  is wholly on or after retention_floor

historical_target = authoritative boundary immediately before that next range
```

At the frozen time:

```text
retention_floor     2026-09-22T08:19:36Z
handoff_session     2026-09-22 REGULAR
handoff_open        2026-09-22T13:30:00Z
handoff_close       2026-09-22T20:00:00Z
historical_target   2026-09-21T20:00:00Z
```

The accepted local bundle ends exactly at the historical target.

## 6. Time-bound risk

The existing scheduler computes the provider start as the maximum of the
retention floor and the selected session open. Therefore the September 22
handoff is only fully recoverable while:

```text
retention_floor <= 2026-09-22T13:30:00Z
```

That condition expires at:

```text
2026-09-23T13:30:00Z
```

After that instant, the September 22 session open is older than the 24-hour
retention floor. A normal scheduler handoff from a September 21-close
checkpoint can no longer guarantee the full September 22 Regular range.

This is a hard moving-window boundary, not a recommended execution deadline.
PB-01 must be rerun immediately before any authorized import/handoff action.

## 7. Disposition

```text
PB-01 current result       PASS
historical target          Sep 21 close
local bundle coverage      MATCHES target
normal handoff candidate   Sep 22 Regular
handoff durability         TIME-BOUND
remote checkpoint          UNCHANGED
PB-04                      IN PROGRESS
PB-05                      BLOCKED pending remote contiguous import/recovery
```

Because the Sep 22 handoff window is transient, collecting Sep 22 locally as
additional no-mutation contingency evidence is permitted and recommended
before designing the final import boundary. This does not change the frozen
PB-01 result or authorize any remote mutation.

## 8. Next controlled action

1. Collect Sep 22 locally as a contingency session.
2. Validate/hash it with the same v3 provider-aware rules.
3. Design the D1 import path so accepted-record and checkpoint-CAS contracts
   remain unchanged.
4. Rerun PB-01 immediately before remote mutation.
5. Freeze the actual historical target at that later preflight.
