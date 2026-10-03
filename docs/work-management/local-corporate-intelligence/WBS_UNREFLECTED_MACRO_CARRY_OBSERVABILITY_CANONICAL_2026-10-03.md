# OrderScope — WBS-Unreflected Macro Carry Observability Canonical Remap

Date: 2026-10-03
Status: **INCORPORATED / HISTORICAL PLANNING SOURCE — SUPERSEDED FOR EXECUTION**
Historical source branch: `docs/uwbs-101-macro-carry-observability`
Historical source file: `WBS_UNREFLECTED_TASK_BACKLOG_APPEND_UWBS-101_2026-10-01.md`
Historical alias: `UWBS-101` — CONFLICT / FROZEN
Canonical ID: `UWBS-105`
Formal WBS: `A0-018`
Release allocation: `v0.1.12`

> Current execution authority is `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_POST100_2026-10-03.md` together with `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md` and the CURRENT CP. This file is retained to preserve the planning/remap provenance that led to A0-018.

## UWBS-105 historical planning record

| Field | Value |
|---|---|
| UWBS ID | `UWBS-105` |
| Task | Macro Release Surprise / Yen Carry Flow Observability |
| Package | A0 / I0 Cross-Market / Macro Release integration |
| Historical planning state | Ready for WBS design |
| Current disposition | **Incorporated -> A0-018; implementation pending; v0.1.12** |
| Git type | `T1-code`; split provider acquisition into `T2-data` only if a new external data path is required |
| Historical source | `docs/uwbs-101-macro-carry-observability` / `WBS_UNREFLECTED_TASK_BACKLOG_APPEND_UWBS-101_2026-10-01.md` |

### Scope

PCE / Durable Goods official-release Facts and yen-carry transmission / flow-inference integration.

### Design policy

- Reuse `UWBS-011..015`; do not create a duplicate rate/FX/carry framework.
- Store official macro observations, timestamps, revisions and provenance as Facts.
- Store `actual - consensus` surprise and market event-window changes as Derived Metrics.
- Keep carry state as Interpretation; never store inferred capital movement as Fact.
- Add `CARRY_BUILD`, `CARRY_STABLE`, and `CARRY_COOLING` around the existing `CARRY_UNWIND_CANDIDATE` / `DELEVERAGING_REGIME` states.
- Preserve contradictory and missing evidence explicitly.

### Historical minimum implementation decomposition

1. U.S. Macro Release Fact — PCE and Durable Goods actual / consensus / prior / revision / release/reference timestamps / provenance.
2. Macro Surprise -> Rate Transmission — deterministic surprise metrics, U.S. 2Y / Japan 2Y / spread, spread velocity, bounded event windows, USDJPY and supported confirmations.
3. Carry Flow State — `CARRY_BUILD`, `CARRY_STABLE`, `CARRY_COOLING`, reusing existing unwind/deleveraging states.

The current release CP expresses these as REL-12A..REL-12D under the single formal task A0-018.

### Canonical relationship

```text
A0-003 + A0-004 + A0-013..016
        |
        v
A0-018 / UWBS-105
        |
        v
A0-005 existing CARRY_UNWIND_CANDIDATE / DELEVERAGING path
```

Historical labels `UWBS-105A/B/C` were decomposition candidates only and are not WBS IDs.

## Historical alias rule

Any old `UWBS-101` reference whose surrounding text mentions PCE, Durable Goods, macro surprise, U.S.-Japan 2Y spread, USDJPY, yen carry, `CARRY_BUILD`, `CARRY_STABLE`, or `CARRY_COOLING` is interpreted as canonical `UWBS-105 / A0-018`.

If `UWBS-101` appears without enough context to distinguish Macro / Carry from Crypto On-chain, it remains `AMBIGUOUS`.

No provider activation, Worker/Cron mutation, D1 mutation, paid procurement, trading action, tag creation, history rewrite, or force push is authorized by this historical planning record.
