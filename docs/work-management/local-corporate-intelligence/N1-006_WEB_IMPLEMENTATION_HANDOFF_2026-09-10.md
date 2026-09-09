# OrderScope — N1-006 Web Implementation Handoff

Status: **Provisional result — evaluator/fixture path implemented; local verification and 1–3 month benchmark execution pending**
Date: 2026-09-10
Task: `N1-006`
Parent WBS: `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `E0-007`, Accepted `N1-005`

## 1. WBS completion target

Measure News discovery quality over a 1–3 month comparison window against SEC/issuer-IR reference events:

- discovery rate / recall;
- discovery lag;
- ticker/subject misattribution.

The evaluation must not promote inferred article-event equivalence into Fact.

## 2. Implementation

Added:

- `analysis/app/orderscope_local/news/recall.py`
- `analysis/tests/news/test_news_recall_evaluator.py`

Updated:

- `analysis/app/orderscope_local/news/__init__.py`

Versioned contracts:

```text
news-recall-evaluator-v0.1
news-recall-report-v0.1
```

## 3. Benchmark boundary

The evaluator consumes an explicitly labeled benchmark rather than guessing matches from headline similarity.

`NewsRecallReferenceEvent` represents one SEC/IR reference event:

- stable reference ID;
- subject identity;
- accepted `NewsEventType`;
- reference `available_at`;
- source kind restricted to `sec` or `ir`.

`NewsRecallDiscovery` represents one News discovery already labeled to a reference event:

- stable discovery ID;
- explicit `reference_id`;
- subject/ticker assigned by the News path;
- News observation timestamp.

Unknown reference IDs fail closed.

This separation means benchmark preparation owns event equivalence. The evaluator only measures the labeled result.

## 4. Metrics

`evaluate_news_recall()` reports:

- reference event count;
- number of reference events with at least one labeled News discovery;
- discovery rate;
- discovery count;
- ticker/subject misattribution count and rate;
- per-reference earliest discovery ID;
- signed first-discovery lag in seconds.

Signed lag is intentional:

```text
positive = News observed after SEC/IR reference availability
zero     = same timestamp
negative = News observed before the SEC/IR reference availability
```

The evaluator never converts negative lag into an error or silently clamps it.

## 5. Evaluation-window rule

The benchmark window must be between 30 and 93 days inclusive.

Both reference events and labeled discoveries must fall inside the half-open window:

```text
window_start <= timestamp < window_end
```

An empty benchmark returns explicit zero counts/rates; it is not represented as successful recall.

## 6. Focused fixture cases

`analysis/tests/news/test_news_recall_evaluator.py` contains 7 cases covering:

1. discovery rate plus positive/negative signed lag;
2. deterministic earliest-discovery selection;
3. ticker/subject misattribution rate;
4. unknown reference rejection;
5. out-of-window reference/discovery rejection;
6. 30–93 day window enforcement;
7. empty benchmark explicit-zero behavior.

Fixtures are synthetic acceptance data only and are not factual claims about AMD/NVDA news coverage.

## 7. Remaining acceptance gap

The implementation/fixture path alone does **not** satisfy the complete WBS N1-006 result.

Final N1-006 acceptance also requires executing at least one real/reference comparison dataset covering 1–3 months of SEC/IR reference events and News discoveries, then recording measured:

- reference count;
- discovered-reference count / discovery rate;
- signed lag distribution or per-event lags;
- ticker/subject misattribution count/rate;
- unresolved benchmark labeling cases.

No such real benchmark values are fabricated in this handoff.

## 8. Required local verification

Run:

```bash
uv run pytest -q analysis/tests/news/test_news_recall_evaluator.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

If these pass, the evaluator implementation can be accepted as the N1-006 fixture/evaluation framework, while the task remains Provisional until the required 1–3 month benchmark is executed.

## 9. Non-scope

N1-006 does not:

- choose a new News provider;
- fetch live News/SEC/IR by itself;
- infer whether two unlabeled events are equivalent;
- alter News taxonomy/extraction/retention;
- authorize body retention beyond accepted lifecycle rules;
- register live scheduler jobs;
- open remote D1 or Worker change windows.
