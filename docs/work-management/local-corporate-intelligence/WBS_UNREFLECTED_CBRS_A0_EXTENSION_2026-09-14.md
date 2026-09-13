# OrderScope — WBS-Unreflected CBRS / A0 Extension

Status: Active append-only extension — not yet incorporated into main WBS/CP
Date: 2026-09-14
Parent backlog: `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
Source report: `REPORT_CBRS_COMPETITOR_DIVERGENCE_MEAN_REVERSION_RATE_PRESSURE_2026-09-14.md`

This file extends the unreflected backlog without changing the existing A0-001/A0-002 WBS or Critical Path. IDs continue from the parent backlog, whose latest allocated ID is UWBS-026.

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Dependencies | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-027 | Define leader/competitor divergence context | A0 / Cross-Market | Represent leader, competitor, substitute and ordinary sector-peer relationships separately; preserve source/effective history; allow leader strength and competitor weakness to coexist without treating both as one-direction theme flow | A0-001/002; I0 relationship/history boundary | Ready for WBS design | Local implementation accepted 2026-09-14; included in combined 9 focused / 604 full Python pass; pending WBS incorporation |
| UWBS-028 | Implement relative overshoot / mean-reversion metrics | A0 Derived Metrics | Compute target drawdown/recovery versus market, sector and leader proxies; include relative volume participation and bounded pre/post catalyst windows; preserve as-of semantics and avoid causal labeling in the metric itself | UWBS-027; A0-002 aligned timeline; market bars | Ready for WBS design | Local implementation accepted 2026-09-14; included in combined 9 focused / 604 full Python pass; pending WBS incorporation |
| UWBS-029 | Define latent catalyst / macro-pressure dominance Interpretation | A0 Interpretation / Market Reaction | Support `LATENT_POSITIVE_CATALYST` and `MACRO_PRESSURE_DOMINANT` only when positive company evidence coexists with broader rate/macro pressure; require multiple independent inputs; prohibit institutional-buyer identity or capital-flow claims from price/volume alone | UWBS-011..015 macro design; UWBS-020/021 market-reaction design; UWBS-028 | Needs decomposition | Contract implemented; local acceptance pending |
| UWBS-030 | Extend repricing state machine for mean-reversion overshoot | Market Reaction / Regime | Distinguish `RELATIVE_OVERSHOOT`, `RELATIVE_MEAN_REVERSION`, `REPRICING_OVERSHOOT`, and `LOCAL_EQUILIBRIUM_CANDIDATE` from persistent catalyst-driven price discovery; no fixed percentage/session threshold from the CBRS case alone | UWBS-020/021; UWBS-028/029 | Needs decomposition | Pending |
| UWBS-031 | Add CBRS competitor-divergence Canary fixture | A0 QA / Market Reaction QA | Reproduce NVDA-led theme strength, competitor divergence, broad/rate-pressure selloff, positive company catalyst, rebound with relative volume expansion, overshoot and later stabilization; include false-positive cases | A0-002; UWBS-027..030 | Ready for WBS design | Pending |

## Planning notes

- These rows are not a rewrite of A0-002. Existing H1..H5 remain intact until a WBS/CP revision explicitly adopts an extension.
- `AI Theme Flow` and `CBRS-specific Repricing` may both be supported while the causal interpretation is competitor-divergence normalization rather than simple same-direction theme buying.
- Historical Analyst Consensus must not be reconstructed from current free-site values. If an as-of historical consensus source is unavailable, the validation result should remain explicitly `UNKNOWN` rather than guessed.
- This extension does not create a trading signal, authorize provider activation, or establish fixed buy/sell thresholds.

## Discovery trace

| Discovery ID | Date | Proposal | Source | Triage state |
|---|---|---|---|---|
| DISC-007 | 2026-09-14 | Model CBRS-like competitor divergence, latent positive catalyst under macro pressure, relative mean reversion and repricing overshoot | `REPORT_CBRS_COMPETITOR_DIVERGENCE_MEAN_REVERSION_RATE_PRESSURE_2026-09-14.md` | Promoted to UWBS-027..031 |
