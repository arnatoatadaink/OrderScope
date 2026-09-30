# OrderScope — Macro Release / Yen Carry Flow Observability Report

Status: **Planning report — WBS/CP unreflected**
Date: 2026-10-01
Scope: PCE, Durable Goods, U.S./Japan short-rate differential, JPY crosses, and cross-market capital-flow inference
Related existing work: `UWBS-011` through `UWBS-015` (Macro-Market Fact / Derived Metric / carry-unwind / provider work)

## 1. Executive conclusion

OrderScope already contains most of the **market-response side** needed to observe yen-carry conditions: sovereign yields, U.S.-Japan 2Y/10Y spreads, spread velocity, USD/JPY context, multi-domain carry-unwind interpretation, and cross-market validation.

The missing scope is primarily the **causal macro-release side**. PCE and Durable Goods should be represented as official release Facts with consensus/revision metadata and deterministic surprise metrics, then linked to existing rate/FX/cross-market observations through event windows.

Therefore this proposal does **not** introduce a second generic carry-unwind framework. It extends the existing `UWBS-011..015` foundation with:

1. normalized U.S. macro-release Facts,
2. deterministic release-surprise Derived Metrics,
3. event-window rate/FX transmission measurements, and
4. a bounded carry-state interpretation that distinguishes cooling from actual unwind.

The minimum useful system is sufficient to observe whether yen-carry **incentive is building, stable, cooling, or plausibly unwinding**, but it must not claim direct observation of capital flows unless an eligible flow dataset explicitly measures them.

## 2. Existing coverage and non-duplication boundary

The canonical WBS-unreflected backlog already defines:

- `UWBS-011`: normalized Macro-Market non-price Facts,
- `UWBS-012`: rate-curve and cross-country Derived Metrics including U.S.-Japan 2Y/10Y spreads and fixed-window deltas/velocity,
- `UWBS-013`: `CARRY_UNWIND_CANDIDATE`, `DELEVERAGING_REGIME`, `RATE_SHOCK`, and `FX_SHOCK_JPY` Interpretation rules,
- `UWBS-014`: carry-unwind / macro-stress validation fixtures,
- `UWBS-015`: structured macro-rate / FX / flow source survey.

Those items already establish the rule that inferred capital movement is **not a Fact**, and that USD/JPY or one news item alone must not establish a carry-unwind conclusion.

This report adds only the missing upstream release-and-transmission layer.

## 3. Proposed observation model

```text
Official Macro Release Facts
  ├─ PCE
  ├─ Durable Goods
  ├─ CPI / employment (existing or future compatible inputs)
  └─ policy-expectation inputs when a permissible source exists
            │
            ▼
Macro Surprise Derived Metrics
  ├─ inflation_surprise
  ├─ growth_capex_surprise
  └─ revision_surprise
            │
            ▼
Rate Transmission
  ├─ US 2Y
  ├─ JP 2Y
  ├─ US-JP 2Y spread
  └─ spread velocity / event-window delta
            │
            ▼
FX Confirmation
  ├─ USD/JPY
  ├─ AUD/JPY (if supported)
  └─ MXN/JPY (if supported)
            │
            ▼
Risk-Asset / Volatility Confirmation
  ├─ Nasdaq / high-beta equities
  ├─ BTC / eligible crypto proxy
  └─ volatility context
            │
            ▼
Carry Interpretation
  ├─ CARRY_BUILD
  ├─ CARRY_STABLE
  ├─ CARRY_COOLING
  ├─ CARRY_UNWIND_CANDIDATE
  └─ DELEVERAGING_REGIME (existing higher-order state)
```

## 4. PCE Fact specification

PCE should not be represented only by YoY inflation. Minimum normalized fields:

- headline PCE MoM,
- headline PCE YoY,
- core PCE MoM,
- core PCE YoY,
- personal income MoM,
- nominal personal consumption expenditure MoM,
- real personal consumption expenditure MoM,
- actual value,
- market consensus value,
- prior value as published before the release,
- revised prior value when the release revises history,
- release timestamp,
- observation/reference period,
- source/provenance,
- accepted timestamp and revision identity.

Primary release impulse for rate/carry analysis:

```text
core_pce_mom_surprise_pp = actual_core_pce_mom - consensus_core_pce_mom
```

This is a Derived Metric, not a causal conclusion.

A softer-than-consensus PCE release may be consistent with lower U.S. front-end yields and a narrower U.S.-Japan 2Y spread, but the system must measure the subsequent market response rather than assume it.

## 5. Durable Goods Fact specification

Durable Goods serves a different role from PCE. It is primarily a growth / capital-expenditure impulse rather than a direct inflation measure.

Minimum normalized fields:

- Durable Goods Orders headline,
- Durable Goods Orders ex transportation,
- Nondefense Capital Goods Orders ex Aircraft (core capital goods orders),
- Nondefense Capital Goods Shipments ex Aircraft when available,
- actual / consensus / prior / revision,
- release timestamp,
- observation/reference period,
- source/provenance,
- accepted timestamp and revision identity.

The headline series must not dominate interpretation because aircraft and other large transport orders can create large one-off moves. Core capital goods orders/shipments should carry greater weight for underlying capex/growth interpretation.

## 6. Event-window transmission metrics

For each accepted macro release, compute deterministic, no-lookahead deltas over configured windows. Initial planning windows:

- `T0 -> T+30m`,
- `T0 -> T+2h`,
- `T0 -> T+1d`.

Candidate metrics:

- `delta_us2y_bp`,
- `delta_jp2y_bp`,
- `delta_us_jp_2y_spread_bp`,
- `delta_usdjpy_pct`,
- `delta_audjpy_pct` if supported,
- `delta_mxnjpy_pct` if supported,
- `delta_nasdaq_pct`,
- `delta_btc_pct`,
- volatility delta where an accepted source exists.

Rules:

1. Market observations before the release timestamp must never be used as post-release confirmation.
2. If a market is closed, stale, or temporally incompatible, mark the observation missing/unknown rather than forward-fill it as evidence.
3. A release surprise and a later price move may be temporally associated; causality remains an Interpretation.

## 7. Carry-state interpretation

### `CARRY_BUILD`

Evidence pattern may include widening U.S.-Japan front-end spread, persistent JPY weakness across more than one relevant cross, and compatible risk-asset behavior.

### `CARRY_STABLE`

No meaningful change in spread incentive or confirmation; mixed/weak signals remain neutral.

### `CARRY_COOLING`

Use for a decline in carry incentive without enough evidence for an unwind. Example pattern:

- softer U.S. macro surprise,
- U.S. 2Y yield lower,
- U.S.-Japan 2Y spread narrower,
- USD/JPY lower,
- but no broad risk-off / cross-JPY / volatility confirmation.

This state is important because it prevents the common false inference:

```text
PCE soft -> USD/JPY down -> carry unwind
```

### `CARRY_UNWIND_CANDIDATE`

Require independent confirmation beyond the rate differential and USD/JPY pair. Candidate support can include:

- broader JPY appreciation such as AUD/JPY and/or MXN/JPY,
- high-beta equity weakness,
- BTC/risk-proxy weakness,
- volatility increase,
- explicit source-grounded deleveraging/carry-reduction evidence.

Contradictory evidence must reduce confidence rather than be discarded.

### `DELEVERAGING_REGIME`

Reuse the existing higher-order regime. Do not create a duplicate state solely for this extension.

## 8. Confidence and evidence rules

The carry-state output is an Interpretation and should expose:

- supporting evidence IDs,
- contradictory evidence IDs,
- unknown/missing evidence,
- confidence / evidence sufficiency,
- event window,
- as-of timestamp.

Suggested minimum rule:

- one macro release + rate differential move + USD/JPY move can support `CARRY_COOLING`,
- `CARRY_UNWIND_CANDIDATE` requires at least one additional independent confirmation domain,
- no signal may claim a directly measured `capital_outflow` unless the input dataset explicitly measures compatible flows and its scope is known.

## 9. Source and data considerations

Official-release Facts should prefer official sources where practical. Consensus is a separate datum with separate provenance and may require a market-data provider. The system must not silently substitute model estimates for consensus.

Open design questions:

- permissible and reproducible consensus source for PCE and Durable Goods,
- whether Fed Funds / SOFR futures policy-expectation data is already modeled as a formal Fact,
- whether AUD/JPY and MXN/JPY are supported in the current FX universe,
- availability/cost/licensing of high-frequency flow data.

Missing data must lower confidence or produce `UNKNOWN`; it must not be imputed as confirming evidence.

## 10. Candidate implementation decomposition

### A. U.S. Macro Release Fact

Implement normalized release records for PCE and Durable Goods, including actual/consensus/prior/revision/timestamps/provenance.

### B. Macro Surprise -> Rate Transmission

Compute release-surprise metrics and bounded event-window deltas for U.S. 2Y, Japan 2Y, U.S.-Japan 2Y spread and supported FX/risk assets.

### C. Carry Flow State

Add `CARRY_BUILD`, `CARRY_STABLE`, and `CARRY_COOLING` as bounded interpretations around the existing `CARRY_UNWIND_CANDIDATE` / `DELEVERAGING_REGIME` framework.

## 11. Acceptance criteria

1. PCE and Durable Goods releases preserve actual, consensus, prior/revision, release/reference timestamps and source provenance.
2. Surprise values are deterministic and unit-safe.
3. Event-window market deltas are reproducible and have no lookahead contamination.
4. A soft PCE + narrower U.S.-Japan 2Y spread + weaker USD/JPY does **not** by itself escalate beyond `CARRY_COOLING`.
5. `CARRY_UNWIND_CANDIDATE` requires at least one independent confirmation domain in addition to rate/primary-FX evidence, subject to existing UWBS-013 rules.
6. Contradictory evidence is retained and lowers confidence.
7. Unsupported/missing cross-JPY, policy-futures, consensus, or volatility inputs become `UNKNOWN`/lower-confidence rather than guessed values.
8. The implementation reuses `UWBS-011..014` contracts and does not duplicate existing `DELEVERAGING_REGIME` semantics.
9. Tests include normal, false-positive, stale-market, revision, missing-consensus and contradictory-evidence cases.
10. The 2026-09-30 August-2026 PCE release may be used as a candidate historical fixture only after its values and revision metadata are revalidated against the accepted official source.

## 12. Proposed CP relationship

```text
UWBS-011 Macro-Market Fact contract
      +
UWBS-012 US-JP spread Derived Metrics
      +
New Macro Release Fact / Surprise work
      |
      v
Event-window Rate / FX Transmission
      |
      v
Carry State (BUILD / STABLE / COOLING)
      |
      +----> existing UWBS-013 CARRY_UNWIND_CANDIDATE
                    |
                    v
             existing DELEVERAGING_REGIME
```

This is a CP candidate only until formal WBS/CP incorporation.

## 13. Recommendation

Treat the work as a **single WBS-unreflected capability proposal with later decomposition**, rather than immediately creating separate PCE, Durable Goods, FX and carry tasks. The causal chain and acceptance boundary should be stabilized first; provider-specific ingestion can then be split if licensing or cadence requires separate work.
