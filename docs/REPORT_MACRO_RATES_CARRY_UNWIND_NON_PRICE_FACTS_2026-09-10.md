# OrderScope — Macro Rates, Carry-Unwind, and Non-Price Fact Extension Report

Status: **Planning / design input — not yet normative**  
Date: 2026-09-10  
Scope: interest-rate structure, cross-asset deleveraging, carry-unwind detection, and non-price Fact capture  
Related WBS: `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`  
Related extension: `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`  
Backlog target: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`

## 1. Purpose

Record the design implications from the 2026-09-10 discussion covering:

- the distinction between policy rates, sovereign yields, and bank-specific lending/deposit rates;
- why policy-rate increases and long-term-yield declines can occur at the same time;
- how yield-curve shape affects bank profitability and market interpretation;
- how JPY carry-trade unwind can create cross-asset selling that is not caused by company fundamentals;
- why carry unwind resembles a forced short-cover/deleveraging process, while remaining structurally distinct;
- how temporary risk reduction can differ from permanent capital flight;
- why news-only capture is insufficient for rate and liquidity conditions;
- which non-price Fact, Derived Metric, and Regime concepts should be added to OrderScope planning.

This report is a design/planning artifact. It does **not** assert that every current-market observation discussed in chat has been independently verified against a primary data provider. Where market attribution is not directly observable, it must remain Interpretation/Hypothesis rather than Fact.

## 2. Core distinction: multiple different "interest rates"

A news headline saying "rates rose" or "long-term rates fell" can refer to different objects.

Minimum useful separation:

1. **Policy rate** — central-bank policy target / administered rate.
2. **Short-term market rate** — overnight / short-tenor money-market pricing.
3. **Sovereign yield curve** — 2Y, 5Y, 10Y, 30Y or equivalent market yields.
4. **Bank deposit rate** — institution-specific funding cost.
5. **Bank lending rate** — institution/product-specific asset yield.

These are related but not interchangeable.

For bank analysis, the relevant question is usually not "did rates rise?" but:

- which tenor moved;
- whether funding cost and lending yield moved by the same amount;
- whether the yield curve steepened or flattened;
- whether credit demand / credit risk changed at the same time.

## 3. Policy-rate increase and long-term-yield decline are not contradictory

Long-term yields embed expectations for future short rates, inflation, growth, and term premium. Therefore a policy-rate increase can coexist with a decline in a 10Y or 30Y yield.

Example mechanism:

```text
Central bank becomes more restrictive now
        ↓
Market expects inflation / growth to cool later
        ↓
Expected future short rates decline or peak sooner
        ↓
Long-end yields can fall
```

This produces an important derived market-state distinction:

- short-end rising faster than long-end -> curve flattening;
- long-end rising faster than short-end -> curve steepening;
- outright inversion -> special risk / regime state.

For a bank such as MUFG, curve shape can matter more than the direction of one isolated rate headline.

## 4. Carry unwind as cross-asset deleveraging

The discussion treated JPY carry activity conceptually as:

```text
Low-cost JPY funding
   ↓
JPY sold / foreign currency acquired
   ↓
Risk assets or higher-yielding assets purchased
```

When JPY appreciates and/or Japanese funding rates rise, the economics can reverse:

```text
JPY appreciation + higher JPY funding cost
   ↓
Carry return deteriorates / losses increase
   ↓
Risk exposure reduced
   ↓
Foreign assets sold
   ↓
Foreign currency converted back to JPY
   ↓
Additional JPY appreciation pressure can occur
```

The important design implication is that an equity decline under this mechanism is not necessarily a company-specific negative Fact.

## 5. Relationship to short-cover / forced-position exit

Carry unwind is analogous to a short squeeze in one important respect: both can become self-reinforcing through position constraints.

### Short-cover loop

```text
Price rises
  ↓
Short losses increase
  ↓
Stop / margin / risk limits trigger
  ↓
Shorts buy to close
  ↓
Price rises further
```

### Carry-unwind loop

```text
JPY strengthens / funding conditions worsen
  ↓
Carry losses / risk usage increase
  ↓
Position size is reduced
  ↓
Foreign risk assets are sold and JPY repurchased
  ↓
JPY can strengthen further
```

However, the two must not be stored as the same event type. Carry unwind is a **cross-asset funding / deleveraging interpretation**, while short covering is usually an **instrument-positioning mechanism**.

## 6. Forced liquidation versus discretionary de-risking

Observed selling can come from multiple causes that look similar in price data:

- margin-call / liquidation;
- stop-loss execution;
- VaR / exposure-limit reduction;
- pre-event risk reduction;
- discretionary profit-taking;
- fundamental repricing;
- broad risk-off allocation;
- carry unwind.

OrderScope must therefore avoid storing "forced selling" or "capital flight" as Fact unless the source explicitly establishes it.

Recommended boundary:

- **Fact**: observed rates, yields, FX, volume, fund-flow data, official policy actions, explicit source statements.
- **Derived Metric**: spreads, curve slope, change velocity, volatility, breadth, relative return/volume.
- **Interpretation/Hypothesis**: carry unwind, deleveraging, event-driven de-risking, Japan->US or US->cash capital rotation.
- **Prediction**: expected continuation / reversal / impact on individual equities.

This is consistent with the existing A0 rule that FX alone must not establish capital movement as Fact.

## 7. Stabilization model from the discussion

The working conceptual model was that a carry/deleveraging shock often stabilizes in phases rather than ending at one timestamp:

1. **Shock / repricing** — rates, FX, and risk assets move quickly.
2. **Forced / high-urgency reduction** — leveraged positions are reduced.
3. **Event clarification** — central-bank meetings, inflation data, or policy communication resolve part of the uncertainty.
4. **Position re-underwriting** — investors recalculate expected return under the new rate / FX regime.
5. **New equilibrium** — volatility and cross-asset correlations normalize enough for position rebuilding.

The prior chat used a rough 1–3 week stabilization range as a scenario estimate, not a measured universal rule. That estimate should **not** be encoded as a system parameter without historical validation.

## 8. Capital outflow / fund-flow interpretation

A crucial distinction from the discussion:

- **fund-flow amount** is observed cash movement into/out of a vehicle or asset class;
- **market-cap decline** is a valuation change;
- **gross position reduction** can be much larger than net flow because the same capital can rotate multiple times.

Therefore OrderScope must not sum unrelated fund-flow, MMF-flow, ETF-flow, FX, and market-cap changes into one "capital outflow" number without a reconciliation model.

Any attempt to estimate a cumulative liquidity withdrawal should carry:

- source scope;
- time window;
- gross vs net designation;
- double-counting risk;
- asset-class boundary;
- whether the number is observed or inferred.

## 9. Existing Cross-Market WBS coverage

`WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md` already establishes important groundwork:

- sovereign yield as cross-market context;
- relevant FX pair;
- policy expectation;
- U.S. 10Y Treasury yield;
- Japan 10Y JGB yield;
- USD/JPY;
- the explicit rule that capital movement remains Interpretation/Hypothesis rather than Fact when it is not directly observed.

Therefore the newly discovered gap is **not** "add FX/yields to the project at all." The gap is deeper:

1. define a reusable non-price macro-market Fact contract;
2. capture the full rate curve rather than only one 10Y point where needed;
3. derive spreads / curve shape / velocity;
4. define carry-unwind and deleveraging interpretations with evidence rules;
5. define a validation / acceptance suite that prevents single-signal over-attribution.

## 10. Proposed non-price macro Fact set

Candidate minimum raw Fact series:

### Japan

- `JP_POLICY_RATE`
- `JP_MONEY_MARKET_OVERNIGHT` or equivalent short-rate series
- `JP_JGB_2Y`
- `JP_JGB_5Y`
- `JP_JGB_10Y`
- `JP_JGB_30Y`

### United States

- `US_POLICY_RATE_TARGET` / effective policy rate
- `US_TREASURY_2Y`
- `US_TREASURY_5Y`
- `US_TREASURY_10Y`
- `US_TREASURY_30Y`

### FX / volatility / liquidity context

- `USDJPY`
- JPY FX realized or implied-volatility series when a suitable licensed source is available
- equity volatility proxy (for example VIX, subject to provider/terms review)
- market breadth or broad-index relative-volume proxy
- observed fund-flow series where a source contract permits use

Exact symbols / providers remain a later provider-contract decision.

## 11. Proposed Derived Metrics

Candidate derived metrics:

- `JP_2S10S = JP_JGB_10Y - JP_JGB_2Y`
- `JP_10S30S = JP_JGB_30Y - JP_JGB_10Y`
- `US_2S10S = US_TREASURY_10Y - US_TREASURY_2Y`
- `US_10S30S = US_TREASURY_30Y - US_TREASURY_10Y`
- `US_JP_2Y_SPREAD`
- `US_JP_10Y_SPREAD`
- policy-rate delta / expectation gap where forecast data is explicitly sourced
- FX change over fixed windows
- yield-change velocity over fixed windows
- curve steepening / flattening state
- cross-asset stress composite, only after component evidence is validated

All metrics must preserve source timestamps and as-of semantics.

## 12. Proposed Interpretation / Regime layer

Candidate labels for later formal design:

- `YIELD_CURVE_STEEPENING`
- `YIELD_CURVE_FLATTENING`
- `YIELD_CURVE_INVERSION`
- `RATE_SHOCK`
- `FX_SHOCK_JPY`
- `CARRY_UNWIND_CANDIDATE`
- `DELEVERAGING_REGIME`
- `EVENT_RISK_REDUCTION_CANDIDATE`

Important boundary: `CARRY_UNWIND_CANDIDATE` should be the default interpretation label unless there is explicit source evidence for actual carry liquidation.

## 13. Candidate carry-unwind evidence model

A v0.1 rule should not use one indicator alone.

Possible evidence bundle:

- rapid JPY appreciation;
- widening JPY FX volatility;
- narrowing Japan-vs-US short-rate differential or a major shift in expected differential;
- broad risk-asset weakness;
- market breadth deterioration;
- volume / liquidity stress;
- explicit reporting of leveraged-fund or carry-position reduction;
- lack of sufficient company-specific negative news for affected equities.

Interpretation result should be ordinal, for example:

- `SUPPORT`
- `PARTIAL`
- `CONTRADICT`
- `UNKNOWN`

This mirrors the existing Cross-Market hypothesis framework rather than introducing pseudo-precision.

## 14. Bank-sector application

The rate Fact extension also improves bank-stock interpretation.

For a bank such as MUFG, useful evidence is not limited to the policy rate:

- policy-rate direction;
- short-end market rate;
- 2Y/10Y/30Y sovereign yields;
- curve slope;
- deposit-cost trend;
- lending-yield trend;
- credit demand / credit-loss context.

A headline such as "long-term rates fell" should therefore resolve to the actual tenor and measured change rather than being stored only as text.

Bank-specific deposit and lending rates may belong in a later company/sector-specific extension rather than the minimum cross-market macro contract.

## 15. Data-source architecture implication

News remains useful for:

- policy statements;
- policy expectations;
- explicit descriptions of investor positioning;
- causal explanations reported by credible sources;
- event discovery.

But numeric rate/FX series should be acquired through a structured provider or official-source adapter wherever practical.

Recommended conceptual path:

```text
Official / structured market data
        ↓
Raw non-price Macro Fact
        ↓
Derived spreads / curve / velocity
        ↓
Evidence bundle
        ↓
Interpretation / Regime
        ↓
Company / sector impact analysis
```

News should supplement this path rather than replace the raw time series.

## 16. WBS implications

The following work is WBS-unreflected and should be added to the planning backlog before any normative WBS revision:

1. **Macro-market non-price Fact contract** for policy rates, sovereign yields, FX and related timestamps/provenance.
2. **Rate-curve and cross-country spread derived metrics** with tests and as-of semantics.
3. **Carry-unwind / deleveraging interpretation contract** with multi-signal evidence rules and explicit Fact-vs-Interpretation boundary.
4. **Macro stress validation fixtures / Canary cases** covering policy-rate up + long-yield down, curve flattening/steepening, JPY shock, broad selloff with/without company news, and false-positive cases.
5. **Provider/source survey and contract selection** for structured rates, yields, FX volatility, and fund-flow inputs, subject to existing provider/terms/security gates.

These should be integrated with A0 rather than duplicating A0-001/A0-002.

## 17. Explicit non-goals

This report does not authorize:

- live provider activation;
- remote Worker mutation;
- proprietary data use without terms review;
- storing inferred capital movement as Fact;
- treating every USD/JPY move as carry unwind;
- treating every broad equity decline as forced deleveraging;
- summing unrelated flow series into a single observed capital-flight total;
- encoding a fixed 1–3 week stabilization duration as a rule.

## 18. Recommended next design step

When the current accepted implementation path reaches an appropriate planning boundary, fold the backlog items into a formal Cross-Market/Macro WBS revision.

The resulting implementation order should likely be:

1. raw macro Fact schema and provider contract;
2. ingestion / normalization;
3. rate-curve / cross-country derived metrics;
4. evidence-bundle contract;
5. carry/deleveraging Interpretation layer;
6. historical validation and false-positive fixtures;
7. sector/company impact adapters such as bank-rate interpretation.

Until then, these remain captured planning items and must not silently expand existing accepted A0 completion conditions.
