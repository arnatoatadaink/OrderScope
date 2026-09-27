# OrderScope — L1-003 PB-05 Handoff Boundary Gate Assessment

Status: **BLOCKED — PB-04 historical boundary not reached**
Date: 2026-09-18 JST
Environment: `live-canary`
Parent: `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`

## 1. Outcome

PB-05 was evaluated read-only and cannot be accepted. The selected NVDA
checkpoint is clean but remains at the end of the September 4 Regular session,
not at the frozen September 16 historical handoff boundary. No checkpoint jump,
normal-retention widening, scheduler activation or remote mutation was used to
hide the missing historical interval.

The next executable work remains PB-04: re-freeze the moving horizon and run the
September 8 one-session campaign under a distinct reviewed change window. PB-06
and Phase B remain gated.

## 2. Read-only observation

```text
observed UTC                  2026-09-18T01:44:18Z
observed JST                  2026-09-18T10:44:18+09:00
release                       5d1b8ba546b665997f25cee35d51702356d3668e
worktree                      clean
environment / account        live-canary / 905a2bdec98321c41ac41e48b2fff501
D1 database                   orderscope-state-live-canary
D1 database id                03c85865-1aa3-4b0c-b219-18987cd260a6
Worker / News                 shadow / disabled
control path                  PASS; all reported statements changed zero rows
checkpoint                    version 14 / COMPLETE / no gaps / no blocker
complete/source through       2026-09-04T20:00:00.000Z
universe revision             stock-monitoring-canary-v0.1
```

The latest authoritative calendar already frozen for `[2026-09-03,
2026-09-19)` is `alpaca-calendar-v2:7bb2446c`. At observation time:

```text
normal retention              1,440 minutes
retention floor               2026-09-17T01:44:18Z
earliest wholly eligible next Regular session
                               2026-09-17 [13:30Z, 20:00Z)
historical handoff boundary   2026-09-16T20:00:00.000Z
```

The September 17 next session was wholly inside normal retention. Therefore the
moving-retention part of the handoff calculation still had a valid intersection;
the failing condition was the historical checkpoint position.

## 3. Continuity and anomaly evidence

Read-only D1 aggregation produced:

```text
historical attempts           8 SUCCEEDED / no other outcome
historical receipts           780 INSERTED / 0 MATCHED
conflict / rejected           0 / 0
bars in [Sep 4 close, Sep 16 close)
                               0
required remaining sessions   Sep 8, 9, 10, 11, 14, 15, 16
required remaining bars       7 x 390 = 2,730
```

The 780 accepted receipts are exactly the previously accepted September 3 and
September 4 sessions. They provide no evidence for the seven remaining sessions.
The selected checkpoint has no missing-range or blocker state, but it is not
contiguous through the required boundary.

## 4. PB-05 acceptance matrix

| Criterion | Observation | Result |
|---|---|---|
| checkpoint contiguous through frozen boundary | v14 ends at September 4 close; boundary is September 16 close | **FAIL** |
| next expected range wholly inside normal retention | September 17 Regular open is after the observed retention floor | PASS at observation time |
| selected checkpoint has no missing state | `missing_ranges_json=[]` | PASS |
| selected checkpoint has no blocker state | `blocker_json=null` | PASS |
| historical recovery has no conflict/rejected evidence | zero conflict and zero rejected | PASS |

PB-05 requires every row to pass. Its gate therefore remains blocked on PB-04;
PB-06 is not authorized.

## 5. Safe restart rule

1. Repeat PB-01 immediately before the next campaign because the retention
   floor moves.
2. Freeze September 8 from checkpoint version 14 and execute no more than that
   one Regular session under a separately reviewed PB-04 change window.
3. Verify every chunk and restore the false gate / absent control-secret safe
   baseline before considering another session.
4. Continue one session at a time until the freshly frozen historical boundary
   is reached. Re-evaluate PB-05 from the then-current UTC and authoritative
   calendar; do not rely on the September 16 target if the horizon has moved.
5. Only after PB-05 passes may PB-06 request separate normal-scheduler
   activation authority.

This assessment authorizes no provider call, D1 write, deploy, secret mutation,
Worker/Cron activation, normal-scheduler handoff or Phase B action.
