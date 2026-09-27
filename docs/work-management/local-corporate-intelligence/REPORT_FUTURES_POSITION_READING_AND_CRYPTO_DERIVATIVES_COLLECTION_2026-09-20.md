# OrderScope — Futures Position Reading and Crypto Derivatives Collection Report

Status: **Planning / design input — not yet normative**  
Date: 2026-09-20  
Scope: perpetual futures / futures position reading, OI / funding / liquidation interpretation, exchange-level collection, OrderScope integration  
Related gap report: `docs/work-management/local-corporate-intelligence/REPORT_CRYPTO_MACRO_LEADER_DERIVATIVES_CONTEXT_2026-09-19.md`  
Related backlog: `UWBS-036..040`

## 1. Purpose

This report formalizes the manual derivatives reading used in the 2026-09-18..20 NEAR observation and converts it into a reusable OrderScope design.

The main objective is to distinguish:

- observed derivatives Facts;
- deterministic Derived Metrics;
- market-structure Interpretations;
- directional Predictions.

The report must not treat open interest, funding, or liquidation as direct evidence of trader identity, institutional participation, or net capital inflow.

## 2. Core mechanics

### 2.1 Open Interest

Open Interest (OI) is the amount of futures/perpetual contracts that have been opened and remain unsettled.

Every futures contract has both sides:

```text
1 long
  ↕
1 short
```

Therefore, a new long and a new short matched together create one new contract and increase OI.

A useful simplified state table is:

| Matched actions | OI effect |
|---|---:|
| new long vs new short | increases |
| existing long closes vs new long takes over | approximately unchanged |
| existing short closes vs new short takes over | approximately unchanged |
| existing long closes vs existing short closes | decreases |

OI does not tell which side is "larger" in contract count; the contract is intrinsically paired.

### 2.2 Why an open position is "already executed" but still visible in OI

The position affects price when the order is executed.

After execution:

```text
entry order executes
    ↓
position becomes open
    ↓
contract remains in OI
    ↓
holding alone creates no new trade
    ↓
close / liquidation executes later
    ↓
price receives a new market impact
```

This allows OI to be used as a memory of unresolved positioning, but not as an exact entry-price ledger.

### 2.3 Funding

Funding is a periodic transfer between perpetual longs and shorts designed to keep perpetual prices close to the underlying spot/index price.

General reading:

- positive funding: long-side demand / perpetual premium is stronger; longs normally pay shorts;
- negative funding: short-side demand / perpetual discount is stronger; shorts normally pay longs.

Funding is not a direct long-position count.

Funding can remain nearly unchanged while OI rises sharply if new long and short interest expands in a relatively balanced way.

### 2.4 Liquidations

Liquidation data describes positions that could no longer satisfy margin requirements and were forcibly reduced/closed.

Important rule:

- long liquidation is not a new short;
- short liquidation is not a new long.

Liquidation is a closing mechanism. It can create directional market orders that amplify price movement.

## 3. Combined reading matrix

### 3.1 Price up + OI up + funding up

Candidate interpretation:

- new leveraged participation;
- long demand relatively stronger;
- continuation is possible;
- leverage overheating risk is accumulating.

Do not convert this automatically into a bullish Prediction.

### 3.2 Price up + OI down + short liquidation up

Candidate interpretation:

- short-squeeze / forced short covering;
- upward move may depend on liquidation fuel;
- continuation quality should be checked after liquidation subsides.

### 3.3 Price flat + OI up + funding flat

Candidate interpretation:

- new contracts are accumulating without a strong directional premium;
- both sides may be building;
- range compression / future liquidation fuel candidate.

This is the closest pattern to the "firepowder storage" behavior seen in the NEAR case.

### 3.4 Price flat + OI down + funding down

Candidate interpretation:

- leverage is leaving while price remains accepted;
- constructive deleveraging / price-retention candidate.

### 3.5 Price down + OI down + long liquidation up

Candidate interpretation:

- long unwind / liquidation cascade;
- if the price later stabilizes while OI and funding cool, the market may be completing a leverage reset.

### 3.6 Price down + OI up + funding up

Candidate interpretation:

- dip-buying / countertrend leveraged long buildup;
- downside liquidation fuel may be replenished.

This is one of the highest-risk combinations for a falling market.

## 4. Position-map interpretation

A useful manual analysis is to record where OI was created and the funding state at that time.

Illustrative record:

```text
price zone: 3.75-3.80
OI delta: +50M USD equivalent
funding: moderate positive
later liquidation: long-heavy
later price: 3.50
```

Possible interpretation:

- the original OI increase was not pure long demand;
- part of the high-price short population may remain open and profitable;
- some long-side contracts were subsequently removed;
- returning toward 3.75-3.80 may encounter both profit-taking and short-cover dynamics.

Important limitation:

OI is aggregate state. It does not reveal the exact entry price, leverage, ownership, or hedge relationship of every remaining contract.

Therefore OrderScope should call this a **Position Map Estimate**, not a reconstructed position ledger.

## 5. "Heavy" price zones

A price zone can be treated as positioning-heavy when several observations align:

- significant OI increase occurred there;
- funding state at entry is known;
- later OI has not fully reverted;
- one-sided liquidations have occurred after leaving the zone;
- price repeatedly reacts when revisiting the zone;
- spot/perpetual basis changes near the zone.

Potential Derived Metrics:

- `oi_delta_by_price_bucket`
- `oi_retention_ratio_by_price_bucket`
- `funding_at_oi_build`
- `post_build_long_liquidation`
- `post_build_short_liquidation`
- `position_zone_pressure_score`

The final score must remain a Derived Metric, not a Fact about actual remaining trader positions.

## 6. Exchange-level observations

Exchange decomposition is important because an aggregate OI spike can be:

- broad across multiple venues;
- concentrated on one venue;
- caused by a data anomaly;
- caused by product-specific contract changes.

Minimum normalized keys:

```text
venue
instrument_id
contract_type
margin_type
quote_asset
timestamp
open_interest_contracts
open_interest_base
open_interest_usd
funding_rate
funding_interval
mark_price
index_price
spot_reference_price
basis
derivatives_volume
long_liquidation_usd
short_liquidation_usd
source_timestamp
retrieved_at
source_revision
```

Not every venue exposes every field. Missing data must remain explicit.

## 7. OrderScope collection strategy

### 7.1 Source hierarchy

Recommended v0.1 approach:

1. official exchange APIs for raw OI / funding / mark / index / contract metadata;
2. exchange WebSocket streams where real-time context materially improves analysis;
3. an aggregator only for fields that exchanges do not expose consistently, especially normalized liquidation history;
4. local archival because some official historical endpoints retain only short windows.

### 7.2 Binance

Binance official derivatives APIs expose:

- current open interest;
- historical open-interest statistics;
- funding-rate history;
- mark/index price;
- basis;
- long/short-account ratios.

Some historical derivatives endpoints expose only a bounded recent period, so OrderScope should archive observations continuously rather than depend on long-lived API history.

Recommended role:

- primary CEX source for NEAR/BTC OI, funding, mark/index and basis;
- periodic REST snapshots;
- WebSocket/trade streams only if required by later high-frequency validation.

### 7.3 Bybit

Bybit V5 exposes:

- open-interest history with 5m/15m/30m/1h/4h/1d intervals;
- historical funding rates;
- instrument metadata needed to resolve funding intervals.

Recommended role:

- independent cross-venue confirmation;
- useful for checking whether an OI change is Binance-specific or market-wide.

### 7.4 OKX

OKX provides public market endpoints for:

- tickers;
- order books;
- candles;
- current/historical funding;
- mark price;
- open interest.

Recommended role:

- third major CEX confirmation source;
- useful for venue-divergence metrics.

### 7.5 Hyperliquid

Hyperliquid's public API exposes perpetual asset context including:

- current funding;
- open interest;
- mark price;
- oracle price;
- premium;
- notional volume.

Historical funding is available via the info endpoint; WebSocket active-asset context can stream OI/funding/price state.

Hyperliquid also publishes historical asset-context / order-book datasets, but archival updates are not guaranteed to be timely and some datasets may be missing. OrderScope should still record its own time series for reproducibility.

Recommended role:

- DEX/perp-native comparison against centralized venues;
- useful for detecting whether positioning is broad across market structure rather than isolated to CEXs.

## 8. Liquidation collection

Liquidation data is the least uniform part of the contract.

Preferred design:

```text
exchange-native liquidation stream if available
        ↓
normalized liquidation event
        ↓
1m / 5m / 15m buckets
        ↓
aggregate across venues
```

Minimum normalized event:

```text
venue
instrument_id
side_liquidated: LONG | SHORT
price
quantity
notional_usd
event_time
retrieved_at
source_ref
```

If a provider only supplies bucketed aggregate liquidation values, preserve the provider's bucket and do not fabricate individual events.

An aggregator such as CoinGlass may reduce integration cost for cross-venue liquidation/OI views, but provider terms, cost, redistribution rights, timestamp semantics and historical depth must be reviewed before use. It should not silently replace official-source data for fields that official APIs already provide.

## 9. Sampling cadence

Suggested initial cadence for monitored crypto assets:

| Data | Initial cadence | Reason |
|---|---|---|
| spot / mark / index price | 1m | align with current market-analysis cadence |
| OI | 1m-5m | large position changes are usually detectable at this resolution |
| funding current / predicted | 1m-5m snapshot | rate changes can precede settlement |
| settled funding history | at each venue settlement + catch-up | immutable historical record |
| basis / premium | 1m | direction-demand context |
| liquidation | event stream or 1m bucket | cascade detection |
| derivatives volume | 1m-5m | activity context |
| order-book depth | optional 1m snapshots / event-driven | expensive; use only for selected Canary assets |

For a free/low-cost v0.1, 5-minute OI/funding/basis snapshots plus event/bucket liquidation capture is a reasonable first implementation.

## 10. Storage model

Do not overload the equity OHLCV schema.

Recommended logical records:

### CryptoDerivativeObservation

```text
observation_id
venue
instrument_id
contract_type
observed_at
available_at
accepted_at
open_interest_contracts?
open_interest_base?
open_interest_usd?
funding_rate?
funding_interval_seconds?
mark_price?
index_price?
basis?
derivatives_volume_usd?
source_ref
source_revision
```

### LiquidationObservation

```text
venue
instrument_id
bucket_start
bucket_end
long_liquidation_usd
short_liquidation_usd
event_count?
source_ref
accepted_at
```

### PositionMapBucket

Derived Metric only:

```text
instrument_id
price_bucket_low
price_bucket_high
window_start
window_end
oi_added_usd
oi_removed_usd
estimated_oi_retention
funding_at_build
subsequent_long_liquidation_usd
subsequent_short_liquidation_usd
confidence
rule_version
```

## 11. Derived metrics

Recommended first set:

- `oi_delta_5m`
- `oi_delta_1h`
- `oi_velocity`
- `oi_to_market_cap`
- `oi_to_spot_volume`
- `funding_delta`
- `funding_zscore`
- `basis_bps`
- `long_liquidation_5m`
- `short_liquidation_5m`
- `liquidation_imbalance`
- `price_return_vs_oi_delta_state`
- `oi_retention_by_price_bucket`
- `cross_venue_oi_dispersion`
- `cross_venue_funding_dispersion`

Thresholds should be calibrated historically and must not be copied from the NEAR case as universal constants.

## 12. Interpretation states

Candidate non-Fact states:

- `LEVERAGE_BUILDUP_CANDIDATE`
- `BALANCED_OI_BUILDUP_CANDIDATE`
- `LONG_CROWDING_CANDIDATE`
- `SHORT_CROWDING_CANDIDATE`
- `SHORT_SQUEEZE_CANDIDATE`
- `LONG_LIQUIDATION_CASCADE_CANDIDATE`
- `LEVERAGE_WASHOUT_CANDIDATE`
- `PRICE_RETENTION_AFTER_DELEVERAGING`
- `POSITION_ZONE_RESISTANCE_CANDIDATE`
- `POSITION_ZONE_SUPPORT_CANDIDATE`
- `RANGE_COMPRESSION_WITH_HIGH_OI`

Interpretations should expose supporting and contradicting evidence rather than producing an unqualified directional label.

## 13. Relation to BTC macro context

Local derivatives structure should never be the highest-level context for BTC-sensitive assets.

Recommended evaluation order:

```text
Macro / Policy / Regulation
        ↓
BTC spot / ETF / CME context
        ↓
Crypto breadth / leader state
        ↓
Target spot relative strength
        ↓
Target OI / funding / liquidation
        ↓
Scenario / prediction
```

This prevents a locally coherent NEAR position read from being treated as complete when BTC or macro capital is driving the broader market.

## 14. Implementation split for OrderScope

### Cloudflare / scheduled acquisition

Suitable for:

- REST snapshots of OI/funding/mark/index/basis;
- limited set of BTC + selected crypto-sensitive assets;
- provider checkpointing;
- normalization;
- idempotency;
- lightweight 5m Derived Metrics;
- short hot-state retention.

### Local analysis server

Suitable for:

- cross-exchange reconstruction;
- price-bucket Position Map;
- historical calibration;
- liquidation-cascade analysis;
- BTC→altcoin lag analysis;
- higher-resolution order-book / trade replay;
- scenario generation.

This matches the existing OrderScope edge-acquisition / local-heavy-analysis split.

## 15. Initial implementation priority

Recommended sequence:

1. Binance + Bybit + Hyperliquid OI/funding/mark/index snapshots for BTC and NEAR.
2. Add OKX after source-neutral contract is stable.
3. Archive every snapshot locally from day one.
4. Add liquidation data as a separate contract.
5. Build price × OI × funding × liquidation state classification.
6. Build Position Map buckets.
7. Add BTC macro-leader context from UWBS-037/038.
8. Replay 2026-09-18..20 NEAR as the first Canary.

## 16. Acceptance criteria

The implementation is acceptable when it can reproduce, without manual chart reading:

- where material OI was added;
- whether funding was rising/falling/neutral at the time;
- whether subsequent liquidation was long- or short-dominant;
- whether OI was retained after price left the build zone;
- whether the same positioning change occurred across multiple venues;
- whether the target move was BTC-led or target-specific;
- when evidence is insufficient to infer direction.

It must also reject the following invalid conclusions:

- OI increase = new long capital;
- positive funding = guaranteed price rise;
- long liquidation = new short opening;
- short liquidation = new long opening;
- price-zone OI estimate = exact entry-price distribution;
- exchange time window = participant nationality.

## 17. Official-source references checked

- Binance Derivatives Market Data: https://developers.binance.com/docs/derivatives/
- Bybit V5 Open Interest: https://bybit-exchange.github.io/docs/api-explorer/v5/market/open-interest
- Bybit Funding Rate History: https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- OKX API: https://www.okx.com/docs-v5/
- Hyperliquid Perpetuals Info API: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals
- Hyperliquid Funding: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- Hyperliquid Historical Data: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data

## 18. Conclusion

The manual NEAR analysis can be converted into a systematic OrderScope feature if the project records derivatives state as its own evidence layer.

The key design idea is:

```text
OI = unresolved contract inventory
Funding = directional demand / perp-vs-spot pressure
Liquidation = forced exit
Price = market outcome
```

No one variable is sufficient alone.

The strongest reusable reading comes from preserving the time and price zone where OI changed, the funding state at that moment, the subsequent liquidation side, and whether the OI remained after price moved away.

This should be implemented under UWBS-036 and feed UWBS-037/040 rather than being treated as an equity OHLCV extension.
