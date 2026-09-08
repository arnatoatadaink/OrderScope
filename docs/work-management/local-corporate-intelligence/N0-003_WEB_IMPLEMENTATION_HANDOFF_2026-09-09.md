# OrderScope — N0-003 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `N0-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `N0-002`

## 1. Local acceptance carried into this cycle

`N0-002` was promoted to Accepted from user-reported local evidence:

```text
focused N0-002 tests -> 13 passed
full pytest suite     -> 268 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N0-003 must classify provider duplicates, syndication, and updated articles with explainable same/different/update rules.

The implementation is deliberately conservative: no fuzzy-text merge, no ticker-based merge, and no changed-hash overwrite without explicit provider revision evidence.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/duplicate.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_duplicate_handling.py`

## 4. Comparison classes

`NewsArticleComparisonKind` contains:

- `provider_duplicate`
- `updated_article`
- `provider_conflict`
- `canonical_url_duplicate`
- `syndication_candidate`
- `distinct`

`NewsArticleComparison` also carries:

- `same_article`
- `same_story_candidate`
- optional canonical URL
- bounded human-readable reason
- explicit `RevisionRelationship` only for a verified update.

## 5. Same provider article ID

Same provider-scoped article identity delegates first to Accepted I0-004 content identity semantics.

Rules:

1. same ID + same normalized metadata hash -> `provider_duplicate`;
2. same ID + different hash + strictly newer provider `updated_at` -> create explicit `RevisionRelationship` and classify `updated_article`;
3. same ID + different hash without a strictly newer `updated_at` -> `provider_conflict`.

A changed hash alone is never enough to overwrite the accepted article.

## 6. Canonical URL

`canonicalize_news_url()` is intentionally conservative.

It normalizes only:

- lowercase scheme/hostname;
- removal of default `:80` / `:443`;
- empty path to `/`;
- removal of fragment;
- removal of well-known tracking parameters (`utm_*`, `fbclid`, `gclid`, `dclid`, `msclkid`);
- deterministic sorting of remaining query parameters.

Semantic query parameters are retained. For example `?id=7` and `?id=8` remain distinct.

Different provider article IDs resolving to the same conservative canonical URL are `canonical_url_duplicate` and `same_article=True`.

Missing URLs remain valid and do not force a duplicate decision.

## 7. Syndication boundary

Different IDs and different canonical URLs are marked `syndication_candidate` only when all of the following hold:

- exact normalized headline match (case/whitespace normalized only);
- different publishers;
- publication timestamps within 15 minutes.

Even then:

```text
same_article = false
same_story_candidate = true
```

The records are not merged. This creates an explainable candidate for later evidence/review without turning headline similarity into durable article identity.

Same headline from the same publisher or outside the 15-minute bound remains `distinct`.

## 8. Explicit non-scope

N0-003 does not:

- fetch article bodies;
- infer syndication from fuzzy semantic similarity;
- use ticker tags as identity evidence;
- follow HTTP redirects live;
- scrape `<link rel=canonical>` from publisher pages;
- merge records across providers automatically;
- generate event Facts.

N0-004 owns temporary body access. N1 owns event extraction.

## 9. Focused fixtures encoded

The focused test module currently contains 11 tests covering:

1. conservative URL normalization;
2. semantic query retention;
3. same provider ID/hash duplicate;
4. same ID + newer updated timestamp update;
5. same ID changed without timestamp advance conflict;
6. cross-ID same canonical URL duplicate;
7. cross-publisher exact-headline near-time syndication candidate;
8. same-publisher headline remains distinct;
9. outside-time-window headline remains distinct;
10. missing URLs do not force a match;
11. non-HTTP URL rejection.

## 10. Local verification boundary

Before promoting N0-003 to Accepted, run:

```bash
uv run pytest -q analysis/tests/news/test_news_duplicate_handling.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check.

## 11. News lane state

```text
N0-001 Accepted
N0-002 Accepted
N0-003 Provisional result — local test pending
N0-004 Ready from N0-002, but shortest serial path waits for N0-003 acceptance
N1-001 Ready independently
N1-002 waits for N0-003 + N1-001
```

## 12. Next action after acceptance

After N0-003 acceptance, either:

- proceed to N0-004 temporary body access, and/or
- execute N1-001 event taxonomy in a controlled parallel slice.

For the shortest route to N1-005/X0, N0-004 and N1-001 are both required downstream and can be advanced with file-overlap control.
