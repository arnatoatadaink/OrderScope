# OrderScope — N1-006 Web Implementation Handoff

Status: **Provisional result — evaluator accepted; benchmark manifest/CLI implementation pending local verification; real 1–3 month execution pending**
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

## 2. Evaluator implementation — Accepted framework

Implemented:

- `analysis/app/orderscope_local/news/recall.py`
- `analysis/tests/news/test_news_recall_evaluator.py`
- exports through `analysis/app/orderscope_local/news/__init__.py`

Versioned contracts:

```text
news-recall-evaluator-v0.1
news-recall-report-v0.1
```

Local acceptance evidence reported by the operator:

```text
focused evaluator tests -> 7 passed
full pytest suite        -> 475 passed
compileall               -> success / no errors
git diff --check         -> clean / no findings
```

This accepts the evaluator/framework only. It does not satisfy the WBS-required real/reference benchmark execution.

## 3. Evaluator benchmark boundary

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

Benchmark preparation owns event equivalence. The evaluator only measures the labeled result.

## 4. Metrics

`evaluate_news_recall()` reports:

- reference event count;
- number of reference events with at least one labeled News discovery;
- discovery rate;
- discovery count;
- ticker/subject misattribution count and rate;
- per-reference earliest discovery ID;
- signed first-discovery lag in seconds.

Signed lag:

```text
positive = News observed after SEC/IR reference availability
zero     = same timestamp
negative = News observed before the SEC/IR reference availability
```

The evaluator never clamps negative lag.

## 5. Evaluation-window rule

The benchmark window must be between 30 and 93 days inclusive.

Both reference events and labeled discoveries must fall inside the half-open window:

```text
window_start <= timestamp < window_end
```

An empty benchmark returns explicit zero counts/rates; it is not represented as successful recall.

## 6. Real-benchmark ingestion path

Repository inspection after evaluator acceptance found no existing 30–93 day dataset that already contains explicit SEC/IR-reference-to-News labels suitable for N1-006 execution.

To avoid fabricating benchmark metrics or committing article bodies, the next Web implementation adds a narrow metadata-only benchmark path:

- `analysis/app/orderscope_local/news/recall_benchmark.py`
- `analysis/tests/news/test_news_recall_benchmark.py`
- `quality news-recall --benchmark <json>` CLI command

Versioned benchmark schema:

```text
news-recall-benchmark-v0.1
```

The JSON manifest contains only:

- benchmark ID;
- 30–93 day window;
- explicit SEC/IR reference metadata;
- explicit News discovery labels;
- unresolved benchmark-label cases with bounded reasons.

It does not contain raw SEC filings, issuer-IR bodies, News bodies, provider credentials, or inferred unlabeled article-event matches.

Unknown JSON fields fail closed so a benchmark cannot silently add unreviewed semantics.

## 7. Benchmark report

`render_news_recall_markdown()` produces deterministic Markdown with:

- reference count;
- discovered-reference count / discovery rate;
- News discovery count;
- subject/ticker misattribution count/rate;
- per-reference signed lag;
- minimum / maximum / median signed lag;
- unresolved benchmark-label cases.

The CLI prints this report to stdout and performs no HTTP mutation, provider call, scheduler registration, or body retention.

## 8. Current focused test boundary

Previously accepted evaluator module:

- `analysis/tests/news/test_news_recall_evaluator.py` — 7 passed measured.

New benchmark-path tests pending local verification:

- `analysis/tests/news/test_news_recall_benchmark.py` — 6 cases;
- existing `analysis/tests/cli/test_cli.py` gains one `quality news-recall` case.

The new cases cover JSON decoding/loading, exact-field validation, taxonomy validation, unresolved-label window validation, deterministic report output, and CLI execution.

## 9. Required next local verification

Run:

```bash
uv run pytest -q analysis/tests/news/test_news_recall_benchmark.py analysis/tests/cli/test_cli.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

If these pass, the benchmark ingestion/reporting path can be accepted. `N1-006` itself remains Provisional until a real/reference 30–93 day benchmark is populated and executed.

## 10. Final N1-006 acceptance gap

Final task acceptance still requires at least one real/reference comparison dataset and measured:

- reference count;
- discovered-reference count / discovery rate;
- signed lag distribution or per-event lags;
- ticker/subject misattribution count/rate;
- unresolved benchmark labeling cases.

Synthetic fixture values are never substituted for these measurements.

## 11. Non-scope

N1-006 does not:

- choose a new News provider;
- fetch live News/SEC/IR by itself;
- infer whether two unlabeled events are equivalent;
- alter News taxonomy/extraction/retention;
- authorize body retention beyond accepted lifecycle rules;
- register live scheduler jobs;
- open remote D1 or Worker change windows.
