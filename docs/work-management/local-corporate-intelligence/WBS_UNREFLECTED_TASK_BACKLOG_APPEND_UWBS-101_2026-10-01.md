# OrderScope — WBS/CP Unreflected Backlog Append

Status: **Captured — intended for canonical backlog consolidation**
Date: 2026-10-01
Canonical backlog: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
Source report: `docs/work-management/local-corporate-intelligence/REPORT_MACRO_RELEASE_YEN_CARRY_FLOW_OBSERVABILITY_2026-10-01.md`

## Registration note

The canonical backlog on `main` currently records the accepted macro/carry foundation as `UWBS-011..015`, while repository feature work has already progressed through `UWBS-100`. A repository/branch search found no existing `UWBS-101` identifier at registration time.

This append file therefore reserves `UWBS-101` without renumbering or rewriting the canonical append-only backlog. It should be folded into the canonical backlog during the next backlog consolidation/WBS revision.

## UWBS-101

| Field | Value |
|---|---|
| UWBS ID | `UWBS-101` |
| Proposed task | Macro Release Surprise / Yen Carry Flow Observability |
| Proposed package | A0 / I0 Cross-Market / Macro Release integration |
| Status | `Ready for WBS design` |
| Disposition | Pending |
| Git type | `T1-code`; split provider acquisition into `T2-data` only if a new external data path is required |
| Source | `REPORT_MACRO_RELEASE_YEN_CARRY_FLOW_OBSERVABILITY_2026-10-01.md` |

### Unreflected task name

PCE / Durable Goods official-release Facts and yen-carry transmission / flow-inference integration.

### Design policy

- Reuse `UWBS-011..015`; do not create a duplicate rate/FX/carry framework.
- Store official macro observations, timestamps, revisions and provenance as Facts.
- Store `actual - consensus` surprise and market event-window changes as Derived Metrics.
- Keep carry state as Interpretation; never store inferred capital movement as Fact.
- Add `CARRY_BUILD`, `CARRY_STABLE`, and `CARRY_COOLING` around the existing `CARRY_UNWIND_CANDIDATE` / `DELEVERAGING_REGIME` states.
- Do not allow one PCE/Durable Goods release, USD/JPY alone, or one news item to establish a carry unwind.
- Preserve contradictory and missing evidence explicitly.

### Minimum implementation unit

1. **U.S. Macro Release Fact**
   - PCE: headline/core MoM/YoY, personal income, nominal/real PCE.
   - Durable Goods: headline, ex-transportation, core capital goods orders, core capital goods shipments when available.
   - actual, consensus, prior/revision, release/reference timestamps, source/provenance.

2. **Macro Surprise -> Rate Transmission**
   - deterministic surprise metrics,
   - U.S. 2Y / Japan 2Y / U.S.-Japan 2Y spread,
   - spread velocity,
   - bounded `30m / 2h / 1d` event-window deltas,
   - USD/JPY plus supported cross-JPY/risk-asset confirmations.

3. **Carry Flow State**
   - `CARRY_BUILD`,
   - `CARRY_STABLE`,
   - `CARRY_COOLING`,
   - reuse existing `CARRY_UNWIND_CANDIDATE`,
   - reuse existing `DELEVERAGING_REGIME` as higher-order state.

### Acceptance conditions

1. PCE and Durable Goods records preserve actual, consensus, prior/revision, release/reference timestamps and source provenance.
2. Surprise values are deterministic and unit-safe.
3. Event-window deltas are reproducible and free of lookahead contamination.
4. Soft PCE + lower U.S. 2Y + narrower U.S.-Japan 2Y spread + lower USD/JPY is classified no higher than `CARRY_COOLING` unless independent confirmation exists.
5. `CARRY_UNWIND_CANDIDATE` requires at least one additional independent confirmation domain under the existing UWBS-013 evidence rules.
6. Missing policy-futures, cross-JPY, consensus or volatility inputs reduce confidence / become `UNKNOWN`; they are not guessed or imputed.
7. Contradictory evidence is retained and affects confidence.
8. Tests cover false positives, stale/closed-market observations, revisions, missing consensus and contradictory evidence.
9. Existing `UWBS-011..014` Fact / Derived Metric / Interpretation boundaries remain intact.

### Uncertainty / unresolved dependencies

- A permissible/reproducible market-consensus source for PCE and Durable Goods is not yet confirmed.
- Formal OrderScope support for Fed Funds / SOFR futures as policy-expectation Facts is not confirmed.
- Formal support for AUD/JPY and MXN/JPY in the current FX universe is not confirmed.
- High-frequency fund-flow data availability, licensing and cost remain separate provider questions.

### Existing-task relationship / non-duplication boundary

- `UWBS-011`: supplies normalized Macro-Market Fact structure.
- `UWBS-012`: supplies U.S.-Japan spread and rate/FX Derived Metrics.
- `UWBS-013`: supplies existing carry-unwind/deleveraging Interpretation rules.
- `UWBS-014`: supplies macro-stress/carry validation pattern.
- `UWBS-015`: owns source/provider survey concerns.

`UWBS-101` is non-duplicate because it introduces **official macro-release Fact + consensus/revision + surprise + event-window transmission + cooling/build state** before the already-defined carry-unwind interpretation.

## Proposed CP relationship

```text
UWBS-011 + UWBS-012
        |
        v
UWBS-101A Macro Release Fact / Surprise
        |
        v
UWBS-101B Event-window Rate / FX Transmission
        |
        v
UWBS-101C Carry BUILD / STABLE / COOLING
        |
        v
UWBS-013 CARRY_UNWIND_CANDIDATE
        |
        v
DELEVERAGING_REGIME
```

The `A/B/C` labels above are decomposition candidates, not final WBS IDs.
