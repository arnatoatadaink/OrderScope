# A0-002 — CBRS Multi-Layer Flow Validation

Status: **Provisional validation complete**
Date: 2026-09-14
Window: baseline 2026-08-26..2026-08-31; primary 2026-09-01..2026-09-04
Rule: `a0-002-directional-rules-v0.1`

## Completed

- A0-001 cross-market contradiction contract accepted locally.
- 12/12 required A0-002 series present.
- 94 observations merged: 74 Alpaca + 20 official macro.
- Relative return, relative volume, UST10Y, JGB10Y, USDJPY and BTC metrics calculated.
- H1..H5 rated without promoting capital movement or short covering to Fact.

## Derived Metrics

| Metric | Value |
|---|---:|
| CBRS return | +21.6025% |
| NVDA return | +5.8393% |
| QQQ return | +1.6180% |
| SOXX return | +3.9084% |
| BTC return | +2.9351% |
| CBRS relative return vs QQQ | +19.9844 pp |
| SOXX relative return vs QQQ | +2.2903 pp |
| CBRS volume ratio | 1.510294x |
| QQQ volume ratio | 1.217586x |
| CBRS relative volume ratio | 1.240400x |
| UST10Y change | -0.0100 pp |
| JGB10Y change | -0.0770 pp |
| USDJPY return | -2.3064% |

## Hypothesis Results

| Hypothesis | Rating | Rationale |
|---|---|---|
| H1 Global Macro Relief | SUPPORT | U.S. market rose while UST10Y did not rise |
| H2 AI Theme Flow | SUPPORT | SOXX and NVDA both outperformed QQQ |
| H3 CBRS-specific Repricing | SUPPORT | CBRS outperformed QQQ with relative volume expansion |
| H4 Short Covering | UNKNOWN | No reviewed CBRS short/borrow series is available |
| H5 Japan → US Capital Rotation | CONTRADICT | USDJPY fell, opposite the simple JPY-sale / USD-buy direction |

## Fact / Derived Metric / Interpretation boundary

Facts / observations are the acquired market and macro series themselves. The return, relative-return, volume-ratio, yield-change and FX-return values are Derived Metrics. H1..H5 are Interpretations.

The results support a layered explanation: broad macro relief and AI/semiconductor strength were present, while CBRS also showed substantial company-specific relative strength and volume expansion. The simple Japan→US rotation explanation is contradicted by USDJPY direction in this window. H4 remains unknown rather than being inferred from price/volume alone.

## Remaining A0-002 item

The WBS completion condition includes consensus-gap evaluation. `CBRS:CONSENSUS_TARGET` remains `provider_unresolved`, so a historical as-of consensus gap has not yet been calculated. A0-002 therefore remains Provisional rather than Accepted.

Next action: identify a historical as-of analyst-consensus source for the validation window, or explicitly revise the A0-002 acceptance rule if consensus is unavailable within v0.1 scope.
