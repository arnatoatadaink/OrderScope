# OrderScope — L1-003 PB-04 NVDA September 4 Campaign Acceptance

Status: **ACCEPTED — first PB-04 session complete; PB-04 remains in progress**
Date: 2026-09-18 JST
Environment: `live-canary`
Parent: `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`

## 1. Outcome and boundary

The explicitly authorized PB-04 change window completed one bounded NVDA
Regular-session campaign. Four independent one-chunk Worker invocations
accepted the complete September 4 session. The checkpoint advanced only along
the frozen chain from version 10 to version 14 and remains `COMPLETE`, gap-free
and blocker-free.

This record accepts only the September 4 campaign. It does not authorize an
automatic next-session campaign, normal-scheduler activation, Phase B, or any
other remote mutation.

## 2. Repeated PB-01 entry preflight

```text
preflight UTC                 2026-09-17T19:49:05Z
preflight JST                 2026-09-18T04:49:05+09:00
release                       582068374b6414eeb996dd5e8257456c5b09b9ac
worktree                      clean
environment / account        live-canary / 905a2bdec98321c41ac41e48b2fff501
D1 database                   orderscope-state-live-canary
D1 database id                03c85865-1aa3-4b0c-b219-18987cd260a6
Worker / News                 shadow / disabled
control path                  PASS; read statements changed zero rows
checkpoint                    version 10 / COMPLETE / no gaps / no blocker
complete through              2026-09-03T20:00:00.000Z
historical endpoint           404
historical control secret     absent
```

The authoritative calendar for `[2026-09-03, 2026-09-19)` retained revision
`alpaca-calendar-v2:7bb2446c`, generated at `2026-09-17T19:50:24.309Z`.
The 1,440-minute retention floor was `2026-09-16T19:49:05Z`; the earliest
wholly eligible following Regular session remained September 17 and the
historical handoff target remained the September 16 close.

The execution route independently retained its frozen authoritative calendar
revision `alpaca-calendar-v2:da7d32f3` for `[2026-09-02, 2026-09-17)`.

## 3. Frozen campaign and accepted evidence

Campaign `PB04-NVDA-20260904-01` owned exactly the September 4 Regular session,
`[2026-09-04T13:30:00.000Z, 2026-09-04T20:00:00.000Z)`.

| Ordinal | Job | Range UTC | Bars | Checkpoint | Pages | External / D1 |
|---:|---|---|---:|---|---:|---:|
| 1 | `historical-market-recovery:01b747d78d8d97c0` | `[13:30, 15:10)` | 100 | v10 -> v11 | 1 | 1 / 15 |
| 2 | `historical-market-recovery:71dc4b562a47ce41` | `[15:10, 16:50)` | 100 | v11 -> v12 | 1 | 1 / 15 |
| 3 | `historical-market-recovery:db706c142a671a82` | `[16:50, 18:30)` | 100 | v12 -> v13 | 1 | 1 / 15 |
| 4 | `historical-market-recovery:3cee03817d2d24f4` | `[18:30, 20:00)` | 90 | v13 -> v14 | 1 | 1 / 15 |

Every response was `accepted=true`, `SUCCEEDED`, and
`stoppedAfterOneChunk=true`. Each invocation was followed by an independent
read-only D1 inspection before the next invocation. The aggregate evidence is:

```text
attempts / SUCCEEDED          4 / 4
receipts                     390
INSERTED / MATCHED            390 / 0
conflict/rejected/missing     0 / 0 / 0
canonical bars                390
first / last bar              2026-09-04T13:30:00.000Z / 19:59:00.000Z
final checkpoint              version 14 / 2026-09-04T20:00:00.000Z
final state                   COMPLETE / no gaps / no blocker
```

## 4. Change-window closure

The safe pre-activation version was
`3e0d2203-a714-46cb-9270-e4fb89bbbf62`; the temporary gate version was
`33205775-fcc2-43d8-88af-59147e45cbcb`; and the immediate false-gate version
was `d087b013-ebfc-4592-8681-5115d9121bdb`. Deleting the temporary control
secret produced final version `bac8cdad-24e9-432b-9f8c-1e6298208067`.

Final verification at `2026-09-17T19:57:16Z` confirmed Worker Shadow mode,
News disabled, recovery endpoint HTTP 404, and only the two Alpaca credentials
present in the secret list. The checked-in configuration is restored to
`HISTORICAL_RECOVERY_ENABLED=false`.

## 5. Verification and next gate

Before remote mutation, the full TypeScript suite passed 199/199, TypeScript
typecheck passed, and the live-canary deploy dry-run passed with the recovery
gate false. All final D1 verification statements reported `changed_db=false`.

PB-04 remains in progress because the checkpoint has not reached the re-frozen
September 16 handoff boundary. The next separately bounded action is to repeat
the read-only entry check, freeze the September 8 Regular session from version
14, and execute another one-session campaign only under explicit change-window
authority. PB-05, PB-06 and Phase B remain gated.
