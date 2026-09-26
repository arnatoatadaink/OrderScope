# OrderScope — Current Critical Path Reconciliation

Status: **CURRENT OPERATING INDEX**
Scope: Local Corporate Intelligence / L1-003 / cross-market extension governance
Branch: `l1-003-local-market-recovery`

## 1. Purpose

This document is the date-independent restart index for the active branch.
It reconciles the currently accepted PB preparation state with the older
integrated progress tracker and the append-only WBS-unreflected backlog.

Historical dated plans remain evidence of their original runs. When their
status text conflicts with a newer accepted closeout or this reconciliation,
use the newer accepted evidence and this index to select the restart point.

## 2. PB / L1-003 lane

Current controlling state:

```text
PB-00..PB-03       accepted preparation/history
PB-04 / PB-05      COMPLETE / ACCEPTED
PB-06              ACCEPTED
PB-07              ACCEPTED
PB-08              ACCEPTED; safe closed
PB-09 preparation  COMPLETE
PB-09 execution    requires fresh active-session entry packet and explicit authorization
PB-10              not authorized / not executed
```

The PB lane is therefore **PARKED WHILE THE APPLICABLE U.S. MARKET SESSION IS
CLOSED**. Accepted PB-04..PB-08 work is not repeated merely because a calendar
day changes.

When PB work resumes, use the moving-retention / re-freeze runbook and obtain a
fresh read-only market-session packet before any authorization or remote
mutation.

## 3. Integrated tracker reconciliation debt

`LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` predates the
current PB closeouts and still contains older L1-003 restart language.

Until that tracker is revised, the authoritative PB status is:

1. the latest accepted PB closeouts;
2. `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md` current-progress table;
3. `L1-003_PB08_MOVING_RETENTION_REFREEZE_RUNBOOK.md` for restart procedure;
4. this reconciliation document for restart selection.

Updating the integrated tracker is a governance task, not a reason to repeat
accepted runtime work.

## 4. WBS-unreflected backlog identifier collision

The append-only backlog correctly states that `UWBS-*` identifiers are
provisional tracking IDs, but later additions reused identifiers already
incorporated by the formal Analyst / Cross-Market WBS.

Confirmed collision examples:

```text
Formal Analyst/Cross-Market WBS
  UWBS-030 -> A0-011  relative repricing / overshoot state work
  UWBS-031 -> A0-012  CBRS Canary
  UWBS-032 -> A0-013  U.S. Treasury adapter
  UWBS-033 -> A0-014  New York Fed adapter
  UWBS-034 -> A0-015  BOJ/MOF adapter
  UWBS-035 -> A0-016  FRED/ALFRED fallback adapter
  UWBS-036 -> A0-017  CFTC positioning adapter

Later append-only backlog
  UWBS-030..034      AI-theme decomposition lane
  UWBS-035           LVWR listing-compliance fixture
  UWBS-036..047      crypto market-structure / derivatives lane
```

Therefore `UWBS-030..047` cannot be used as unambiguous cross-document task
identifiers until the backlog is normalized.

This is a planning/governance defect only. It does not invalidate already
accepted source code, fixtures, PB evidence, or formally mapped A0 tasks.

## 5. Selected market-closed restart point

### GOV-CP-01 — Normalize provisional backlog identifiers and sync the tracker

This is the immediate restart point while the market-dependent PB lane is
parked.

Completion conditions:

1. preserve every backlog row and its provenance;
2. preserve all existing final WBS mappings;
3. assign unique provisional IDs to later rows that collide with already
   incorporated IDs;
4. update Discovery references and CP candidate arrows to the new provisional
   IDs;
5. repair the backlog mapping table so incorporated rows show their actual
   dispositions where already known;
6. update the integrated progress tracker so L1-003 points to the current PB
   state rather than the historical restart state;
7. run a repository search proving that each active provisional `UWBS-*` ID has
   one unambiguous task meaning.

No provider activation, Worker/Cron change, D1 mutation, PB authorization, or
trading action is part of GOV-CP-01.

## 6. First implementation lane after GOV-CP-01

After governance normalization, the preferred market-independent feature lane
is the direct oil / commodity macro extension, beginning with the task currently
named:

```text
Define direct WTI / Brent Macro Instrument contract and provider survey
```

Rationale:

- it is already marked `Ready for WBS design` in the backlog;
- it is upstream of the oil-down-reason / Risk-On interpretation chain;
- it can be designed and provider-surveyed while the U.S. market is closed;
- it directly closes the known gap where USO is only a tradable proxy and must
  not be treated as canonical crude price;
- downstream commodity fundamentals, event taxonomy, BTC ETF flow and
  cross-asset regime work can remain gated behind its formalized contract.

Do not freeze its final WBS ID until GOV-CP-01 has completed the identifier
normalization.

## 7. Current critical-path view

```text
MARKET-DEPENDENT PB LANE
PB-08 ACCEPTED
  -> PB-09 fresh active-session packet
  -> explicit PB-09 authorization
  -> PB-10 bounded execution
  [PARKED while applicable market session is closed]

MARKET-INDEPENDENT GOVERNANCE LANE
GOV-CP-01 backlog-ID normalization + integrated tracker sync
  -> formalize direct WTI/Brent contract task
  -> commodity source/event tasks
  -> oil interpretation
  -> cross-asset Risk-On integration
  -> historical / capacity Canary
```

The two lanes are intentionally independent. Work on GOV-CP-01 or the later
market-independent design lane must not silently alter PB runtime state.

## 8. Restart rule

When selecting work after an interruption:

1. inspect this reconciliation;
2. inspect the latest package-specific WBS/CP for the selected lane;
3. preserve accepted evidence;
4. re-run only time-dependent preflight for market/runtime work;
5. for market-independent work, resume at the first incomplete dependency in
   the selected CP rather than repeating completed prerequisites.

Current selected restart:

```text
GOV-CP-01
  first action: normalize WBS-unreflected provisional IDs and dispositions
```
