# OrderScope — VIX / Cross-Asset Volatility Observation Report

Date: 2026-09-27
Status: **Planning / WBS-unreflected input**
Scope: U.S. equity volatility, VIX futures term structure, BTC implied volatility, MSTR option-implied volatility

## 1. Purpose

This report defines a proposed volatility-observation lane for OrderScope.

The goal is not to treat a fear index as a standalone trading signal. The goal is to preserve observable volatility-market state and derive inspectable cross-asset stress / divergence metrics that can later be validated against price, volume, rates, crypto and company-specific events.

The initial observation layers are:

1. VIX level and change,
2. VIX futures term structure,
3. BTC 30-day implied volatility,
4. MSTR option-implied volatility,
5. MSTR-vs-BTC implied-volatility differential,
6. later cross-asset volatility-regime interpretation after historical validation.

## 2. Fact / Derived Metric / Interpretation boundaries

### 2.1 Facts

The following may be stored as Facts only when obtained from an accepted source with timestamp, units and provenance:

- VIX index level,
- VIX futures contract prices and expiries,
- BTC 30-day implied-volatility benchmark value,
- MSTR option observations sufficient to derive or source 30-day implied volatility,
- option expiries / strikes / call-put identity where raw option inputs are retained,
- provider timestamp, available time, accepted time and stale/missing state.

VIX itself is an index derived from S&P 500 option prices. It is not a directly held spot asset. Futures, options and futures-based exchange-traded products are separate instruments and must not be stored as interchangeable with spot VIX.

### 2.2 Derived Metrics

Candidate derived metrics:

```text
vix_d1_pt                 = vix_t - vix_prev_close
vix_d1_pct                = (vix_t / vix_prev_close) - 1
vix_f1_spot_basis_pct     = (vix_f1 / vix_spot) - 1
vix_f2_f1_spread_pct      = (vix_f2 / vix_f1) - 1
mstr_btc_iv_ratio         = mstr_iv30 / btc_iv30
mstr_btc_iv_spread        = mstr_iv30 - btc_iv30
```

Additional metrics such as percentile, z-score, slope and change velocity may be added only with a frozen lookback/window definition and tests.

### 2.3 Interpretations

Possible interpretation states are intentionally provisional:

- `EQUITY_VOL_STRESS_CANDIDATE`
- `VIX_CURVE_BACKWARDATION_CANDIDATE`
- `CRYPTO_VOL_STRESS_CANDIDATE`
- `MSTR_SPECIFIC_VOL_PREMIUM_CANDIDATE`
- `CROSS_ASSET_VOL_STRESS_CANDIDATE`

These are not Facts and must preserve supporting, contradicting and unknown evidence.

No numerical threshold is frozen in this report. Thresholds must remain configurable/TBD until historical calibration is performed.

## 3. Why VIX level alone is insufficient

A single VIX value cannot describe the whole volatility regime.

Required distinctions:

- absolute level versus daily point change,
- absolute level versus daily percentage change,
- spot VIX versus VIX futures,
- futures contango versus backwardation,
- broad equity volatility versus crypto volatility,
- crypto-wide volatility versus MSTR-specific option premium.

A futures-based VIX ETF may decay in a persistent contango environment even if spot VIX does not fall materially. Therefore an ETF price is not a canonical VIX observation and should not substitute for VIX plus futures-curve data.

## 4. VIX observation contract candidate

Minimum fields:

```text
instrument_id
observation_time
available_time
accepted_time
source_id
value
unit
quality_state
stale_reason?
```

Minimum VIX series:

```text
VIX_SPOT
VIX_F1
VIX_F2
```

Recommended initial cadence is **TBD**. The cadence should be selected after provider limits, licensing, use case and Worker budget are measured. A daily close-only path can validate the schema before intraday acquisition is considered.

## 5. VIX futures term structure

The term structure is required because it carries information that spot VIX alone does not expose and because VIX-linked exchange-traded products are generally futures-based.

Proposed curve state:

```text
CONTANGO
FLAT
BACKWARDATION
UNKNOWN
```

The exact tolerance for `FLAT` is TBD and must not be inferred from a single episode.

Candidate observations:

- F1 minus spot basis,
- F2 minus F1 spread,
- curve-state transition,
- persistence of backwardation/contango,
- change velocity.

A transition to backwardation may be treated as stress evidence only after validation; it must not become an automatic sell/buy trigger.

## 6. BTC implied-volatility observation

OrderScope should support a source-neutral `BTC_IV_30D` concept rather than hard-code one commercial benchmark into the domain model.

Required source survey items:

- benchmark methodology,
- real-time versus settlement availability,
- historical depth,
- redistribution/license terms,
- API accessibility,
- timestamp semantics,
- cost/rate limits,
- revision behavior.

The selected benchmark/provider is **TBD**.

## 7. MSTR option-implied-volatility observation

MSTR does not require a proprietary "MSTR VIX" index to obtain useful fear/volatility context. Its listed option market can provide a company-specific implied-volatility layer.

Candidate fields:

```text
mstr_iv30
mstr_iv_rank
mstr_iv_percentile
mstr_put_skew
mstr_iv60
mstr_iv90
```

Only `mstr_iv30` is considered minimum scope for the first contract. IV rank/percentile require a defined historical lookback; skew requires a defined delta/strike convention; 60d/90d require term-structure interpolation or accepted provider outputs. Those definitions remain TBD.

## 8. MSTR versus BTC volatility differential

The key cross-asset purpose is to separate broad crypto stress from MSTR-specific volatility premium.

Candidate metrics:

```text
mstr_btc_iv_ratio  = mstr_iv30 / btc_iv30
mstr_btc_iv_spread = mstr_iv30 - btc_iv30
```

Interpretation hypothesis:

- BTC IV rises and MSTR IV rises proportionally -> broad crypto stress may dominate.
- MSTR IV rises materially faster than BTC IV -> company/equity-structure-specific premium may be present.
- BTC IV rises while MSTR relative premium compresses -> broad crypto volatility may dominate over MSTR-specific repricing.

These are **hypotheses**, not validated causal rules.

## 9. Initial storage / data-quality requirements

The observation layer should preserve:

- source and provider identity,
- exact observation/available/accepted times,
- market/session context where relevant,
- value units,
- expiry metadata for futures/options,
- missing/stale state,
- source revision or retrieval identity where available.

Missing BTC IV or MSTR IV must not be silently replaced with realized volatility. If a fallback is ever introduced, it requires an explicit metric identity and quality state.

## 10. Alert candidates

Alerts are proposed only as future calibrated interpretations:

- VIX point/percentage acceleration,
- VIX curve transition from contango to backwardation,
- BTC IV acceleration,
- MSTR IV divergence above BTC IV,
- simultaneous equity + crypto volatility stress.

No threshold is authorized by this report.

## 11. Historical validation plan

Before promoting volatility states into a formal Regime signal:

1. collect a reproducible historical sample,
2. replay multiple calm / correction / shock / recovery windows,
3. measure false positives and lead/lag against price/volume rather than assuming causality,
4. compare absolute thresholds with percentile/z-score approaches,
5. validate whether curve transitions add information beyond spot VIX,
6. validate whether `mstr_btc_iv_ratio` and spread add information beyond BTC price beta,
7. freeze only thresholds that survive documented tests.

Reference cases should include both positive and negative controls. No single crisis or MSTR episode is sufficient to establish a production threshold.

## 12. Provider / cost boundary

Unknown until source survey:

- VIX spot source,
- VIX futures source,
- BTC 30-day IV source,
- MSTR option-chain / IV source,
- redistribution rights,
- historical API cost,
- intraday rate limits,
- Worker/D1 capacity impact.

The first implementation should prefer source-neutral contracts and Shadow/local validation. Live provider activation, paid procurement and Worker/Cron changes remain separately gated.

## 13. Non-goals

This report does not authorize:

- VIX ETF trading,
- VIX futures/options execution,
- automated MSTR/BTC trading,
- a claim that VIX or IV predicts direction,
- fixed VIX fear thresholds,
- fixed MSTR/BTC IV-ratio thresholds,
- replacement of spot VIX with a VIX ETF price,
- live provider activation or paid procurement.

## 14. Proposed WBS-unreflected decomposition

Canonical provisional IDs are allocated in the companion extension/registry update:

- `UWBS-094` — volatility-source/provider survey and source-neutral instrument contract
- `UWBS-095` — VIX spot + F1/F2 acquisition and term-structure metrics
- `UWBS-096` — VIX level/change/curve interpretation contract
- `UWBS-097` — BTC 30-day IV acquisition/normalization
- `UWBS-098` — MSTR 30-day option-IV acquisition/normalization
- `UWBS-099` — MSTR/BTC IV differential and cross-asset volatility interpretation
- `UWBS-100` — historical calibration, Canary/false-positive and Worker/D1 capacity acceptance

## 15. Proposed critical-path candidate

```text
UWBS-094
  +-> UWBS-095 -> UWBS-096
  +-> UWBS-097
  +-> UWBS-098

UWBS-097 + UWBS-098
  -> UWBS-099

UWBS-096 + UWBS-099
  -> UWBS-100
```

This is a **CP candidate only**. It is not part of the normative project critical path until a formal WBS/CP revision incorporates it.
