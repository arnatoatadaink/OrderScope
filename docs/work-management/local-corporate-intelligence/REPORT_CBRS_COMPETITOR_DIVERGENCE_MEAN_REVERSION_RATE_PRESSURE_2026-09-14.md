# OrderScope — CBRS Competitor Divergence / Mean Reversion / Rate Pressure Case

Status: design report — WBS/CP not yet incorporated
Date: 2026-09-14
Reference validation: A0-002 CBRS 2026-09-01..2026-09-04

## 1. Purpose

Record the design implications identified from the CBRS validation case without silently changing the existing A0-001/A0-002 WBS completion conditions.

The case suggests that a high-growth AI company may move opposite an otherwise positive AI/semiconductor theme when it is positioned as a competitor/substitute to the current theme leader. It also suggests that company-positive information can remain latent while macro/rate pressure dominates price formation, then contribute to an overshooting mean-reversion move after that pressure weakens.

This report is not a trading recommendation and does not promote causal interpretation to Fact.

## 2. Observed A0-002 measurements

The accepted local validation run produced:

- CBRS return: +21.6025%
- NVDA return: +5.8393%
- QQQ return: +1.6180%
- SOXX return: +3.9084%
- BTC return: +2.9351%
- CBRS relative return vs QQQ: +19.9844 percentage points
- CBRS primary/baseline volume ratio: 1.510294x
- QQQ primary/baseline volume ratio: 1.217586x
- CBRS relative volume ratio: 1.240400x
- UST10Y change: -0.010 percentage point over the selected primary endpoints
- JGB10Y change: -0.077 percentage point
- USDJPY return: -2.3064%

The deterministic A0-002 ratings were:

- H1 Global Macro Relief: SUPPORT
- H2 AI Theme Flow: SUPPORT
- H3 CBRS-specific Repricing: SUPPORT
- H4 Short Covering: UNKNOWN
- H5 Japan → US Capital Rotation: CONTRADICT

These ratings are directional validation outputs. They do not themselves establish the causal reason for CBRS repricing.

## 3. Refined interpretation

The current H2/H3 labels are too coarse to describe the CBRS case alone.

A more useful decomposition is:

1. AI theme strength existed, led by NVDA and the semiconductor complex.
2. CBRS can be a competitor/substitute to the theme leader rather than a simple same-direction theme constituent.
3. Therefore leader strength can coexist with competitor relative weakness.
4. A broad-market/rate-pressure episode can extend that weakness beyond what company-specific information alone would imply.
5. A positive company catalyst can remain latent while macro selling dominates.
6. When macro pressure weakens, relative overshoot can unwind quickly.
7. The unwind can overshoot above the eventual local equilibrium before settling.

This is different from a simple catalyst-price-discovery case where a new company Fact immediately creates a higher equilibrium range.

## 4. Fact / Derived Metric / Interpretation boundary

### Fact

Eligible source-grounded Facts include:

- company announcement / filing / official event;
- NVDA earnings release and other source-grounded competitor events;
- observed prices, volumes, yields and FX values;
- observed publication/availability timestamps.

### Derived Metric

Candidate derived metrics include:

- target return vs market proxy;
- target return vs leader/competitor proxy;
- target return vs sector proxy;
- target volume ratio vs own baseline;
- target volume ratio vs market/sector baseline;
- pre-catalyst drawdown;
- post-catalyst rebound magnitude;
- leader-versus-competitor divergence;
- rate-pressure window return differential;
- catalyst-to-price delay.

### Interpretation

Candidate Interpretations include:

- `COMPETITOR_DIVERGENCE`
- `RELATIVE_OVERSHOOT`
- `RELATIVE_MEAN_REVERSION`
- `LATENT_POSITIVE_CATALYST`
- `MACRO_PRESSURE_DOMINANT`
- `REPRICING_OVERSHOOT`
- `LOCAL_EQUILIBRIUM_CANDIDATE`

No one metric should convert these into Fact.

## 5. Rate-pressure design implication

Institutional timing should not be modeled as a single claim that institutions "wait for the exact bottom". A reusable system interpretation should instead test whether macro/rate pressure is suppressing high-duration growth equities even when company evidence is neutral or positive.

Candidate rate-pressure context should include, where available:

- U.S. 2Y and 10Y yield level/change;
- yield change velocity and intraday shock where the source permits it;
- Fed policy-expectation proxy;
- broad U.S. market response;
- high-duration / semiconductor / AI proxy relative response;
- target-company relative response.

The system may infer `MACRO_PRESSURE_DOMINANT` only as an Interpretation supported by multiple independent observations. It must not infer institutional buyer identity or exact capital movement from price/yield behavior alone.

## 6. Relationship to existing A0-002

Keep existing A0-002 H1..H5 unchanged until WBS/CP formally adopts an extension.

Use this case as an auxiliary validation layer:

- H2 remains evidence that the AI/semiconductor theme was strong.
- H3 remains evidence that CBRS materially outperformed the broad market during the selected rebound window.
- New auxiliary tests should determine whether H3 is better described as new information repricing, competitor-divergence normalization, relative mean reversion, or a mixture.
- H4 remains UNKNOWN until reviewed short/borrow data is available.
- H5 remains CONTRADICT for the simple Japan→US new-capital-flow story because USDJPY fell in the selected window.

## 7. Design tasks to capture before WBS/CP incorporation

1. Define leader/competitor relationship context separate from ordinary sector membership.
2. Add relative drawdown / recovery metrics against market, sector and leader proxies.
3. Define latent-catalyst state when company-positive evidence exists but market/macro pressure prevents immediate repricing.
4. Define rate-pressure dominance as an Interpretation using multiple market/macro inputs.
5. Add a mean-reversion / repricing-overshoot state machine distinct from persistent price discovery.
6. Add CBRS as a Canary fixture covering competitor divergence, broad selloff, latent positive catalyst, rebound overshoot and later local-equilibrium formation.

## 8. Non-goals

- Do not infer institutional buyer identity from volume alone.
- Do not treat an index or ETF flow as proof of deliberate bottom-fishing.
- Do not encode a fixed yield threshold or exact buy level from this single case.
- Do not equate a temporary rebound peak with intrinsic fair value.
- Do not classify short covering without reviewed short/borrow evidence.
