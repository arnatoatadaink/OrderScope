# v0.1.6 UWBS-070 — BTC institutional-flow / market-structure source survey — 2026-09-30

Status: **SURVEY COMPLETE / NO LIVE ACTIVATION AUTHORIZED**

## Scope

Canonical task:

```text
UWBS-070 — Survey BTC institutional-flow / market-structure sources
```

This task is a source-governance and implementation-readiness survey. It does not activate providers, create credentials, mutate Worker/Cron/D1, or authorize redistribution of third-party data.

## Design boundary

The v0.1.6 source hierarchy should separate four evidence classes:

1. exchange-native crypto market/derivatives data;
2. regulated futures-market institutional context;
3. spot-BTC ETP/ETF issuer/regulatory evidence;
4. optional aggregators for normalization gaps only.

Source observations remain Fact. Institutional-flow or causal market interpretation remains Interpretation unless directly evidenced.

## Recommended source hierarchy

### Tier A — exchange-native public market / derivatives APIs

#### Binance derivatives

Recommended role: primary raw derivatives venue for BTC and selected crypto assets.

Observed capabilities from current official documentation:

- current open interest;
- open-interest statistics;
- funding-rate history;
- mark/index prices;
- perpetual funding metadata;
- recent historical market trades.

Important retention constraint:

- Binance open-interest statistics documentation states that only the latest 30 days are available for that endpoint.

Implication:

```text
UWBS-073 adapter
    -> periodic snapshots
UWBS-074 archive/catch-up
    -> required for reproducible history beyond provider retention
```

Classification: **PRIMARY_RAW_DERIVATIVES / ARCHIVE_REQUIRED**.

#### Bybit V5

Recommended role: independent cross-venue confirmation.

Observed capabilities from official documentation:

- open interest for linear/inverse contracts;
- intervals from 5m through 1d;
- pagination and launch-time-bounded history;
- historical funding rates;
- instrument-specific funding interval metadata through instruments information.

The API documentation warns that extreme volatility can increase latency or temporarily delay data delivery.

Classification: **SECONDARY_RAW_DERIVATIVES / CROSS_VENUE_CONFIRMATION**.

#### OKX

Recommended role: third venue for OI/funding/mark/index and divergence checks.

Official API documentation currently exposes:

- open interest;
- current and historical funding rates;
- mark prices;
- index data;
- trades/candles/order book.

OKX also documents funding-formula changes and exposes formula metadata. Therefore funding records must retain source revision/formula context; historical values should not be treated as formula-invariant without metadata.

The API agreement states availability and API terms can vary by jurisdiction and service category.

Classification: **SECONDARY_RAW_DERIVATIVES / REVISION_METADATA_REQUIRED**.

#### Hyperliquid

Recommended role: perp-native / DEX comparison source.

Official documentation exposes historical funding through the public info endpoint. Hyperliquid should be treated as a structurally distinct venue rather than merged blindly with CEX contracts.

Classification: **DEX_PERP_CONFIRMATION / PRODUCT_NORMALIZATION_REQUIRED**.

## Tier B — BTC spot-market context

### Coinbase Advanced Trade

Recommended role: U.S.-venue BTC spot context.

Official Coinbase documentation provides:

- REST and WebSocket market data;
- product candles;
- market trades;
- ticker/order-book channels;
- real-time WebSocket price and Level 2 updates.

This is useful for BTC spot reference/activity context. It should not be treated as a direct institutional-flow feed.

Classification: **PRIMARY_US_SPOT_CONTEXT**.

## Tier C — regulated institutional context

### CME Group Bitcoin futures

Recommended role: regulated institutional futures context for BTC.

CME publishes volume/open-interest reporting. Current CME documentation states:

- daily volume and open-interest reports are available;
- preliminary daily reports are released at the end of the trading day;
- official data is published in the Daily Bulletin the following morning;
- preliminary and final reports may differ.

Required OrderScope semantics:

```text
preliminary CME observation -> source_revision = preliminary
final Daily Bulletin        -> source_revision = final
final may supersede preliminary observation
```

Do not collapse preliminary and final values into one immutable Fact without revision lineage.

Classification: **REGULATED_INSTITUTIONAL_CONTEXT / REVISION_AWARE**.

## Tier D — spot Bitcoin ETP / ETF evidence

### SEC / issuer filings

Recommended role: authoritative structural and periodic ETP evidence.

SEC filings can contain creations/redemptions, share transactions, Bitcoin holdings and fund accounting detail. SEC evidence is authoritative but generally not a same-day high-frequency flow feed.

The SEC also permits in-kind creations/redemptions for crypto ETPs under orders approved in July 2025, so simple assumptions that all spot Bitcoin ETF flows are cash-only are no longer valid.

Classification: **AUTHORITATIVE_REGULATORY / LOW_FREQUENCY**.

### Issuer holdings pages (example: iShares IBIT)

Issuer product pages expose current product/AUM information and may provide holdings-related evidence. Use as issuer-native context where machine-access and terms permit.

Do not infer daily net ETF flow from AUM change alone because price change, creations/redemptions and fees can all alter fund value.

Classification: **ISSUER_NATIVE_CONTEXT / FLOW_INFERENCE_NOT_ALLOWED_WITHOUT CONTRACT**.

## Optional aggregators

Cross-venue aggregators may reduce integration cost for liquidations, normalized OI or historical dashboards, but should be treated as optional secondary sources.

Before activation, each aggregator requires explicit review of:

- API terms;
- redistribution rights;
- timestamp semantics;
- historical depth;
- revision policy;
- rate limits;
- cost;
- survivorship/product mapping.

No aggregator is accepted by UWBS-070 as a substitute for official venue data where an official source already exposes the field.

## Source-to-contract mapping

```text
Binance / Bybit / OKX / Hyperliquid
    -> UWBS-068 CryptoDerivativeObservation / LiquidationObservation
    -> UWBS-073 adapters
    -> UWBS-074 durable archive
    -> UWBS-077 cross-venue guards

Coinbase spot
    -> BTC spot/activity context
    -> UWBS-069 relative-context inputs

CME
    -> institutional futures context
    -> revision-aware Fact lineage

SEC / issuer ETF evidence
    -> institutional/ETP context Facts
    -> later cross-asset / ETF-flow lane where applicable
```

## Important boundary with UWBS-084

Canonical registry assigns BTC spot ETF flow acquisition/normalization to:

```text
UWBS-084
```

Existing `analysis/app/orderscope_local/crypto/btc_spot_etf_flow.py` work belongs to that later lane and must not be replayed into v0.1.6 merely because UWBS-070 surveys ETF sources.

UWBS-070 may define source readiness and semantics only.

## v0.1.6 provider selection recommendation

For v0.1.6 implementation readiness:

```text
Primary derivatives source:      Binance
Cross-venue confirmations:       Bybit + OKX
DEX/perp-native confirmation:    Hyperliquid
U.S. BTC spot reference:         Coinbase
Institutional futures context:   CME
ETF structural evidence:         SEC + issuer-native evidence
Aggregator:                      deferred / optional
```

This is a design recommendation, not provider activation.

## Retention and revision requirements discovered by survey

### Mandatory local archive

Provider history is not uniformly durable. Binance OI history alone is sufficient evidence that local durable capture is necessary for reproducible historical studies.

Therefore UWBS-074 is not optional if UWBS-073 becomes active.

### Revision-aware storage

CME preliminary/final reporting and venue funding-formula/version changes require explicit revision semantics.

At minimum preserve:

```text
source_ref
source_revision
observed_at
available_at
accepted_at
retrieved_at
provider/product metadata
```

## Cost posture

The reviewed official public market endpoints are suitable for a low-cost initial implementation, but this survey does not certify commercial redistribution rights or unlimited production use.

No paid procurement is required to begin adapter development against public documentation/test fixtures.

Paid aggregation should be deferred until UWBS-075/077 demonstrates a field or historical-depth gap that official sources cannot satisfy economically.

## Acceptance result

UWBS-070 acceptance criteria for v0.1 development are satisfied as a survey task:

- source classes identified;
- primary/secondary role assigned;
- history/retention risk identified;
- revision semantics identified;
- cost/terms review boundary recorded;
- no live activation performed;
- UWBS-084 ETF implementation kept outside v0.1.6.

Status: **ACCEPTED — SOURCE SURVEY ONLY**.

## Next task

Proceed to:

```text
UWBS-071 — Define 24/7 crypto time-window / weekend-liquidity contract
```

That contract should remain provider-independent and should treat Asia/Europe/U.S. labels as analysis windows only, never as proof of participant nationality or causal origin.
