# OrderScope — Crypto Macro-Leader / Derivatives Context Gap Report

Status: **Planning / design input — not yet normative**  
Date: 2026-09-19  
Scope: BTC-led macro transmission, crypto derivatives positioning, 24/7 session effects, and altcoin leader/follower context  
Related WBS: `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`  
Related macro report: `docs/REPORT_MACRO_RATES_CARRY_UNWIND_NON_PRICE_FACTS_2026-09-10.md`  
Backlog target: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`

## 1. Purpose

Record the analysis gap exposed by the 2026-09-18..19 NEAR/BTC observation.

The NEAR case showed that local price/volume/derivatives structure can look internally coherent while a larger BTC/macroeconomic flow is simultaneously changing the direction and available liquidity of the whole crypto market.

The design objective is therefore not to replace local market-structure analysis, but to place it under a higher-level context:

```text
Macro / Policy / Regulation / Institutional Flow
                 ↓
               BTC
                 ↓
      Crypto market risk regime
                 ↓
        Altcoin / theme leader
                 ↓
       Target instrument (NEAR)
                 ↓
 Local OI / Funding / Liquidation / Price
```

A local reading should remain valid as a description of current positioning while being explicitly marked incomplete when higher-layer context is missing.

## 2. Existing OrderScope coverage

The current repository already covers several important prerequisites.

### 2.1 Macro / cross-market context

`stock_monitoring_v0.1_spec.md` §14 and `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md` already define:

- U.S. and Japan policy/rate context;
- USD/JPY;
- sovereign yield curves and spreads;
- carry-unwind / deleveraging interpretations;
- cross-market capital-rotation hypotheses;
- the rule that capital movement must remain Interpretation/Hypothesis unless directly observed.

A0-003..017 additionally provide reusable raw macro Facts, derived metrics, carry/deleveraging interpretations, validation fixtures, and official/fallback source adapters.

### 2.2 Price / volume interpretation boundary

`REPORT_VOLUME_FLOW_ALPACA_2026-08-28.md` already prohibits treating OHLCV as literal net capital inflow and provides relative-volume / notional-activity semantics.

### 2.3 Catalyst / price-discovery planning

UWBS-020/021 already plan fixed-window catalyst reaction and price-discovery / new-equilibrium states.

### 2.4 BTC as contextual series

A0-002 already used BTC as one of the aligned cross-market series in the CBRS validation case.

These components mean the project is **not missing macro context in general**.

## 3. Gap discovered by the NEAR/BTC case

The missing layer is crypto-specific and materially affects interpretation.

### 3.1 BTC is currently only a context series, not a leader-state model

The existing A0 design can align BTC with equities, rates and FX, but does not yet represent:

- BTC as the crypto-market leader / transmission node;
- BTC-led risk-on / risk-off propagation into altcoins;
- target relative return versus BTC;
- delayed altcoin response to BTC;
- divergence between BTC-led market beta and target-specific catalyst alpha.

Without this layer, a NEAR move can be misclassified as primarily target-specific when it is partly or mainly a BTC-led market move.

### 3.2 Crypto derivatives positioning is not captured

Current market analysis is centered on OHLCV and equity-oriented market data.

The following crypto derivatives observations are not represented as reusable Facts / Derived Metrics:

- open interest;
- open-interest delta / velocity;
- perpetual funding rate;
- futures/perpetual basis;
- long liquidation amount;
- short liquidation amount;
- liquidation imbalance;
- derivatives volume;
- spot-vs-derivatives volume relationship;
- exchange-level positioning provenance where legally/licensably available.

This prevents OrderScope from distinguishing, for example:

```text
price ↑ + OI ↑ + funding ↑
  = new leveraged participation / overheating candidate

price ↑ + OI ↓ + short liquidations ↑
  = short-squeeze candidate

price → + OI ↓ + funding ↓
  = leverage washout with price retention candidate

price ↓ + OI ↓ + long liquidations ↑
  = long unwind / liquidation cascade candidate
```

These are Interpretation candidates, not Facts about trader identity.

### 3.3 BTC institutional / macro flow is not modeled at the needed granularity

For BTC, local derivatives data is insufficient because large institutional channels can dominate direction.

Candidate context includes:

- spot BTC ETF creations/redemptions or net flows;
- CME futures OI / basis / volume where source terms permit;
- Coinbase/major spot-market activity proxies;
- policy/regulatory events affecting crypto;
- U.S. dollar / Treasury-rate changes;
- broad equity risk appetite.

The existing macro contract can supply rates/FX, but there is no BTC-specific institutional-flow context contract tying these observations to crypto market state.

### 3.4 24/7 crypto sessions and weekend liquidity are absent

The current session model is equity-centered: Premarket / Regular / After-hours plus holidays and shortened sessions.

Crypto requires a different calendar model:

- continuous 24/7 trading;
- exchange maintenance / provider outages;
- UTC day-boundary effects;
- Asia / Europe / U.S. participation windows as analysis buckets, not exchange sessions;
- weekend / weekday liquidity regime;
- Friday U.S. close / CME close context;
- Sunday / Monday reopen effects for traditional-market-linked derivatives.

These should not be encoded as claims that participants from a named region caused a move. They are time-window context only.

### 3.5 News-to-BTC-to-altcoin transmission is not explicit

The current News layer can capture events, and A0 can capture macro context, but the project does not yet provide a reusable event-transmission chain such as:

```text
Fed / BOJ / regulation / ETF event
    ↓
BTC reaction
    ↓
crypto breadth / beta reaction
    ↓
NEAR relative reaction
    ↓
local leverage amplification
```

This is the key gap exposed by the NEAR discussion.

## 4. Recommended analytical boundary

The project should preserve five layers.

### Layer 1 — Source-grounded event / macro Facts

Examples:

- policy decision;
- regulatory action;
- official statement;
- ETF flow observation from an accepted source;
- Treasury / FX observation.

### Layer 2 — BTC market Facts

Examples:

- BTC spot bars;
- BTC derivatives observations;
- accepted ETF / CME observations.

### Layer 3 — Crypto-market Derived Metrics

Examples:

- BTC return / volatility;
- target return minus BTC return;
- OI change / velocity;
- funding change;
- liquidation imbalance;
- spot/derivatives activity ratio;
- BTC dominance or breadth proxy where source contracts permit.

### Layer 4 — Interpretation

Candidate labels:

- `BTC_MACRO_LEADER_ACTIVE`
- `BTC_LED_CRYPTO_RISK_ON`
- `BTC_LED_CRYPTO_RISK_OFF`
- `ALTCOIN_RELATIVE_STRENGTH`
- `ALTCOIN_IDIOSYNCRATIC_REPRICING`
- `LEVERAGE_BUILDUP_CANDIDATE`
- `LEVERAGE_WASHOUT_CANDIDATE`
- `SHORT_SQUEEZE_CANDIDATE`
- `LONG_LIQUIDATION_CASCADE_CANDIDATE`
- `WEEKEND_LIQUIDITY_THINNING_CANDIDATE`

No label should identify trader nationality, institution, or capital source without explicit evidence.

### Layer 5 — Prediction / scenario

Examples:

- expected persistence;
- likely support/retest window;
- scenario ranges.

Predictions must not be promoted to Facts.

## 5. NEAR 2026-09-18..19 Canary value

The observed NEAR episode is a strong candidate validation fixture because it contains multiple distinct phases:

1. target-specific positive narrative / repricing;
2. elevated volume and repeated local price discovery;
3. short-liquidation-driven acceleration;
4. new leveraged longs and rising OI/funding;
5. leverage washout while price retained a higher range;
6. BTC and macro risk-on context becoming material to interpretation;
7. 24/7 / weekend transition risk.

The fixture should test whether OrderScope avoids the false conclusion:

> "NEAR local order-flow structure alone explains the move."

The expected result should instead preserve multiple simultaneous hypotheses:

- NEAR-specific catalyst support;
- BTC-led crypto beta support;
- macro-risk-appetite support;
- short-squeeze amplification;
- leveraged-long buildup;
- weekend liquidity risk.

## 6. Proposed WBS-unreflected work

### UWBS-036 — Crypto derivatives Fact / Derived Metric contract

Define source-neutral observations for OI, funding, basis, derivatives volume and long/short liquidations with event/as-of/provenance semantics.

Do not infer trader identity or directional net capital flow from aggregate derivatives values.

### UWBS-037 — BTC macro-leader / altcoin relative-context model

Define BTC as a configurable crypto-market leader proxy and compute target-relative return, lagged response, breadth/market-beta context and divergence evidence.

Keep BTC-led propagation as Interpretation unless validated by explicit event and reaction evidence.

### UWBS-038 — BTC institutional-flow / market-structure source survey

Survey acceptable sources for spot BTC ETF flows, CME futures/OI/basis and selected spot-market context.

Record terms, latency, historical depth, revision behavior and cost. No live activation through this task.

### UWBS-039 — 24/7 crypto time-window / weekend-liquidity contract

Define UTC-continuous observations plus Asia/Europe/U.S. analysis windows, weekend flags and traditional-market boundary context.

Do not label a window move as caused by traders from that geography.

### UWBS-040 — NEAR/BTC multi-layer Canary and false-positive suite

Replay the 2026-09-18..19 episode using macro/news, BTC, NEAR spot, OI, funding and liquidation layers.

Acceptance must distinguish local positioning from higher-level market transmission and include false positives where:
- OI/funding move without BTC confirmation;
- BTC moves but NEAR does not;
- NEAR-specific catalyst dominates;
- weekend liquidity creates a price jump without new information;
- liquidation activity is mistaken for new directional positioning.

## 7. Relationship to existing work

Proposed dependency sketch:

```text
A0-003..017 macro context
        |
        +-------------------+
                            |
UWBS-036 derivatives        |
        |                   |
        +--> UWBS-037 <-----+
        |       |
UWBS-038 -----+ |
                |
UWBS-039 -------+
                |
                v
           UWBS-040 Canary
                |
         UWBS-020/021
   market reaction / repricing
```

No existing accepted task should be rewritten to absorb this silently.

## 8. Priority

Recommended priority: **Medium-High for analysis quality, non-blocking for current equity v0.1 completion**.

Reason:

- For ordinary U.S. equity monitoring, existing A0 coverage is already substantial.
- For BTC-linked equities, crypto treasury companies, miners, and crypto-sensitive technology themes, the missing layer can materially change causal interpretation.
- If OrderScope is used to interpret crypto assets directly, this gap becomes High priority.

## 9. Explicit non-goals

This extension does not authorize:

- automatic trading;
- buy/sell signals;
- inferring trader nationality from time of day;
- treating OI growth as observed long-only capital inflow;
- treating liquidation bars as proof of newly opened opposite-side positions;
- treating BTC correlation as causal proof;
- live provider activation without terms/cost/security review;
- adding crypto assets to the normative U.S.-equity Universe without a separate scope decision.

## 10. Conclusion

The existing OrderScope design would have captured a meaningful part of the 2026-09-18..19 environment:

- macro rates / FX;
- carry/deleveraging context;
- BTC price as a cross-market series;
- news/events;
- target price/volume and relative-market observations.

It would **not** yet have captured enough information to reproduce the full NEAR reading performed manually in this session.

The main missing components are:

1. crypto derivatives positioning;
2. BTC institutional-flow context;
3. BTC→altcoin leader/follower decomposition;
4. 24/7 / weekend liquidity regimes;
5. explicit news/macro→BTC→altcoin transmission validation.

Therefore the manual NEAR analysis benefited from favorable market behavior: the local positioning read was useful, but without the BTC/macro layer it could have failed abruptly if a larger cross-market impulse had reversed.

This gap merits a dedicated report and WBS-unreflected extension rather than being silently folded into existing A0 tasks.


## 11. Pacific weekend handoff / early-Monday timing hypothesis

### 11.1 Geographic boundary

The International Date Line runs approximately along the 180° meridian through the central Pacific and bends around national borders and island groups. Hawaii is east of the Date Line; crossing westward across the Date Line advances the calendar date.

The earliest civil time zone is UTC+14. The principal inhabited reference area is Kiribati's Line Islands, including Kiritimati (Christmas Island). These locations enter Monday before New Zealand, Australia, East Asia, Europe and the Americas.

This geographic fact must be kept separate from any market-causality claim.

### 11.2 "Pacific empty-zone weekend effect" as a hypothesis, not a Fact

The 2026-09-20..21 NEAR episode suggests a candidate timing effect:

```text
weekend liquidity thinning
    ↓
leveraged positions accumulate / are partially cleared
    ↓
a long Pacific interval exists before major Asian financial centers enter Monday
    ↓
liquidity providers / discretionary traders gradually return
    ↓
small imbalances can be amplified before broader weekday liquidity normalizes
```

Provisional label:

- `PACIFIC_WEEKEND_HANDOFF_CANDIDATE`

This label is an Interpretation/Hypothesis. It must not be stored as a Fact merely because price changes near the calendar transition.

Required evidence should include:

- exact UTC/JST timing;
- OI/funding/liquidation state before and after the move;
- BTC and major-crypto confirmation;
- venue breadth;
- spot/derivatives volume change;
- comparison with control weekends where no similar move occurred.

### 11.3 Re-risking selection after weekend de-risking

A second hypothesis raised by the NEAR case is:

> When participants reduce risk over the weekend and re-enter as weekday liquidity returns, instruments with a more favorable perceived risk/return balance may receive cleaner or more persistent re-risking flows.

This is **not an existing Fact** in OrderScope.

The observable Facts are things such as:

- weekend OI reduction;
- funding change;
- liquidation amount;
- spot/derivatives volume;
- Monday re-entry volume;
- target-relative return versus BTC or a crypto basket;
- persistence after the first re-entry window.

The statement that "better risk/return-balanced names move more cleanly" belongs to Interpretation/Hypothesis until validated historically.

Candidate label:

- `WEEKEND_RERISKING_SELECTION_CANDIDATE`

Potential validation design:

1. identify weekends with material de-risking;
2. rank candidate assets using only pre-Monday observable risk/return features;
3. measure Monday/Tuesday re-entry volume, relative return, drawdown, and persistence;
4. compare against BTC and matched-control altcoins;
5. reject the hypothesis if apparent "clean" moves disappear after market-beta and liquidity controls.

No fixed threshold or scoring rule should be frozen from the NEAR case alone.
