# OrderScope — L1-003 Phase B Start-Readiness WBS and Critical Path

Status: **ACTIVE PLAN — Phase B not authorized**
Date: 2026-09-18 JST
Parent WBS: `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md` (`L1-003`)
Parent CP: `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Recovery plan: `L1-003_PHASE_B_PREREQUISITE_MARKET_RECOVERY_SCHEDULE_2026-09-16.md`
Latest evidence: `L1-003_PB04_NVDA_SEP04_CAMPAIGN_ACCEPTANCE_2026-09-18.md`

## 1. Objective and authority boundary

Bring one NVDA Regular-session Market checkpoint into the unchanged normal
scheduler's valid retention horizon, demonstrate stable normal following, and
prepare a separately authorized Phase B pause/resume window.

This plan authorizes documentation, read-only preflight, deterministic local
planning and review. It does not authorize a deploy, secret mutation, provider
call, D1 write, Cron/Worker activation, pause/resume action, or Phase B.

## 2. Reconciled baseline

```text
as of                         2026-09-17T19:57:16Z
coverage key                  NVDA|1Min|REGULAR|stock:iex:raw
checkpoint                    version 14
complete through              2026-09-04T20:00:00.000Z
state / gaps                  COMPLETE / none
Worker / News                 shadow / disabled
recovery endpoint             404
control secret                absent
normal retention horizon      1,440 minutes
Phase B                       NOT READY
```

### Snapshot remaining-work estimate

The existing Worker recovery boundary reaches the September 15 Regular close.
From the current September 4 close baseline that is six full Regular sessions:

```text
sessions                      Sep 8, 9, 10, 11, 14, 15
bars                          6 x 390 = 2,340
current session-bounded plan  24 chunks (100 + 100 + 100 + 90 per session)
```

At the reconciliation timestamp, reaching the September 16 close would require
one additional full session, for a snapshot total of 2,730 bars / 28 chunks.
This is not a permanent target. The 24-hour retention floor moves with time;
therefore the handoff target and remaining count must be re-frozen from an
authoritative exchange calendar immediately before each authorized recovery
campaign. A stale fixed count cannot establish readiness.

## 3. Work breakdown structure

| ID | Work item | Completion evidence | Gate / dependency | State |
|---|---|---|---|---|
| PB-00 | Close version-8 and version-9 windows | Exact jobs, ranges, counts, checkpoints, gate removal, secret deletion and current read-only reconciliation recorded | Existing accepted remote evidence | Done |
| PB-01 | Re-freeze recovery target | Authoritative calendar, current UTC, 24-hour retention floor, last completed session and earliest valid normal-scheduler range captured | PB-00; read-only only | Repeated at PB-04 entry — target remains September 16 close |
| PB-02 | Select bounded continuation campaign shape | Reviewed choice between repeated one-chunk windows and a separately implemented session-bounded driver; explicit maximum jobs/pages/bars/external/D1 ops and stop-after-each-chunk verification | PB-01; no remote mutation | Done — one-session operator campaign selected |
| PB-03 | Accept continuation mechanism locally | Deterministic planning, checkpoint re-read/CAS, failure stop, replay closure, budget and full regression evidence | PB-02 | Done — local campaign driver accepted |
| PB-04 | Execute bounded historical campaign | Every chunk has separate frozen identity and accepted-record evidence; no unexplained checkpoint movement; safe gate removal after each authorized window | PB-03; separate change-window authority | In progress — September 4 campaign accepted; checkpoint v14; next session September 8 separately gated |
| PB-05 | Establish handoff boundary | Checkpoint is contiguous through the frozen boundary and the next expected range is wholly inside normal retention; no missing/conflict/rejected/blocker state | PB-04 | Gated |
| PB-06 | Normal-scheduler handoff | Unchanged scheduler plans and accepts the exact next range; checkpoint advances only from accepted bars; control PASS and within budget | PB-05; separate scheduler activation authority | Gated |
| PB-07 | Stability observation | At least two consecutive eligible scheduler opportunities advance the same coverage cleanly; no unresolved state or budget/control regression | PB-06; active U.S. session | Gated |
| PB-08 | Freeze Phase B entry packet | `checkpoint_before_pause`, deployment/config/calendar/universe identity, pause duration, exact-gap expectation, rollback and stop criteria recorded | PB-07 | Gated |
| PB-09 | Request Phase B authorization | A distinct reviewed market-session change window is approved | PB-08 | Gated |
| PB-10 | Execute Phase B | Short pause creates only the fresh bounded gap; resume catches up exactly; no false checkpoint advance; safe baseline restored | PB-09 | Not authorized |

## 4. Selected planning rule for PB-02

Do not run 28 or more manual one-shot deployments as an unreviewed loop. PB-02
selected this bounded form:

```text
B. new operator-side session-bounded campaign driver
   -> locally implemented and reviewed first
   -> fixed maximum of one Regular session / four chunks
   -> checkpoint re-read and acceptance verification after every chunk
   -> immediate stop on any mismatch
   -> no cross-session automatic continuation
```

The selected driver uses four independent Worker invocations rather than an
in-Worker loop. Four observed 15-D1-operation chunks would total about 60 and
exceed the per-invocation D1 ceiling of 40. The decision and exact bounds are
recorded in `L1-003_PB01_PB02_RECOVERY_CAMPAIGN_DECISION_2026-09-18.md`.
Selection does not authorize implementation deployment or remote execution.

## 5. Critical path

```text
PB-00 accepted closeout
  -> PB-01 moving-horizon preflight
  -> PB-02 campaign-shape review
  -> PB-03 local acceptance
  -> PB-04 authorized bounded recovery campaign(s)
  -> PB-05 retention-horizon intersection
  -> PB-06 unchanged normal-scheduler handoff
  -> PB-07 two clean scheduler opportunities
  -> PB-08 Phase B entry packet
  -> PB-09 separate authorization
  -> PB-10 pause / exact-gap catch-up / safe-baseline restoration
```

PB-01 through PB-05 are the current controlling chain. Full-universe recovery,
News activation, prediction promotion, purge, remote backup/restore and other
symbols are outside this critical path.

## 6. Handoff calculation

At every PB-01/PB-04 entry, compute:

```text
retention_floor = preflight_now - 1,440 minutes
handoff_session = earliest authoritative session whose required next range is
                  wholly on or after retention_floor
historical_target = authoritative boundary immediately before that next range
remaining_bars = authoritative one-minute Regular bars in
                 [checkpoint.complete_through, historical_target)
```

The campaign must finish early enough that the selected handoff range has not
fallen behind the moving retention floor. If it has, stop and re-freeze PB-01;
never jump the checkpoint or widen normal retention to compensate.

## 7. Phase B READY gate

Phase B may be proposed only when all are true:

- active applicable U.S. market session;
- selected checkpoint is current, `COMPLETE`, and gap-free;
- historical campaign has ended and the unchanged normal scheduler owns the
  next range;
- at least two consecutive normal opportunities completed cleanly;
- missing, conflict, rejected and blocker state are absent;
- control path is `PASS` and all executions are within budget;
- Worker/config/calendar/Universe identity is frozen;
- `checkpoint_before_pause`, pause duration, expected exact gap and rollback
  path are recorded.

Failure of any item keeps Phase B `NOT READY` and prohibits pause/resume.

## 8. Immediate next action

The first PB-04 campaign is accepted in
`L1-003_PB04_NVDA_SEP04_CAMPAIGN_ACCEPTANCE_2026-09-18.md`. Repeat the
read-only entry check, freeze the exact September 8 session identities from
checkpoint version 14, and obtain a separate change-window authorization for
that one-session campaign. Do not cross sessions automatically. PB-05 remains
gated until the checkpoint reaches the re-frozen September 16 handoff target.
