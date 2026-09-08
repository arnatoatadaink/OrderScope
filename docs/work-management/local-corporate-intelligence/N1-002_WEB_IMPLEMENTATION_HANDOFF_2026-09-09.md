# OrderScope — N1-002 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `N1-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `N0-003`, Accepted `N1-001`

## 1. Local acceptance evidence

`N1-002` is Accepted from user-reported local evidence:

```text
focused N1-002 tests -> 12 passed
full pytest suite     -> 309 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N1-002 generates deterministic News Fact candidates from headline/metadata and explicit patterns while never inventing values absent from the source.

The implementation uses the Accepted N1-001 versioned event taxonomy and N0-003 article identity boundary. It does not read temporary News bodies and does not invoke an LLM.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/deterministic_extraction.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_deterministic_extraction.py`

## 4. Versioned extractor contract

Extractor version:

```text
news-deterministic-extractor-v0.1
```

Fact schema:

```text
news-event-fact-v0.1
```

Evidence schema:

```text
news-event-evidence-v0.1
```

The pattern registry is immutable and contains one explicit baseline pattern family for each frozen `NewsEventType`.

## 5. Input boundary

`extract_headline_fact_candidates()` requires:

- accepted `NewsArticleMetadata`;
- matching accepted `ContentIdentity` for the same provider/article ID;
- an explicit registry-resolved `subject_ref` supplied by the caller;
- UTC `retrieved_at` and `accepted_at`.

Provider symbol/ticker tags never determine the durable `subject_ref`.

## 6. Deterministic pattern policy

The v0.1 baseline uses explicit headline patterns only. It contains bounded rules for contract, CAPEX, financing, M&A, regulation, earnings, partnership, major-customer, product/service, supply-chain, leadership, and legal events.

No fuzzy semantic similarity or model inference is used.

## 7. One explicit event = one Fact candidate

Each matched event pattern emits one `Fact` plus reciprocal `Evidence`. If the same headline explicitly establishes independent events, multiple candidates are emitted rather than a multi-label Fact.

The Fact type is:

```text
news.event.<event_type>
```

and its value records only taxonomy/extractor/pattern/provider/article/headline metadata established by the source and extraction method.

## 8. No invented values

The baseline intentionally does not populate absent amount/value, currency, counterparty/customer identity, event date, period, accounting basis, earnings metrics, sentiment, impact, Regime strength, or predicted price direction.

Detailed earnings semantics remain delegated to E0.

## 9. Provenance and Evidence

Each candidate uses accepted N0-002 normalized metadata/content identity. Article URL is used when present; otherwise provider-scoped article identity is the locator. Source publication time is preserved independently from retrieval/acceptance time. Headline SHA-256 is retained as excerpt hash.

## 10. Deterministic IDs

Fact/Evidence record IDs are deterministic from provider article ID + pattern ID + subject_ref. Reprocessing identical accepted metadata reproduces the same candidate identity.

## 11. Focused fixtures accepted

The accepted focused suite covers taxonomy pattern coverage, reciprocal Fact/Evidence, multi-event splitting, no invented values, provider ticker non-authority, speculation rejection, taxonomy boundaries, earnings delegation, safe URL fallback, deterministic IDs, and identity/timestamp validation.

## 12. Explicit non-scope

N1-002 does not inspect temporary body content, produce body evidence spans, use LLM/model extraction, resolve contradictions, infer unnamed entities/values, or perform sentiment/impact/Regime analysis.

N1-003 owns body extraction provenance/span boundaries. N1-004 owns contradiction/pending-review handling.

## 13. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Accepted
N1-003 Ready
N1-004 waits for N1-003
N1-005 waits for N1-004
```

## 14. Next action

Proceed to `N1-003 — body-extraction boundary`: read only Accepted temporary-content refs, retain extractor name/version/confidence/evidence span/source reference, keep body text out of durable records, and leave any LLM adoption behind a separate ADR.
