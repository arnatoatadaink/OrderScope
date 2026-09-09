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
| L1-004 | Provisional result | Fixture canonical Parquet implementation complete; local verification pending |
| L1-005 | Not started | Fixture path waits for L1-004 acceptance |
| L1-006 | Not started | Depends on L0-004 and L1-005 |

## 4. Current primary serial path

The remaining fixture-path serial work toward X0-001 is:

```text
L1-004 fixture acceptance
  -> L1-005 market-data quality
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
L1-005  Not started
```

Therefore `X0-001` remains blocked only by the fixture-market quality path through L1-005.

## 6. Current L1-004 fixture implementation boundary

`analysis/app/orderscope_local/market_import/canonical_bars.py` now implements the fixture path:

- verifies L1-001 manifest byte size and SHA-256;
- loads UTF-8 fixture SQL only into isolated in-memory SQLite;
- requires exact columns `symbol, bar_time, open, high, low, close, volume, receipt_time`;
- normalizes UTC bar/receipt timestamps and validates manifest half-open window;
- validates finite non-negative OHLC, OHLC envelope, and non-negative integer volume;
- rejects duplicate/conflicting `(symbol, bar_time)` keys;
- sorts deterministically by `(symbol, bar_time, receipt_time)`;
- writes Parquet with source manifest/artifact/environment/revision provenance;
- returns only dataset metadata/path/hash, never raw SQL or parsed rows.

Focused local verification is pending before L1-004 can become Accepted.

## 7. Parallel/deferred lanes

- L0-003 and L0-004 may proceed as separate bounded cycles after overlap review; both are required before L0-006.
- L1-003 remains deferred behind the approved remote D1 export window.
- N1-006 remains important for News recall quality but is not the current X0-001 serial blocker.
- A0-001 remains Provisional and A0-002 remains a separate validation lane; neither serially blocks Core unless release DoD changes.
- Worker remains Shadow; Local work must not directly change Worker runtime state.

## 8. Current restart rule

- **Main local session:** run L1-004 fixture tests/full suite/compileall/diff check.
- If L1-004 passes, promote it to Accepted and start `L1-005` as the next main task.
- Do not start X0-001 before L1-005 acceptance.
- Do not treat fixture-path acceptance as real-D1 acceptance.

## 9. Unresolved items

- `SMOKE-007` / L1-003 approved remote D1 export change window and real-data evidence.
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

## 11. Progress-update rule

After normal implementation progress, update this tracker only. Update the Critical Path or WBS only if dependency structure, permanent gates, safe-parallelization rules, or completion definitions actually change.
