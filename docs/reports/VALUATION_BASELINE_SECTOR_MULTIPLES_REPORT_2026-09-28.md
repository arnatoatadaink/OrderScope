# Valuation Baseline / Sector Multiples Research Report

- Date: 2026-09-28
- Project: OrderScope
- Status: Research proposal / WBS-CP unreflected
- Primary market: United States
- Secondary market: Japan

## 1. Purpose

OrderScope currently observes price, volume, market regime, catalysts, filings, news, and cross-market factors. This proposal adds a valuation baseline so that price movement can be interpreted relative to a company's normal valuation, its sector, and the overall market.

The objective is not to produce one deterministic fair value. The objective is to estimate a valuation band and separate price movement into market, sector, valuation, earnings, catalyst, and residual components.

Conceptual decomposition:

`Return = Market + Sector + Valuation + Earnings + Catalyst + Residual`

This should improve catalyst interpretation and price-rediscovery analysis by answering not only whether a stock moved, but whether the move was large or small relative to the valuation change implied by the event.

## 2. Core design principle

Do not use a universal rule such as `PBR < 1 = cheap` or `PER < 15 = cheap`. Appropriate multiples differ materially by industry, profitability, growth, leverage, accounting structure, and macro regime.

Use a hierarchy:

`Market -> Sector -> Industry/Sub-industry -> Company`

For OrderScope, the United States is the primary implementation target. Japanese equities should use the same normalized internal schema, but their source adapters can differ.

## 3. Metrics

Minimum baseline metrics:

- P/B (PBR)
- trailing P/E (PER)
- forward P/E
- EV/EBITDA
- EV/Sales or P/S
- ROE
- ROIC
- dividend yield where relevant
- revenue growth
- EPS growth
- FCF margin where relevant

Derived metrics:

- `relative_pbr = company_pbr / sector_pbr`
- `relative_per = company_per / sector_per`
- company historical premium/discount versus sector
- sector premium/discount versus market
- 1Y / 3Y / 5Y valuation percentile or Z-score

The relation `PBR ≈ PER × ROE` is useful as an identity-level consistency check when definitions and periods are aligned, but should not be treated as a valuation model by itself.

## 4. Metric priority by business type

| Business type | Primary | Secondary | Key conditioning variables |
|---|---|---|---|
| Banks | P/B | P/E | ROE, NIM, rates, credit cost |
| Insurance | P/B | P/E | ROE, investment yield, rates |
| Brokers / investment banks | P/B | P/E | ROE, market activity |
| Semiconductors | Forward P/E | EV/EBITDA | EPS growth, cycle, capex |
| Software / SaaS | EV/Sales | Forward P/E | growth, FCF margin |
| Loss-making growth | EV/Sales | P/S | growth, cash runway, path to profit |
| Autos / cyclicals | P/E | P/B | cycle, FX, margin |
| Materials | EV/EBITDA / P/B | P/E | commodity prices, utilization |
| Energy | EV/EBITDA | P/B | oil/gas prices, reserve economics |
| REIT / real estate | NAV multiple | P/B | rates, NAV, LTV |
| Utilities | P/E | EV/EBITDA | rates, regulation, yield |
| Consumer / brands | P/E | P/B | margin, pricing power, growth |
| Biotech | EV/Cash or pipeline-adjusted measures | P/S where applicable | pipeline, runway, trial events |

Therefore the schema should include `sector_primary_valuation_metric` rather than treating P/B as the universal primary metric.

## 5. Baseline representation

A baseline should be a distribution/time series, not one fixed number.

Recommended fields:

```text
market
sector
industry
as_of_date
metric
current
median_1y
median_3y
median_5y
median_10y_optional
percentile_1y
percentile_3y
percentile_5y
zscore_1y
zscore_3y
zscore_5y
source
methodology
```

For individual companies, additionally retain the historical premium/discount to the corresponding sector/industry baseline.

## 6. United States: primary implementation

### 6.1 Sector model

Start from a stable US sector/industry taxonomy and map each OrderScope ticker to sector and industry. The analysis should be performed primarily on US equities because OrderScope's monitored universe is US-centered.

The initial implementation should support at least:

1. market baseline;
2. sector baseline;
3. industry baseline where the sector is too heterogeneous;
4. company historical baseline;
5. relative valuation versus sector/industry.

Financials are a clear example where industry subdivision is necessary: money-center banks, regional banks, insurers, brokers and asset managers should not share one P/B baseline.

### 6.2 US information sources

**Primary / authoritative fundamentals**

- SEC EDGAR submissions and XBRL Company Facts API.
- Use for company-reported assets, equity, revenue, net income, EPS and other filing-derived fundamentals.
- This is the preferred authoritative source for raw issuer fundamentals, but valuation ratios must be calculated by combining filing data with market-price/share-count data and by normalizing accounting periods.

Official source:
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces

**Sector/industry valuation research baseline**

- NYU Stern / Aswath Damodaran industry datasets.
- Useful fields include Price/Book, ROE, ROIC, trailing/forward P/E and other industry valuation/profitability measures.
- Best used as an external research/reference baseline and validation source rather than the only production source.

Sources:
- https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/pbvdata.html
- https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/pedata.html

**Market price / bars**

- Continue to use OrderScope's market-data provider architecture (currently Alpaca first, with Tiingo/Massive candidates according to the existing design) for price-derived valuation snapshots where licensing/coverage permits.

### 6.3 US production recommendation

For reproducibility, OrderScope should ultimately calculate its own company multiples from normalized fundamentals plus observed market data, then aggregate them into internal sector/industry distributions. Damodaran data can bootstrap the taxonomy, sanity-check expected ranges, and validate aggregate outputs.

This avoids making the model dependent on a third-party precomputed P/E or P/B whose denominator methodology may differ.

## 7. Japan: secondary implementation

### 7.1 Japanese market baseline

JPX publishes monthly P/E and P/B statistics by market section, size and 33 industries. This is a strong authoritative source for Japanese sector-level validation and historical baseline construction.

Official source:
- https://www.jpx.co.jp/markets/statistics-equities/misc/04.html

JPX's published sector statistics should be retained with their stated methodology and should not be assumed to be definition-identical to US datasets.

### 7.2 Company fundamentals

For individual Japanese companies, production implementation will require a company-fundamentals source suitable for broad TSE coverage. Candidate architecture should separate:

- exchange/market aggregate statistics;
- issuer financial statements;
- market prices;
- derived valuation metrics.

J-Quants is a natural candidate for Japanese listed-company financial/market data, subject to plan coverage, licensing and required history. EDINET can serve as an authoritative filing source where direct filing extraction is needed.

Sources:
- https://jpx-jquants.com/
- https://disclosure2.edinet-fsa.go.jp/

The exact production provider combination remains an implementation decision and should be benchmarked before CP assignment.

## 8. Cross-market normalization

US and Japan data must not be merged by assuming identical definitions. Each stored observation should include at least:

- source;
- accounting period;
- trailing vs forward designation;
- weighted/aggregate methodology;
- currency where applicable;
- market-cap timestamp;
- sector taxonomy/version;
- treatment of negative earnings/equity;
- data freshness.

Internal normalized names can be common while preserving source methodology metadata.

## 9. Catalyst interpretation

For each material catalyst, capture valuation before and after the event.

Example flow:

`Catalyst -> earnings/BPS/growth expectation change -> justified multiple change -> valuation band change -> actual price response`

Then classify the response conceptually as:

- underreaction;
- normal/within expected valuation repricing;
- overreaction;
- unresolved because fundamentals have not yet updated.

The first implementation should not automatically assert a causal decomposition. `Market`, `Sector`, `Valuation`, `Earnings`, `Catalyst`, and `Residual` are model components/hypotheses whose estimation methodology must be validated.

## 10. Proposed internal model

```text
VALUATION_BASELINE
├─ Market baseline
│  ├─ P/E
│  ├─ P/B
│  ├─ EV/EBITDA
│  └─ Yield
├─ Sector / Industry baseline
│  ├─ P/E
│  ├─ Forward P/E
│  ├─ P/B
│  ├─ EV/EBITDA
│  ├─ EV/Sales
│  ├─ ROE
│  └─ ROIC
├─ Company baseline
│  ├─ historical multiples
│  ├─ profitability/growth
│  └─ historical sector premium/discount
└─ Relative valuation
   ├─ company / industry
   ├─ company / sector
   ├─ sector / market
   ├─ percentile
   └─ Z-score
```

## 11. Proposed valuation outputs

Do not output a single deterministic fair price initially. Prefer a band:

- low valuation reference;
- base valuation reference;
- high valuation reference.

Candidate calculation families:

- BPS × justified/normal P/B;
- EPS × justified/normal forward P/E;
- EBITDA × EV/EBITDA with net-debt adjustment;
- sales × EV/Sales for appropriate growth companies;
- NAV-based approaches for REIT/asset-heavy cases.

Multiple models can coexist, with sector-specific priority and confidence metadata.

## 12. Relationship to existing OrderScope work

This proposal complements rather than replaces:

- minute-bar price/volume monitoring;
- Regime detection;
- EDGAR/filing monitoring;
- news/catalyst detection;
- cross-market/macroeconomic observation;
- price-rediscovery studies.

A catalyst can therefore be evaluated on two axes:

1. observed price/volume response;
2. change in valuation relative to market, sector, industry and the company's own history.

## 13. WBS/CP status

**Not yet reflected in formal WBS/CP.**

Provisional backlog key: `UWBS-VALUATION-001`.

Suggested future decomposition, not yet assigned as formal CPs:

- US sector/industry taxonomy and ticker mapping;
- US raw fundamentals source benchmark;
- valuation normalization rules;
- historical sector/industry baseline builder;
- company-relative valuation model;
- catalyst pre/post valuation snapshot;
- valuation-band output and confidence model;
- Japanese adapter / JPX validation path;
- backtest against known price-rediscovery events.

## 14. Open questions before formal planning

- Which US sector taxonomy becomes canonical (and whether to license/use an external taxonomy or maintain an internal mapping)?
- What exact provider supplies historical shares outstanding and point-in-time fundamentals for backtests?
- How should negative EPS, negative book value, financial companies and extreme outliers be aggregated?
- Which aggregation method becomes canonical: median, market-cap weighted, harmonic mean, trimmed mean, or multiple views?
- How much history is required initially: 1Y/3Y/5Y versus 10Y?
- Should fair-value outputs be restricted to Low/Base/High bands until backtesting establishes calibration?

## 15. Recommendation

Prioritize the US implementation. Build a reproducible internal sector/industry valuation baseline from point-in-time fundamentals and market data, with SEC filings as the authoritative raw-fundamental anchor and Damodaran industry data as a research/validation reference. Implement Japan later through the same normalized schema, using JPX sector statistics for authoritative aggregate validation and a Japan-specific fundamentals adapter.
