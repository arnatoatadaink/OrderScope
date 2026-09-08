# OrderScope — N1-003 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `N1-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `N0-004`, Accepted `N1-002`

## 1. Local acceptance

N1-003 is Accepted from user-reported local evidence:

```text
focused N1-003 tests -> 11 passed
full pytest suite     -> 320 passed
git diff --check      -> clean / no findings
```

## 2. Accepted boundary

N1-003 establishes the temporary-body extraction boundary and durably retains extractor name/version, extraction confidence, evidence span offsets/hash, and source reference without retaining article body content.

The implementation reuses Accepted N0-004 `NewsBodyAcquisition` / `TemporaryContent`, Accepted N1-002 deterministic pattern registry, and Accepted I0-005 Fact/Evidence records. No LLM/model path is enabled; any future model extractor requires a separate ADR.

## 3. Accepted implementation

Files:

- `analysis/app/orderscope_local/news/body_extraction.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_body_extraction_boundary.py`

Integrity checks require matching provider/article identity, staged `TEMPORARY_SUCCESS` content, extraction before expiry, and exact SHA-256 body match to the N0-004 acquisition hash.

Durable output contains only taxonomy/event type, extractor name/version, pattern ID, provider/article identity, source reference, confidence, character offsets, and matched-span SHA-256. Raw body and span text are not persisted.

Successful extraction transitions the temporary-content audit record to `EXTRACTION_SUCCEEDED`; N1-005 remains responsible for deletion and deletion proof.

## 4. Focused acceptance coverage

The accepted 11-test fixture set covers:

1. Fact/Evidence with extractor identity, confidence, source ref, and evidence span;
2. raw body absent from durable output;
3. multiple explicit events split into separate candidates;
4. lifecycle transition to `EXTRACTION_SUCCEEDED` without deletion;
5. no-match extraction still completes lifecycle;
6. expired staged content rejection;
7. body-hash mismatch rejection;
8. metadata/content/body article identity consistency;
9. confidence and timestamp boundaries;
10. locator fallback for near-limit source URLs;
11. deterministic candidate IDs/span hashes.

## 5. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Accepted
N1-003 Accepted
N1-004 Ready
N1-005 waits for N1-004
```

## 6. Next action

Proceed to `N1-004 — contradiction / pending review`. Source-grounded SEC/IR/News Facts must remain append-only; contradictions and ambiguity are represented separately with explicit review reason rather than overwriting prior evidence.
