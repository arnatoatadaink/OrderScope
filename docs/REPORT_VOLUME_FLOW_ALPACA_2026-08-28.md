# Stock Monitoring Fact — Volume / Capital-Activity Report

Date: 2026-08-28
Status: non-normative implementation report
Scope: Alpaca market data, volume-aware Attention, capital-activity estimation, volatility-oriented derived metrics

## 1. Conclusion

The current v0.1 design already accepts OHLCV bars and treats `volume` as an auxiliary market-analysis input. The next implementation slice should make volume-derived activity explicit without redefining volume as literal capital inflow.

The key boundary is:

```text
Observed bar data
  -> deterministic volume / price features
  -> capital-activity proxy
  -> Attention / volatility-oriented derived metrics
  -> interpretation
```

`volume` and OHLC prices are observed market data. `relative_volume`, notional turnover and signed/activity scores are Derived Metrics. Statements such as "capital is flowing into this symbol" remain interpretation unless supported by a stronger trade/quote-level model.

## 2. Required observed inputs

Minimum bar-level inputs:

- open
- high
- low
- close
- volume
- bar start/end
- session kind
- market date
- logical feed/data variant

Minimum contextual inputs for short-horizon activity ranking:

- market benchmark return
- sector/theme benchmark return where configured
- previous close / gap context
- historical volume baseline

## 3. Derived market-activity features

The implementation should expose at least the following deterministic features:

```text
return
high_low_range
volume
relative_volume
close_location
opening_gap
market_relative_return
sector_relative_return
notional_turnover_proxy
```

Recommended definitions are configuration/versioned analysis contracts rather than provider contracts.

### 3.1 Relative volume

```text
relative_volume = current_volume / comparable_baseline_volume
```

The baseline must compare compatible session/time buckets. Premarket, Regular and After-hours must not be mixed into one baseline without an explicit policy.

### 3.2 Close location

A simple bounded feature may use:

```text
close_location = (close - low) / (high - low)
```

for non-zero ranges. The zero-range case must be represented explicitly rather than divided by zero.

### 3.3 Notional turnover proxy

A bar-level approximation of capital activity may use a price proxy multiplied by volume, for example:

```text
notional_turnover_proxy = representative_price * volume
```

where `representative_price` is a versioned analysis choice such as close, VWAP when available, or an OHLC-derived typical price.

This measures traded notional activity, not net inflow. Buys and sells are two sides of the same executed volume, so OHLCV bars alone cannot identify true net capital inflow.

## 4. Capital-flow interpretation boundary

The system must not treat the following as Facts:

- "net buying was X dollars",
- "institutional money entered",
- "capital inflow equals price × volume",
- buy/sell direction inferred without a defined trade-direction model.

At bar level the safer wording is:

- activity concentration,
- unusually high traded notional,
- positive/negative price response with elevated volume,
- relative strength combined with elevated volume.

A future trade/quote-level extension may define signed flow using explicit aggressor/trade-direction methodology, but that is outside the current bar-level v0.1 contract.

## 5. Attention use

Volume should participate in Attention ranking together with price and context.

Illustrative evidence pattern:

```text
positive return
+ high relative volume
+ close near bar/session high
+ positive market-relative return
+ positive sector-relative return
=> stronger activity-concentration candidate
```

Conversely, a large positive return with subnormal volume while the whole market rises strongly should receive less idiosyncratic Attention weight.

Thresholds are intentionally not fixed here. They require measurement against the initial Universe.

## 6. Volatility-oriented use

Volume is not volatility itself. It is an explanatory/conditioning feature that may improve estimates of near-term volatility or identify regimes in which price movement is more likely to persist.

Recommended first-stage feature set:

- absolute/log return
- high-low range
- realized short-window volatility
- relative volume
- notional turnover proxy
- opening gap
- close location
- market/sector relative return
- session kind
- earnings/event proximity

The first implementation should preserve these deterministic inputs and defer model selection for volatility prediction until enough observations are collected.

## 7. Alpaca feed implications

For Alpaca Basic, real-time equities data is IEX-scoped and must not be treated as full-market volume. Therefore real-time IEX volume is suitable as a provisional Attention signal, not a literal whole-market volume measure.

The design should retain `logical_data_variant` / feed provenance so later SIP historical observations can be compared with IEX observations.

Recommended Basic validation loop:

```text
IEX real-time observation
  -> provisional Attention features
  -> delayed SIP historical observation when available
  -> compare volume / relative-volume / ranking differences
  -> store quality evidence
```

The value of upgrading to real-time SIP should be decided from measured signal-quality differences, not from Universe size alone.

## 8. Deployment split

Cloud/Worker responsibilities:

- scheduled acquisition
- session gate
- historical catch-up
- schema validation
- lightweight normalization
- checkpoint maintenance
- lightweight volume/activity feature updates where CPU budget permits
- digest/state materialization

Main-PC/heavy-analysis responsibilities:

- FFT
- multi-window correlation
- bulk baseline recomputation
- richer volatility modelling
- Regime recomputation
- LLM-assisted event interpretation
- backtesting / exploratory analysis

This preserves `DD-DEPLOY-001` and keeps Cloudflare/Alpaca behind replaceable adapters.

## 9. Design impact

No Code of Truth v0.1 document is changed by this report.

Implementation/design follow-up should connect this report to:

- `HLD-MKT-001` — market data pipeline
- `HLD-FFT-001` — analysis-ready series and market analysis
- `HLD-SCH-001` — cadence and acquisition
- `DETAILED_DESIGN_SCHEDULER_MARKET_v0.1.md` — OHLCV acceptance and feed provenance
- the next Market/FFT detailed-design slice — deterministic feature contracts and Fact / Derived Metric boundary

## 10. Open items

- comparable relative-volume baseline definition
- exact representative-price definition for notional turnover
- Attention score/threshold policy
- IEX vs SIP quality metrics and tolerance
- volatility prediction model and target horizon
- storage location/retention for high-density bars and derived features
- whether quotes/trades are ever promoted into v0.1 scope
