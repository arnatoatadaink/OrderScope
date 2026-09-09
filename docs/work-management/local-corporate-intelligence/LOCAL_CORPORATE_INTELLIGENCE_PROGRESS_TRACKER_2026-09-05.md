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
| L0-003 | Ready | Config/secret boundary remains separate work |
| L0-004 | Ready | Localhost health remains separate work |
| L0-005 | Accepted | focused 7; full 352; compileall success; diff clean |
| L0-006 | Not started | Waits for L0-003/L0-004/L0-005 |
| L1-001 | Accepted | focused 8; full 360; diff clean |
| L1-002 | Accepted | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-003 | Blocked | Requires separately approved `SMOKE-007` remote D1 window |
| L1-004 | Accepted — fixture path | focused 11; full 372; diff clean |
| L1-005 | Accepted — fixture path | focused 12; full 391; diff clean |
| L1-006 | Not started | Depends on L0-004 and L1-005 |

## 3. X0 runtime state

| Task | Status | Reason / next action |
|---|---|---|
| X0-001 | Provisional result | Unified timeline implementation complete; local verification pending |
| X0-002 | Ready for separate design/implementation cycle | Coverage summary still needed before X0-003 |
| X0-003 | Blocked | Depends on L0-004 + X0-001 + X0-002 |
| X0-004 | Blocked | Depends on adapter availability + L0-006 |
| X0-005 | Not started | Depends on X0-001..004 |
| X0-006 | Not started | Depends on X0-005 |

The explicit X0-001 dependencies are satisfied on the fixture path:

```text
L1-005 Accepted
I0-005 Accepted
E0-007 Accepted
N1-005 Accepted
O0-005 Accepted
```

Real D1 promotion is still separately gated by L1-003 and must not be conflated with fixture-path X0 development.

## 4. Current X0-001 boundary

`analysis/app/orderscope_local/integration/timeline.py` implements a read-only deterministic as-of timeline.

Knowledge-order semantics:

- Fact visibility requires `provenance.available_at <= as_of` and `Fact.accepted_at <= as_of`;
- market bar visibility uses canonical `receipt_time <= as_of`;
- sorting is by availability/acceptance and deterministic tie-break fields;
- exact UTC source event instants may be exposed as metadata;
- date-only source timestamps are never coerced into invented instants;
- Fact values/raw bodies/raw D1 fixture content are not duplicated into TimelineItem records.

Focused local verification is pending.

## 5. Parallel/deferred lanes

- `L0-003` and `L0-004` remain Ready and are required before `L0-006`; `L0-004` is also required for X0-003.
- `L1-003` remains externally Blocked and does not invalidate fixture-path work.
- `N1-006` remains important for News quality but is not the current X0 integration blocker.
- `A0-001` remains Provisional and `A0-002` remains separate validation work.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 6. Current restart rule

1. Run X0-001 focused/full/compileall/diff verification.
2. If X0-001 passes, promote it to Accepted.
3. Before X0-003, complete both `X0-002` and `L0-004`.
4. Before X0-004, complete `L0-003`, `L0-004`, then `L0-006`.
5. Keep L1-003/SMOKE-007 real-D1 work separate.

## 7. Latest acceptance evidence

| Task | Evidence |
|---|---|
| L0-005 | focused 7; full 352; compileall success; diff clean; upstream 0/0 |
| L1-001 | focused 8; full 360; diff clean |
| L1-002 | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-004 fixture | focused 11; full 372; diff clean |
| L1-005 fixture | focused 12; full 391; diff clean |

## 8. Unresolved items

- `SMOKE-007` / L1-003 approved remote D1 export window and real-data evidence.
- Production exchange calendar/holiday/short-session source.
- N1-006 evaluation window/history availability.
- Analyst Consensus as-of provider/terms.
- A0-002 AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.

## 9. Progress-update rule

Update this tracker for normal execution progress. Update WBS/CP only when completion definitions, dependency structure, permanent gates, or safe-parallelization rules actually change.
