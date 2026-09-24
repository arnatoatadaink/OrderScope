# OrderScope — L1-003 PB-07 Stability Change-Window Authorization Template

Status: **READY FOR EXPLICIT AUTHORIZATION — not yet authorized**
Date: 2026-09-24 JST
Environment: `live-canary`

## Scope to authorize

Only the bounded PB-07 stability observation window:

```text
entry checkpoint        v59 / 2026-09-23T15:10:00.000Z
maximum Cron windows    7

NVDA clean advance 1
  v59 -> v60
  2026-09-23T15:09:00.000Z -> 2026-09-23T16:49:00.000Z

NVDA clean advance 2
  v60 -> v61
  2026-09-23T16:48:00.000Z -> 2026-09-23T18:28:00.000Z
```

Temporary runtime change:

```text
WORKER_MODE shadow -> live
```

Everything else must remain unchanged:
- Cron `* * * * *`;
- Universe `canary-v0.1`;
- retention 1,440 minutes;
- maxJobsPerTick 2;
- maxBarsPerJob 100;
- fairness priority;
- IEX feed;
- News disabled;
- historical recovery disabled at baseline.

## Acceptance

PB-07 is accepted only when:
- exact v60 is separately observed before v61;
- exact final checkpoint is v61 / 18:28Z;
- exactly two clean NVDA normal-scheduler attempts occur in the window;
- every NVDA attempt is SUCCEEDED;
- conflicts = 0;
- rejected = 0;
- missing = 0;
- no unresolved NVDA attempt exists;
- every observed live scheduler digest reports `budget.withinBudget=true`;
- no selected market summary in the observation window is non-SUCCEEDED;
- combined frozen NVDA interval contains 199 canonical one-minute bars;
- final checkpoint remains COMPLETE, gap-free, blocker-free and retry-free;
- the checked-in Shadow deployment is restored on exit.

## Stop conditions

Stop and restore Shadow if:
- activation-time retention floor has passed
  `2026-09-23T15:09:00.000Z`;
- exact v59 entry has changed;
- the safe baseline is not Shadow / News-disabled / historical-closed;
- any market scheduler summary fails;
- budget regression occurs;
- any NVDA attempt is non-clean;
- v60 is not separately observed before v61;
- v61 is not reached within seven Cron opportunities;
- final evidence differs from the frozen packet.

## Out of scope

PB-08 and later Phase B work are not authorized by PB-07.

## Explicit authorization phrase

Use:

```text
PB-07 stability observation change-windowを実行してよい
```
