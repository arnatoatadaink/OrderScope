# OrderScope — News Provider Comparison Refresh (N0-001)

Status: Web research complete; adoption decision recorded
Date: 2026-09-09
Task: `N0-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Dependency: `W0-004`

## 1. Purpose

Refresh the current provider comparison before implementing the News metadata adapter. The WBS requires current official checks for price, history, rate limits, body access/rights, internal-use terms, and credentials. Point-in-time values in older provider research are not authoritative for implementation.

This report compares the three providers already relevant to the project: Alpaca, Tiingo, and Massive (formerly Polygon.io).

## 2. Decision summary

For the v0.1 AMD/NVDA local Canary:

- **Primary provider candidate: Alpaca News API**, but only for the current local personal/non-commercial use boundary and subject to runtime entitlement verification.
- **Secondary comparison / recall candidate: Tiingo News API**, especially for metadata-level coverage comparison and a future explicit commercial-internal-use path.
- **Massive News API: not adopted for v0.1 News ingestion**. It remains a later market-data/provider option, but the current individual Market Data license is too restrictive for derived/non-display/business use without a separate license.

The primary reason to prefer Alpaca for v0.1 News is not price alone. N0-004 requires temporary body access for extraction. Alpaca's current News API exposes historical and streaming news with article content when available, while Tiingo's public product description fixes metadata/description fields but does not establish a full-article body contract suitable for N0-004.

## 3. Current official comparison

| Dimension | Alpaca News | Tiingo News | Massive News |
|---|---|---|---|
| Current public pricing relevant to individual use | News is part of Alpaca Market Data surface; current stock Market Data Basic is free and Algo Trader Plus is $99/month. No separate current public News surcharge was established in this refresh. | Power individual $30/month; commercial internal-use $50/month. | Stocks Basic $0, Starter $29, Developer $79, Advanced $199 monthly for individual stock-data plans. |
| News history | Historical News documents data back to 2015. | Non-institutional News: 3 months queryable history plus ongoing data. Institutional/enterprise history extends much further by contract. | News records documented back to 2016-06-22. Basic exposes 2 years; paid Stocks plans expose all News history. |
| Incremental / real-time | Historical REST plus real-time News WebSocket. | REST, real-time updates; product page also describes bulk delivery for enterprise. | REST News endpoint; current plan table says News updates hourly. |
| News-specific bounded query | Start/end, symbols, sorting, page token, 1-50 results/page. | REST News query with ticker/tag/date controls per documentation. | ticker + published_utc filtering, sort/order, max 1000 results/page. |
| Body/content availability | Historical endpoint supports `include_content`; stream schema includes `content`, summary, headline, URL, timestamps. Content may be unavailable for some articles. | Public product fields explicitly include title, URL, source, description, tags, tickers, published/crawl dates. Full body access is not established by the public v0.1 comparison. | Public News endpoint is treated as metadata/news data; this refresh does not establish a licensed temporary full-body extraction right. |
| Rate limit | Current News pages expose 429/limit handling but do not publish a separate fixed News RPM in the page used here. Older launch material tied News to Market Data plan rates. Runtime adapter must read rate-limit headers and probe entitlement rather than hard-code an old beta number. | Power: 10,000 requests/hour, 100,000/day, 40 GB/month. Commercial: 20,000/hour, 150,000/day, 100 GB/month. | Basic plan: 5 API calls/minute. Paid Stocks pricing advertises unlimited API calls; adapter still must handle 429/server limits. |
| Internal-use / redistribution boundary | Alpaca Terms grant ordinary Service/Content use for personal, non-commercial purposes unless another agreement applies. Third-party content is included. Do not redistribute News/body or promote this v0.1 decision to commercial use without rechecking the applicable agreement. | Pricing explicitly labels individual and commercial plans as Internal Use Only and defines internal use as not displaying/sharing the data with another person or organization. Redistribution requires a separate offering. | Individual Market Data terms allow personal/non-business/non-commercial use and restrict redistribution, business/commercial use, non-display use, and derivative works absent license/consent. |
| Credentials | Alpaca Market Data API key/secret. | Tiingo API token. | Massive API key. |

## 4. Alpaca findings

Current Alpaca documentation states:

- Historical News is available back to 2015 and is currently supplied by Benzinga.
- The News REST endpoint supports symbols, start/end bounds, sorting, pagination token, and `include_content`.
- The real-time News WebSocket schema includes article ID, headline, summary, author, created/updated timestamps, content, URL, and symbols.
- Alpaca's current Market Data Basic/Algo Trader Plus pricing is Free / $99 monthly for equities Market Data, with 200/min vs 10,000/min historical stock calls; this refresh does **not** assume those stock-call rates are a guaranteed News-specific rate.
- Alpaca's general Terms describe Service Content, including news and third-party content, and establish a personal/non-commercial default use boundary unless another agreement applies.

### Consequence for N0-002/N0-004

The adapter may implement Alpaca as a provider-specific News candidate because it satisfies both metadata and temporary-body capability. However:

1. rate limits are configuration/runtime observations, not hard-coded from the 2022 News beta launch article;
2. `include_content=false` is sufficient for N0-002 metadata acquisition;
3. N0-004 may request content only through the temporary-content boundary;
4. no raw body is durable Fact Store metadata;
5. a move to business/commercial/redistributed use requires a new terms review and ADR revision.

## 5. Tiingo findings

Tiingo's current pricing/product pages are unusually explicit:

- Power individual: $30/month or $300/year.
- Internal commercial use: $50/month or $499/year on the general pricing page; the News product page also lists Commercial $50/month.
- Power rate: 10,000/hour, 100,000/day, 40 GB/month.
- Commercial rate: 20,000/hour, 150,000/day, 100 GB/month.
- Non-institutional News: 3 months queryable history plus ongoing real-time data.
- Public News fields list title, URL, source, description, tags, asset tickers, date published, and crawl date.
- License is Internal Use Only; redistribution/history expansion is separately contracted.

### Consequence

Tiingo is a strong metadata/recall comparator and a plausible future commercial-internal-use provider. It is **not selected as the sole v0.1 provider** because the public contract examined here does not establish full-article body availability needed by N0-004.

## 6. Massive findings

Massive currently documents:

- News access in all Stocks plans.
- Basic: free, 5 API calls/minute, 2 years News history.
- Starter $29/month and above: all documented News history, with News records dating to 2016-06-22.
- News recency currently listed as updated hourly.
- Individual Market Data Terms are personal/non-business/non-commercial and restrict redistribution, commercial/business use, non-display use, and derived works without additional licensing.

### Consequence

Massive is not adopted for N0-002. Its current News cadence is less attractive than Alpaca/Tiingo for breaking-news discovery, and its individual license requires extra care for the intended derived-analysis path. Reconsider only with a business/non-display license or if empirical News recall shows a material advantage.

## 7. Provider-neutral contract requirements for N0-002

The adoption decision must not leak provider schemas into Core. N0-002 should normalize at minimum:

- provider/source identity
- stable provider article ID when supplied
- headline/title
- publisher/source name
- canonical article URL as supplied
- published/created timestamp with source precision
- provider updated timestamp when supplied
- retrieved/available/accepted timestamps
- symbols/tags as provider observations, not Corporate identity truth
- page/cursor/checkpoint state
- sanitized partial/error status
- a provider capability flag for temporary body retrieval; body itself is excluded

Do not infer company identity solely from provider ticker tags. Canonical URL and duplicate/update logic remain N0-003.

## 8. Rate-limit and entitlement policy

N0-002 must not encode a single permanent numeric rate for Alpaca News. The adapter should:

- expose configured conservative request budgets;
- persist 429/retryable status through the accepted common adapter contract;
- honor returned rate-limit headers when available;
- provide a local entitlement smoke fixture/probe before real Canary acquisition;
- keep rates/provider plan outside Fact records.

Tiingo's published plan limits may be used as configuration defaults only for the selected account tier and still remain revisitable external configuration.

## 9. Body-right / retention guardrail

The existing `ADR_TEMPORARY_CONTENT_LIFECYCLE_v0.1` remains authoritative:

- body access is temporary and extraction-only;
- successful bodies are deleted after extraction;
- exception bodies expire within 30 days;
- durable records retain metadata, source reference, hashes, Facts/Evidence, and deletion proof, not provider body text.

This ADR does not grant rights beyond the provider agreement. If a provider/account does not permit body use for the intended operation, N0-004 must disable that capability rather than bypass the contract via direct article scraping.

## 10. Revisit triggers

Re-run N0-001 before any of the following:

- commercial/business operation, redistribution, shared UI, or external API exposure;
- provider price/plan or terms change;
- replacing Alpaca with Tiingo/Massive as primary;
- storing News bodies beyond the accepted temporary lifecycle;
- adding a news source whose body rights are not explicitly known;
- empirical N1-006 recall shows the primary provider misses material AMD/NVDA events.

## 11. Sources checked on 2026-09-09

Official/current pages used for this refresh include:

- Alpaca Historical News Data: `https://docs.alpaca.markets/us/docs/historical-news-data`
- Alpaca News REST reference: `https://docs.alpaca.markets/us/reference/news-3`
- Alpaca real-time News: `https://docs.alpaca.markets/us/docs/streaming-real-time-news`
- Alpaca Market Data plan description: `https://docs.alpaca.markets/us/docs/about-market-data-api`
- Alpaca Terms and Conditions: `https://files.alpaca.markets/disclosures/alpaca_terms_and_conditions.pdf`
- Tiingo News product: `https://www.tiingo.com/products/news-api`
- Tiingo pricing: `https://www.tiingo.com/about/pricing`
- Tiingo Terms: `https://api.tiingo.com/tos/`
- Massive News reference: `https://massive.com/docs/rest/stocks/news`
- Massive pricing: `https://massive.com/pricing`
- Massive Market Data Terms: `https://massive.com/legal/market-data-terms-of-service`
