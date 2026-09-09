# OrderScope — Local Corporate Intelligence Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-09
Parent WBS: `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Extension WBS: `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Model assignment: `MODEL_ASSIGNMENT_POLICY_2026-09-05.md`
Runtime-status authority: **this file**

## 1. Purpose and authority

This file is the sole integrated authority for Local Corporate Intelligence runtime progress. The Parent WBS owns completion conditions and the Integrated Critical Path owns static dependency structure/permanent gates. Runtime advancement alone must not modify those static documents.

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| Accepted | WBS completion conditions and dependencies are satisfied; safe downstream prerequisite |
| Provisional result | Implementation exists but local acceptance or an external gate is still pending |
| Ready | Dependencies are satisfied and work may start |
| Blocked | Waiting on an external window or unresolved upstream gate |
| Not started | Work has not begun or a dependency is still closed |

## 3. Integrated snapshot

### 3.1 Corporate information lanes

| Lane / task | Status | Interpretation |
|---|---|---|
| I0-001..007 | Accepted | Common registry/provenance/checkpoint/identity/Fact/temporary-content/provider contracts complete |
| S0-001..007 | Accepted | SEC acquisition/normalization/Canary acceptance complete |
| E0-001..007 | Accepted | Earnings/fundamental Canary lane complete |
| O0-001..005 | Accepted | Official context lane complete |
| N0-001..004 | Accepted | News provider/metadata/duplicate/body-access lane complete |
| N1-001..005 | Accepted | Taxonomy/extraction/review/retention lane complete |
| N1-006 | Ready* | Needs a credible 1–3 month News-vs-SEC/IR evaluation window |

`*` Dependency-ready; meaningful execution still depends on evaluation data availability.

### 3.2 Local foundation / market import

| Task | Status | Evidence / next action |
|---|---|---|
| L0-001 | Accepted / inherited prerequisite | Reference only |
| L0-002 | Accepted | Scaffold/Git boundary complete |
| L0-003 | Ready | Config/secret boundary remains separate bounded work |
| L0-004 | Ready | Localhost health remains separate bounded work |
| L0-005 | Accepted | SQLite migrations accepted: focused 7, full 352, compileall success, diff clean |
| L0-006 | Not started | Waits for L0-003/L0-004/L0-005 |
| L1-001 | Accepted | D1 manifest contract accepted: focused 8, full 360, diff clean |
| L1-002 | Accepted | Fixture raw import accepted after migration regression fix: storage 7, focused 8, full 368, compileall success, diff clean |
| L1-003 | Blocked | Real D1 export requires separately approved `SMOKE-007` change window |
| L1-004 | Accepted — fixture path | Canonical Parquet fixture path accepted: focused 11, full 372, diff clean; real-data promotion remains gated by L1-003 |
| L1-005 | Provisional result | Market-data quality implementation complete; focused/full local verification pending |
| L1-006 | Not started | Depends on L0-004 and L1-005 |

## 4. Current primary serial path

The remaining fixture-path serial work toward X0-001 is now:

```text
L1-005 fixture acceptance
  -> X0-001 unified timeline
```

`L1-003` remains independently blocked and does not invalidate fixture progress. Real-data promotion must still wait for the approved remote D1/SMOKE-007 window.

## 5. X0 gate reconciliation

`X0-001` static dependencies are:

```text
L1-005 + I0-005 + E0-007 + N1-005 + O0-005
```

Current runtime state:

```text
I0-005  Accepted
E0-007  Accepted
N1-005  Accepted
O0-005  Accepted
L1-005  Provisional result — local verification pending
```

Therefore `X0-001` remains blocked only by formal fixture-path acceptance of L1-005.

## 6. Current L1-005 fixture implementation boundary

`analysis/app/orderscope_local/market_import/quality.py` implements provider-neutral quality evaluation over the persisted canonical Parquet:

- verifies the actual Parquet SHA-256 against the L1-004 dataset descriptor;
- verifies canonical field order/types and schema-version metadata;
- verifies actual row count against the dataset descriptor;
- distinguishes duplicate from conflicting `(symbol, bar_time)` identities;
- revalidates OHLC envelope, finite/non-negative prices, non-negative volume, and receipt ordering;
- checks row provenance against source manifest/artifact identity;
- evaluates explicit caller-supplied UTC `SessionWindow` grids;
- reports missing and off-grid points without interpolation or timestamp snapping;
- returns an immutable deterministic issue report and does not mutate source data.

Exchange holiday/short-session policy is intentionally not embedded in L1-005. A replaceable calendar/provider layer supplies explicit session windows later.

## 7. Parallel/deferred lanes

- L0-003 and L0-004 may proceed as separate bounded cycles after overlap review; both are required before L0-006.
- L1-003 remains deferred behind the approved remote D1 export window.
- N1-006 remains important for News recall quality but is not the current X0-001 serial blocker.
- A0-001 remains Provisional and A0-002 remains a separate validation lane; neither serially blocks Core unless release DoD changes.
- Worker remains Shadow; Local work must not directly change Worker runtime state.

## 8. Current restart rule

- **Main local session:** run L1-005 focused tests/full suite/compileall/diff check.
- If L1-005 passes, promote it to Accepted and reconcile/start `X0-001` as the next main task.
- Do not treat fixture-path acceptance as real-D1 acceptance.
- L0-003/L0-004 remain separate foundation work required later for L0-006/X0-003/X0-004 paths.

## 9. Unresolved items

- `SMOKE-007` / L1-003 approved remote D1 export change window and real-data evidence.
- Exchange calendar/holiday/short-session source for production session-window generation; L1-005 itself remains calendar-provider-neutral.
- N1-006 exact evaluation window and News history availability.
- Analyst Consensus as-of provider/terms.
- A0-002 AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.

## 10. Latest acceptance evidence

| Task | Evidence |
|---|---|
| L0-005 | focused 7; full 352; compileall success; diff clean; upstream 0/0 |
| L1-001 | focused 8; full 360; diff clean |
| L1-002 | migration tests 7; focused 8; full 368; compileall success; diff clean |
| L1-004 fixture | focused 11; full 372; diff clean |

## 11. Progress-update rule

After normal implementation progress, update this tracker only. Update the Critical Path or WBS only if dependency structure, permanent gates, safe-parallelization rules, or completion definitions actually change.
