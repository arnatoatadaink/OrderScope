# OrderScope — N1-006 Local Repair Handoff

Status: **Ready for local implementation and acceptance**
Date: 2026-09-10
Task: `N1-006 — Evaluate news recall`
Scope: live candidate-population provider-input repair only
Not task: `UWBS-016`
Parent handoff: `docs/work-management/local-corporate-intelligence/N1-006_WEB_IMPLEMENTATION_HANDOFF_2026-09-10.md`

## 1. Purpose

This report is the local execution handoff for the currently observed Alpaca News live-data blocker in `N1-006`.

The goal is to make the authenticated 30-day candidate population complete without weakening the normalized News metadata contract, without storing News bodies, and without expanding scope into Worker/Schedule production activation.

## 2. Current accepted baseline

The non-live N1-006 toolchain is already Accepted.

Latest accepted local evidence before this repair:

```text
focused adapter/population tests -> 22 passed
full pytest suite                -> 497 passed
compileall                       -> success / no errors
git diff --check                 -> clean / no findings
```

Previously accepted live-shape fixes include:

- Alpaca `content` member may be present even with `include_content=false`; body is discarded and never normalized/persisted.
- missing/blank publisher is normalized to `None`.
- optional summary whitespace is normalized without making summary a benchmark key.
- sanitized field-level `invalid_response_<field>` diagnostics are available without printing provider values or credentials.

These accepted boundaries must remain intact.

## 3. Observed live blocker

Authenticated execution for the official N1-006 window:

```text
2026-08-11T00:00:00Z <= timestamp < 2026-09-10T00:00:00Z
```

fails with:

```text
ContractViolation: News candidate acquisition failed: invalid_response_symbols
```

A local structure-only investigation found:

| Query symbol | Pages | Articles | Invalid `symbols` values |
|---|---:|---:|---:|
| AMD | 2 | 93 | 0 |
| NVDA | 12 | 599 | 1 |

The incompatible provider observation is article ID `61371589`, provider `created_at` `2026-08-22T13:00:00Z`, with:

```text
[' MA', ' V', 'ALLY', 'BAC', 'BRK', 'COF', 'MA', 'META', 'NVDA', 'V', 'WBD']
```

The issue is surrounding whitespace on two provider symbol observations. After trimming, those observations duplicate later `MA` and `V` values.

No candidate JSON was created by the failed run. Credentials and News body content must remain absent from output and logs.

## 4. Approved repair scope

Implement the repair only at the Alpaca provider-normalization boundary in:

```text
analysis/app/orderscope_local/news/alpaca.py
```

For each element of the provider `symbols` sequence:

1. Require the raw element to be a string.
2. Trim surrounding whitespace.
3. Reject the normalized value if it is empty/whitespace-only.
4. Reject the normalized value if it exceeds 32 characters.
5. Deduplicate **after normalization** while preserving first-observed order.

The observed provider value must normalize to:

```text
('MA', 'V', 'ALLY', 'BAC', 'BRK', 'COF', 'META', 'NVDA', 'WBD')
```

Do not invent symbols and do not infer ticker identity from headlines.

## 5. Contract that must remain fail-closed

The repair must not make `symbols` permissive beyond surrounding-whitespace normalization.

The following cases must still fail with sanitized:

```text
invalid_response_symbols
```

- `symbols is None`
- symbols value is not a sequence
- a sequence member is not a string
- a sequence member becomes blank after trimming
- a normalized symbol is longer than 32 characters

Normalized `provider_symbols` must remain an immutable, unique tuple of bounded non-blank strings.

## 6. Focused regression tests

Update:

```text
analysis/tests/news/test_alpaca_news_metadata_adapter.py
```

Required positive fixture:

```python
symbols=[" MA", " V", "ALLY", "MA", "NVDA", "V"]
```

Expected normalized result:

```python
("MA", "V", "ALLY", "NVDA")
```

The test must prove:

- whitespace is removed;
- duplicates created by normalization are removed;
- first-observed order is preserved.

Required negative coverage must prove rejection of:

```text
None
non-sequence symbols
non-string member
whitespace-only member
normalized over-limit member
```

Do not add logging or diagnostics that emit raw provider symbol values.

## 7. Local acceptance commands

Run focused tests first:

```bash
uv run pytest -q \
  analysis/tests/news/test_alpaca_news_metadata_adapter.py \
  analysis/tests/news/test_news_recall_population.py
```

Then run the full acceptance set:

```bash
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Record:

```text
focused passed =
full passed =
compileall =
git diff --check =
```

## 8. Authenticated candidate rerun

After local acceptance succeeds, rerun:

```bash
PYTHONPATH=analysis/app uv run python -m orderscope_local.cli \
  quality news-recall-candidates \
  --start 2026-08-11T00:00:00Z \
  --end 2026-09-10T00:00:00Z \
  --filename amd-nvda-news-candidates.json
```

Credentials must remain only in:

```text
ORDERSCOPE_SECRET_ALPACA_API_KEY
ORDERSCOPE_SECRET_ALPACA_API_SECRET
```

Never copy either credential into this report, terminal output intended for sharing, JSON, Git, or chat.

## 9. Live rerun acceptance conditions

The authenticated rerun is successful only when all of the following hold:

1. pagination completes for AMD and NVDA;
2. candidate JSON is written beneath:

   ```text
   $ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/
   ```

3. candidate output remains metadata-only;
4. no credentials are present in output;
5. no untrimmed provider symbols are present;
6. same provider article ID returned by AMD/NVDA queries is merged rather than duplicated;
7. candidate count is non-zero and consistent with the observed raw population.

The local structure survey observed:

```text
AMD raw query articles  = 93
NVDA raw query articles = 599
raw query total         = 692
```

Therefore the deduplicated candidate count should be `<= 692`, because cross-query provider article IDs may merge.

Record after success:

```text
candidate_count =
output =
```

If practical, also record the raw per-query counts used for the successful run:

```text
AMD query article count =
NVDA query article count =
```

These counts are diagnostic evidence only; benchmark scoring is based on the finalized candidate/reference review, not raw article volume.

## 10. Stop conditions

If the candidate command fails again with another sanitized provider-shape category such as:

```text
invalid_response_<field>
```

stop the benchmark progression at that point and investigate that provider field separately.

Do not:

- skip the offending article;
- silently drop an entire page;
- replace unknown values with invented defaults;
- convert a failed population into a zero-recall benchmark;
- weaken unrelated Core contracts to make the run pass.

A new provider-shape repair should remain minimal and be covered by focused regression tests before rerunning live acquisition.

## 11. Next phase after successful candidate generation

Once the candidate JSON is successfully generated, provider-shape repair stops and N1-006 proceeds to benchmark review:

```text
candidate JSON
  -> news-recall-label-template
  -> explicit review of every candidate
       matched / unrelated / unresolved
  -> news-recall-finalize
  -> quality news-recall
  -> measured recall / signed lag / misattribution / unresolved count
  -> N1-006 acceptance decision
```

Generate the label template with an explicit output filename:

```bash
PYTHONPATH=analysis/app uv run python -m orderscope_local.cli \
  quality news-recall-label-template \
  --candidates "$ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/amd-nvda-news-candidates.json" \
  --filename amd-nvda-news-labels.json
```

Do not auto-match by headline similarity. Every candidate must be explicitly reviewed.

## 12. Scope boundary versus UWBS-016

This local repair is part of:

```text
N1-006 — live benchmark execution / Alpaca provider-shape compatibility
```

It is **not**:

```text
UWBS-016 — Worker/Schedule News metadata acquisition
```

`UWBS-016` remains a later production-operation task. Its cadence and activation decision should use the measured N1-006 recall/lag result.

No Worker registration, Worker mode change, remote D1 change window, or scheduler activation is authorized by this handoff.

## 13. Local completion report back to Web

After implementation and rerun, report only the following non-secret evidence:

```text
focused tests: <n> passed
full tests: <n> passed
compileall: success/no errors
git diff --check: clean/no findings
candidate command: success | <sanitized failure category>
candidate_count: <n, if success>
output path: <path, if success>
```

If successful, the next Web task is candidate review/final benchmark preparation, not UWBS-016 implementation.
