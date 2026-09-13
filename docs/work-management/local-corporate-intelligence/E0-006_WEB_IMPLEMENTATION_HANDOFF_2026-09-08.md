# OrderScope — E0-006 Web Implementation Handoff

Status: **Accepted — local verification passed**
Date: 2026-09-09
Task: `E0-006`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_SEGMENT_REVENUE_FALLBACK_WEB_009_2026-09-04.md`
Depends on: Accepted `E0-005`

## 1. Web implementation scope

Implemented immutable SegmentIdentityHistory contracts and focused Canary fixtures.

Changed/added files:

- `analysis/app/orderscope_local/earnings/segment_identity.py`
- `analysis/app/orderscope_local/earnings/__init__.py`
- `analysis/tests/earnings/test_segment_identity.py`

## 2. Identity boundary

Segment identity is never resolved by issuer label alone. Each version preserves:

- stable `segment_id`
- Corporate Canary instrument
- classification role
- issuer-reported label
- validity interval
- `as_reported_at`
- filing accession
- source Provenance
- explicit recast flag

Classification roles are separated at minimum into:

- `reportable_segment`
- `disaggregated_business`
- `market_platform`

Identical labels under different roles therefore do not imply one identity.

## 3. History changes

The contract represents structural changes as explicit history edges:

- introduced
- renamed
- merged
- split
- recast
- retired

Merge/split/rename shapes are validated. Edges must reference known stable segment IDs and remain source-grounded through filing accession and Provenance.

## 4. Canary cases encoded

Focused tests encode the WEB-009 structural cases:

- AMD Client + Gaming reportable segments merge into a distinct Client-and-Gaming stable identity;
- the merged AMD identity is marked as recast where the filing retrospectively adjusts prior periods;
- AMD Data Center can retain the same stable ID across a recast while keeping separate non-overlapping versions and explicit recast history;
- NVIDIA identical-looking labels under reportable-segment vs market-platform roles remain distinct identities;
- overlapping validity intervals for the same stable segment ID are rejected;
- merge edges referencing unknown segment IDs are rejected;
- resolution requires stable `segment_id`; an issuer label such as `Graphics` is not an identity lookup key.

## 5. Resolution behavior

`resolve_segment_version` resolves by:

1. stable `segment_id`;
2. validity interval;
3. optional classification-role guard.

It never searches by display label. Missing or ambiguous resolution fails explicitly rather than selecting a same-name segment.

## 6. Explicit non-scope

E0-006 does not yet:

- auto-discover rename/merge/split/recast from filing text;
- map E0-005 raw labels automatically to stable segment IDs;
- reconcile original-vs-recast numeric values;
- calculate segment growth or Regime strength;
- infer effective dates absent from source evidence.

Those concerns belong to ingestion/reconciliation and E0-007 quality reporting.

## 7. Local verification evidence

Local verification completed after fetch/pull:

- focused SegmentIdentityHistory tests: **6 passed**
- full regression suite: **210 passed**
- `git diff --check`: **clean**

The result is therefore Accepted and safe as the E0-007 prerequisite.

## 8. Next action

Begin `E0-007` earnings Canary quality report as a separate cycle. Reconcile multiple AMD/NVDA quarters across SEC/IR/basic earnings/segment sources and report extraction success plus unresolved differences rather than silently choosing one source.
