# OrderScope — WBS-Unreflected CBRS / A0 Extension

Status: **Incorporated into formal A0 WBS/CP on 2026-09-15 — retained as provenance**
Date: 2026-09-14
Parent backlog: `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
Source report: `REPORT_CBRS_COMPETITOR_DIVERGENCE_MEAN_REVERSION_RATE_PRESSURE_2026-09-14.md`
Formal WBS: `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Critical Path: `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`

This file preserves the original unreflected proposal and acceptance provenance. The 2026-09-15 planning revision incorporated the rows below without changing the accepted local evidence or inventing threshold calibration.

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Dependencies | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-027 | Define leader/competitor divergence context | A0 / Cross-Market | Represent leader, competitor, substitute and ordinary sector-peer relationships separately; preserve source/effective history; allow leader strength and competitor weakness to coexist without treating both as one-direction theme flow | A0-001/002; I0 relationship/history boundary | Incorporated | `A0-008`; local implementation accepted 2026-09-14; combined 9 focused / 604 full Python pass |
| UWBS-028 | Implement relative overshoot / mean-reversion metrics | A0 Derived Metrics | Compute target drawdown/recovery versus market, sector and leader proxies; include relative volume participation and bounded pre/post catalyst windows; preserve as-of semantics and avoid causal labeling in the metric itself | UWBS-027; A0-002 aligned timeline; market bars | Incorporated | `A0-009`; local implementation accepted 2026-09-14; combined 9 focused / 604 full Python pass |
| UWBS-029 | Define latent catalyst / macro-pressure dominance Interpretation | A0 Interpretation / Market Reaction | Support `LATENT_POSITIVE_CATALYST` and `MACRO_PRESSURE_DOMINANT` only when positive company evidence coexists with broader rate/macro pressure; require multiple independent inputs; prohibit institutional-buyer identity or capital-flow claims from price/volume alone | UWBS-011..015 macro design; UWBS-020/021 market-reaction design; UWBS-028 | Incorporated | `A0-010`; local contract accepted 2026-09-14; combined 15 focused / 619 full Python pass; numeric/provider-specific thresholds remain deferred |
| UWBS-030 | Extend repricing state machine for mean-reversion overshoot | Market Reaction / Regime | Distinguish `RELATIVE_OVERSHOOT`, `RELATIVE_MEAN_REVERSION`, `REPRICING_OVERSHOOT`, and `LOCAL_EQUILIBRIUM_CANDIDATE` from persistent catalyst-driven price discovery; no fixed percentage/session threshold from the CBRS case alone | UWBS-020/021; UWBS-028/029 | Incorporated | `A0-011`; local state contract accepted 2026-09-14; combined 15 focused / 619 full Python pass; historical threshold calibration remains deferred |
| UWBS-031 | Add CBRS competitor-divergence Canary fixture | A0 QA / Market Reaction QA | Reproduce NVDA-led theme strength, competitor divergence, broad/rate-pressure selloff, positive company catalyst, rebound with relative volume expansion, overshoot and later stabilization; include false-positive cases | A0-002; UWBS-027..030 | Incorporated | `A0-012`; local Canary accepted 2026-09-14; focused 3 passed; full Python 622 passed |

## Planning notes

- These rows extend rather than rewrite A0-002. Existing H1..H5 historical results remain intact.
- `AI Theme Flow` and `CBRS-specific Repricing` may both be supported while the causal interpretation is competitor-divergence normalization rather than simple same-direction theme buying.
- Historical Analyst Consensus must not be reconstructed from current free-site values. If an as-of historical consensus source is unavailable, the validation result remains explicitly `UNKNOWN` rather than guessed.
- This extension does not create a trading signal, authorize provider activation, or establish fixed buy/sell thresholds.

## Incorporation mapping — 2026-09-15

| UWBS ID | Final WBS ID |
|---|---|
| UWBS-027 | A0-008 |
| UWBS-028 | A0-009 |
| UWBS-029 | A0-010 |
| UWBS-030 | A0-011 |
| UWBS-031 | A0-012 |

## Discovery trace

| Discovery ID | Date | Proposal | Source | Triage state |
|---|---|---|---|---|
| DISC-007 | 2026-09-14 | Model CBRS-like competitor divergence, latent positive catalyst under macro pressure, relative mean reversion and repricing overshoot | `REPORT_CBRS_COMPETITOR_DIVERGENCE_MEAN_REVERSION_RATE_PRESSURE_2026-09-14.md` | Promoted to UWBS-027..031; incorporated as A0-008..012 on 2026-09-15 |
