# OrderScope — Analyst / Cross-Market Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-05
Scope: `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Parent: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`

## 1. Purpose

Keep Analyst Consensus / Cross-Market Context progress restartable from repository state rather than conversation history.

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| Not started | Dependency is not satisfied or work has not begun |
| Design complete | Schema/contract/decision boundaries are documented; implementation/acceptance remains |
| In progress | Implementation, data acquisition, or validation is underway |
| Validated | Acceptance criteria are satisfied with Evidence |
| Blocked by dependency | Waiting for upstream contract/provider/data |

## 3. Current state

As of 2026-09-05, package `A0` has been added and integrated into the Local Corporate Intelligence Critical Path.

- `A0-001`: FX contradiction conditions for Cross-Market Rotation are design complete.
- `A0-001`: integrated into the v0.1 Cross-Market acceptance lane; implementation acceptance waits for Accepted `I0-002/005`.
- `A0-002`: CBRS 2026-09-01..09-04 Multi-Layer Flow Validation is not started.
- `A0-002`: treated as a parallel validation lane, not a serial blocker for Core SEC/Earnings implementation.
- `A0-002` requires as-of market/macro/consensus data.

## 4. Task ledger

| ID | Status | Artifact | Dependency / blocker | Next action | Updated |
|---|---|---|---|---|---|
| A0-001 | Design complete / CP integrated | `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`; `stock_monitoring_v0.1_spec.md` §14; Integrated CP | Implementation acceptance waits for Accepted I0-002/005 | After provenance/Fact-schema alignment, implement `fx_direction_consistency`, hypothesis evidence refs, and confidence ordinal in Interpretation/Hypothesis types/schema | 2026-09-05 |
| A0-002 | Not started / CP validation lane integrated | Planned: `REPORT_CBRS_MULTI_LAYER_FLOW_VALIDATION_2026-09-05.md` | A0-001 plus CBRS/NVDA/QQQ-or-Nasdaq/AI proxy/UST10Y/JGB10Y/USDJPY/BTC and Consensus as-of data | Define datasets/sources now; after A0-001 implementation contract is fixed, collect 2026-08-26..09-04 data and evaluate five hypotheses | 2026-09-05 |

## 5. A0-001 design decisions

### Separation from Fact

`CROSS_MARKET_CAPITAL_ROTATION_CANDIDATE` is an Interpretation/Hypothesis, not a Fact.

### FX consistency

`fx_direction_consistency` values:
- SUPPORT
- NEUTRAL
- CONTRADICT
- UNKNOWN

If a direct Japan→US rotation is hypothesized while USD/JPY falls materially, that is a contradiction candidate to the simple JPY-selling / USD-buying path.

FX can also move independently because of carry unwind, rate expectations, hedging, intervention risk, etc.; FX alone neither promotes the hypothesis to Fact nor fully rejects it.

### Confidence

v0.1 uses ordinal confidence only:
- HIGH
- MEDIUM
- LOW
- UNKNOWN

A major FX contradiction prevents HIGH unless other independent support Evidence is strong enough.

## 6. A0-002 initial hypotheses

- H1 Global Macro Relief
- H2 AI Theme Flow
- H3 CBRS-specific Repricing
- H4 Short Covering
- H5 Japan → US Capital Rotation

Known Evidence candidates:
- H5 contradiction candidate: USD/JPY roughly 160 → 155 → 156
- H3 support candidate: positive CBRS corporate news + consensus gap
- H1/H2: market/theme proxy comparison not yet performed
- H4: short/borrow data not yet acquired

## 7. CP integration decision

`A0-001` belongs to the v0.1 acceptance lane because the integrated Definition of Done requires Evidence and FX-direction consistency for Cross-Market Rotation hypotheses.

The specific CBRS case in `A0-002` is not currently a named Definition-of-Done requirement, so it is not a serial Core blocker. Treat it as an empirical validation lane and decide later whether to promote it to a mandatory release gate.

## 8. Restart point

The main CP continues at `I0-002`.

The shortest A0 work that can proceed independently is `A0-002` source verification and as-of dataset definition. Schema implementation waits for Accepted `I0-002/005`, after which A0-001 fields can be applied to the Fact Store / Interpretation schema.
