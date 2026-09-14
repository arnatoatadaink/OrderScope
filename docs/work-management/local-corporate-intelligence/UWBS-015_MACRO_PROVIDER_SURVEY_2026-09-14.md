# OrderScope — UWBS-015 Structured Macro Provider Survey

Status: **Research complete / provider activation not authorized**
Date: 2026-09-14 (JST)
Scope: structured policy-rate, sovereign-yield, FX, volatility/positioning/flow-adjacent sources for UWBS-011..014
Related backlog: `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
Related contracts: `macro_market.py`, `macro_metrics.py`, `macro_stress.py`

## 1. Executive decision

Use **official direct sources as the primary acquisition path** for v0.1 macro Facts, and use **FRED/ALFRED as a revision/history/fallback layer rather than the sole source of truth**.

Recommended source split:

| Data family | Primary source | Secondary/fallback | v0.1 role |
|---|---|---|---|
| U.S. Treasury 2Y/5Y/10Y/30Y | U.S. Treasury Daily Treasury Rates CSV/XML | Federal Reserve H.15 / FRED | Primary raw sovereign-yield Fact |
| U.S. effective overnight policy/short rate | New York Fed EFFR; optionally SOFR/OBFR | FRED | Primary short-market-rate Fact |
| FOMC target range | Federal Reserve Board Open Market Operations history | FRED | Policy-rate Fact / policy event context |
| Japan policy/administered rates and money-market rates | BOJ Time-Series Data Search API | BOJ downloadable files | Primary Japan rate Fact |
| USD/JPY daily official statistical series | BOJ Time-Series Data Search API (`FM08`) | FRED only when the underlying series rights/metadata are acceptable | Primary daily FX context; not intraday market FX |
| JGB 2Y/5Y/10Y/30Y constant-maturity yields | Ministry of Finance JGB interest-rate CSV | BOJ/FRED only if exact series semantics match | Primary JGB sovereign-yield Fact |
| Explicit Japan FX intervention | Ministry of Finance intervention statistics | none required | Event/flow Fact; not generic capital-flow proxy |
| Futures positioning | CFTC Traders in Financial Futures / COT | none required | Weekly positioning Evidence/Derived Metric; not fund flow |
| Broad financial-account flows | BOJ Flow of Funds | — | Structural quarterly context only; not shock-timing evidence |
| High-frequency ETF/fund flow | **No official v0.1 source selected** | commercial source requires separate terms/cost review | Deferred |

The minimum v0.1 path therefore does **not** require a paid macro provider for policy rates, sovereign curves, EFFR, daily statistical USD/JPY, or official intervention facts.

## 2. U.S. Treasury yield curve

### Primary: U.S. Department of the Treasury

Treasury publishes Daily Treasury Par Yield Curve Rates with downloadable CSV and XML feeds. The current table contains the maturities needed by UWBS-012, including 2Y, 5Y, 10Y, 20Y, and 30Y. Treasury also provides archived daily par-yield data back to 1990.

Developer documentation states that the XML feed remains available for API consumers, supports pagination for all-history retrieval, and provides explicit feed URLs. No API key requirement or fixed public request-per-minute limit was found in the reviewed Treasury documentation.

Important semantic boundary:

- store the Treasury published **par yield curve** as the source series;
- do not silently substitute a different constant-maturity or market-price series under the same `series_id`;
- retain source date and acquisition/availability time separately.

Sources:
- https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve
- https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rate-archives
- https://home.treasury.gov/developer-notice-xml-changes

### Fallback: Federal Reserve H.15 / FRED

The Federal Reserve H.15 Data Download Program still exposes Treasury constant-maturity CSV/XML, but the Board announced plans to remove the DDP Build Your Package option in November 2026 in preparation for eventual DDP retirement, explicitly directing users toward FRED or release XML. Therefore OrderScope should not add a new hard dependency on DDP-specific interfaces.

Source:
- https://www.federalreserve.gov/datadownload/Choose.aspx?rel=H15

## 3. U.S. policy / overnight rates

### Primary operational series: New York Fed EFFR

The New York Fed publishes the Effective Federal Funds Rate for the prior business day at approximately 09:00 ET. Historical data and Markets Data APIs are available. EFFR is directly suitable for `SHORT_MARKET_RATE`; the FOMC target range remains a separate policy-rate series.

SOFR/OBFR may be added as additional funding/liquidity context, but they must remain distinct series rather than being merged into one generic U.S. policy rate.

Sources:
- https://www.newyorkfed.org/markets/reference-rates/effr
- https://www.newyorkfed.org/markets/data-hub

### Policy target range: Federal Reserve Board

The Federal Reserve Board publishes the FOMC target federal funds rate/range history. This should be used for policy-state transitions; it is not a substitute for the observed EFFR.

Source:
- https://www.federalreserve.gov/monetarypolicy/openmarket.htm

## 4. FRED / ALFRED role

FRED API v1 provides per-series retrieval in XML, JSON, XLSX, or CSV and requires a registered API key. `series/vintagedates` exposes historical release/revision dates, making ALFRED/FRED especially useful for as-of/revision-aware validation.

However, FRED's API terms explicitly state that individual series can be owned by third parties and retain their own copyright/use restrictions. FRED can also impose or change access limits. Therefore:

- FRED is approved as a **convenience, revision, historical-reconstruction, and fallback adapter**;
- each selected series still needs source-owner/notes review before redistribution or production use;
- do not assume that FRED availability itself grants downstream redistribution rights;
- keep the FRED API key out of persistence/logs.

Sources:
- https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
- https://fred.stlouisfed.org/docs/api/terms_of_use.html

## 5. Japan rates and FX

### BOJ Time-Series Data Search API

The BOJ launched the Time-Series Data Search API on 2026-02-18. It supports JSON/CSV and three primary interfaces: `/getDataCode`, `/getDataLayer`, and `/getMetadata`.

Relevant available statistical families include:

- administered/base lending rate series;
- uncollateralized overnight call rate and other money-market series;
- foreign-exchange-rate database `FM08`, including a daily U.S. dollar/yen spot series;
- Flow of Funds and other structural datasets.

BOJ guidance says time-series data may be revised retroactively. The API notice also states that service may be suspended/degraded, specifications may change, access may be limited according to load, and excessive access is prohibited. No fixed request-per-minute quota was found in the reviewed notice, so OrderScope should implement bounded polling/backoff rather than assuming an unlimited service.

BOJ's general search guidance notes a 60,000-observation output limit for site retrieval; API-specific request sizing should still be bounded independently.

Sources:
- https://www.boj.or.jp/en/statistics/outline/notice_2026/not260218a.htm
- https://www.stat-search.boj.or.jp/info/api_manual_en.pdf
- https://www.stat-search.boj.or.jp/info/api_notice_en.pdf
- https://www.stat-search.boj.or.jp/

### USD/JPY semantic boundary

BOJ `FM08` is suitable for a **daily official statistical FX observation**. It should not be treated as an intraday executable FX quote. Intraday FX shock detection, if later required, remains a separate provider decision.

## 6. JGB yield curve

### Primary: Ministry of Finance JGB interest-rate data

Japan's Ministry of Finance publishes JGB interest-rate information and historical CSV data extending back to 1974. MOF states that the published rate is a semiannual compound constant-maturity rate based on prevailing fixed-income JGB prices at the 15:00 market close and is released at 09:30 on the following business day.

This is well aligned with UWBS-012 because the contract needs explicit tenor identity and stable daily sovereign-curve history.

Implementation rule:

- retain `observed_at` as the underlying market date/close semantics;
- retain publication/availability separately (next-business-day publication);
- do not treat next-day availability as same-day tradable information.

Sources:
- https://www.mof.go.jp/jgbs/reference/interest_rate/index.htm
- https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/qa.htm

## 7. Flow and positioning sources

### MOF FX intervention data

MOF publishes monthly and quarterly/daily-base foreign-exchange intervention statistics, including historical CSV data. This can establish an explicit official intervention Fact when present.

It must **not** be generalized into total JPY carry unwind, total Japan-to-U.S. flow, or total market deleveraging.

Source:
- https://www.mof.go.jp/policy/international_policy/reference/feio/data/index.html

### CFTC Traders in Financial Futures / COT

CFTC publishes weekly Commitments of Traders datasets and a Public Reporting Environment/API. Traders in Financial Futures includes dealer, asset-manager, and leveraged-money long/short/spread positions and weekly changes.

This is useful for delayed/weekly positioning context, particularly a JPY futures positioning proxy, but:

- it is futures positioning, not cash FX fund flow;
- it is weekly and therefore unsuitable as sole evidence for an intraday/daily carry-unwind event;
- leveraged-money categories must not be equated with all hedge funds or all carry traders.

Sources:
- https://publicreporting.cftc.gov/stories/s/User-s-Guide/p2fg-u73y/
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/cotvariablestfm.html

### BOJ Flow of Funds

BOJ Flow of Funds is appropriate for structural balance-sheet/sector-flow context but is too low-frequency for shock timing. It should therefore remain contextual evidence, not the trigger for `CARRY_UNWIND_CANDIDATE`.

## 8. Unresolved high-frequency flow gap

No reviewed official source provides a clean, comprehensive, high-frequency observed series for "JPY-funded carry capital leaving U.S. risk assets" or equivalent aggregate flow.

Therefore v0.1 must continue to model carry unwind as an Interpretation built from independent evidence classes, for example:

1. FX/rate Derived Metrics;
2. broad market stress/volume/breadth metrics;
3. optional CFTC positioning context;
4. explicit source reporting;
5. absence/presence of stronger company-specific negative evidence.

If daily ETF/fund flow is later required, a commercial provider survey should be a separate task with licensing, redistribution, historical-depth, timestamp and cost review. It must not be silently substituted by market-cap change or volume.

## 9. Recommended v0.1 acquisition topology

```text
U.S. Treasury CSV/XML -----------------------> US sovereign-yield Facts
NY Fed Markets Data API ---------------------> EFFR/SOFR Facts
Fed Board policy history --------------------> FOMC target-range Facts/events

MOF JGB CSV ---------------------------------> JP sovereign-yield Facts
BOJ Time-Series API -------------------------> JP policy/short-rate + daily USDJPY Facts
MOF intervention CSV ------------------------> explicit intervention Facts

FRED/ALFRED ---------------------------------> fallback + vintages/revision reconstruction
CFTC TFF/COT --------------------------------> weekly positioning Evidence

                           Facts
                             |
                             v
                       UWBS-012 metrics
                             |
                             v
                       UWBS-013 Interpretation
```

## 10. Provider contract requirements

Any adapter implemented from this survey must record at minimum:

- canonical source/provider identity;
- source series code/name and semantic definition;
- frequency and market/tenor identity;
- observation/event date separately from publication/availability/retrieval/accepted time;
- unit;
- revision policy and, where available, vintage/revision identity;
- bounded request window and retry/backoff policy;
- source terms/attribution notes;
- explicit statement whether the series is Fact, positioning proxy, or Interpretation input.

No adapter should convert FX, COT, market volume, or intervention statistics into inferred total capital movement as a Fact.

## 11. Cost and operational summary

| Source | Direct monetary cost found | Credential | Operational caveat |
|---|---:|---|---|
| U.S. Treasury | none stated | none | XML feed pagination; feed changes have occurred historically |
| NY Fed | none stated | API/public data | holiday/publication-calendar differences matter |
| Fed Board policy pages | none stated | none | DDP-specific interface is being retired; avoid new DDP coupling |
| BOJ API | none stated | no API key described in reviewed manual | load-dependent access limiting; no excessive polling |
| MOF JGB/intervention | none stated | none | JGB data availability is next business day; intervention disclosure is not real-time |
| FRED/ALFRED | none stated | API key required | per-series rights/terms; limits may be imposed |
| CFTC COT/PRE | none stated | public API/download | weekly lag; positioning proxy only |

"None stated" means no usage fee was found in the reviewed official documentation; it is not a warranty that terms or service conditions cannot change.

## 12. UWBS-015 disposition recommendation

UWBS-015 research/decomposition is complete enough for formal WBS design.

Recommended implementation split if incorporated later:

1. `MACRO-PROVIDER-US-001`: Treasury + NY Fed + Fed policy adapters.
2. `MACRO-PROVIDER-JP-001`: MOF JGB + BOJ API adapters.
3. `MACRO-POSITIONING-001`: CFTC TFF optional weekly positioning adapter.
4. `MACRO-REVISION-001`: FRED/ALFRED fallback/vintage adapter.
5. `MACRO-FLOW-COMMERCIAL-001`: deferred commercial high-frequency flow survey only if required by later acceptance criteria.

This report does **not** authorize live-provider activation, credentials, Worker/Cron changes, or remote D1 mutation.