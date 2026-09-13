# OrderScope — N1-006 Web Implementation Handoff

Status: **Provisional result — complete non-live toolchain accepted; real 30-day execution pending**
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

## 3. Accepted benchmark manifest / reporting CLI

Implemented:

- `analysis/app/orderscope_local/news/recall_benchmark.py`
- `analysis/tests/news/test_news_recall_benchmark.py`
- `quality news-recall --benchmark <json>`

Measured acceptance evidence:

```text
focused benchmark/CLI command -> 15 passed
full pytest suite              -> 482 passed
compileall                     -> success / no errors
git diff --check               -> clean / no findings
```

## 4. Official 30-day reference seed

Human-readable provenance ledger:

`docs/work-management/local-corporate-intelligence/N1-006_REFERENCE_SEED_2026-08-11_2026-09-10.md`

Machine-readable seed:

`analysis/config/benchmarks/n1-006-amd-nvda-20260811-20260910-reference.json`

Window:

```text
2026-08-11T00:00:00Z <= timestamp < 2026-09-10T00:00:00Z
```

References:

| Reference ID | Subject | Type | SEC availability |
|---|---|---|---|
| `n1r-amd-20260813-financing` | AMD | financing | 2026-08-17T16:05:40Z |
| `n1r-nvda-20260817-partnership` | NVDA | partnership | 2026-08-17T08:41:33Z |
| `n1r-amd-20260819-leadership` | AMD | leadership | 2026-08-19T16:16:56Z |
| `n1r-nvda-20260826-earnings` | NVDA | earnings | 2026-08-26T16:21:19Z |

The seed is never evaluated as zero recall before News population.

## 5. Retrospective timestamp rule

For this historical provider-recall benchmark:

- Tier-1 reference side uses SEC/IR `available_at`;
- News side uses Alpaca source-provided article `created_at`, normalized by the accepted adapter as provider `published_at`;
- signed lag therefore measures provider article availability relative to the Tier-1 reference;
- local scheduler/retrieval delay is a separate operational metric and is not reconstructed retrospectively.

## 6. Candidate-population path — Accepted implementation

Implemented:

- `analysis/app/orderscope_local/news/alpaca_http.py`
- `analysis/app/orderscope_local/news/recall_population.py`
- `analysis/tests/news/test_news_recall_population.py`
- `quality news-recall-candidates`

Candidate acquisition forces `include_content=false`, uses bounded pagination, and writes metadata-only JSON beneath:

```text
ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/
```

Measured acceptance evidence:

```text
focused population/CLI command -> 15 passed
full pytest suite               -> 488 passed
compileall                      -> success / no errors
git diff --check                -> clean / no findings
```

This accepts implementation only; no provider benchmark values are inferred from tests.

## 7. Explicit labeling / finalization path — Accepted implementation

Implemented:

- `analysis/app/orderscope_local/news/recall_labeling.py`
- `analysis/tests/news/test_news_recall_labeling.py`
- machine-readable reference seed under `analysis/config/benchmarks/`
- CLI `quality news-recall-label-template`
- CLI `quality news-recall-finalize`

Workflow:

```text
news-recall-candidates
  -> metadata-only candidate JSON
  -> news-recall-label-template
  -> every article explicitly reviewed
       matched / unrelated / unresolved
  -> news-recall-finalize
  -> final news-recall-benchmark-v0.1 JSON
  -> quality news-recall
```

Rules:

- `unreviewed` is allowed only in the generated template and blocks finalization.
- `matched` requires one explicit reference ID and explicit News-side assigned subject.
- `unrelated` is omitted from benchmark discoveries.
- `unresolved` becomes an explicit unresolved label, not a guessed match.
- every candidate must have exactly one label.
- unknown reference IDs fail closed.
- final discovery `observed_at` preserves provider publication timestamp.

Measured acceptance evidence reported by the operator:

```text
focused labeling/CLI command -> 15 passed
full pytest suite             -> 494 passed
compileall                    -> success / no errors
git diff --check              -> clean / no findings
```

The entire non-live N1-006 preparation/toolchain is now accepted.

## 8. API requirement for real execution

The real News population step requires authenticated Alpaca Market Data News API access.

Process-local environment variables already used by the accepted config boundary:

```text
ORDERSCOPE_SECRET_ALPACA_API_KEY
ORDERSCOPE_SECRET_ALPACA_API_SECRET
```

The transport maps these to Alpaca's key/secret authentication headers. Credentials are never written into candidate JSON, benchmark JSON, logs, or Git.

Real execution does not require article-body access; the collector forces `include_content=false`.

## 9. Real execution sequence

With local Alpaca credentials configured:

```bash
export ORDERSCOPE_SECRET_ALPACA_API_KEY='<key-id>'
export ORDERSCOPE_SECRET_ALPACA_API_SECRET='<secret-key>'

uv run orderscope quality news-recall-candidates \
  --start 2026-08-11T00:00:00Z \
  --end 2026-09-10T00:00:00Z \
  --filename amd-nvda-news-candidates.json
```

Then:

```bash
uv run orderscope quality news-recall-label-template \
  --candidates "$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-candidates.json"
```

Explicitly review all generated labels, then finalize against:

```text
analysis/config/benchmarks/n1-006-amd-nvda-20260811-20260910-reference.json
```

Finally execute `quality news-recall` on the final benchmark.

Final N1-006 acceptance requires measured reference count, discovery rate, signed lags, misattribution, and unresolved cases from that real bounded run.

## 10. Current acceptance sequence

```text
Evaluator framework                         Accepted
Benchmark manifest/report path              Accepted
Official reference seed                     Complete
Candidate population implementation         Accepted
Explicit labeling/finalization implementation Accepted
Complete non-live N1-006 toolchain          Accepted
  -> authenticated Alpaca metadata fetch
  -> explicit candidate review
  -> final benchmark JSON
  -> measured quality news-recall report
  -> N1-006 Accepted
```

## 11. Safety / non-scope

N1-006 does not:

- request or persist News body content for recall measurement;
- auto-infer article-event equivalence;
- expose credentials in JSON/output;
- register live scheduler jobs;
- alter Worker mode;
- open remote D1 / SMOKE-007;
- treat local historical retrieval time as provider historical availability.

## 12. Live candidate-population blocker — proposed repair pending Web scope review

On 2026-09-10, the authenticated N1-006 candidate command was executed for the
official comparison window:

```bash
PYTHONPATH=analysis/app uv run python -m orderscope_local.cli \
  quality news-recall-candidates \
  --start 2026-08-11T00:00:00Z \
  --end 2026-09-10T00:00:00Z \
  --filename amd-nvda-news-candidates.json
```

Candidate generation stopped before writing the output file:

```text
ContractViolation: News candidate acquisition failed: invalid_response_symbols
```

The failure was reproduced by calling the Alpaca News transport directly and
inspecting only response structure and metadata. The full bounded window
returned this snapshot:

| Query symbol | Pages | Articles | Invalid `symbols` values |
|---|---:|---:|---:|
| AMD | 2 | 93 | 0 |
| NVDA | 12 | 599 | 1 |

The single incompatible provider observation was article ID `61371589`, with
provider `created_at` `2026-08-22T13:00:00Z`:

```text
[' MA', ' V', 'ALLY', 'BAC', 'BRK', 'COF', 'MA', 'META', 'NVDA', 'V', 'WBD']
```

Alpaca supplied leading whitespace on ` MA` and ` V`. The current adapter
requires each provider symbol to already be stripped, so one malformed symbol
rejects the entire page. After trimming, those two observations duplicate the
later `MA` and `V` values.

No candidate JSON was created by the failed run. Credentials and article body
content were not printed or persisted.

### 12.1 Proposed bounded repair

Change only the Alpaca response-normalization boundary and its tests:

1. In `analysis/app/orderscope_local/news/alpaca.py`, trim surrounding
   whitespace from each string element decoded from `symbols`.
2. Validate the normalized value, continuing to reject non-string elements,
   empty/whitespace-only symbols, and symbols longer than 32 characters after
   trimming.
3. Deduplicate after normalization while preserving first-observed order. The
   observed value above would normalize to:

   ```text
   ('MA', 'V', 'ALLY', 'BAC', 'BRK', 'COF', 'META', 'NVDA', 'WBD')
   ```

4. Add focused regression coverage in
   `analysis/tests/news/test_alpaca_news_metadata_adapter.py` for surrounding
   whitespace plus post-normalization duplicates.
5. Retain negative coverage proving that `None`, non-sequence values,
   non-string members, whitespace-only members, and over-limit normalized
   symbols still fail closed with the sanitized `invalid_response_symbols`
   category.
6. Run the focused Alpaca adapter and N1-006 population/CLI tests, then the full
   Python suite, `compileall`, and `git diff --check`.
7. Re-run the authenticated candidate command and verify that:
   - pagination completes for both query symbols;
   - AMD/NVDA cross-query articles are merged by provider article ID;
   - the output contains no untrimmed provider symbols;
   - the output remains metadata-only and contains no credentials;
   - the file is written only beneath
     `ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/`.

### 12.2 Scope rationale

This is provider-input hygiene required to complete the real-data execution of
N1-006. It does not relax the normalized News metadata contract: normalized
symbols remain bounded, non-blank, unique strings. It also does not change
query identity, article identity, recall matching, labeling, scoring, storage,
scheduling, Worker behavior, or external infrastructure.

Implementation is intentionally deferred until Web review confirms that this
repair scope is appropriate for N1-006.
