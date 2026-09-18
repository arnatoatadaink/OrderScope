# OrderScope — A0-002 CBRS Multi-Layer Flow Validation Acceptance

Status: Accepted locally
Date: 2026-09-14
Task: A0-002

## Acceptance evidence

Local focused Cross-Market suite: 22 passed.

Real bounded validation artifacts:

- Alpaca observations: 74
- Official macro observations: 20
- Combined observations: 94
- Required source series: 12/12

Primary validation window: 2026-09-01..2026-09-04.
Baseline window: 2026-08-26..2026-08-31.

## Derived metrics

- CBRS return: 0.216025
- NVDA return: 0.058393
- U.S. market proxy return: 0.016180
- semiconductor proxy return: 0.039084
- BTC return: 0.029351
- CBRS relative return: 0.199844
- semiconductor relative return: 0.022903
- CBRS volume ratio: 1.510294
- market volume ratio: 1.217586
- CBRS relative volume ratio: 1.240400
- UST10Y change: -0.010000 percentage point
- JGB10Y change: -0.077000 percentage point
- USDJPY return: -0.023064

## Hypothesis ratings

- H1 Global Macro Relief: SUPPORT
- H2 AI Theme Flow: SUPPORT
- H3 CBRS-specific Repricing: SUPPORT
- H4 Short Covering: UNKNOWN
- H5 Japan → US Capital Rotation: CONTRADICT

## Consensus-gap disposition

A0-002 requires the consensus gap to be evaluated, but the WBS also prohibits reconstructing historical Consensus from current values on free aggregation sites.

No reviewed historical as-of CBRS Analyst Consensus series is currently available in the accepted source manifest. Therefore the A0-002 consensus-gap result is:

`UNKNOWN — historical as-of consensus source unavailable`

This is an explicit evaluation outcome, not a guessed or backfilled value. It does not block A0-002 local acceptance. If a reviewed historical as-of source is adopted later, the validation may be revised with a numeric consensus gap while preserving this accepted record.

## Interpretation boundary

The deterministic H2/H3 ratings are retained. The later CBRS case review identified additional causal interpretations — competitor divergence, relative overshoot, latent positive catalyst, macro-pressure dominance and mean reversion — that exceed the current A0-002 completion condition. Those extensions are tracked separately as WBS-unreflected design work and do not rewrite this acceptance result.

H4 remains UNKNOWN because price/volume behavior is not sufficient evidence of short covering.

H5 remains CONTRADICT for the simple Japan→US new-capital-flow hypothesis because USDJPY fell during the selected validation window.

## Boundary

This acceptance is local validation only. It authorizes no live provider activation, Worker/Cron mutation, remote D1 mutation, trading action, or normative trading threshold.
