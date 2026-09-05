# OrderScope — Local Corporate Intelligence Integrated Critical Path

Status: non-normative dependency plan
Date: 2026-09-05
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Extension WBS: `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Normative spec: `stock_monitoring_v0.1_spec.md`
Progress authority: `work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`

## 1. Purpose and responsibility boundary

This document defines static dependency order, gates, and safe parallelization for Local Corporate Intelligence. It does not own execution status.

Current task state, latest accepted task, blockers, restart point, model actually used, test evidence, and next safe action are maintained only in the Progress Tracker. Do not add `current`, `latest`, `completed`, `ready`, or restart-state annotations here unless they describe a permanent dependency rule rather than runtime progress.

This document does not change WBS completion conditions.

## 2. Integrated dependency graph

```text
I0-001
  ↓
I0-002
  ├─→ I0-003 ─┐
  ├─→ I0-004 ─┼─→ I0-007 formal acceptance
  └─→ I0-005 ─┤
        │       │
        │       └─→ I0-006 ───────┘
        │
        └─→ A0-001 implementation acceptance
                  ↓
               A0-002 Validation

I0-007
  ↓
S0-002
  ↓
S0-003
  ├─→ S0-004
  ├─→ S0-005
  └─→ S0-006
        ↓
      S0-007
        ↓
   E0-001..007
        ↓
   N1 / O0 / X0
```

`A0-001` implementation acceptance requires Accepted `I0-002` and `I0-005`. `A0-002` depends on A0-001 plus available as-of market/macro/consensus datasets.

## 3. Core Corporate Intelligence dependency path

The primary dependency path is:

1. `I0-002`
2. `I0-003` and `I0-004`
3. `I0-005` acceptance
4. `I0-006`
5. `I0-007` formal acceptance
6. `S0-002 → S0-003 → S0-005/S0-006 → S0-007`
7. `E0-001..007`
8. `N1 / O0 / X0`

The A0 extension does not serially extend this Core path.

## 4. Parallelization rules

### Lane A — Common contracts

Dependency shape:

- `I0-002 → I0-003`
- `I0-002 → I0-004`
- `I0-002 → I0-005`
- `I0-005 → I0-006`
- `I0-003 + I0-004 + I0-006 → I0-007 formal acceptance`

`I0-003` and `I0-004` may run in parallel after I0-002 acceptance if their file/schema boundaries do not overlap unsafely.

### Lane B — Local foundation

- `L0-002 → L0-003/L0-004/L0-005 → L0-006`
- `L1-001 → L1-002 → L1-004 → L1-005` via fixture path

`L1-003` requires the separately approved `SMOKE-007` change window. That external gate must not block the fixture path.

### Lane C — Cross-Market extension

- `A0-001` design may precede its implementation acceptance.
- A0-001 schema/fixture integration waits for Accepted `I0-002` and `I0-005`.
- `A0-002` dataset/source definition may proceed before final Hypothesis-record schema write.
- A0-002 is a validation lane, not a serial blocker for Core implementation unless release criteria are explicitly changed later.

### Lane D — SEC / Earnings

This lane opens after `I0-007` formal acceptance:

- `S0-002 → S0-003`
- `S0-005` and `S0-006` may run in parallel after their dependencies are satisfied
- `S0-004`, `S0-005`, and `S0-006 → S0-007`
- `S0-007 → E0-001..007`

## 5. Permanent gate decisions

- Provider-specific schema stays inside adapters.
- Provisional artifacts must be reconciled rather than discarded when their upstream dependencies are later satisfied.
- `L1-003` remote D1 work is independently gated and must not block local fixture implementation.
- A0-001 implementation acceptance is part of the v0.1 Cross-Market acceptance lane.
- A0-002 remains a validation case unless the release Definition of Done is explicitly amended.
- SEC implementation starts only after `I0-007` formal acceptance.

## 6. Added-package integration

The post-2026-09-04 addition integrated by this plan is the `A0` Analyst Consensus / Cross-Market package:

- `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
- `ANALYST_CROSS_MARKET_PROGRESS_TRACKER_2026-09-05.md`
- related additions in `stock_monitoring_v0.1_spec.md`

A0-001 carries the Cross-Market/FX contradiction contract; A0-002 is the concrete validation case.

## 7. Unresolved planning questions

The following remain unresolved planning inputs, not runtime status:

- Provider and contract conditions for Analyst Consensus as-of history
- Final AI/Semiconductor proxy for A0-002
- short/borrow provider for H4 validation
- whether A0-002 becomes mandatory for v0.1 release acceptance

Do not infer these values. Resolve them only from confirmed source/contract information or validation evidence.

## 8. Status lookup rule

For any question equivalent to "what is current", "what is next", "what is blocked", "what was accepted", or "where should work resume", consult only:

`docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`

The Critical Path is updated only when dependency structure, permanent gates, or parallelization rules change.