# OrderScope — X0-002 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `X0-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `I0-003` plus adapter checkpoint/lifecycle state

## 1. Local acceptance carried into this cycle

`X0-001` is Accepted from user-reported local evidence:

```text
focused X0-001 tests -> 7 passed
full pytest suite    -> 398 passed
git diff --check     -> clean / no findings
```

## 2. WBS completion boundary

X0-002 shows Corporate source coverage state without mutating adapters. Per source it exposes:

- last successful checkpoint time;
- latest checkpoint observation/state;
- resumable opaque cursor;
- lag from last success to query `as_of`;
- sanitized partial/error category and retry state;
- temporary-content retention pending/overdue state.

## 3. Changed/added files

- `analysis/app/orderscope_local/integration/coverage.py`
- `analysis/app/orderscope_local/integration/__init__.py`
- `analysis/tests/integration/test_corporate_coverage.py`

## 4. Versioned summary contract

Schema version:

```text
corporate-coverage-summary-v0.1
```

The summary is provider-neutral. Callers identify one stable `(provider_key, source_key)` and pass the accepted `AcquisitionCheckpoint` history for that stream.

## 5. Success / cursor / lag semantics

`last_success_at` is derived only from `CheckpointState.COMPLETE` records visible as of the query time. A partial or error checkpoint never fabricates a successful acquisition.

The latest visible checkpoint supplies:

```text
latest_observed_at
latest_state
resume_cursor
error_category
error_retryable
retry_not_before
```

The cursor remains opaque. X0-002 does not parse or reinterpret provider cursor contents.

Lag is:

```text
as_of - last_success_at
```

and remains `None` when no completed checkpoint exists.

## 6. As-of behavior

Only checkpoints whose `observed_at <= as_of` are visible. A future checkpoint therefore cannot change historical coverage output.

The resulting source summaries are deterministically ordered by:

```text
(provider_key, source_key)
```

## 7. Retention-pending boundary

`TemporaryContent` itself does not contain a provider/source key. X0-002 therefore does not infer ownership from content refs or filenames.

Callers use `RetentionObservation(source_key, content)` to associate an accepted lifecycle record with a source explicitly.

For visible, non-deleted content the summary reports:

- `retention_pending_count`;
- `retention_overdue_count` where `expires_at <= as_of`;
- earliest `retention_next_due_at`.

Deleted content is not counted as pending. Future-captured lifecycle records are excluded from historical as-of output.

## 8. Failure/secret boundary

X0-002 only surfaces the sanitized checkpoint error contract (`category`, `retryable`, `retry_not_before`). It does not carry provider exception bodies, credentials, HTTP bodies, raw news content, or deletion bodies.

## 9. Focused fixtures encoded

The focused module currently contains 9 tests covering:

1. completed checkpoint -> last success and lag;
2. later partial checkpoint preserves prior success while exposing cursor/retry/error;
3. error without prior completion does not invent last success;
4. future checkpoint exclusion by as-of;
5. retention pending/overdue/next due;
6. future lifecycle observation exclusion;
7. checkpoint/retention source-scope mismatch rejection;
8. deterministic provider/source ordering;
9. UTC and immutable collection boundaries.

## 10. Explicit non-scope

X0-002 does not:

- persist checkpoints;
- acquire data;
- parse provider cursors;
- perform retries;
- delete temporary content;
- implement `/sources/health` HTTP endpoint;
- choose provider-specific health thresholds;
- infer source ownership from content refs.

`X0-003` will expose the accepted summary through localhost-only read access after L0-004 is also Accepted.

## 11. Local verification boundary

Run:

```bash
uv run pytest -q analysis/tests/integration/test_corporate_coverage.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires focused tests, full regression, compileall success, and clean diff check.

## 12. Next action after acceptance

After X0-002 acceptance, X0-003 remains blocked only by `L0-004 — localhost health`. The shortest integration path is therefore to complete L0-004 next rather than start the scheduler lane.
