# OrderScope — E0-005 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-08
Task: `E0-005`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_SEGMENT_REVENUE_FALLBACK_WEB_009_2026-09-04.md`
Depends on: Accepted `S0-006`, Accepted `E0-004`

## 1. Web implementation scope

Implemented the bounded segment-revenue fallback chain and focused tests without running the local suite.

Changed/added files:

- `analysis/app/orderscope_local/earnings/segment_revenue.py`
- `analysis/app/orderscope_local/earnings/__init__.py`
- `analysis/tests/earnings/test_segment_revenue.py`

## 2. Fixed fallback order

The implementation enforces exactly:

1. `company_facts`
2. `xbrl_dimension`
3. `filing_table`

The chain stops at the first successful method. Every attempted stage is retained as a `SegmentRevenueAttempt` with method, status, source accession/ref, and explicit failure reason where unsuccessful.

An empty or unsuitable Company Facts result is never interpreted as zero segment revenue or as proof that the segment does not exist.

## 3. Failure semantics

The bounded v0.1 reasons include:

- `entity_wide_only`
- `dimension_fact_not_in_companyfacts_scope`
- `custom_extension_not_normalized`
- `concept_not_found`
- `period_mismatch`
- `unit_mismatch`
- `context_member_unresolved`
- `table_layout_unresolved`
- `transport_error`

Unsuccessful stages require a failure reason. Successful stages cannot carry one.

## 4. Source-grounded observation boundary

Successful output preserves:

- Corporate Canary instrument
- raw issuer label
- `classification_role` without name-only SegmentIdentity normalization
- explicit period start/end
- exact Decimal value
- explicit USD currency
- display scale for filing-table values
- filing accession
- extraction method
- actual concept QName where XBRL-backed
- actual axis/member pairs for dimension-backed values
- table role for filing-table fallback
- accepted `Provenance`

XBRL/Company Facts success requires caller-supplied Provenance whose source ref matches the normalized `XbrlFact`. The implementation does not synthesize hashes, retrieval times, or acceptance times.

## 5. Period and ambiguity boundaries

Quarter and YTD duration facts are distinct because selection requires exact period start/end. A 6M YTD fact therefore cannot satisfy a 3M quarter request.

If more than one normalized XBRL fact matches accession, period, unit, and dimension-presence criteria, extraction raises an explicit ambiguity instead of choosing one value.

E0-005 deliberately does not normalize segment identity by raw label. AMD Client/Gaming recast/merge cases and NVIDIA classification-axis differences remain E0-006 work.

## 6. Focused tests encoded

Tests cover:

- Company Facts success stopping the chain
- dimension fallback after recorded Company Facts failure
- filing-table success as the third method
- all-three failure path preserving reasons and no numeric synthesis
- quarter vs YTD distinction
- explicit/matching Provenance requirement
- ambiguous XBRL match rejection
- axis/member preservation

## 7. Explicit non-scope

E0-005 does not yet:

- parse live filing HTML
- discover XBRL contexts/linkbases from raw filings
- normalize or merge segment identities
- infer missing period/unit/segment values
- reconcile restated/recast segment histories
- calculate segment growth or Regime strength

## 8. Local verification boundary

Before promoting `E0-005` to Accepted, run:

```bash
uv run pytest -q analysis/tests/earnings/test_segment_revenue.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression suite, and clean diff check. Semantic review should confirm that the fixed fallback order and explicit failure reasons are preserved and that no missing source/provenance/value semantics are invented.

## 9. Next action after acceptance

If local verification passes, promote `E0-005` to Accepted and begin `E0-006` SegmentIdentityHistory as a separate cycle. That task must model rename/merge/split/recast history without equating segments by name alone.
