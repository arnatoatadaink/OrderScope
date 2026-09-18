# OrderScope — L1-003 PB-04 NVDA September 8 Campaign Acceptance

Status: **ACCEPTED — second PB-04 session complete; PB-04 remains in progress**
Date: 2026-09-18 JST
Environment: `live-canary`
Parent: `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`

## 1. Outcome and boundary

The explicitly authorized PB-04 change window completed exactly one bounded
NVDA Regular-session campaign. Four independent one-chunk Worker invocations
accepted the complete September 8 session. The checkpoint advanced only along
the frozen chain from version 14 to version 18 and remains `COMPLETE`, gap-free
and blocker-free.

This record accepts only the September 8 campaign. It does not authorize an
automatic September 9 campaign, normal-scheduler activation, Phase B, or any
other remote mutation.

## 2. Entry preflight and frozen identity

```text
preflight UTC                 2026-09-18T02:28:36Z
preflight JST                 2026-09-18T11:28:36+09:00
release                       8b68170cb50d3b4f93c79eb7d26cd341979451ba
worktree / upstream           clean / ahead 0, behind 0
environment / account        live-canary / 905a2bdec98321c41ac41e48b2fff501
D1 database                   orderscope-state-live-canary
D1 database id                03c85865-1aa3-4b0c-b219-18987cd260a6
Worker / News                 shadow / disabled
control path                  PASS; read statements changed zero rows
checkpoint                    version 14 / COMPLETE / no gaps / no blocker
complete through              2026-09-04T20:00:00.000Z
historical endpoint           404
historical control secret     absent
```

At final observation `2026-09-18T09:56:44Z`, the 1,440-minute retention floor
was `2026-09-17T09:56:44Z`. The September 17 Regular session remained wholly
inside normal retention, so the historical handoff boundary remained the
September 16 close. The execution route retained its reviewed authoritative
calendar revision `alpaca-calendar-v2:da7d32f3` for `[2026-09-02,
2026-09-17)`.

Campaign `PB04-NVDA-20260908-01` owned exactly the September 8 Regular session,
`[2026-09-08T13:30:00.000Z, 2026-09-08T20:00:00.000Z)`.

## 3. Frozen chunks and accepted evidence

| Ordinal | Job | Range UTC | Bars | Checkpoint | Pages | External / D1 |
|---:|---|---|---:|---|---:|---:|
| 1 | `historical-market-recovery:944872abfb045c60` | `[13:30, 15:10)` | 100 | v14 -> v15 | 1 | 1 / 15 |
| 2 | `historical-market-recovery:53a6bfe5f57f1881` | `[15:10, 16:50)` | 100 | v15 -> v16 | 1 | 1 / 15 |
| 3 | `historical-market-recovery:8937d40d66ec431a` | `[16:50, 18:30)` | 100 | v16 -> v17 | 1 | 1 / 15 |
| 4 | `historical-market-recovery:80b0703de37c382c` | `[18:30, 20:00)` | 90 | v17 -> v18 | 1 | 1 / 15 |

Every response was HTTP 200, `accepted=true`, `SUCCEEDED`, and
`stoppedAfterOneChunk=true`. Each call was followed by an independent read-only
D1 inspection before the next invocation. The final aggregate evidence was:

```text
attempts / SUCCEEDED          4 / 4
receipts                      390
INSERTED / MATCHED            390 / 0
conflict/rejected/missing     0 / 0 / 0
canonical bars                390
first / last bar              2026-09-08T13:30:00.000Z / 19:59:00.000Z
final checkpoint              version 18 / 2026-09-08T20:00:00.000Z
final state                   COMPLETE / no gaps / no blocker
```

All D1 verification statements reported `changed_db=false`.

## 4. Change-window closure

The safe false-gate deployment was
`c501ec06-d95e-4be6-bb09-0f63741b47ab`; the temporary gate deployment was
`66931205-e9c4-4edb-8418-bc4b767d1936`; and the immediate false-gate deployment
was `e9b0dfdd-5549-4c1d-9d6a-4aad42b9cf82`. Deleting the temporary control
secret produced final version `790c36b8-6fe7-4b7e-b611-af7c430ce2b4`.

Final verification at `2026-09-18T09:56:44Z` confirmed Worker Shadow mode,
News disabled, recovery endpoint HTTP 404, and only the two Alpaca credentials
present in the secret list. The checked-in configuration is restored to
`HISTORICAL_RECOVERY_ENABLED=false`. The local temporary token file was deleted.

## 5. Local verification and next gate

Before remote mutation, the full TypeScript suite passed 199/199, TypeScript
typecheck passed, Wrangler generated-type check passed, the live-canary deploy
dry-run passed, and `git diff --check` passed.

PB-04 remains in progress. Against the current September 16 boundary, the
remaining sessions are September 9, 10, 11, 14, 15 and 16: six sessions / 2,340
bars. The next separately bounded action is to repeat the moving-horizon
read-only entry check, freeze September 9 from checkpoint version 18, and obtain
a distinct change-window authorization for that one-session campaign. PB-05,
PB-06 and Phase B remain gated.
