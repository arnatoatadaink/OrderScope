# OrderScope — Local Corporate Intelligence Integrated Critical Path

Status: non-normative execution plan
Date: 2026-09-05
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Extension WBS: `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Normative spec: `stock_monitoring_v0.1_spec.md`

## 1. Purpose

Integrate the Analyst Consensus / Cross-Market Context `A0` extension into the Local Corporate Intelligence critical path established on 2026-09-04.

This document does not change completion conditions. It overlays Parent WBS dependencies, extension-WBS dependencies, and current repository state to define the next safe execution order.

## 2. Delta since the 2026-09-04 CP baseline

Since baseline commit `b60f562d027fb4226baf82162ec5e21a447ca7a1`, the newly WBS-defined package is `A0`, introduced through:

- `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
- `docs/ANALYST_CROSS_MARKET_PROGRESS_TRACKER_2026-09-05.md`
- updates to `docs/stock_monitoring_v0.1_spec.md`

No other new WBS package was identified in that repository delta.

## 3. Integrated dependency graph

```text
I0-001
  ↓
I0-002  ← current main task
  ├─→ I0-003 ─┐
  ├─→ I0-004 ─┼─→ I0-007 formal acceptance
  └─→ I0-005 ─┤
        │       │
        │       └─→ I0-006 ───────┘
        │
        └─→ A0-001 design complete / implementation acceptance pending
                  ↓
               A0-002 Validation

I0-007
  ↓
S0-002
  ↓
S0-003
  ├─→ S0-004 provisional/completed artifact
  ├─→ S0-005
  └─→ S0-006
        ↓
      S0-007
        ↓
   E0-001..007
        ↓
   N1 / O0 / X0
```

`A0-001` implementation acceptance is gated by Accepted `I0-002` and `I0-005`. `A0-002` depends on A0-001 plus available as-of market/macro/consensus datasets.

## 4. Critical-path decisions

### 4.1 Core Corporate Intelligence delivery CP

The primary delivery path remains:

1. `I0-002`
2. `I0-003` / `I0-004`
3. `I0-005` acceptance
4. `I0-006`
5. `I0-007` formal acceptance
6. `S0-002 → S0-003 → S0-005/S0-006 → S0-007`
7. `E0-001..007`
8. `N1 / O0 / X0`

The A0 extension does not serially extend this core path.

### 4.2 v0.1 Cross-Market acceptance lane

The integrated Definition of Done requires Cross-Market Rotation hypotheses to preserve support/contradiction evidence and FX-direction consistency. Therefore A0-001 schema/contract acceptance is part of the v0.1 acceptance lane.

Once `I0-002/I0-005` are Accepted, A0-001 implementation may proceed in parallel with Core SEC work.

### 4.3 A0-002 treatment

`A0-002` is a concrete CBRS validation case, not currently a serial Core implementation blocker. Treat it as a validation gate for Cross-Market rule quality. Decide later, from validation evidence, whether it becomes mandatory for v0.1 release acceptance.

## 5. Parallel execution plan

### Lane A — Common contracts / main CP

- `I0-002`
- `I0-003` / `I0-004`
- `I0-005` acceptance
- `I0-006`
- `I0-007` formal acceptance

### Lane B — Local foundation

- `L0-002 → L0-003/L0-004/L0-005 → L0-006`
- `L1-001 → L1-002 → L1-004 → L1-005` via fixture path

`L1-003` waits for the `SMOKE-007` change window and must not block other lanes.

### Lane C — Cross-Market extension

- Keep `A0-001` design complete.
- After `I0-002/I0-005` acceptance, apply its fields/schema/fixtures.
- `A0-002` may advance through as-of dataset definition and source availability checks before final Hypothesis-record schema write.

### Lane D — SEC / Earnings

Start after `I0-007` acceptance:

- `S0-002 → S0-003`
- run `S0-005` / `S0-006` in parallel
- connect existing `S0-004`
- `S0-007`
- `E0-001..007`

## 6. Added-task integration audit

| Addition | Spec | WBS | CP | State |
|---|---|---|---|---|
| Analyst Consensus tracking | Included | A0 validation input | Integrated as A0 lane | Provider/as-of dataset unresolved |
| Macro / Cross-Market Context | Included | `A0-001/002` | Integrated | A0-001 design complete; acceptance pending |
| FX contradiction rule | Included | `A0-001` | Branches from `I0-002/I0-005` | Design complete |
| CBRS Multi-Layer Flow Validation | Separate validation case | `A0-002` | Validation lane | Not started |

Classification:
- Spec + WBS + CP integrated: `A0-001`
- WBS + CP integrated, validation not started: `A0-002`
- No additional untracked WBS package found in the post-baseline repository delta

## 7. Current execution priority

1. Finish `I0-002` as the main task.
2. Run `I0-003` and `I0-004` in parallel.
3. Align `I0-005` to I0-002 provenance types and make it Accepted.
4. At the same point, apply A0-001 fields (`fx_direction_consistency`, evidence refs, confidence ordinal) to Interpretation/Hypothesis schema.
5. Finish `I0-006` and formal acceptance of `I0-007`.
6. In parallel with SEC work, finalize A0-002 as-of dataset definitions and source availability.

## 8. Restart rules

- Main session: `I0-002`
- Second parallel session: `L0-002`
- A0 session: dataset/source definition for `A0-002` may proceed; schema writes wait for Accepted `I0-002/I0-005`
- Preserve provisional artifacts for `I0-005`, `I0-007`, and `S0-004`; reconcile and formally accept after dependencies are satisfied

## 9. Unresolved items

- Provider and contract conditions for Analyst Consensus as-of history
- Final AI/Semiconductor proxy for A0-002
- short/borrow provider for H4 validation
- whether A0-002 becomes mandatory for v0.1 release acceptance

Do not infer these values. Resolve them only from confirmed source/contract information or validation evidence.
