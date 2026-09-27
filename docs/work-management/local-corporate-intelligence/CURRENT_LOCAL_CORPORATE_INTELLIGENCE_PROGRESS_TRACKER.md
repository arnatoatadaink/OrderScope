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
UWBS-086  historical Canary + Worker/D1 capacity acceptance               [SOFTWARE ACCEPTED / HISTORICAL-CAPACITY OPEN]
```

### UWBS-080 current state

Status: **ACCEPTED**

Acceptance evidence: `UWBS-080_LOCAL_ACCEPTANCE_2026-09-27.md`

### UWBS-081 current state

Status: **ACCEPTED**

Acceptance evidence: `UWBS-081_LOCAL_ACCEPTANCE_2026-09-27.md`

```text
commodity fundamental contract: 9 passed
EIA petroleum normalizer:        7 passed
full Python regression:          725 passed
compileall:                      PASS
git diff --check:                PASS
```

### UWBS-082 current state

Status: **ACCEPTED**

Acceptance evidence: `UWBS-082_LOCAL_ACCEPTANCE_2026-09-27.md`

```text
commodity event focused tests: 7 passed
full Python regression:        732 passed
compileall:                    PASS
git diff --check:              PASS
```

### UWBS-083 current state

Status: **ACCEPTED**

Acceptance evidence: `UWBS-083_LOCAL_ACCEPTANCE_2026-09-27.md`

```text
commodity interpretation focused tests: 8 passed
full Python regression:                 740 passed
compileall:                             PASS
git diff --check:                       PASS
```

### UWBS-084 current state

Status: **ACCEPTED**

Acceptance evidence: `UWBS-084_LOCAL_ACCEPTANCE_2026-09-27.md`

```text
BTC spot ETF flow contract:     7 passed
BTC spot ETF flow normalizer:   6 passed
full Python regression:       753 passed
compileall:                    PASS
git diff --check:              PASS
```

### UWBS-085 current state

Status: **ACCEPTED**

Acceptance evidence: `UWBS-085_LOCAL_ACCEPTANCE_2026-09-27.md`

```text
cross-asset regime focused tests: 9 passed
full Python regression:          762 passed
compileall:                      PASS
git diff --check:                PASS
```

Accepted boundary requires multiple independent signal classes and prevents a single BTC move, ETF-flow print or commodity interpretation from establishing a broad Risk-On regime.

### UWBS-086 current state

Status: **SOFTWARE BOUNDARY ACCEPTED / FINAL HISTORICAL-CAPACITY ACCEPTANCE OPEN**

Software acceptance evidence:

`UWBS-086_SOFTWARE_BOUNDARY_ACCEPTANCE_2026-09-27.md`

```text
cross-asset Canary focused tests: 8 passed
replay/capacity focused tests:    10 passed
full Python regression:          780 passed
compileall:                      PASS
git diff --check:                PASS
```

Accepted software boundary now includes:

- deterministic replay/capacity evaluator `cross_asset_canary_replay.py`;
- external `CapacityEnvelope` rather than hard-coded Cloudflare quotas;
- synthetic regression scenarios explicitly labelled synthetic;
- Worker/D1 headroom calculation using the most constrained supplied resource;
- accepted UWBS-083..086 contracts exported through the shared contract namespace.

Current repository-grounded capacity observations:

```text
checked-in cron:              every minute -> 1,440 invocations/day when enabled
internal external ceiling:    40 subrequests/invocation
internal D1 ceiling:          40 executions/invocation
conservative D1 executions:   <= 57,600/day
```

The 57,600 number is statement execution count, **not** rows written/read. Final D1 capacity acceptance therefore still needs measured or defensibly bounded billing rows and storage growth.

Historical evidence audit:

`UWBS-086_HISTORICAL_CAPACITY_EVIDENCE_GAP_2026-09-27.md`

No repository-backed dataset has yet been established that supplies the complete canonical UWBS-080..085 cross-asset inputs for an end-to-end historical regime replay. Synthetic scenarios must not be reported as historical calibration.

### Selected restart point

```text
UWBS-086 historical-capacity evidence
  -> acquire/build repository-backed historical replay packet
  -> replay canonical UWBS-080..085 inputs
  -> summarize false positives / false negatives / regime mismatches
  -> measure or defensibly bound D1 rows read/written + storage growth
  -> calculate Worker/D1 quota headroom
  -> final ACCEPT / REVIEW / REJECT
```

UWBS-086 remains open until historical replay and capacity evidence satisfy the final acceptance prerequisites.

## 9. Restart rule

After an interruption:

1. read this tracker;
2. read `CURRENT_CRITICAL_PATH_RECONCILIATION.md`;
3. use `WBS_PROVISIONAL_ID_REGISTRY.md` for all provisional IDs;
4. preserve accepted runtime evidence;
5. for market-dependent work, refresh only time-dependent preflight inputs;
6. for market-independent work, resume at the first incomplete canonical dependency.

Current restart is `UWBS-086 historical-capacity evidence` unless the user explicitly selects another lane.
