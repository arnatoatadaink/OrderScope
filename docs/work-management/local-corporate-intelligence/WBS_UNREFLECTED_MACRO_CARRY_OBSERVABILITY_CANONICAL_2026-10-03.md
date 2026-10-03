# OrderScope — WBS-Unreflected Macro Carry Observability Canonical Remap

Date: 2026-10-03
Status: Active planning extension — canonical post-collision ID
Historical source branch: `docs/uwbs-101-macro-carry-observability`
Historical source file: `WBS_UNREFLECTED_TASK_BACKLOG_APPEND_UWBS-101_2026-10-01.md`
Historical alias: `UWBS-101` — CONFLICT / FROZEN
Canonical ID: `UWBS-105`

## UWBS-105

| Field | Value |
|---|---|
| UWBS ID | `UWBS-105` |
| Proposed task | Macro Release Surprise / Yen Carry Flow Observability |
| Proposed package | A0 / I0 Cross-Market / Macro Release integration |
| Status | Ready for WBS design |
| Disposition | Pending / Canonical remap from legacy `UWBS-101` |
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

### Minimum implementation unit

1. U.S. Macro Release Fact — PCE and Durable Goods actual / consensus / prior / revision / release/reference timestamps / provenance.
2. Macro Surprise -> Rate Transmission — deterministic surprise metrics, U.S. 2Y / Japan 2Y / spread, spread velocity, bounded event windows, USDJPY and supported confirmations.
3. Carry Flow State — `CARRY_BUILD`, `CARRY_STABLE`, `CARRY_COOLING`, reusing existing unwind/deleveraging states.

### Canonical CP relationship

```text
UWBS-011 + UWBS-012
        |
        v
UWBS-105A Macro Release Fact / Surprise
        |
        v
UWBS-105B Event-window Rate / FX Transmission
        |
        v
UWBS-105C Carry BUILD / STABLE / COOLING
        |
        v
UWBS-013 CARRY_UNWIND_CANDIDATE
        |
        v
DELEVERAGING_REGIME
```

The A/B/C labels are decomposition candidates, not separate UWBS IDs.

## Historical alias rule

Any old `UWBS-101` reference whose surrounding text mentions PCE, Durable Goods, macro surprise, U.S.-Japan 2Y spread, USDJPY, yen carry, `CARRY_BUILD`, `CARRY_STABLE`, or `CARRY_COOLING` is interpreted as canonical `UWBS-105`.

If `UWBS-101` appears without enough context to distinguish Macro / Carry from Crypto On-chain, it must remain marked ambiguous rather than guessed.
