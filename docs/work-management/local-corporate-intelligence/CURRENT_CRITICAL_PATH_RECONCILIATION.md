# OrderScope — Current Critical Path Reconciliation

Status: **CURRENT OPERATING INDEX**
Scope: Local Corporate Intelligence / L1-003 / cross-market extension governance
Branch: `l1-003-local-market-recovery`

## 1. Purpose

This document is the date-independent restart index for the active branch.
It reconciles the currently accepted PB preparation state, the current integrated
progress tracker, and the append-only WBS-unreflected backlog.

Historical dated plans remain evidence of their original runs. When their status
text conflicts with a newer accepted closeout or this reconciliation, use the
newer accepted evidence and this index to select the restart point.

Current companion authorities:

- `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`
- `WBS_PROVISIONAL_ID_REGISTRY.md`
- latest package-specific acceptance / closeout evidence

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

The PB lane is therefore **PARKED UNTIL ITS NEXT INTENTIONALLY OPENED ACTIVE
MARKET-SESSION WINDOW**. Accepted PB-04..PB-08 work is not repeated merely
because a calendar day changes.

When PB work resumes, use the moving-retention / re-freeze runbook and obtain a
fresh read-only market-session packet before any authorization or remote
mutation.

## 3. Integrated tracker reconciliation

The older dated tracker
`LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` remains historical
acceptance evidence. Its old L1-003 status is no longer the current restart
state.

Current operating status is now carried by:

`CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`

This preserves the dated tracker without rewriting historical evidence while
providing one date-independent current runtime/planning overlay.

Updating tracker governance does not authorize or repeat accepted runtime work.

## 4. WBS-unreflected backlog identifier normalization

The append-only backlog reused provisional identifiers already incorporated by
the formal Analyst / Cross-Market WBS.

Reserved incorporated examples:

```text
UWBS-030 -> A0-011
UWBS-031 -> A0-012
UWBS-032 -> A0-013
UWBS-033 -> A0-014
UWBS-034 -> A0-015
UWBS-035 -> A0-016
UWBS-036 -> A0-017
```

Later historical backlog rows that reused these numbers are now treated as
legacy aliases only.

Canonical registry:

`WBS_PROVISIONAL_ID_REGISTRY.md`

Canonical later ranges:

```text
UWBS-062..066  AI-theme lane
UWBS-067       LVWR listing-compliance fixture
UWBS-068..079  crypto market-structure / derivatives lane
UWBS-080..086  oil / commodity / cross-asset lane
UWBS-087..093  Physical-SaaS lane
```

Historical backlog text remains unchanged for provenance. New WBS, CP,
implementation and acceptance records must use the canonical IDs.

## 5. GOV-CP-01 result

### GOV-CP-01 — Normalize provisional backlog identifiers and sync the tracker

Status: **COMPLETE FOR ACTIVE PLANNING**

Completion result:

1. existing incorporated formal WBS mappings are preserved;
2. later colliding backlog rows have unique canonical IDs in the registry;
3. historical aliases are retained rather than destructively rewritten;
4. Discovery/CP interpretation is normalized by the canonical registry;
5. known incorporated R0/A0 dispositions are recorded in the registry/current tracker;
6. current L1-003/PB state is represented in the date-independent integrated tracker;
7. future active provisional references have one canonical task meaning.

No provider activation, Worker/Cron change, D1 mutation, PB authorization, or
trading action occurred as part of GOV-CP-01.

## 6. Selected market-closed restart point

The next market-independent feature lane is canonical:

```text
UWBS-080 — Define direct WTI / Brent Macro Instrument contract and provider survey
```

Rationale:

- its historical source row was already `Ready for WBS design`;
- it is upstream of the oil-down-reason / Risk-On interpretation chain;
- it can be designed and provider-surveyed while the U.S. market is closed;
- it closes the known gap where USO is only a tradable proxy and cannot be
  treated as canonical crude price;
- downstream commodity fundamentals, event taxonomy, BTC ETF flow and
  cross-asset regime work remain dependency-gated behind the direct commodity
  contract/source decision.

UWBS-080 design/research does not itself activate a live provider.

## 7. Current critical-path view

```text
MARKET-DEPENDENT PB LANE
PB-08 ACCEPTED
  -> PB-09 fresh active-session packet
  -> explicit PB-09 authorization
  -> PB-10 bounded execution
  [PARKED]

MARKET-INDEPENDENT GOVERNANCE / FEATURE LANE
GOV-CP-01 COMPLETE
  -> UWBS-080 direct WTI/Brent contract + provider survey   <-- CURRENT
  -> UWBS-081 / UWBS-082 commodity source + event work
  -> UWBS-083 oil interpretation
  -> UWBS-084 BTC spot ETF flow normalization
  -> UWBS-085 cross-asset Risk-On integration
  -> UWBS-086 historical / capacity Canary
```

The two lanes are intentionally independent. Market-independent work must not
silently alter PB runtime state.

## 8. Restart rule

When selecting work after an interruption:

1. inspect this reconciliation;
2. inspect `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`;
3. resolve provisional IDs through `WBS_PROVISIONAL_ID_REGISTRY.md`;
4. inspect the latest package-specific WBS/CP for the selected lane;
5. preserve accepted evidence;
6. re-run only time-dependent preflight for market/runtime work;
7. for market-independent work, resume at the first incomplete canonical
   dependency rather than repeating completed prerequisites.

Current selected restart:

```text
UWBS-080
  first action: formalize the source-neutral WTI/Brent instrument contract and
                provider-survey acceptance boundary
```
