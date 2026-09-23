# OrderScope — N0-003 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `N0-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `N0-002`

## 1. Local acceptance evidence

```text
focused N0-003 tests -> 11 passed
full pytest suite     -> 279 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N0-003 classifies provider duplicates, syndication, and updated articles with explainable same/different/update rules.

The implementation is deliberately conservative: no fuzzy-text merge, no ticker-based merge, and no changed-hash overwrite without explicit provider revision evidence.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/duplicate.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_duplicate_handling.py`

## 4. Comparison classes

`NewsArticleComparisonKind` contains `provider_duplicate`, `updated_article`, `provider_conflict`, `canonical_url_duplicate`, `syndication_candidate`, and `distinct`.

Same provider article ID uses Accepted I0-004 identity semantics. Same ID/hash is duplicate; changed hash plus strictly newer provider `updated_at` creates an explicit `RevisionRelationship` and is update; otherwise it is conflict.

## 5. Canonical URL and syndication

Canonicalization is intentionally conservative: lowercase scheme/host, default-port removal, fragment removal, tracking-query removal, and deterministic sorting of remaining query parameters. Semantic query parameters remain.

Different provider IDs with the same canonical URL are article duplicates. Different URLs are only marked `syndication_candidate` when normalized headlines exactly match, publishers differ, and publication times are within 15 minutes. Syndication candidates remain separate article records.

## 6. Explicit non-scope

N0-003 does not fetch article bodies, infer fuzzy semantic syndication, use ticker tags as identity evidence, follow redirects live, scrape publisher canonical tags, auto-merge records, or generate event Facts.

## 7. News lane state

```text
N0-001 Accepted
N0-002 Accepted
N0-003 Accepted
N0-004 Ready
N1-001 Ready independently
N1-002 waits for N0-003 + N1-001
```

## 8. Next action

Proceed to N0-004 temporary body access. N1-001 remains a safe parallel slice after this boundary.
