# OrderScope — N1-002 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `N1-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `N0-003`, Accepted `N1-001`

## 1. Local acceptance carried into this cycle

`N1-001` was promoted to Accepted from user-reported local evidence:

```text
focused N1-001 tests -> 10 passed
full pytest suite     -> 297 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N1-002 must generate deterministic News Fact candidates from headline/metadata and explicit patterns, while never inventing values absent from the source.

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

This prevents an Alpaca tag such as `NVDA` on an AMD query from silently changing Corporate identity.

## 6. Deterministic pattern policy

The v0.1 baseline uses explicit headline patterns only. It contains bounded rules for:

- contract award/agreement language;
- CAPEX investment/spending tied to facilities/equipment/capacity;
- financing issuance/raising/offering language;
- M&A/ownership transaction language;
- regulator/government formal-action language;
- earnings/result release language;
- partnership/collaboration language;
- explicit customer/client selection/deployment/purchase language;
- product/service launch/release/recall/discontinuation language;
- supply-chain/production/capacity change language;
- leadership appointment/resignation/succession language;
- private legal proceeding/settlement language.

No fuzzy semantic similarity or model inference is used.

## 7. One explicit event = one Fact candidate

Each matched event pattern emits one `Fact` plus reciprocal `Evidence`.

If the same headline explicitly establishes independent events, for example financing plus CAPEX, two candidates are emitted rather than a multi-label Fact.

The Fact type is:

```text
news.event.<event_type>
```

and its value records only:

- taxonomy version;
- event type;
- extractor version;
- matched pattern ID;
- provider key;
- provider article ID;
- exact headline.

## 8. No invented values

The baseline intentionally does **not** populate absent:

- amount/value;
- currency;
- counterparty/customer identity;
- event date;
- period start/end;
- GAAP/non-GAAP basis;
- earnings metric values;
- sentiment;
- impact;
- Regime strength;
- predicted price direction.

For example, `AMD wins contract for accelerator systems` creates a contract event candidate but does not invent contract value or counterparty.

Detailed earnings semantics remain delegated to E0.

## 9. Provenance and Evidence

Each candidate uses the accepted N0-002 normalized metadata/content identity:

- `source_ref` is article URL when present;
- if URL is absent, fallback locator is provider-scoped article identity (`alpaca-news:article:<id>`);
- content hash is the accepted normalized metadata hash from N0-002;
- `published_at` remains the source article timestamp;
- `available_at` is not inferred from publication time and remains the actual local retrieval point in this baseline;
- headline SHA-256 is stored as `Evidence.excerpt_hash`;
- Evidence quality is `provider` and retention is `durable_metadata`.

The headline itself is already durable N0-002 metadata; no article body crosses this boundary.

## 10. Deterministic IDs

Fact/Evidence record IDs are deterministic from:

```text
provider article ID + pattern ID + subject_ref
```

This makes repeated processing of identical accepted article metadata reproduce the same candidate identity. It does not replace the N0-003 article duplicate/syndication rules.

## 11. Focused fixtures encoded

The focused test module currently contains 12 tests covering:

1. immutable pattern registry covers all frozen event types;
2. contract headline creates reciprocal Fact/Evidence;
3. explicit financing + CAPEX yields two separate candidates;
4. absent amount/counterparty/date are not invented;
5. provider ticker tags cannot change registry-resolved subject;
6. speculative/analyst headline emits no Fact;
7. partnership is not promoted to contract;
8. regulator action vs private legal case separation;
9. earnings category does not invent financial values/basis;
10. missing URL uses provider article locator safely;
11. identical input reproduces candidate record IDs;
12. article identity mismatch and invalid timestamp order are rejected.

## 12. Explicit non-scope

N1-002 does not:

- inspect temporary body content;
- produce body evidence spans;
- use LLM/model extraction;
- resolve ambiguous or contradictory source claims;
- infer unnamed counterparties/customers;
- parse arbitrary numeric amounts;
- create detailed E0 earnings metrics;
- perform sentiment/impact/Regime analysis.

N1-003 owns body extraction provenance/span boundaries. N1-004 owns contradiction/pending-review handling.

## 13. Local verification boundary

Before promoting N1-002 to Accepted, run:

```bash
uv run pytest -q analysis/tests/news/test_news_deterministic_extraction.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check.

## 14. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Provisional result — local test pending
N1-003 waits for N1-002 (N0-004 already Accepted)
N1-004 waits for N1-003
N1-005 waits for N1-004
```

## 15. Next action after acceptance

After N1-002 acceptance, proceed to `N1-003 — body-extraction boundary`. That task should use the already Accepted temporary content reference, retain extractor name/version/confidence/evidence span/source reference, and keep LLM adoption behind a separate ADR.
