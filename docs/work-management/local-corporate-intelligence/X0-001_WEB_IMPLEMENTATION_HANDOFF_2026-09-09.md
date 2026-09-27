# OrderScope — X0-001 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `X0-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L1-005`, `I0-005`, `E0-007`, `N1-005`, `O0-005`

## 1. Local acceptance evidence

User-reported local verification:

```text
focused X0-001 tests -> 7 passed
full pytest suite    -> 398 passed
git diff --check     -> clean / no findings
```

The fixture-path dependency chain through L1-005 is Accepted. Real D1 promotion remains separately gated by `L1-003` / `SMOKE-007`.

## 2. Accepted boundary

X0-001 provides a deterministic, read-only unified timeline over canonical market bars plus Filing, Earnings/Fundamental, News, and Official/Policy Facts.

Knowledge-order semantics are fixed as follows:

- Fact availability = `provenance.available_at`;
- Fact internal acceptance = `Fact.accepted_at`;
- market availability/acceptance = preserved `receipt_time`;
- both availability and acceptance must be `<= as_of`;
- date-only source event timestamps are never coerced to an invented UTC instant;
- stable ordering is `available_at, accepted_at, source_kind, subject_ref, item_id`.

Timeline items contain lightweight integration metadata and references only. They do not duplicate Fact values, news bodies, SEC document bodies, or raw market payloads.

## 3. Accepted files

- `analysis/app/orderscope_local/integration/__init__.py`
- `analysis/app/orderscope_local/integration/timeline.py`
- `analysis/tests/integration/test_unified_timeline.py`

## 4. Focused fixtures

Accepted coverage includes:

1. information-availability ordering versus event-time ordering;
2. exclusion of future-available/future-accepted Facts;
3. no fabricated instant for date-only source event time;
4. conservative deterministic Fact source-kind classification;
5. market receipt time as availability;
6. deterministic tie-breaking independent of input order;
7. market dataset lineage preservation.

## 5. Non-scope retained

X0-001 does not implement HTTP endpoints, source-health/coverage summary, scheduling, real D1 export, contradiction resolution, or missing-bar synthesis.

`X0-002` owns Corporate coverage summary. `X0-003` remains gated by Accepted X0-001, X0-002, and L0-004.
