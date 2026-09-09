# OrderScope — N1-006 Live Candidate Population Acceptance

Status: **Accepted — authenticated candidate population complete; explicit labeling pending**
Date: 2026-09-10
Task: `N1-006 — Evaluate news recall`
Scope: authenticated Alpaca 30-day candidate population and provider-shape compatibility

## 1. Result

The live candidate-population blocker is resolved.

Local validation reported:

```text
focused tests: 28 passed
full tests: 503 passed, 2 dependency deprecation warnings
compileall: success / no errors
git diff --check: clean / no findings
candidate command: success
candidate_count: 645
output: var/benchmarks/n1-006/amd-nvda-news-candidates.json
```

The two deprecation warnings are dependency-maintenance warnings and do not invalidate this acceptance result.

## 2. Generated-artifact validation

```text
unique provider article IDs: 645
duplicate provider article IDs: 0
untrimmed provider symbols: 0
per-candidate duplicate symbols: 0
cross-query merged candidates: 47
content key present: False
configured secrets present: False
```

The provider-shape regression case for article `61371589` normalized successfully to:

```text
['MA', 'V', 'ALLY', 'BAC', 'BRK', 'COF', 'META', 'NVDA', 'WBD']
```

The normalized output therefore preserves the News metadata contract: provider symbols are stripped, bounded, non-blank, and unique while provider-originated duplicates after trimming are collapsed.

## 3. Count reconciliation

The live provider inspection previously observed:

```text
AMD query articles: 93
NVDA query articles: 599
raw query-total: 692
cross-query merged candidates: 47
```

Therefore the expected unique candidate count is:

```text
692 - 47 = 645
```

This exactly matches the generated `candidate_count=645`.

This is acceptance evidence that the bounded pagination, provider-article identity merge, and cross-query deduplication completed coherently for the official N1-006 comparison window.

## 4. Security / retention boundary

The accepted output remains metadata-only:

- no `content` field is present;
- configured Alpaca credentials are absent;
- output is written under the configured data-root benchmark path;
- no News body content is required for N1-006 recall measurement.

## 5. Task boundary

This work remains part of `N1-006` live benchmark execution.

It is **not** `UWBS-016`.

`UWBS-016` remains the later Worker/Schedule production News-acquisition task and must not start before N1-006 has produced measured recall/lag evidence and the proposed production cadence is reviewed.

## 6. Current N1-006 state

```text
Evaluator framework                           Accepted
Benchmark manifest/report path                Accepted
Official SEC reference seed                   Complete
Candidate population implementation           Accepted
Provider-shape compatibility                  Accepted
Authenticated 30-day candidate population     Accepted (645 candidates)
Explicit labeling/finalization implementation Accepted
  -> generate label template
  -> explicitly review all 645 candidates
  -> finalize benchmark
  -> execute quality news-recall
  -> record measured recall / signed lag / misattribution / unresolved
  -> N1-006 Accepted
```

No automatic article-to-reference matching has been performed or accepted.

## 7. Next action

Generate the label template from the accepted candidate file:

```bash
PYTHONPATH=analysis/app uv run python -m orderscope_local.cli \
  quality news-recall-label-template \
  --candidates "$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-candidates.json" \
  --filename amd-nvda-news-labels.json
```

Expected output location:

```text
$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-labels.json
```

Every generated row must initially remain `unreviewed`. Finalization must continue to fail until every candidate has been explicitly classified as `matched`, `unrelated`, or `unresolved` according to the accepted labeling contract.

## 8. Non-goals for the next step

Do not yet:

- auto-match headlines to the four SEC references;
- infer event equivalence from ticker overlap alone;
- finalize a benchmark with any `unreviewed` candidate;
- start `UWBS-016`;
- register Worker/Schedule jobs;
- change Worker mode or open remote D1 work.
