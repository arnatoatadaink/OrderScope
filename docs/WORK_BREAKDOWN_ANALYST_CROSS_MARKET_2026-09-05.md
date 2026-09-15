# OrderScope — Analyst Expectations / Cross-Market Context Work Breakdown

Status: non-normative execution backlog extension
Date: 2026-09-15
Parent: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Normative spec: `stock_monitoring_v0.1_spec.md`

## 1. Purpose

Add Analyst Consensus and Cross-Market Context validation work that was not present in the original Corporate Intelligence WBS.

Preserve the separation of Fact / Derived Metric / Interpretation / Prediction. Do not promote unobserved capital movement to Fact.

The 2026-09-15 revision formally incorporates the previously WBS-unreflected Macro/Carry, CBRS competitor-divergence, and official macro-source adapter extensions. Incorporation records dependency and completion boundaries only; it does not authorize live provider activation, Worker/Cron mutation, remote D1 mutation, or trading signals.

## 2. A0 — Analyst Expectations / Allocation Context

| ID | Source | Task | Completion condition | Dependency |
|---|---|---|---|---|
| A0-001 | Original | Define FX contradiction conditions for Cross-Market Rotation | Specify source/destination, expected FX direction, support/contradiction evidence, `fx_direction_consistency`, and confidence-degradation rules; FX alone must not establish capital movement as Fact | `I0-005` logical schema; design may proceed early, implementation acceptance waits for Accepted `I0-002/005` |
| A0-002 | Original | CBRS 2026-09-01..09-04 Multi-Layer Flow Validation | Align CBRS/NVDA/market + AI proxy/UST/JGB/USDJPY/BTC on one timeline and rate Macro / Theme / Company-specific / Short-cover / Japan→US rotation hypotheses as SUPPORT/PARTIAL/CONTRADICT/UNKNOWN | A0-001 plus available market/macro/consensus data |
| A0-003 | UWBS-011 | Define Macro-Market non-price Fact contract | Define normalized raw Facts for policy rates, short-market rates, sovereign 2Y/5Y/10Y/30Y yields, USD/JPY and eligible volatility/flow context; preserve event/available/accepted/as-of times, units, market/tenor identity and source provenance; inferred capital movement must not be stored as Fact | A0-001; I0-002/004/005; provider/source gates |
| A0-004 | UWBS-012 | Implement rate-curve and cross-country Derived Metrics | Compute tested 2s10s/10s30s slopes, U.S.-Japan 2Y/10Y spreads, fixed-window FX/yield deltas and change velocity; distinguish steepening, flattening and inversion without causal labeling; preserve as-of semantics | A0-003; A0-001; I0 Fact/Derived Metric boundary |
| A0-005 | UWBS-013 | Define carry-unwind / deleveraging Interpretation contract | Define `CARRY_UNWIND_CANDIDATE`, `DELEVERAGING_REGIME`, `RATE_SHOCK`, `FX_SHOCK_JPY` and evidence rules from multiple independent inputs; support SUPPORT/PARTIAL/CONTRADICT/UNKNOWN; prohibit one FX move or one news item from establishing capital movement as Fact | A0-003/004; A0-001 hypothesis rules; News evidence |
| A0-006 | UWBS-014 | Macro stress / carry-unwind validation fixtures and Canary cases | Cover policy-rate-up + long-yield-down, curve regime changes, rapid JPY appreciation, broad selloff with/without company-specific negative evidence, explicit carry-reduction reports, event-risk de-risking and false positives; validate Fact/Derived Metric/Interpretation separation | A0-003..005; A0-002 validation pattern |
| A0-007 | UWBS-015 | Survey and select structured macro-rate / FX / flow data sources | Record permissible official/structured sources, terms, cadence, historical depth, timestamps, revision behavior, cost, rate limits and fallback boundary; prefer official-direct raw macro sources; do not activate live providers as part of survey | Existing provider/terms/security gates; A0-003 data requirements |
| A0-008 | UWBS-027 | Define leader / competitor divergence context | Represent leader, competitor, substitute and ordinary sector-peer relationships separately; preserve source/effective history; allow leader strength and competitor weakness to coexist without treating both as one-direction theme flow | A0-001/002; I0 relationship/history boundary |
| A0-009 | UWBS-028 | Implement relative overshoot / mean-reversion metrics | Compute target drawdown/recovery versus market, sector and leader proxies; include relative volume participation and bounded pre/post catalyst windows; preserve as-of semantics and keep causality out of the metric itself | A0-008; A0-002 aligned timeline; market bars |
| A0-010 | UWBS-029 | Define latent catalyst / macro-pressure dominance Interpretation | Support `LATENT_POSITIVE_CATALYST` and `MACRO_PRESSURE_DOMINANT` only when positive company evidence coexists with broader rate/macro pressure; require multiple independent inputs; prohibit institutional-buyer identity or capital-flow claims from price/volume alone | A0-003..005; A0-009; catalyst/market-reaction evidence |
| A0-011 | UWBS-030 | Extend repricing state machine for mean-reversion overshoot | Distinguish `RELATIVE_OVERSHOOT`, `RELATIVE_MEAN_REVERSION`, `REPRICING_OVERSHOOT`, and `LOCAL_EQUILIBRIUM_CANDIDATE` from persistent catalyst-driven price discovery; do not freeze fixed percentage/session thresholds from the CBRS case alone | A0-009/010; market-reaction state contract |
| A0-012 | UWBS-031 | Add CBRS competitor-divergence Canary fixture | Reproduce NVDA-led theme strength, competitor divergence, broad/rate-pressure selloff, positive company catalyst, rebound with relative volume expansion, overshoot and later stabilization; include false positives | A0-002; A0-008..011 |
| A0-013 | UWBS-032 | Implement U.S. Treasury par-yield source adapter | Parse official Daily Treasury Par Yield Curve responses into source-neutral 2Y/5Y/10Y/30Y raw points; preserve source date, tenor, unit and source reference; malformed/missing required columns fail closed; parser does not invent Fact acceptance time | A0-003/004/007; existing validation collector only as compatibility reference |
| A0-014 | UWBS-033 | Implement New York Fed overnight-rate source adapter | Parse EFFR and optional SOFR/OBFR official reference-rate responses into distinct short-market-rate raw points; preserve reference date, unit and revision/footnote metadata where available; do not merge EFFR with the FOMC target range | A0-003/007; A0-013 acquisition pattern |
| A0-015 | UWBS-034 | Implement BOJ/MOF Japan macro source adapters | Normalize BOJ API and MOF 2Y/5Y/10Y/30Y source data; preserve source semantics and release/observation boundaries; do not invent Japanese-holiday availability | A0-003/004/007; official Japanese source contracts |
| A0-016 | UWBS-035 | Implement FRED/ALFRED revision-aware fallback adapter | Provide explicit fallback/history retrieval with vintage/revision lineage and underlying-source/terms references; never silently replace official-direct semantics or licensing constraints | A0-007; provider/security terms boundary |
| A0-017 | UWBS-036 | Add CFTC positioning evidence adapter | Normalize selected TFF/COT positioning series as positioning Evidence/Derived Metric; never label positioning changes as fund flow or capital movement | A0-003/005/007 |

## 3. A0-001 design boundary

### Minimum input context

- source-market index / proxy
- destination-market index / proxy
- source/destination volume or flow proxy
- source/destination sovereign yield
- relevant FX pair
- policy expectation
- observation window

### Hypothesis Record

Capital movement is stored as Interpretation/Hypothesis, not Fact.

Candidate required fields:

- `hypothesis_type`
- `source_region`
- `destination_region`
- `proposed_direction`
- `observed_window_start`
- `observed_window_end`
- `supporting_evidence_refs`
- `contradicting_evidence_refs`
- `fx_direction_consistency`
- `confidence`
- `generated_at`
- `model_or_rule_version`

### `fx_direction_consistency`

Values:
- `SUPPORT`
- `NEUTRAL`
- `CONTRADICT`
- `UNKNOWN`

For a simple direct Japan→US new-capital-flow hypothesis, the expected FX direction is JPY selling / USD buying; a rising USD/JPY is therefore a support candidate.

A material USD/JPY decline is a contradiction candidate. FX can also move because of carry unwind, policy expectations, hedging, intervention risk, and other factors, so FX alone must neither confirm the hypothesis as Fact nor fully reject it.

### Confidence rule

v0.1 uses ordinal confidence rather than a precise probability:

- `HIGH`: multiple independent Evidence sources align and no major contradiction exists
- `MEDIUM`: support dominates but contradiction or missing data remains
- `LOW`: major directional inconsistency or weak support
- `UNKNOWN`: required context missing

If FX is `CONTRADICT`, do not assign `HIGH` unless other independent Evidence strongly supports the hypothesis.

## 4. A0-002 validation case

Windows:
- baseline: 2026-08-26..2026-08-31
- primary: 2026-09-01..2026-09-04

Minimum series:
- CBRS
- NVDA
- Nasdaq Composite or QQQ
- AI/Semiconductor proxy
- U.S. 10Y Treasury yield
- Japan 10Y JGB yield
- USD/JPY
- BTC

Hypotheses:
- H1 Global Macro Relief
- H2 AI Theme Flow
- H3 CBRS-specific Repricing
- H4 Short Covering
- H5 Japan → US Capital Rotation

Known contradiction candidate: USD/JPY moved roughly 160 → 155 → 156. That direction is opposite to a simple Japan-asset sale → JPY sale → USD purchase → U.S.-asset purchase explanation, so H5 starts with low confidence pending other Evidence.

## 5. Incorporated extension boundaries

### 5.1 Macro / carry lane

`A0-003..007` turns the one-off A0-002 macro context into reusable Fact, Derived Metric, Interpretation, QA and source-selection contracts. Official-direct sources are preferred for v0.1 raw macro observations. High-frequency ETF/fund-flow remains deferred pending commercial terms/cost review.

`A0-013..017` are source-adapter tasks. Adapters stop before Fact Store acceptance; the owning acquisition layer attaches acceptance/provenance timestamps. Existing `official_macro.py` remains the A0-002 validation collector until an explicit migration/removal task is accepted.

### 5.2 CBRS competitor-divergence lane

`A0-008..012` extends A0-002 without changing H1..H5 historical results. It models peer-role divergence, relative overshoot/mean reversion, and bounded interpretations while preserving the prohibition on causal buyer/capital-flow claims from price/volume alone.

No fixed buy/sell threshold, fixed percentage overshoot threshold, or fixed session count is authorized by this lane. Historical threshold calibration remains separate future work if later required.

### 5.3 Market-day and activation boundary

All tasks in this A0 extension may be designed, fixture-tested, historically replayed, reviewed and WBS-maintained while the U.S. market is closed. Live freshness/session acceptance remains market-day gated where explicitly required. Provider activation, Worker/Cron mutation and remote D1 changes remain separately change-window gated.

## 6. Definition of Done

### A0-001

- FX can be represented as support/contradiction Evidence for a capital-movement hypothesis.
- `fx_direction_consistency` is defined.
- ordinal confidence rules are defined.
- FX alone never turns capital movement into Fact.
- Evidence references preserve as-of state.

### A0-002

- Target series are aligned to one timeline.
- CBRS relative return / relative volume are calculated.
- Consensus gap is evaluated.
- UST/JGB/USDJPY direction is evaluated.
- All five hypotheses receive SUPPORT/PARTIAL/CONTRADICT/UNKNOWN.
- Validation report separates Fact from Interpretation.

### A0-003..017

- Each task satisfies its table completion condition with source-grounded, deterministic evidence appropriate to its layer.
- Fact, Derived Metric and Interpretation outputs remain distinct.
- Missing historical/as-of data remains UNKNOWN rather than backfilled from current values.
- Source adapters preserve revision/source lineage and fail closed on malformed required input.
- Positioning evidence is not mislabeled as fund flow or observed capital movement.
- No task silently activates a live provider or remote runtime.

## 7. Execution order

1. Keep `A0-001/002` accepted baseline intact.
2. Use `A0-003..007` as the reusable macro/carry contract and source-selection lane.
3. Use `A0-008..012` for CBRS competitor-divergence / relative-repricing analysis and QA.
4. Use `A0-013..017` as official/fallback macro source adapters beneath the reusable macro contract.
5. Calibrate any future numeric thresholds only from separate historical validation; do not infer them from CBRS alone.

## 8. Non-goals

- Do not estimate total international capital flow from FX alone.
- Do not identify institutional buyers from a single news item or from price/volume alone.
- Do not reconstruct historical Consensus from current values on free aggregation sites.
- Do not express capital-flow confidence as a precise probability in v0.1.
- Do not treat CFTC positioning changes as observed fund flow.
- Do not activate providers, Worker/Cron, or remote D1 through this WBS revision.
