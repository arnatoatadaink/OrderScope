# OrderScope — L1-003 PB-01 / PB-02 Recovery Campaign Decision

Status: **ACCEPTED — PB-01/PB-02 complete; PB-03 locally accepted**
Date: 2026-09-18 JST
Environment: `live-canary`
Parent: `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`

## 1. Authority boundary

This record covers read-only remote preflight and deterministic campaign-shape
review. It does not authorize a deploy, secret mutation, provider bar request,
D1 write, Worker/Cron activation, historical recovery execution, or Phase B.

## 2. PB-01 read-only preflight result

The checked-in read-only preflight completed against the isolated live-canary
database. Independent health, deployment, secret-list, checkpoint and calendar
reads were also captured. The read-only SQL statements reported zero rows
written and `changed_db=false`.

```text
preflight started UTC          2026-09-17T19:17:16Z
preflight started JST          2026-09-18T04:17:16+09:00
release                        4abf28e08961297ab2f41fafa4ed0e59d220ad8a
worktree                       clean
environment                    live-canary
Cloudflare account             905a2bdec98321c41ac41e48b2fff501
D1 database                    orderscope-state-live-canary
D1 database id                 03c85865-1aa3-4b0c-b219-18987cd260a6
control path                   PASS (`SELECT 1`)
Worker                         HTTP 200 / shadow
feed / Universe                iex / canary-v0.1
News                           disabled
historical endpoint            HTTP 404
historical control secret      absent
latest deployment version      369c4cdc-ef87-42b7-aa43-e806c862973c
checkpoint                     NVDA version 10 / COMPLETE / no gaps
complete/source through        2026-09-03T20:00:00.000Z
universe revision              stock-monitoring-canary-v0.1
blocker                        none
```

The authoritative Alpaca calendar was read for the half-open range
`[2026-09-03, 2026-09-19)`. With Regular sessions only it produced revision
`alpaca-calendar-v2:7bb2446c`.

```text
calendar generated at          2026-09-17T19:18:05.805Z
retention floor                2026-09-16T19:18:05.805Z
earliest wholly eligible next session
                               2026-09-17 Regular
historical handoff target      2026-09-16T20:00:00.000Z
remaining sessions             Sep 4, 8, 9, 10, 11, 14, 15, 16
remaining bars                 8 x 390 = 3,120
existing 100-bar chunks        32 (four per session)
```

The target is a planning snapshot, not a permanent execution identity. PB-04
entry must repeat PB-01 because the 1,440-minute retention floor moves.

## 3. PB-02 selected campaign shape

Select the session-bounded campaign form, implemented as an operator-controlled
orchestrator around the existing one-chunk Worker contract:

```text
one authorized campaign
  -> exactly one Regular session
  -> at most four sequential Worker invocations
  -> chunks of 100 + 100 + 100 + 90 bars on a 390-minute session
  -> independent checkpoint and accepted-record verification after every chunk
  -> immediate stop on the first mismatch
```

“One trading day” therefore means one bounded campaign, not one acquisition
job and not one Worker invocation. The existing planner already prevents a job
from crossing a session boundary.

### 3.1 Fixed bounds

| Boundary | Per chunk | Per full Regular-session campaign |
|---|---:|---:|
| Jobs / Worker invocations | 1 | 4 |
| Eligible bars | 100 maximum | 390 exact maximum |
| Provider pages | 10 maximum | 40 maximum |
| Provider attempts | 30 maximum from 10 pages x 3 attempts, also bounded by the 40 external ceiling | 120 maximum |
| D1 operations | 40 hard ceiling; 15 observed on each accepted prior chunk | 160 hard-ceiling sum; approximately 60 at the observed path |
| Sessions crossed | 0 | 0; the campaign owns exactly one frozen session |

Each Worker invocation receives a fresh `InvocationBudget`; aggregate campaign
figures are reporting and stop bounds, not permission to weaken the per-invocation
40/40 ceilings.

### 3.2 Why four independent invocations are required

The four accepted remote chunks each used one external request and 15 D1
operations. Reusing one budget inside a single Worker invocation would require
approximately 60 D1 operations for a full session, exceeding the reviewed
internal D1 ceiling of 40. PB-02 therefore rejects an in-Worker four-chunk loop.

The operator orchestrator may keep one reviewed change window open, but must
call the existing fail-closed one-chunk endpoint separately for each chunk.
It must not perform direct D1 writes or checkpoint edits.

### 3.3 Mandatory stop-after-each-chunk verification

Before planning the next chunk, the orchestrator must re-read persisted truth
and require all of the following:

- response outcome `SUCCEEDED` and `accepted=true`;
- exactly one job and the frozen requested half-open range;
- inserted plus matched equals the exact expected bar count;
- conflicts, rejected and missing are all zero;
- checkpoint remains `COMPLETE`, gap-free and blocker-free;
- `complete_through` equals the chunk end and version increments by exactly one;
- exactly one successful attempt and exact receipt/canonical-bar counts;
- external and D1 counts remain inside their per-invocation ceilings;
- the next deterministic plan remains inside the same frozen Regular session.

Any failure, ambiguity, timeout, lease conflict, calendar/checkpoint/config drift,
or unexpected extra checkpoint movement stops the entire session campaign. No
retry or move to the next session is automatic.

## 4. PB-03 implementation requirements

PB-03 implemented and locally accepted the operator-side session orchestrator
in `src/historical-recovery-campaign.ts`. The detailed acceptance evidence is
recorded in `L1-003_PB03_SESSION_CAMPAIGN_LOCAL_ACCEPTANCE_2026-09-18.md`.
The mechanism:
It must:

1. freeze one session, recovery identity, calendar revision, initial checkpoint
   and expected four chunk identities;
2. invoke only the existing authenticated one-chunk Worker boundary;
3. re-plan from freshly read checkpoint truth after every accepted chunk;
4. enforce four jobs, one session and 390 bars as immutable maxima;
5. persist an allow-listed evidence record for every chunk;
6. stop without retry on any non-success or evidence mismatch;
7. prove replay closure, resume from the last accepted checkpoint, and no
   cross-session continuation in deterministic tests;
8. retain the existing temporary gate, secret deletion and safe-baseline
   restoration procedure.

PB-03 does not authorize PB-04. Remote execution still requires a separately
reviewed change window after a fresh moving-horizon preflight.
