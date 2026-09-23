# OrderScope — NEAR 7-Day Price Discovery / Liquidation Phase Transition Report

Status: **Observed market-structure case / validation required — not normative**  
Date: 2026-09-24  
Scope: NEAR 2026-09-18..24 repricing, BTC coupling, short-squeeze exhaustion, long-liquidation transition, OI/funding normalization, news-discovery/distribution risk

Related reports:

- `docs/work-management/local-corporate-intelligence/REPORT_CRYPTO_MACRO_LEADER_DERIVATIVES_CONTEXT_2026-09-19.md`
- `docs/work-management/local-corporate-intelligence/REPORT_FUTURES_POSITION_READING_AND_CRYPTO_DERIVATIVES_COLLECTION_2026-09-20.md`
- `docs/work-management/local-corporate-intelligence/REPORT_BTC_ALTCOIN_SYNCHRONIZATION_VALIDATION_2026-09-21.md`

Related WBS / backlog concepts:

- `UWBS-036` crypto derivatives Fact / Derived Metric contract
- `UWBS-037` BTC macro-leader / altcoin relative-context model
- `UWBS-039` 24/7 crypto time-window / weekend-liquidity contract
- `UWBS-040` NEAR/BTC multi-layer Canary
- `UWBS-047` Pacific weekend handoff / weekday re-risking validation

## 1. Purpose

This report consolidates the NEAR market observation followed across approximately seven calendar days and five business-day equivalents from the initial repricing phase through the first clear long-liquidation-driven pullback.

The objective is to preserve the observed sequence without converting it into a deterministic trading rule.

The case is useful because it contains multiple distinct phases:

1. local catalyst / narrative repricing;
2. BTC-compatible risk-on propagation;
3. repeated short liquidations and upward price discovery;
4. rapidly expanding OI and leveraged participation;
5. high-price consolidation;
6. declining marginal buying support;
7. transition from short-liquidation-driven upside to long-liquidation-driven downside;
8. partial synchronization with BTC deleveraging;
9. increasing public/news discovery and possible distribution behavior.

## 2. Observation boundary

The following items are treated as **observations from the supplied charts** rather than independently verified external Facts:

- NEAR traded from the low-$3 range into the mid/high-$4 range during the observation window;
- local highs reached approximately the $4.6-$4.7 area;
- OI expanded from the high-$700M / low-$800M region to above $1B at peak;
- funding remained mostly positive and repeatedly re-expanded during rising phases;
- early upside contained multiple large short-liquidation episodes;
- later downside contained a materially larger long-liquidation episode;
- on 2026-09-24 around 01:00 JST, visible OI was approximately $987M with price around $4.28;
- around 01:14 JST, the liquidation view showed approximately $5.89M long liquidation versus about $0.21M short liquidation while price was near $4.26;
- funding near the same period was approximately +0.007%.

These values are not normalized provider records and should not be used as acceptance fixtures until a source adapter captures them reproducibly.

## 3. Phase reconstruction

### Phase A — Initial repricing / discovery

Observed characteristics:

- price advanced steadily from the low-$3 area;
- local volume expanded;
- repeated short-liquidation events appeared during upward breaks;
- OI rose rather than collapsing after the squeezes.

Interpretation candidate:

- `ALTCOIN_IDIOSYNCRATIC_REPRICING`
- `SHORT_SQUEEZE_CANDIDATE`
- `NEW_LEVERAGED_PARTICIPATION_CANDIDATE`

The key point is that the move was not explained by a single mechanism. Short liquidation amplified the move, while increasing OI indicated that new contracts were also being created.

### Phase B — BTC-compatible acceleration

During the weekend-to-Monday transition, BTC and NEAR displayed a high degree of directional agreement before NEAR-specific liquidation amplification became dominant.

The prior synchronization report recorded the working structure:

```text
BTC risk-on
    ↓
broad crypto confirmation
    ↓
NEAR follows with short lag / near-synchronous move
    ↓
local OI and short positioning become stressed
    ↓
NEAR amplitude exceeds ordinary BTC beta
```

This phase remains linked to:

`REPORT_BTC_ALTCOIN_SYNCHRONIZATION_VALIDATION_2026-09-21.md`

The observed relationship is correlation / transmission candidate evidence, not proof that BTC caused each NEAR move.

### Phase C — High-OI price discovery above $4

The move subsequently established a new trading region roughly around $4.0-$4.7.

Observed characteristics:

- OI repeatedly approached or exceeded $1B;
- price could remain above $4 even after funding cooled;
- funding varied materially while price remained elevated;
- both short and long liquidations became visible in the same high-price region.

Interpretation:

The market had moved beyond a simple one-sided short squeeze.

The high-OI region represented a new two-sided derivatives market in which both:

- bullish continuation positions; and
- mean-reversion / ceiling shorts

were being created.

This corresponds to the "firepowder storage" / Position Map logic formalized in:

`REPORT_FUTURES_POSITION_READING_AND_CRYPTO_DERIVATIVES_COLLECTION_2026-09-20.md`

## 4. Transition detected on 2026-09-24

The most important new observation is the direction of liquidation.

Earlier phases were dominated by short liquidation during price rises.

The latest phase contains:

```text
price falls sharply
    +
OI falls from the recent extreme
    +
large long liquidation appears
    +
BTC also experiences a material long-liquidation episode
```

This is qualitatively different from the prior regime.

Candidate state:

- `LONG_LIQUIDATION_CASCADE_CANDIDATE`
- `LEVERAGE_WASHOUT_CANDIDATE`
- `BTC_LED_RISK_REDUCTION_CANDIDATE`

The current evidence does **not** prove a full trend reversal. It does show that the asymmetry changed.

Earlier:

```text
down-move / short accumulation
    → recovery
    → short liquidation
    → upward amplification
```

Latest:

```text
high-price long accumulation
    → BTC support weakens
    → NEAR price falls
    → long liquidation
    → downside amplification
```

That directional switch is the principal regime-change observation.

## 5. BTC relationship at the transition

BTC and NEAR do not move tick-for-tick.

The relevant observation is instead that:

- BTC buying support weakened;
- BTC experienced a visible long-liquidation event;
- NEAR then experienced a substantially sharper local long-liquidation event;
- NEAR's amplitude remained larger than BTC's.

This is consistent with the earlier multi-layer model:

```text
BTC / broad crypto regime
        ↓
NEAR market beta
        ↓
NEAR local OI / funding / liquidation structure
        ↓
amplified realized move
```

Therefore OrderScope should avoid both extremes:

- "NEAR is completely independent of BTC"; and
- "NEAR is simply a fixed multiple of BTC."

A regime-sensitive beta plus local derivatives amplification model remains more appropriate.

## 6. Time-in-theme / maturity observation

The move has now persisted for approximately:

- seven calendar days; and
- roughly five business-day equivalents from broad short-term discovery.

This timing is not itself a causal variable, but it matters as a maturity marker.

Candidate interpretation:

- early discovery premium may be decaying;
- early short positions have already been heavily consumed;
- early momentum buyers now possess meaningful unrealized gains and can become sellers;
- later participants enter at worse risk/reward;
- new news coverage increases awareness but can also provide exit liquidity to earlier participants.

Suggested state:

- `PRICE_DISCOVERY_MATURING_CANDIDATE`
- `MOMENTUM_PARTICIPANT_ROTATION_CANDIDATE`

Do not freeze "5 business days" or "7 calendar days" as a normative duration threshold. It is an observation that requires comparison with other repricing episodes.

## 7. News-discovery / distribution hypothesis

As the move became broadly visible, explanatory news and market commentary began appearing after a substantial part of the repricing had already occurred.

This creates a testable hypothesis:

```text
price discovery already advanced
    ↓
news / public attention rises
    ↓
new retail / momentum participation increases
    ↓
liquidity improves
    ↓
early participants can realize profits into new demand
```

Candidate label:

- `DISTRIBUTION_ON_DISCOVERY_CANDIDATE`

Evidence that would support it:

- news publication / social attention spike;
- volume increase after publication;
- failure to make a durable new high;
- OI remains high or falls;
- price weakens despite increased attention;
- early high-OI zones show position reduction.

Evidence against it:

- post-news volume expands;
- spot demand broadens;
- price breaks and retains a new high;
- OI/funding normalize rather than overheat;
- relative strength versus BTC persists.

This is a hypothesis about market structure, not a claim that a publisher or trader intended to facilitate selling.

## 8. Current market-structure interpretation

The current state is best described as:

**Mature repricing / high-OI consolidation with the first material long-side deleveraging event.**

The evidence is stronger for:

- first-wave short-squeeze fuel being substantially consumed;
- increased two-sided positioning;
- reduced marginal upside efficiency;
- higher sensitivity to BTC/broad-crypto risk changes;
- long-liquidation risk becoming material.

The evidence is not yet sufficient to conclude:

- durable trend termination;
- return to the pre-repricing $3 range;
- institutional distribution;
- a fixed new equilibrium price.

## 9. Key price-zone interpretation

The current charts suggest several observation zones rather than forecasts.

### Approximately $4.6-$4.7

Role:

- recent local high / failed continuation region;
- high-OI and high-attention area;
- candidate distribution / ceiling test zone.

### Approximately $4.3-$4.4

Role:

- repeated consolidation / re-entry area;
- current balance area after deleveraging.

### Approximately $4.0-$4.15

Role:

- first major long-liquidation / retest zone;
- important test of whether the repriced regime survives deleveraging.

A revisit should be judged by:

- OI delta;
- funding;
- long liquidation;
- spot/derivatives volume;
- recovery speed;
- BTC regime at the same time.

The price level alone is insufficient.

## 10. Proposed validation tasks

### 10.1 BTC → NEAR deleveraging lag

Measure 1m / 5m:

- BTC price return;
- BTC long liquidation;
- BTC OI;
- NEAR return;
- NEAR long liquidation;
- NEAR OI.

Test lags:

- 0;
- 5;
- 10;
- 15;
- 30;
- 60 minutes.

Goal:

Determine whether BTC deleveraging reliably precedes NEAR long-liquidation acceleration.

### 10.2 Liquidation-regime flip

Detect transition from:

- short-liquidation-dominant upside

to:

- long-liquidation-dominant downside.

Candidate metrics:

- `liquidation_side_ratio`
- `liquidation_regime_flip`
- `oi_change_after_regime_flip`
- `price_retention_after_long_washout`

### 10.3 Theme-age / maturity study

For repricing episodes, record:

- calendar days since initial breakout;
- active-market windows since discovery;
- cumulative return;
- cumulative volume;
- OI expansion;
- funding distribution;
- cumulative long/short liquidation;
- number of public-news references;
- subsequent return / drawdown.

Goal:

Test whether the apparent "5 business days / 7 calendar days" maturity effect repeats.

### 10.4 News-discovery reaction

For each material article / attention event:

- publication timestamp;
- price before/after;
- volume before/after;
- OI before/after;
- funding before/after;
- relative return versus BTC.

Classify as:

- continuation;
- neutral;
- distribution candidate;
- insufficient evidence.

## 11. Relationship to prior reports

### 11.1 2026-09-19 Crypto Macro-Leader report

`REPORT_CRYPTO_MACRO_LEADER_DERIVATIVES_CONTEXT_2026-09-19.md`

This report originally identified the primary analytical gap: local NEAR price/derivatives structure can appear internally coherent while BTC/macroeconomic flow changes the broader crypto regime.

The 2026-09-24 observation strengthens the importance of this gap because BTC weakening and BTC long liquidation coincided with a transition to NEAR long-side liquidation.

### 11.2 2026-09-20 Futures Position Reading report

`REPORT_FUTURES_POSITION_READING_AND_CRYPTO_DERIVATIVES_COLLECTION_2026-09-20.md`

This report formalized OI, funding, liquidation and Position Map reading.

The latest episode supplies a concrete example of:

```text
price ↓ + OI ↓ + long liquidation ↑
    = long unwind / leverage washout candidate
```

and should be retained as a Canary fixture.

### 11.3 2026-09-21 BTC / Altcoin Synchronization report

`REPORT_BTC_ALTCOIN_SYNCHRONIZATION_VALIDATION_2026-09-21.md`

That report focused on BTC-compatible upside synchronization before NEAR-specific amplification.

The latest episode adds the inverse case:

- BTC support weakens;
- BTC long liquidation appears;
- NEAR then exhibits larger local downside liquidation.

Together, the two observations support testing **bidirectional BTC-to-altcoin transmission**, not only upside correlation.

## 12. OrderScope interpretation boundary

Facts / source observations:

- timestamped price;
- OI;
- funding;
- liquidation;
- volume;
- BTC and NEAR aligned bars;
- publication timestamps.

Derived Metrics:

- lagged correlation;
- liquidation-side ratio;
- BTC-adjusted NEAR return;
- OI velocity;
- funding delta;
- price-retention after OI reduction.

Interpretations:

- short squeeze;
- long unwind;
- BTC-led risk reduction;
- mature price discovery;
- distribution-on-discovery candidate.

Predictions:

- next support;
- next breakout;
- trend termination;
- persistence.

Predictions must remain separate from the observations above.

## 13. Current conclusion

The NEAR observation has progressed from a simple upward repricing case into a full multi-phase derivatives case.

The strongest current observation is not that "NEAR has topped."

It is:

> **After approximately one week of discovery and repeated short-liquidation-driven upside, the market produced its first clear large long-liquidation episode while BTC buying support also weakened.**

This suggests the market has moved from an asymmetric upside squeeze regime into a more mature two-sided regime where both long and short leverage can be liquidated.

The next decisive evidence is whether:

- price can retain the $4 area while OI/funding normalize; or
- repeated long-liquidation events force the market into a lower accepted range.

This report should be used together with the 2026-09-19, 2026-09-20, and 2026-09-21 reports as a continuous NEAR/BTC Canary sequence rather than as an isolated event note.
