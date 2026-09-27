# OrderScope — BTC / Altcoin Synchronization Observation and Validation Plan

Status: **Observed pattern / validation required — not normative**  
Date: 2026-09-21  
Scope: BTC-led synchronization, altcoin co-movement, volume/return preconditions, recurrence testing, algorithmic/agent-driven flow hypotheses  
Related crypto context report: `docs/work-management/local-corporate-intelligence/REPORT_CRYPTO_MACRO_LEADER_DERIVATIVES_CONTEXT_2026-09-19.md`  
Related derivatives report: `docs/work-management/local-corporate-intelligence/REPORT_FUTURES_POSITION_READING_AND_CRYPTO_DERIVATIVES_COLLECTION_2026-09-20.md`  
Related backlog: `UWBS-037`, `UWBS-040`, `UWBS-047`

## 1. Purpose

Record the observed BTC/NEAR synchronization seen during the 2026-09-20..21 weekend-to-Monday transition and define a validation plan.

The current observation is:

- NEAR and BTC showed high directional agreement before the large NEAR short-squeeze phase;
- the major upward transition appeared nearly synchronous on a 5-minute chart;
- NEAR displayed substantially larger amplitude than BTC;
- after the local short-squeeze threshold was crossed, NEAR behavior diverged from simple BTC beta because local derivatives structure became dominant.

This is an observation, not yet an accepted causal Fact.

The research question is whether BTC acts as a market leader and whether a set of altcoins is selected and moved together by systematic strategies, algorithmic allocation, or autonomous/agent-driven execution.

## 2. Observation from the NEAR case

The working decomposition is:

```text
BTC risk-on move
    ↓
broad crypto directional confirmation
    ↓
NEAR follows with short lag / near-synchronous response
    ↓
NEAR-specific OI / short positioning becomes stressed
    ↓
short-cover / liquidation amplification
    ↓
NEAR decouples from normal BTC beta
```

The important boundary is that BTC can explain direction while local derivatives can explain excess amplitude.

This means OrderScope should not model the relationship as one constant beta or one fixed lag.

## 3. Validation question A — same-time cross-coin synchronization

### 3.1 Goal

Determine whether the BTC/NEAR relationship was isolated or part of a broader synchronized altcoin move.

### 3.2 Candidate comparison universe

At minimum:

- BTC
- ETH
- NEAR
- SOL
- AVAX
- ARB
- UNI
- another liquid Layer-1 / Layer-2 control
- one relatively weak or low-volume altcoin control

The universe should be selected before inspecting the target interval result to avoid cherry-picking.

### 3.3 Required observations

For each asset:

- 1m and 5m spot returns;
- 1m and 5m volume;
- rolling relative volume;
- realized volatility;
- OI;
- funding;
- long liquidation;
- short liquidation;
- derivatives volume;
- spread / basis where available.

### 3.4 Measurements

Calculate:

- contemporaneous return correlation with BTC;
- lagged cross-correlation at -60, -30, -15, -10, -5, 0, +5, +10, +15, +30, +60 minutes;
- beta to BTC by rolling window;
- residual return after BTC beta adjustment;
- correlation before and after liquidation events;
- cross-sectional breadth: fraction of monitored coins moving in BTC's direction.

Do not infer causality from correlation alone.

## 4. Validation question B — pre-move price and volume state

### 4.1 Goal

Test whether coins that participate most strongly in the synchronized move were already characterized by:

- recent positive momentum;
- elevated volume;
- high relative volume;
- recent repricing;
- elevated derivatives activity;
- high market attention / liquidity.

### 4.2 Pre-event feature window

Suggested initial windows:

- 30 minutes;
- 2 hours;
- 6 hours;
- 24 hours;
- 3 days.

These are research windows, not normative constants.

### 4.3 Candidate features

Observed / Derived Metric candidates:

- return over pre-event window;
- volume / trailing median volume;
- turnover proxy;
- realized volatility;
- OI change;
- OI / spot volume;
- funding level / funding change;
- short-liquidation pressure;
- distance from recent high;
- BTC-relative strength;
- cross-venue activity breadth.

The purpose is to identify whether synchronized capital preferentially selects already-active / already-rising assets.

## 5. Validation question C — recurrence on other weekends / weeks

### 5.1 Goal

Determine whether the pattern repeats beyond the 2026-09-20..21 case.

### 5.2 Minimum historical sample

The initial study should include multiple independent weekends, including:

- weekends with broad crypto risk-on;
- weekends with risk-off;
- weekends with BTC flat;
- weekends with target-specific altcoin catalysts;
- weekends with no material event.

A single similar weekend is insufficient for acceptance.

### 5.3 Event alignment

Each weekend should be aligned around:

- Friday U.S. market close context;
- weekend OI reduction / build;
- UTC+14 Monday boundary;
- New Zealand / Australia weekday transition;
- major Asian financial-center Monday transition;
- Europe weekday transition;
- U.S. weekday transition.

These are timing windows only. They must not be interpreted as evidence of participant nationality.

### 5.4 Recurrence metrics

For each weekend:

- BTC return by window;
- altcoin return by window;
- synchronized breadth;
- maximum BTC→altcoin lag correlation;
- spot volume change;
- derivatives volume change;
- OI change;
- funding change;
- liquidation imbalance;
- persistence 1h / 3h / 6h / 24h after the move.

## 6. Volume-specific validation

Volume is essential because synchronized price movement without participation may be a thin-liquidity artifact.

The study should separate:

### Case A — price up + volume up across many coins

Interpretation candidate:

- broad participation / coordinated risk-on allocation.

### Case B — price up + low volume + liquidation spike

Interpretation candidate:

- derivatives-driven squeeze / thin-liquidity amplification.

### Case C — BTC volume up first, altcoin volume up later

Interpretation candidate:

- BTC-led capital transmission.

### Case D — altcoin volume already elevated before BTC move

Interpretation candidate:

- local setup existed before BTC provided directional confirmation.

This distinction is central to the NEAR case.

## 7. Hypothesis hierarchy

The following hypotheses must be stored with different confidence levels.

### H1 — BTC-centered systematic execution

**Strength: testable hypothesis**

A meaningful fraction of short-horizon crypto flow may be driven by algorithmic or systematic strategies that use BTC as the primary directional / risk-regime signal and then adjust exposure in selected altcoins.

Observable expectations:

- BTC turns first or nearly simultaneously;
- multiple liquid altcoins move in the same direction;
- lag distribution is short and relatively stable;
- altcoin amplitude varies by liquidity / beta / local positioning;
- synchronization is stronger during high-volume BTC moves.

This hypothesis does not require identifying whether execution is human-authored algorithmic trading, institutional systematic trading, market making, or an autonomous Agent.

### H2 — Agent-driven execution

**Strength: more speculative**

Some part of synchronized allocation may be executed by autonomous Agents or AI-assisted trading systems.

This cannot be inferred from synchronized charts alone.

Evidence would require stronger source material such as:

- public strategy disclosures;
- platform/provider disclosures;
- observable execution signatures that differ from conventional algorithmic strategies;
- explicit wallet/account attribution where lawful and reliable.

Without such evidence, OrderScope should group this under `SYSTEMATIC_EXECUTION_CANDIDATE`, not `AI_AGENT_FLOW`.

### H3 — Cross-sectional selection based on volume / recent winners

**Strength: testable but currently speculative**

Systematic crypto allocation may first identify assets with:

- high recent volume;
- positive recent return;
- rising relative strength;
- high liquidity;
- active derivatives markets;

and then allocate to a basket of such assets as diversified crypto risk exposure.

Observable expectations:

- participating coins rank high on pre-event volume / momentum;
- non-participating controls rank lower;
- basket members exhibit correlated re-entry around BTC risk-on;
- selection remains predictive out of sample.

This should be tested with pre-event-only features to prevent look-ahead bias.

### H4 — "Buy all high-volume risers" basket behavior

**Strength: strongly speculative**

A simpler rule may exist where strategies mechanically basket assets that are both rising and liquid.

This is plausible but currently unsupported.

A valid test requires:

- pre-defined selection rule;
- historical out-of-sample weekends;
- matched liquidity controls;
- transaction-cost awareness;
- comparison against simple market-cap-weighted or BTC-beta baskets.

## 8. Alternative explanations that must be tested

The study must explicitly test alternatives before accepting H1/H3.

Possible alternatives:

- common macro news;
- common exchange / stablecoin liquidity event;
- market-maker inventory adjustment;
- BTC collateral effects;
- cross-margin deleveraging;
- ETF / institutional BTC flow that indirectly changes crypto risk appetite;
- broad retail sentiment;
- thin weekend liquidity;
- simultaneous liquidation cascades;
- index / basket products;
- simple high-beta behavior with no active basket selection.

A high correlation by itself cannot distinguish these mechanisms.

## 9. Proposed OrderScope Derived Metrics

Candidate metrics:

- `btc_alt_return_corr_5m`
- `btc_alt_max_lag_corr_60m`
- `btc_alt_lag_at_max_corr`
- `btc_alt_beta_rolling`
- `btc_adjusted_residual_return`
- `crypto_breadth_same_direction`
- `pre_event_relative_volume`
- `pre_event_momentum`
- `pre_event_oi_velocity`
- `post_event_volume_expansion`
- `synchronization_break_after_liquidation`
- `cross_sectional_selection_score`

No threshold should be frozen from the NEAR case alone.

## 10. Candidate Interpretation states

- `BTC_LED_SYNCHRONIZATION_CANDIDATE`
- `BROAD_CRYPTO_SYSTEMATIC_FLOW_CANDIDATE`
- `BTC_TO_ALTCOIN_TRANSMISSION_CANDIDATE`
- `ALTCOIN_LOCAL_AMPLIFICATION_CANDIDATE`
- `SYSTEMATIC_EXECUTION_CANDIDATE`
- `CROSS_SECTIONAL_RERISKING_SELECTION_CANDIDATE`
- `CORRELATION_BREAK_AFTER_LIQUIDATION`
- `INSUFFICIENT_EVIDENCE`

The label `AGENT_DRIVEN_FLOW` should not be emitted without explicit external evidence.

## 11. Suggested test design

### Stage 1 — Event study

Use the 2026-09-20..21 NEAR case.

Compare BTC, NEAR and 6-10 liquid altcoins on 1m/5m data.

Measure:

- pre-event momentum / volume;
- correlation and lag;
- breadth;
- OI/funding/liquidation;
- exact point where NEAR correlation breaks.

### Stage 2 — Historical weekend replication

Repeat the same calculation for a fixed historical weekend sample.

Do not choose weekends based on known success of the pattern.

### Stage 3 — Cross-sectional selection test

Before each candidate re-risking window, rank assets using only data available at that time.

Candidate ranking inputs:

- recent return;
- relative volume;
- liquidity;
- BTC-relative strength;
- OI activity.

Test whether top-ranked assets subsequently show stronger synchronized risk-on flow.

### Stage 4 — Out-of-sample validation

Freeze the rule, then test later weekends not used in calibration.

Without this stage, no selection rule should move beyond Hypothesis.

## 12. Acceptance / rejection conditions

### Accept as recurring synchronization evidence if:

- high BTC/altcoin synchronization repeats over multiple independent periods;
- short lags remain stable enough to distinguish from random co-movement;
- multiple coins participate;
- volume confirms participation;
- the effect survives exclusion of liquidation-only episodes.

### Accept cross-sectional selection evidence if:

- pre-event volume/momentum/liquidity features predict participation out of sample;
- result remains after BTC beta control;
- result is not explained solely by market capitalization or baseline liquidity.

### Reject / retain UNKNOWN if:

- the relationship is confined to NEAR;
- high correlation appears only during one macro event;
- lag changes sign randomly;
- the result disappears after beta/liquidity control;
- participating assets can only be identified using post-event information.

## 13. Relationship to current OrderScope work

This report primarily extends:

- `UWBS-037` BTC macro-leader / altcoin relative-context model;
- `UWBS-040` NEAR/BTC multi-layer Canary;
- `UWBS-047` weekend handoff / re-risking validation;
- `UWBS-041..046` derivatives acquisition and Position Map work.

It should be treated as a validation plan, not as evidence that algorithmic or Agent-driven basket allocation already exists.

## 14. Conclusion

The current NEAR/BTC case is strong enough to justify systematic testing of synchronized crypto flows.

The strongest current hypothesis is:

> BTC provides a common short-horizon directional / risk signal, while selected altcoins respond nearly synchronously and then diverge according to liquidity, beta, and local derivatives positioning.

A plausible second hypothesis is that systematic strategies select actively traded / already-strong coins for diversified crypto exposure.

The idea that autonomous Agents specifically drive the synchronized flow is materially more speculative and requires evidence beyond chart correlation.

The next useful evidence is not another single NEAR chart, but a cross-sectional and cross-week dataset combining:

- BTC;
- multiple altcoins;
- pre-event returns;
- pre-event volume;
- OI/funding/liquidations;
- lagged correlation;
- recurrence across independent weekends.
