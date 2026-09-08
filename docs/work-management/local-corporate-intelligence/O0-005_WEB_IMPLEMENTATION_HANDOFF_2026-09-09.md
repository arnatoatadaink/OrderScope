# OrderScope — O0-005 Web Implementation Handoff

Status: **Provisional result — focused tests pass / full-suite collection fix pending recheck**
Date: 2026-09-09
Task: `O0-005`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `O0-002`, Accepted `O0-003`, Accepted `O0-004`
Research inputs: `WEB-016`, `WEB-017`, `WEB-018`

## 1. Local acceptance carried into this cycle

`O0-004` was promoted to Accepted from user-reported local evidence:

```text
focused relevance tests -> 9 passed
full pytest suite        -> 248 passed
git diff --check         -> clean / no findings
```

## 2. WBS completion boundary

O0-005 must verify Official Signal quality across:

- update / duplicate / missing / availability observations;
- timestamp precision;
- statement / proposal / decision / implementation separation;
- direct-instrument / theme / mention / unresolved relevance errors;
- durable source/evidence behavior.

The implementation combines the already accepted O0 contracts instead of introducing a new source parser.

## 3. Changed/added files

- `analysis/app/orderscope_local/official/quality_report.py`
- `analysis/app/orderscope_local/official/__init__.py`
- `analysis/tests/official/test_official_quality_report.py`

The test module was initially named `analysis/tests/official/test_quality_report.py`. A full-suite run exposed a pytest import-name collision with `analysis/tests/earnings/test_quality_report.py`; the official test module was renamed to `test_official_quality_report.py` without changing its test semantics.

## 4. Quality model

`OfficialSignalQualityCase` binds one canonical official item with:

- one or more O0-003 semantic policy observations;
- one or more O0-004 relevance observations;
- optional prior canonical observation for revision comparison.

`assess_official_signal_quality()` emits deterministic findings with three severities:

- `pass`
- `review`
- `error`

A quality report is accepted when it contains no semantic `error`; review states are retained rather than silently promoted or discarded.

## 5. Acquisition / update / delete checks

The integrated matrix preserves O0-002 boundaries:

- same canonical URL + same hash -> unchanged/pass;
- same canonical URL + changed hash -> revision candidate/review;
- `listing_missing` -> review and explicitly **not deletion**;
- `canonical_unavailable` -> review, retained history, no hard delete instruction;
- a first observation is treated as new, not as an update.

The quality layer does not reinterpret availability observations as deletion semantics.

## 6. Timestamp checks

If source publication precision is `DATE_ONLY`, the quality finding explicitly confirms that it remains date-only.

No quality check converts date-only values to midnight UTC or infers a source publication clock time from `retrieved_at`.

## 7. Semantic Fact checks

The matrix rechecks O0-003 invariants:

- statement/proposal cannot carry decision/effective semantics;
- decision requires source-grounded `decision_at` and cannot carry effective semantics;
- implementation cannot reuse `decision_at` and requires exactly one explicit `effective_at` or `effective_expression`;
- multiple semantic Facts from one official document are preserved rather than collapsed.

## 8. Relevance checks

The matrix rechecks O0-004 false-positive boundaries:

- theme-only exposure remains theme-only and does not fan out to AMD/NVDA;
- direct instrument + theme may coexist only as separate already-validated Evidence-grounded links;
- mention-only remains non-instrument relevance;
- unresolved remains review;
- no-link remains no inferred durable relation.

No numeric relevance confidence is invented.

## 9. Focused fixtures encoded

Tests cover:

1. White House-style one-document multi-Fact semantics with theme-only linkage;
2. same URL / changed hash as review-level revision candidate;
3. listing disappearance as review, never deletion;
4. unresolved product relevance remains review rather than direct link;
5. date-only publication precision remains date-only;
6. deterministic Markdown quality rendering;
7. duplicate quality case IDs are rejected.

These are deterministic contract fixtures, not a live-policy precision/recall benchmark.

## 10. Local verification evidence / collection issue

User-reported local verification after the initial implementation:

```text
focused O0-005 tests -> 7 passed in 0.77s
full pytest suite     -> collection error before execution
```

The full-suite failure was not a production-code or assertion failure. Pytest imported the earnings module as top-level `test_quality_report`, then attempted to collect the official file with the same basename and raised an import-file mismatch:

```text
analysis/tests/earnings/test_quality_report.py
analysis/tests/official/test_quality_report.py
```

Repository fix applied:

- created `analysis/tests/official/test_official_quality_report.py` with the same seven fixtures;
- removed `analysis/tests/official/test_quality_report.py`.

O0-005 remains Provisional until the renamed focused test, full suite, and diff check are rerun locally.

## 11. Explicit non-scope

O0-005 does not yet:

- perform live HTTP quality measurement;
- establish empirical precision/recall percentages;
- test ETag/Last-Modified reliability against live providers;
- automatically parse official source bodies;
- resolve all individual officials/products from raw text;
- define news-lane quality or contradiction scoring.

Those belong to later integration/runtime or N1 work.

## 12. Local verification boundary

Before promoting O0-005 to Accepted, run:

```bash
uv run pytest -q analysis/tests/official/test_official_quality_report.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check. Semantic review should confirm that review-level update/missing/unresolved cases are visible but never silently interpreted as deletion, implementation, or direct AMD/NVDA relevance.

## 13. Official Context lane state

```text
O0-001 Accepted
O0-002 Accepted
O0-003 Accepted
O0-004 Accepted
O0-005 Provisional result — collection fix applied / local recheck pending
```

If local verification passes, the O0 Official Context lane is complete for the v0.1 Corporate Canary fixture boundary.

## 14. Next action after acceptance

After O0-005 acceptance, return to the integrated Critical Path and select the next safe branch. X0-001 remains gated on the News/Interpretation side (`N1-005`) and local foundation dependencies, so do not start X0 merely because E0/O0 are complete. Reconcile the runtime tracker, then select the next Ready N0/N1 or Local-foundation task according to dependency state.
