# OrderScope — N1-006 Local Review Handoff

Status: **Ready for local explicit review and final benchmark execution**
Date: 2026-09-10
Task: `N1-006 — Evaluate news recall`
Scope: explicit review of the accepted 645-candidate Alpaca News label template, benchmark finalization, measured recall/lag reporting
Branch: `docs/mermaid-conventions-v0.1`
Not task: `UWBS-016`

## 1. Purpose

This is the restart handoff for the current N1-006 critical lane after authenticated candidate population and label-template generation completed successfully.

The local objective is now to review every generated candidate explicitly, finalize the real-data benchmark, execute the accepted quality evaluator, and return measured evidence sufficient for an N1-006 acceptance decision.

Do not repeat the already accepted candidate-population repair unless new provider-shape evidence requires it.

## 2. Current accepted baseline

The live candidate-population blocker has been resolved and accepted.

Recorded evidence:

```text
focused tests: 28 passed
full tests: 503 passed, 2 dependency deprecation warnings
compileall: success / no errors
git diff --check: clean / no findings
candidate command: success
candidate_count: 645
candidate output: var/benchmarks/n1-006/amd-nvda-news-candidates.json
```

Generated-artifact validation:

```text
unique provider article IDs: 645
duplicate provider article IDs: 0
untrimmed provider symbols: 0
per-candidate duplicate symbols: 0
cross-query merged candidates: 47
content key present: False
configured secrets present: False
```

The label template is also generated and structurally validated:

```text
label_count: 645
all labels unreviewed: True
unique label IDs: 645
candidate IDs exact match: True
window match: True
content key present: False
configured secrets present: False
focused tests: 15 passed
```

Expected label file:

```text
$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-labels.json
```

## 3. Benchmark reference set

Use the existing machine-readable reference seed without modifying its meaning:

```text
analysis/config/benchmarks/n1-006-amd-nvda-20260811-20260910-reference.json
```

Official benchmark window:

```text
2026-08-11T00:00:00Z <= timestamp < 2026-09-10T00:00:00Z
```

Reference IDs:

| Reference ID | Subject | Event type | Tier-1 availability |
|---|---|---|---|
| `n1r-amd-20260813-financing` | AMD | financing | 2026-08-17T16:05:40Z |
| `n1r-nvda-20260817-partnership` | NVDA | partnership | 2026-08-17T08:41:33Z |
| `n1r-amd-20260819-leadership` | AMD | leadership | 2026-08-19T16:16:56Z |
| `n1r-nvda-20260826-earnings` | NVDA | earnings | 2026-08-26T16:21:19Z |

Do not add new reference events during this bounded run. Any newly discovered reference-worthy event belongs in a separate follow-up/revision rather than silently changing this benchmark denominator.

## 4. Explicit review contract

Every one of the 645 label rows must end in exactly one accepted decision:

```text
matched
unrelated
unresolved
```

`unreviewed` is temporary only and blocks finalization.

### `matched`

Use only when the News candidate is explicitly judged to represent one of the four benchmark reference events.

Required fields:

```json
{
  "decision": "matched",
  "reference_id": "<one exact reference ID>",
  "assigned_subject_ref": "<explicit News-side subject>",
  "reason": null
}
```

Rules:

- `reference_id` must be one exact ID from §3.
- `assigned_subject_ref` must be explicitly set from the News-side subject attribution.
- Do not match from ticker overlap alone.
- Do not match from broad thematic similarity alone.
- Do not use headline similarity as an automatic decision rule.
- Multiple News articles may legitimately map to the same reference event if they independently report that event.

### `unrelated`

Use when the candidate does not represent any of the four benchmark references.

Required fields:

```json
{
  "decision": "unrelated",
  "reference_id": null,
  "assigned_subject_ref": null,
  "reason": null
}
```

Do not retain match metadata on unrelated rows.

### `unresolved`

Use when the candidate is relevant enough that a definitive unrelated/matched decision cannot be justified from the available metadata, or subject attribution remains materially ambiguous.

Required fields:

```json
{
  "decision": "unresolved",
  "reference_id": null,
  "assigned_subject_ref": "<explicit best-supported subject>",
  "reason": "<bounded non-blank explanation>"
}
```

Do not convert uncertainty into a guessed match. `unresolved` is an explicit benchmark result, not an error state.

## 5. Review procedure

Review the existing label JSON in bounded batches while preserving its schema and candidate identity fields.

For each row, inspect at minimum:

```text
provider_article_id
headline
publisher
provider_published_at
query_symbols
provider_symbols
```

The generated template also carries these fields for traceability. Do not edit them unless the accepted candidate source itself is proven corrupt; this handoff authorizes decision-field editing only.

Recommended bounded review cycle:

```text
1. Select a manageable batch of unreviewed rows.
2. Classify each as matched / unrelated / unresolved.
3. Save the JSON.
4. Validate that JSON remains parseable and row count remains 645.
5. Confirm no provider_article_id was added, removed, or duplicated.
6. Continue until unreviewed count reaches zero.
```

The review may be performed with local helper scripts if desired, but the helper must not auto-decide matches. Any automation may only assist filtering, sorting, counting, or presenting rows for human/explicit review.

## 6. Pre-finalization validation

Before running finalization, verify all of the following:

```text
label rows = 645
unique provider_article_id = 645
unreviewed = 0
matched rows have reference_id and assigned_subject_ref
matched rows have reason = null
unresolved rows have assigned_subject_ref and non-blank reason
unresolved rows have reference_id = null
unrelated rows have all match metadata = null
candidate/reference/label windows are identical
```

If any of these fail, repair the label file before finalization. Do not weaken the loader/finalizer contract to accept malformed review data.

## 7. Finalize the real benchmark

Run:

```bash
PYTHONPATH=analysis/app uv run python -m orderscope_local.cli \
  quality news-recall-finalize \
  --references analysis/config/benchmarks/n1-006-amd-nvda-20260811-20260910-reference.json \
  --candidates "$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-candidates.json" \
  --labels "$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-labels.json" \
  --filename amd-nvda-news-benchmark-final.json
```

Expected output:

```text
$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-benchmark-final.json
```

The command must fail if any row remains `unreviewed`, if a matched row references an unknown reference ID, if label coverage differs from candidate coverage, or if benchmark windows do not match.

Record:

```text
references =
discoveries =
unresolved =
output =
```

## 8. Execute measured quality evaluation

Run:

```bash
PYTHONPATH=analysis/app uv run python -m orderscope_local.cli \
  quality news-recall \
  --benchmark "$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-benchmark-final.json"
```

Capture the complete non-secret Markdown result produced by the evaluator.

At minimum, retain the measured values required by N1-006:

```text
reference count
discovery / recall result
signed discovery lag(s)
ticker / subject misattribution result
unresolved count
```

These are real measured benchmark values. Do not substitute fixture metrics, test counts, or synthetic examples for them.

## 9. Acceptance checks after finalization

Run the focused labeling/evaluator tests, then full local acceptance:

```bash
uv run pytest -q \
  analysis/tests/news/test_news_recall_labeling.py \
  analysis/tests/news/test_news_recall_evaluator.py \
  analysis/tests/news/test_news_recall_benchmark.py

uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Record separately from benchmark metrics:

```text
focused tests =
full tests =
compileall =
git diff --check =
```

Test-pass counts are implementation evidence only; they are not News-quality measurements.

## 10. N1-006 acceptance decision boundary

N1-006 may be promoted to `Accepted` only after all of the following exist:

1. all 645 candidates explicitly reviewed;
2. final benchmark JSON successfully generated;
3. measured `quality news-recall` result captured;
4. recall/discovery, signed lag, misattribution, and unresolved evidence recorded;
5. focused/full acceptance remains clean;
6. no credentials or News body content enter committed artifacts;
7. integrated progress tracker is updated with the measured result and acceptance decision.

If measured quality is poor, N1-006 can still complete as an evaluation task if the measurement is valid and the tracker records the result accurately. Do not reinterpret an unfavorable metric as an implementation failure unless the benchmark construction itself is invalid.

## 11. Stop conditions

Stop and report a bounded failure instead of guessing if:

- label/candidate/reference IDs or windows do not reconcile;
- a candidate cannot be assigned even to a defensible subject for `unresolved`;
- finalization reports an unknown reference ID;
- candidate or label files no longer contain exactly 645 unique article IDs;
- secrets or News body content are found in benchmark artifacts;
- another provider-shape incompatibility is discovered that changes candidate identity/content;
- review reveals that the four-reference seed itself is materially invalid.

A seed defect requires a separate benchmark-reference review; do not silently alter the denominator in this execution.

## 12. Explicit non-scope

Do not in this handoff:

- start `UWBS-016`;
- register Worker/Schedule News jobs;
- change Worker Shadow mode;
- open or mutate remote D1 / `SMOKE-007`;
- persist News article bodies;
- add another News provider;
- broaden AMD/NVDA Canary scope;
- alter the five-minute Worker cadence proposal;
- modify the four-event benchmark reference set without a separate review.

## 13. Progress-tracker update

After the measured evaluation, update:

```text
docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md
```

The update should replace the current `N1-006 real-data execution pending` state with the measured result and one of:

```text
Accepted
Measured — remediation/follow-up required
Blocked — benchmark invalid or incomplete
```

Do not mark `UWBS-016` started merely because N1-006 completed.

## 14. Report back to Web

Return only non-secret execution evidence:

```text
reviewed labels: 645/645
matched: <n>
unrelated: <n>
unresolved: <n>
finalize: success | <sanitized failure>
references: <n>
discoveries: <n>
measured recall: <value>
measured signed lag: <summary>
misattribution: <value/summary>
unresolved benchmark cases: <n>
focused tests: <n> passed
full tests: <n> passed
compileall: success/no errors
git diff --check: clean/no findings
final benchmark path: <path>
progress tracker: updated/not updated
```

If N1-006 is accepted, the next planning step is to use measured recall/lag to confirm or adjust the proposed `UWBS-016` Worker News cadence before any production activation.
