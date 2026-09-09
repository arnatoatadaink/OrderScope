# OrderScope — N1-006 Web Implementation Handoff

Status: **Provisional result — evaluator and benchmark path accepted; official reference seed complete; News population path pending local verification/execution**
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

## 2. Accepted evaluator framework

Implemented:

- `analysis/app/orderscope_local/news/recall.py`
- `analysis/tests/news/test_news_recall_evaluator.py`

Measured acceptance evidence:

```text
focused evaluator tests -> 7 passed
full pytest suite        -> 475 passed
compileall               -> success / no errors
git diff --check         -> clean / no findings
```

The evaluator consumes explicitly labeled SEC/IR reference events and News discoveries. It measures discovery rate, signed lag, and subject/ticker misattribution without guessing event equivalence.

## 3. Accepted benchmark manifest / CLI path

Implemented:

- `analysis/app/orderscope_local/news/recall_benchmark.py`
- `analysis/tests/news/test_news_recall_benchmark.py`
- `quality news-recall --benchmark <json>`

Measured acceptance evidence reported by the operator:

```text
focused benchmark/CLI command -> 15 passed
full pytest suite              -> 482 passed
compileall                     -> success / no errors
git diff --check               -> clean / no findings
```

The benchmark schema is metadata-only and retains explicit unresolved-label cases. It excludes raw SEC/IR/News bodies and credentials.

## 4. Official 30-day reference seed

Added:

`docs/work-management/local-corporate-intelligence/N1-006_REFERENCE_SEED_2026-08-11_2026-09-10.md`

Window:

```text
2026-08-11T00:00:00Z <= timestamp < 2026-09-10T00:00:00Z
```

Real SEC reference set:

| Reference ID | Subject | Type | SEC availability |
|---|---|---|---|
| `n1r-amd-20260813-financing` | AMD | financing | 2026-08-17T16:05:40Z |
| `n1r-nvda-20260817-partnership` | NVDA | partnership | 2026-08-17T08:41:33Z |
| `n1r-amd-20260819-leadership` | AMD | leadership | 2026-08-19T16:16:56Z |
| `n1r-nvda-20260826-earnings` | NVDA | earnings | 2026-08-26T16:21:19Z |

The seed is not itself evaluated as a zero-recall benchmark. News discoveries must be populated first.

## 5. Retrospective News timestamp rule

This benchmark is populated retrospectively after the 30-day window has occurred. Therefore local retrieval time cannot represent historical News availability.

For N1-006 retrospective provider-recall measurement:

- SEC/IR side uses reference `available_at`;
- News side uses Alpaca's source-provided article `created_at`, normalized by the accepted adapter as `published_at`;
- the resulting signed lag measures provider article availability relative to the Tier-1 reference event;
- local scheduler/retrieval delay is a separate operational metric and is not reconstructed from this historical benchmark.

## 6. News candidate population path — pending local verification

Added:

- `analysis/app/orderscope_local/news/alpaca_http.py`
- `analysis/app/orderscope_local/news/recall_population.py`
- `analysis/tests/news/test_news_recall_population.py`
- exports through `analysis/app/orderscope_local/news/__init__.py`
- CLI command `quality news-recall-candidates`

Current Alpaca official News endpoint was rechecked before implementation and matches the accepted adapter assumptions: bounded `limit` 1–50, pagination with `page_token`, symbol/start/end filters, API-key headers, and optional `include_content`. Candidate acquisition forces `include_content=false`.

Manual CLI:

```bash
uv run orderscope quality news-recall-candidates \
  --start 2026-08-11T00:00:00Z \
  --end 2026-09-10T00:00:00Z \
  --filename amd-nvda-news-candidates.json
```

Required credentials remain process-local:

```text
ORDERSCOPE_SECRET_ALPACA_API_KEY
ORDERSCOPE_SECRET_ALPACA_API_SECRET
```

Output is forced beneath:

```text
ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/<simple-json-filename>
```

The output contains only candidate metadata:

- provider article ID;
- AMD/NVDA query-symbol membership;
- headline;
- publisher;
- URL;
- provider symbol tags;
- provider publication timestamp.

It does not contain article bodies or credentials and does not assign reference IDs automatically.

## 7. Candidate labeling boundary

After acquisition, each candidate must be explicitly classified as:

1. matching one reference ID;
2. unrelated to all references; or
3. unresolved / ambiguous.

Only explicit matches become `NewsRecallDiscovery` rows in the final benchmark. Ambiguous items become `unresolved_labels`. Headline similarity alone must never create a match.

Preserve the News path's assigned subject/ticker so misattribution can be measured rather than corrected away during benchmark preparation.

## 8. New focused tests

`analysis/tests/news/test_news_recall_population.py` contains 6 cases covering:

1. concrete HTTP request targets Alpaca News with `include_content=false`;
2. any body request fails closed;
3. provider article IDs are deduplicated across AMD/NVDA queries while query-symbol membership is preserved;
4. candidate JSON remains under `ORDERSCOPE_DATA_ROOT` and contains no credentials;
5. path traversal/output escape is rejected;
6. retrospective window remains constrained to 30–93 days.

## 9. Required local verification

Run:

```bash
uv run pytest -q analysis/tests/news/test_news_recall_population.py analysis/tests/cli/test_cli.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

If these pass, the candidate-acquisition implementation can be accepted. N1-006 itself remains Provisional until the real candidate window is fetched, explicitly labeled, and evaluated.

## 10. Final acceptance sequence

```text
Evaluator framework                       Accepted
Benchmark manifest/report CLI             Accepted
Official 30-day SEC reference seed        Complete
News candidate acquisition implementation Provisional
        -> local tests
        -> execute Alpaca 30-day metadata fetch
        -> explicit candidate/reference labeling
        -> final benchmark JSON
        -> quality news-recall execution
        -> record measured recall/lag/misattribution/unresolved
        -> N1-006 Accepted
```

## 11. Non-scope / safety

N1-006 does not:

- request or persist News body content for recall measurement;
- infer article-event equivalence automatically;
- register a live scheduler job;
- alter Worker mode;
- open remote D1 / SMOKE-007;
- reconstruct local historical scheduler latency from a retrospective provider query.
