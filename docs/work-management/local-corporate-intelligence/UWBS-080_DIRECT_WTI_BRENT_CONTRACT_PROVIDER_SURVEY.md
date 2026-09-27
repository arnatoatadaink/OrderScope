# OrderScope — UWBS-080 Direct WTI / Brent Contract and Provider Survey

Status: **WEB IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**
Canonical task: `UWBS-080`
Legacy backlog alias: `UWBS-048`
Scope: Macro-Commodity / provider-neutral contract / source survey

## 1. Objective

Introduce direct crude-oil observations without treating USO or another tradable
proxy as the canonical crude price and without collapsing fundamentally different
price identities into one ambiguous `WTI` or `Brent` series.

This task defines the Fact boundary and source-selection boundary only. It does
not activate a provider, create a Worker/Cron job, mutate D1, procure a paid
plan, or create a Risk-On interpretation.

## 2. Identity decision

The v0.1 commodity-price boundary recognizes two distinct price forms:

```text
SPOT_REFERENCE
  WTI   -> Cushing, Oklahoma reference spot
  Brent -> Europe reference spot

FUTURES_CONTRACT
  WTI   -> explicitly identified NYMEX listed contract
  Brent -> explicitly identified ICE Futures Europe listed contract
```

These identities are deliberately separate.

Forbidden collapses:

```text
WTI spot == CL front month              NO
Brent spot == ICE Brent front month     NO
front month == continuous rolled series NO
USO == WTI                              NO
USO == Brent                            NO
```

A continuous/rolled futures series requires a separately versioned roll
methodology and is not part of UWBS-080 v0.1.

## 3. Implemented contract

Implementation:

`analysis/app/orderscope_local/contracts/commodity_market.py`

Public exports:

- `CrudeBenchmark`
- `CommodityPriceForm`
- `CommodityVenue`
- `CommodityLocation`
- `CommodityPriceObservation`

Fact schema:

```text
commodity-price-observation-v0.1
```

Fact types:

```text
commodity_price.spot_reference
commodity_price.futures_contract
```

v0.1 normalized unit:

```text
usd_per_barrel
```

### Required identity fields

Spot reference:

```text
benchmark
location
series_id
observed_at
value/unit
provenance
```

Futures contract:

```text
benchmark
venue
contract_code
delivery_month
series_id
observed_at
value/unit
provenance
```

### Negative price rule

The generic crude-price contract accepts finite negative prices. Positivity is
not a valid invariant for listed crude futures because a historically valid WTI
futures observation can be below zero.

Non-finite numeric values remain invalid.

## 4. Provider survey

### 4.1 EIA — daily reference spot candidate

EIA Open Data API v2 exposes the Petroleum / Prices / Spot Prices route with:

```text
RWTC  Cushing, OK WTI Spot Price FOB (Dollars per Barrel)
RBRTE Europe Brent Spot Price FOB (Dollars per Barrel)
```

The EIA petroleum definitions describe WTI Cushing as a domestic reference or
marker crude traded in the spot market at Cushing. EIA defines spot price as a
one-time open-market transaction for immediate delivery at a specified location.
The EIA table also identifies Refinitiv, an LSEG business, as the source of the
spot-price data.

Decision:

```text
EIA API v2 = preferred v0.1 source candidate for DAILY WTI/Brent reference spot
```

Boundary:

- preserve the exact EIA series identity;
- preserve source/retrieval lineage;
- do not relabel the daily EIA series as an exchange futures price;
- do not claim EIA itself originated the underlying spot observation;
- production redistribution/reuse remains subject to source/terms review because
  EIA identifies Refinitiv/LSEG as the underlying spot-price source.

API v1 is retired; new implementation must use the supported API v2 route.

### 4.2 Massive — U.S. futures candidate

Massive Futures currently documents contract discovery, product metadata,
trading schedules, historical aggregate bars, snapshots, trades and quotes for
supported U.S. futures exchanges including NYMEX. Its aggregate-bar interface is
contract-ticker based and supports minute resolution.

Current individual-plan survey shows:

```text
Basic      free       5 API calls/min, 2y history, minute aggregates
Starter    $29/mo     10-minute delayed, unlimited API calls
Developer  $79/mo     5y history, delayed, trades/top-of-book
Advanced   $199/mo    real-time, 7+ years
```

Decision:

```text
Massive = acceptable candidate for NYMEX WTI listed-futures observations
          and historical/minute contract-aware research
```

It must not be used to label CL futures as WTI spot.

Massive's documented exchange set does not establish ICE Futures Europe Brent
coverage. Therefore Massive is not selected here as the Brent futures source.

### 4.3 CME / NYMEX direct licensing boundary

CME Group treats non-display system/program use as a licensing category. A
production OrderScope adapter that consumes CME/NYMEX market information must
therefore remain behind the provider/terms gate even when accessed through a
vendor.

This survey does not authorize direct CME market-data licensing or procurement.

### 4.4 ICE Brent futures

ICE identifies Brent Crude Futures as an ICE Futures Europe contract. Current
ICE material exposes explicit expiry/contract identity and lists APIs/bulk feeds
as enterprise data-access mechanisms. ICE also documents authorized quote vendors
for real-time, delayed, EOD and historical exchange data.

Decision:

```text
ICE Brent intraday futures source = NOT YET SELECTED
```

Accepted candidates for the next source decision are:

1. ICE enterprise API/feed under reviewed license; or
2. an ICE-authorized distributor whose contract-level data, history, latency,
   non-display terms and cost satisfy OrderScope requirements.

Do not substitute a generic web quote or an unverified continuous Brent symbol.

## 5. Source-selection table

| Need | v0.1 decision | Identity | Activation state |
|---|---|---|---|
| WTI daily reference | EIA API v2 candidate | WTI / Cushing spot / RWTC | Not activated |
| Brent daily reference | EIA API v2 candidate | Brent / Europe spot / RBRTE | Not activated |
| WTI intraday | Massive NYMEX futures candidate | explicit CL contract | Not activated |
| Brent intraday | ICE/licensed-distributor decision pending | explicit ICE Brent contract | Not activated |
| USO | retain existing cross-asset ETF proxy | ETF security | Already separate; never canonical crude |

## 6. Provider-neutral adapter boundary

Any future adapter should normalize through the existing bounded
`ProviderAdapter` / `AdapterPage` contract.

Provider-specific payload fields stop at the adapter. The accepted commodity
record retains only source-neutral identity plus provenance.

A futures adapter must obtain or validate explicit contract metadata. It must
not infer a continuous contract from a short symbol such as `CL` or `BRN`.

## 7. Local acceptance

Focused acceptance:

```bash
cd /mnt/c/Users/Y/Projects/codex_work/OrderScope
PYTHONPATH=analysis/app python -m pytest -q \
  analysis/tests/contracts/test_commodity_market.py
```

Regression acceptance:

```bash
PYTHONPATH=analysis/app python -m pytest -q analysis/tests
python -m compileall -q analysis/app

git diff --check
```

Required focused behaviors:

1. WTI Cushing spot materializes as a distinct spot-reference Fact;
2. Brent Europe spot has a separate identity;
3. listed WTI futures require explicit contract identity;
4. listed Brent futures require ICE Futures Europe venue identity;
5. spot and futures fields cannot be collapsed;
6. finite negative crude futures observations remain valid;
7. USO is absent from both the crude benchmark and commodity price-form enums.

## 8. UWBS-080 acceptance boundary

UWBS-080 may be marked locally accepted when:

- focused commodity-contract tests pass;
- full Python regression passes;
- compileall passes;
- diff check is clean;
- provider survey remains explicit about spot-vs-futures identity;
- no live provider or remote runtime mutation occurred.

The unresolved Brent intraday provider is not a blocker to the v0.1 contract.
It is a source/terms selection gate before live intraday Brent acquisition.

## 9. Next CP

After local acceptance:

```text
UWBS-080 Accepted
  +-> UWBS-081 structured commodity supply/fundamental acquisition
  +-> UWBS-082 commodity supply/shipping/geopolitical event taxonomy

UWBS-080 + UWBS-081 + UWBS-082
  -> UWBS-083 oil-down-reason / inflation-growth-risk interpretation
```

No Risk-On state is introduced by UWBS-080 itself.

## 10. External references reviewed

- EIA Open Data API Dashboard, Petroleum / Prices / Spot Prices
- EIA Table Definitions, Sources, and Explanatory Notes for Petroleum Spot Prices
- Massive Futures REST API overview and current Futures pricing
- CME Group market-data non-display licensing guidance
- ICE Brent Crude Futures product/expiry pages
- ICE Futures Europe / proprietary-data licensing and authorized-vendor material

External provider conditions are time-sensitive and must be rechecked before
procurement or production activation.
