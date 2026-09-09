# OrderScope — Local Corporate Intelligence Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-09
Parent WBS: `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Extension WBS: `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Model assignment: `MODEL_ASSIGNMENT_POLICY_2026-09-05.md`
Runtime-status authority: **this file**

## 1. Purpose and authority

This file is the sole integrated authority for Local Corporate Intelligence runtime progress. Parent WBS owns completion conditions; Integrated Critical Path owns static dependencies/permanent gates. Runtime progress alone does not modify those static documents.

## 2. Integrated snapshot

### Corporate information

| Lane / task | Status |
|---|---|
| I0-001..007 | Accepted |
| S0-001..007 | Accepted |
| E0-001..007 | Accepted |
| O0-001..005 | Accepted |
| N0-001..004 | Accepted |
| N1-001..005 | Accepted |
| N1-006 | Ready* |

`*` Needs a credible 1–3 month News-vs-SEC/IR evaluation dataset/window.

### Local foundation / market import

| Task | Status | Evidence / next action |
|---|---|---|
| L0-001 | Accepted / inherited prerequisite | Reference only |
| L0-002 | Accepted | Scaffold/Git boundary complete |
| L0-003 | Ready | Config/secret boundary is the next foundation gate before L0-006/X0-004 |
| L0-004 | Accepted | focused 11; full 418; diff clean; upstream deprecation warnings non-blocking |
| L0-005 | Accepted | focused 7; full 352; compileall success; diff clean |
| L0-006 | Not started | Waits for L0-003/L0-004/L0-005 |
| L1-001 | Accepted | focused 8; full 360; diff clean |
| L1-002 | Accepted | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-003 | Blocked | Requires separately approved `SMOKE-007` remote D1 window |
| L1-004 | Accepted — fixture path | focused 11; full 372; diff clean |
| L1-005 | Accepted — fixture path | focused 12; full 391; diff clean |
| L1-006 | Ready | L0-004 and L1-005 are Accepted; separate import/dataset API task remains |

## 3. X0 runtime state

| Task | Status | Reason / next action |
|---|---|---|
| X0-001 | Accepted | focused 7; full 398; diff clean |
| X0-002 | Accepted | focused 9; full 407; diff clean |
| X0-003 | Provisional result | Localhost read-only API implementation complete; local verification pending |
| X0-004 | Blocked | Depends on adapter availability + L0-006 |
| X0-005 | Not started | Depends on X0-001..004 |
| X0-006 | Not started | Depends on X0-005 |

Real D1 promotion remains separately gated by L1-003 and must not be conflated with fixture-path X0 development.

## 4. Current X0-003 implementation boundary

`analysis/app/orderscope_local/local_api/read_api.py` extends the accepted localhost-only FastAPI surface.

Read-only routes:

```text
GET /health
GET /facts
GET /filings
GET /earnings
GET /news
GET /sources/health
```

Properties:

- reuses `LocalServerBinding`, so bind remains literal `127.0.0.1` only;
- `/facts` enforces source availability/internal acceptance as-of visibility;
- optional subject filtering is exact and does not infer aliases;
- `/filings`, `/earnings`, and `/news` reuse X0-001 source-kind classification;
- `/sources/health` serializes the accepted X0-002 coverage summary rather than recomputing adapter state;
- no provider/raw body, credentials, or temporary content is exposed;
- no HTTP mutation route is defined.

Focused local verification is pending.

## 5. Primary integration path

After X0-003 acceptance, scheduler work remains gated by Local foundation:

```text
L0-003 config/secret boundary
  -> L0-006 CLI entry point
  -> X0-004 local scheduler
```

`L1-006` is now independently Ready because both L0-004 and L1-005 are Accepted; it can be implemented as a separate read-only import/dataset API cycle without blocking the scheduler path.

## 6. Parallel/deferred lanes

- `L0-003` should be the next primary foundation task after X0-003 acceptance because it opens L0-006.
- `L1-006` is Ready as a parallel read-only API extension.
- `L1-003` remains externally Blocked and does not invalidate fixture-path work.
- `N1-006` remains important for News quality but is not the current X0 integration blocker.
- `A0-001` remains Provisional and `A0-002` remains separate validation work.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 7. Current restart rule

1. Run X0-003 focused/full/compileall/diff verification.
2. If X0-003 passes, promote it to Accepted.
3. Complete `L0-003 — config/secret boundary`, then `L0-006 — CLI entry point` before X0-004 scheduler work.
4. `L1-006` may proceed in a separate bounded API cycle.
5. Keep L1-003/SMOKE-007 real-D1 work separate.

## 8. Latest acceptance evidence

| Task | Evidence |
|---|---|
| L0-005 | focused 7; full 352; compileall success; diff clean; upstream 0/0 |
| L1-001 | focused 8; full 360; diff clean |
| L1-002 | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-004 fixture | focused 11; full 372; diff clean |
| L1-005 fixture | focused 12; full 391; diff clean |
| X0-001 | focused 7; full 398; diff clean |
| X0-002 | focused 9; full 407; diff clean |
| L0-004 | focused 11; full 418; diff clean; dependency deprecation warnings non-blocking |

## 9. Unresolved items

- `SMOKE-007` / L1-003 approved remote D1 export window and real-data evidence.
- Production exchange calendar/holiday/short-session source.
- N1-006 evaluation window/history availability.
- Analyst Consensus as-of provider/terms.
- A0-002 AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.
- FastAPI/Starlette/AnyIO test-client deprecation warnings should be handled in dependency maintenance, not inside L0-004/X0-003 feature logic.

## 10. Progress-update rule

Update this tracker for normal execution progress. Update WBS/CP only when completion definitions, dependency structure, permanent gates, or safe-parallelization rules actually change.
