# OrderScope — N1-003 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `N1-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `N0-004`, Accepted `N1-002`

## 1. Local acceptance carried into this cycle

`N1-002` was promoted to Accepted from user-reported local evidence:

```text
focused N1-002 tests -> 12 passed
full pytest suite     -> 309 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N1-003 must establish the temporary-body extraction boundary and durably retain extractor name/version, extraction confidence, evidence span, and source reference without retaining article body content. LLM adoption requires a separate ADR and is not enabled here.

The implementation reuses:

- Accepted N0-004 `NewsBodyAcquisition` / `TemporaryContent` lifecycle;
- Accepted N1-002 deterministic pattern registry;
- Accepted I0-005 Fact/Evidence records.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/body_extraction.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_body_extraction_boundary.py`

## 4. Extraction architecture

`extract_body_fact_candidates()` receives:

- accepted `NewsArticleMetadata`;
- matching provider-scoped `ContentIdentity`;
- accepted N0-004 `NewsBodyAcquisition` with staged TemporaryContent;
- injected `TemporaryBodyReader`;
- registry-resolved `subject_ref`;
- UTC extraction/acceptance timestamps;
- bounded confidence.

Only the injected reader resolves `content_ref` to raw text. The body exists only inside the call and is not part of returned durable records.

## 5. Integrity boundary

Before extraction:

1. metadata article identity must match the accepted provider article identity;
2. body acquisition article ID must match metadata;
3. TemporaryContent must be `STAGED` + `TEMPORARY_SUCCESS`;
4. extraction must occur before `expires_at`;
5. body bytes read from temporary storage must SHA-256 match the N0-004 `content_hash`.

A mismatch is rejected before Fact creation.

## 6. Deterministic body extractor

Extractor identity is frozen as:

```text
extractor_name    = orderscope-deterministic-body
extractor_version = news-body-deterministic-v0.1
```

The implementation reuses N1-002 `headline_patterns()` over the body text. It does not add fuzzy similarity, arbitrary numeric parsing, entity inference, or model calls.

One explicit body pattern match produces one Fact/Evidence candidate. Multiple explicit independent events produce separate candidates.

## 7. Durable Fact/Evidence payload

Fact schema:

```text
news-body-event-fact-v0.1
```

Evidence schema:

```text
news-body-event-evidence-v0.1
```

Durable Fact value contains only:

- taxonomy version;
- event type;
- extractor name/version;
- matched deterministic pattern ID;
- provider key/article ID;
- source reference;
- evidence span start/end character offsets.

`Fact.extraction_confidence` stores the explicit bounded confidence supplied to the extraction boundary.

Evidence uses `EvidenceKind.EXTRACTION_SPAN`, provider quality, durable-metadata retention, and SHA-256 of the exact matched span. The span text itself is not stored.

## 8. Evidence span / locator

`BodyEvidenceSpan` stores:

- `start` inclusive character offset;
- `end` exclusive character offset;
- exact matched-span SHA-256.

Evidence locator normally appends:

```text
#char=<start>-<end>
```

to the source reference. If that would exceed the Fact Store 2048-character locator bound, the locator safely falls back to the provider-scoped article identity while `Provenance.source_ref` still retains the original source reference.

## 9. Temporary-content lifecycle handoff

A successful read/extraction returns the same content reference as:

```text
state = extraction_succeeded
retention_class = temporary_success
extraction_completed_at = extracted_at
```

N1-003 does **not** delete the content and does not create deletion proof. N1-005 remains responsible for prompt success deletion and exception expiry/deletion.

A body with no matching event still counts as a successful extraction pass and transitions to `EXTRACTION_SUCCEEDED` with an empty candidate tuple.

## 10. LLM boundary

No LLM/model path exists in this implementation.

Any future LLM body extractor requires a separate adoption ADR covering at minimum:

- model/provider identity and versioning;
- deterministic/reproducibility limits;
- confidence semantics;
- evidence-span requirements;
- body disclosure/privacy/provider-right implications;
- failure and fallback behavior;
- evaluation/acceptance criteria.

Until such an ADR is accepted, N1-003 remains deterministic only.

## 11. Focused fixtures encoded

The focused module contains 11 tests covering:

1. Fact/Evidence with extractor identity, confidence, source ref, and evidence span;
2. raw body absent from durable Fact/Evidence output;
3. multiple explicit body events split into separate candidates;
4. extraction lifecycle transitions to `EXTRACTION_SUCCEEDED` without deletion;
5. no event match still completes extraction lifecycle;
6. expired staged content rejection;
7. body hash mismatch rejection;
8. metadata/content/body article identity consistency;
9. confidence and timestamp boundaries;
10. durable locator fallback for near-limit source URLs;
11. deterministic candidate IDs and span hashes.

Fixtures use in-memory body readers only. No live provider body is fetched or committed.

## 12. Explicit non-scope

N1-003 does not:

- adopt or invoke an LLM;
- infer event values not explicitly matched;
- persist raw body or matched span text;
- resolve contradictions between body/headline/SEC/IR;
- decide pending-review policy;
- delete temporary content;
- produce retention deletion proof;
- perform sentiment/impact/Regime/prediction analysis.

N1-004 owns contradiction/pending-review. N1-005 owns retention/deletion.

## 13. Local verification boundary

Before promoting N1-003 to Accepted, run:

```bash
uv run pytest -q analysis/tests/news/test_news_body_extraction_boundary.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check.

## 14. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Accepted
N1-003 Provisional result — local test pending
N1-004 waits for N1-003 acceptance
N1-005 waits for N1-004
```

## 15. Next action after acceptance

After N1-003 acceptance, proceed to `N1-004 — contradiction / pending review`. Preserve conflicts among News, SEC, IR, and multiple article revisions rather than overwriting source-grounded Facts; ambiguous cases must retain an explicit exception/review reason.
