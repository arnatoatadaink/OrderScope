# OrderScope — Analyst Expectations / Cross-Market Context Work Breakdown

Status: non-normative execution backlog extension
Date: 2026-09-05
Parent: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Normative spec: `stock_monitoring_v0.1_spec.md`

## 1. Purpose

Add Analyst Consensus and Cross-Market Context validation work that was not present in the original Corporate Intelligence WBS.

Preserve the separation of Fact / Derived Metric / Interpretation / Prediction. Do not promote unobserved capital movement to Fact.

## 2. A0 — Analyst Expectations / Allocation Context

| ID | Task | Completion condition | Dependency |
|---|---|---|---|
| A0-001 | Define FX contradiction conditions for Cross-Market Rotation | Specify source/destination, expected FX direction, support/contradiction evidence, `fx_direction_consistency`, and confidence-degradation rules; FX alone must not establish capital movement as Fact | `I0-005` logical schema; design may proceed early, implementation acceptance waits for Accepted `I0-002/005` |
| A0-002 | CBRS 2026-09-01..09-04 Multi-Layer Flow Validation | Align CBRS/NVDA/market + AI proxy/UST/JGB/USDJPY/BTC on one timeline and rate Macro / Theme / Company-specific / Short-cover / Japan→US rotation hypotheses as SUPPORT/PARTIAL/CONTRADICT/UNKNOWN | A0-001 plus available market/macro/consensus data |

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

## 5. Definition of Done

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

## 6. Execution order

1. Finalize `A0-001` design.
2. Align fields with `I0-002/005`.
3. Acquire data and execute `A0-002` validation.
4. Use validation results to decide whether confidence needs numeric scoring.

## 7. Non-goals

- Do not estimate total international capital flow from FX alone.
- Do not identify institutional buyers from a single news item.
- Do not reconstruct historical Consensus from current values on free aggregation sites.
- Do not express capital-flow confidence as a precise probability in v0.1.
