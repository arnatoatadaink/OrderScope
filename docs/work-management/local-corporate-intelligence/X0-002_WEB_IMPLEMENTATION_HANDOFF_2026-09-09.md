# OrderScope — X0-002 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `X0-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `I0-003` plus adapter checkpoint/lifecycle state

## 1. Local acceptance evidence

User-reported local verification:

```text
focused X0-002 tests -> 9 passed
full pytest suite    -> 407 passed
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

The cursor remains opaque. Lag is `as_of - last_success_at` and remains `None` when no completed checkpoint exists.

## 6. As-of behavior

Only checkpoints whose `observed_at <= as_of` are visible. The resulting source summaries are deterministically ordered by `(provider_key, source_key)`.

## 7. Retention-pending boundary

`TemporaryContent` does not contain provider/source identity. Callers use `RetentionObservation(source_key, content)` to associate lifecycle records explicitly.

Visible non-deleted content contributes to:

- `retention_pending_count`;
- `retention_overdue_count` where `expires_at <= as_of`;
- earliest `retention_next_due_at`.

Deleted content is not pending and future-captured lifecycle records are excluded.

## 8. Failure/secret boundary

X0-002 surfaces only sanitized checkpoint error fields and never provider exception bodies, credentials, HTTP bodies, raw news content, or deletion bodies.

## 9. Focused fixtures accepted

The accepted 9-test module covers complete success/lag, partial/error state, future exclusion, retention pending/overdue, explicit source scope, deterministic ordering, and UTC/immutable boundaries.

## 10. Next action

`X0-003` now waits only for `L0-004 — localhost health`. Complete and accept L0-004 next.
