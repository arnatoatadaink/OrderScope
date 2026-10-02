# OrderScope — Current Local Corporate Intelligence Progress Tracker

Status: **CURRENT INTEGRATED OPERATING TRACKER**
Scope: Local Corporate Intelligence / runtime + market-independent planning
Branch: `l1-003-local-market-recovery`

## 1. Authority and history rule

This file is the date-independent current operating overlay for the older dated integrated tracker:

`LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`

The dated tracker remains historical acceptance evidence and is not rewritten merely because later runtime work advanced. When current status conflicts with an older dated status line, use this tracker together with the latest task-specific acceptance/closeout evidence.

No status in this tracker by itself authorizes live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action.

## 2. Current L0 / L1 state

| Task | Current status | Restart / evidence boundary |
|---|---|---|
| L0-001..006 | Accepted | Preserve accepted local foundation evidence |
| L1-001 | Accepted | No repeat required |
| L1-002 | Accepted | No repeat required |
| L1-003 | PB-08 ACCEPTED / PB-09 PREPARED / PB-10 NOT AUTHORIZED | Market-dependent lane parked; resume only from fresh active-session packet and explicit PB authorization |
| L1-004 | Accepted — fixture path | Preserve accepted evidence |
| L1-005 | Accepted — fixture path | Preserve accepted evidence |
| L1-006 | Accepted — fixture path | Preserve accepted evidence |

### L1-003 controlling PB state

```text
PB-00..PB-03       accepted preparation/history
PB-04 / PB-05      COMPLETE / ACCEPTED
PB-06              ACCEPTED
PB-07              ACCEPTED
PB-08              ACCEPTED; safe closed
PB-09 preparation  COMPLETE
PB-09 execution    fresh active-session entry packet + explicit authorization required
PB-10              NOT AUTHORIZED / NOT EXECUTED
```

Do not repeat PB-04..PB-08 because a calendar day changed. Use `L1-003_PB08_MOVING_RETENTION_REFREEZE_RUNBOOK.md` and the latest PB closeouts when runtime work resumes.

## 3. Accepted runtime / integration foundation

| Package | Current status |
|---|---|
| X0-001..006 | Accepted for fixture-path integration boundary |
| N1-006 | Real-data benchmark Accepted |
| W1-001 confirmation / closeout | Accepted; checked-in safe baseline restored |
| W1-007 control-path diagnostic | Accepted locally / reviewed |
| CS0-001..003 | Accepted locally |
| MR0-001..003 | Accepted locally |

Historical measurements and detailed evidence remain in the dated tracker and task-specific handoffs.

## 4. Analyst / Cross-Market formal WBS state

The formal Analyst/Cross-Market WBS has already incorporated these provisional IDs:

```text
UWBS-011 -> A0-003
UWBS-012 -> A0-004
UWBS-013 -> A0-005
UWBS-014 -> A0-006
UWBS-015 -> A0-007
UWBS-027 -> A0-008
UWBS-028 -> A0-009
UWBS-029 -> A0-010
UWBS-030 -> A0-011
UWBS-031 -> A0-012
UWBS-032 -> A0-013
UWBS-033 -> A0-014
UWBS-034 -> A0-015
UWBS-035 -> A0-016
UWBS-036 -> A0-017
```

The formal mappings above are reserved and must not be reinterpreted by later backlog rows.

## 5. Operational WBS incorporation state

Known incorporated mappings:

```text
UWBS-001 -> R0-001
UWBS-002 -> R0-002
UWBS-003 -> R0-003
UWBS-004 -> R0-004
UWBS-016 -> R0-005
UWBS-023 -> R0-006
UWBS-024 -> R0-007
UWBS-025 -> R0-008
UWBS-026 -> R0-009
```

`UWBS-005..010` and `UWBS-017..022` remain valid non-colliding backlog IDs until separately incorporated/remapped.

## 6. GOV-CP-01 — identifier normalization

Status: **ACCEPTED FOR ACTIVE PLANNING**

Canonical registry: `WBS_PROVISIONAL_ID_REGISTRY.md`

Canonical later ranges currently include:

```text
UWBS-062..066  AI theme lane
UWBS-067       LVWR listing-compliance fixture
UWBS-068..079  Crypto market-structure / derivatives lane
UWBS-080..086  Oil / commodity / cross-asset lane
UWBS-087..093  Physical-SaaS lane
UWBS-094..100  VIX / cross-asset volatility lane
```

All new CP, implementation and acceptance records must use canonical IDs from the registry.

## 7. Current market-dependent CP

```text
PB-08 ACCEPTED
  -> fresh active-session PB-09 entry packet
  -> explicit PB-09 authorization
  -> PB-10 bounded execution / safe close
```

State: **PARKED** until the applicable market-session execution window is intentionally reopened.

## 8. Current market-independent CP

### Oil / commodity / cross-asset lane

```text
UWBS-080  Direct WTI / Brent Macro Instrument contract + provider survey   [ACCEPTED]
   |
   +-> UWBS-081  structured commodity supply/fundamental acquisition      [ACCEPTED]
   +-> UWBS-082  commodity supply/shipping/geopolitical event taxonomy     [ACCEPTED]
   |
   v
UWBS-083  oil-down-reason / inflation-growth-risk interpretation           [ACCEPTED]
   |
   +-> UWBS-084  BTC spot ETF flow normalization                           [ACCEPTED]
   |
   v
UWBS-085  cross-asset Risk-On / Crypto Risk-On regime                     [ACCEPTED]
   |
   v
UWBS-086  historical Canary + Worker/D1 capacity acceptance               [ACCEPTED — CURRENT CHECKED-IN SHADOW RUNTIME]
```

### Physical-SaaS lane

```text
UWBS-087  Physical-SaaS deployment lifecycle Fact contract                [ACCEPTED]
   |
   v
UWBS-088  operational-milestone extraction and reconciliation             [IMPLEMENTED / LOCAL ACCEPTANCE PENDING]
   |
   v
UWBS-089  deployment-funnel Derived Metrics and slippage interpretation    [PENDING]

UWBS-087 -> UWBS-090  recurring-revenue quality/cash conversion model      [PENDING]
UWBS-088 -> UWBS-091  M&A integration / legacy-system evidence overlay     [PENDING]
UWBS-087 -> UWBS-092  Physical-SaaS classifier/applicability guard         [PENDING]
UWBS-089 + UWBS-090 + UWBS-091 + UWBS-092 -> UWBS-093 Canary              [PENDING]
```

### UWBS-087 current state

Status: **ACCEPTED**

Acceptance evidence: `UWBS-087_LOCAL_ACCEPTANCE_2026-09-27.md`

```text
Physical-SaaS deployment focused tests: 10 passed in 1.95s
full Python regression:                845 passed in 47.84s
compileall:                            PASS
git diff --check:                     PASS
```

Accepted boundary keeps source-observed physical deployment lifecycle Facts separate from backlog, bookings, connected-base totals, billing, ARR and recognized revenue.

### UWBS-088 current state

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**

Design evidence: `UWBS-088_OPERATIONAL_MILESTONE_RECONCILIATION_2026-09-27.md`

Implementation:

```text
analysis/app/orderscope_local/physical_saas/milestone_reconciliation.py
analysis/tests/physical_saas/test_milestone_reconciliation.py
```

Reconciliation keeps duplicate, consistent, conflict and insufficient-identity outcomes explicit. It does not silently choose a preferred source or convert commercial guidance into deployment evidence.

### UWBS-086 current state

Status: **ACCEPTED — CURRENT CHECKED-IN SHADOW RUNTIME ONLY**

Final acceptance evidence:

`UWBS-086_FINAL_SHADOW_CAPACITY_ACCEPTANCE_2026-09-27.md`

Latest local verification:

```text
shadow capacity bound focused tests:      10 passed
D1 capacity evidence focused tests:       10 passed
historical Canary evaluation tests:        7 passed
full Python regression:                  835 passed
compileall:                              PASS
git diff --check:                        PASS
```

Accepted historical result:

```text
expected_regime:      risk_off
observed_regime:      risk_off
expected_alert:       true
observed_alert:       true
false positives:      0
false negatives:      0
regime mismatches:    0
historical clean:     true
```

Accepted checked-in runtime boundary:

```text
WORKER_MODE=shadow
UNIVERSE_PROFILE=canary-v0.1
ACQUISITION_MAX_JOBS_PER_TICK=2
ACQUISITION_MAX_PAGES_PER_JOB=10
ACQUISITION_MAX_BARS_PER_JOB=100
NEWS_ACQUISITION_ENABLED=false
cron=* * * * *
```

Conservative shadow projection with 1.25x safety margin:

```text
Worker requests/day:       1,440
D1 rows read/day:        720,000
D1 rows written/day:      14,400
storage warm-up:        1,986,560 bytes
```

Planning-envelope headroom:

```text
Worker requests: 98.56%
D1 rows read:    85.60%
D1 rows written: 85.60%
```

Existing R0-007 custody billing evidence remains classified as a specific read-query observation only:

```text
rows_read:      3906
rows_written:   0
size_after:     4,796,416 bytes
changed_db:     false
returned rows:  1
```

It must not be multiplied by 1,440/day as though it represented one scheduled Worker tick.

### UWBS-086 live-mode boundary

`WORKER_MODE=live` is **NOT COVERED / NOT ACCEPTED** by the shadow capacity acceptance.

Live acquisition introduces additional checkpoint, lease, attempt, normalized-bar, conflict, scheduler-evidence and digest D1 activity. Before live capacity acceptance, obtain measured or defensibly bounded billing rows for representative live/shadow-canary acquisition samples and rerun the same capacity assessment.

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by the UWBS-086 shadow acceptance.

### Selected restart point

```text
PB lane remains PARKED
UWBS-087 is ACCEPTED
  -> verify UWBS-088 locally
  -> if accepted, advance to UWBS-089
```

## 9. Restart rule

After an interruption:

1. read this tracker;
2. read `CURRENT_CRITICAL_PATH_RECONCILIATION.md`;
3. use `WBS_PROVISIONAL_ID_REGISTRY.md` for all provisional IDs;
4. preserve accepted runtime evidence;
5. for market-dependent work, refresh only time-dependent preflight inputs;
6. for market-independent work, resume at the first incomplete canonical dependency.

Do not reopen accepted boundaries merely because a calendar day changed. Reopen capacity only if the accepted runtime boundary materially changes, especially `WORKER_MODE=live`, cron cadence, D1 schema/indexes, digest retention, news enablement, or acquisition limits.
