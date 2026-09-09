# OrderScope — L1-005 Web Implementation Handoff

Status: **Provisional result — fixture-path implementation complete / local test pending**
Date: 2026-09-09
Task: `L1-005`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted fixture-path `L1-004`

## 1. Local acceptance carried into this cycle

L1-004 fixture-path acceptance is complete from user-reported local evidence:

```text
focused L1-004 tests -> 11 passed
full pytest suite    -> 372 passed
git diff --check     -> clean / no findings
```

Real D1 promotion remains independently gated by `L1-003` / `SMOKE-007`.

## 2. WBS completion boundary

L1-005 validates the canonical market dataset for:

- schema/version integrity;
- dataset row count;
- canonical bar identity duplicate/conflict;
- OHLCV constraints;
- receipt ordering;
- gaps against an explicit session grid;
- off-grid bars;
- row provenance;
- Parquet content hash.

It reports quality issues; it does not repair, interpolate, rewrite, or silently discard bad bars.

## 3. Changed/added files

- `analysis/app/orderscope_local/market_import/quality.py`
- `analysis/app/orderscope_local/market_import/__init__.py`
- `analysis/tests/market_import/test_market_data_quality.py`

## 4. Versioned quality contract

Schema version:

```text
market-data-quality-v0.1
```

Issue taxonomy:

```text
schema
row_count
identity_duplicate
identity_conflict
ohlcv
receipt_order
missing_grid_point
off_grid_point
provenance
dataset_hash
```

`MarketDataQualityReport.passed` is true only when the immutable issue tuple is empty.

## 5. Session-grid boundary

L1-005 intentionally does not embed an exchange holiday calendar or infer shortened sessions.

Callers provide one or more explicit `SessionWindow` values:

```text
name
start UTC
end UTC
cadence
```

Each window defines expected half-open grid points:

```text
start, start+cadence, ... < end
```

Windows must be UTC, positive, cadence-aligned, and non-overlapping.

This keeps market-calendar/provider policy replaceable. A future calendar source can generate `SessionWindow` values without changing quality semantics.

## 6. Gap and off-grid semantics

For every expected symbol and session-grid point:

- absent bar -> `missing_grid_point`;
- bar outside all supplied grid points -> `off_grid_point`.

Missing bars are never synthesized or interpolated.

An expected symbol with no rows produces missing-grid issues for its full supplied session grid.

## 7. Dataset integrity / provenance

The quality pass rechecks the persisted Parquet rather than trusting L1-004 construction alone.

It verifies:

- actual Parquet SHA-256 against `CanonicalBarDataset.parquet_sha256`;
- expected canonical field order/types and Arrow schema metadata;
- actual row count against the dataset descriptor;
- unique `(symbol, bar_time)` identity;
- OHLC envelope and non-negative volume;
- `receipt_time >= bar_time`;
- row `source_manifest_id` and `source_artifact_sha256` against the dataset descriptor;
- nonblank source environment/revision provenance.

A duplicate row and a conflicting row sharing the same identity receive different issue kinds.

## 8. Failure/repair policy

The quality layer is observational and fail-visible:

- no row mutation;
- no winner selection for conflicts;
- no interpolation;
- no timestamp snapping;
- no automatic holiday/session inference;
- no source-provenance rewrite.

Downstream code can refuse a failed report or expose its issues, but L1-005 does not erase the evidence.

## 9. Focused fixtures encoded

The focused module currently contains 12 tests covering:

1. fully valid fixture dataset passes;
2. one missing grid point is reported;
3. off-grid bar is reported;
4. Parquet content-hash tamper is observable;
5. schema drift is reported;
6. duplicate and conflicting identities are distinguished;
7. OHLCV and receipt ordering are revalidated after Parquet mutation;
8. row provenance must match dataset descriptor;
9. an expected symbol with no rows produces a full-grid gap;
10. invalid session clock/cadence is rejected;
11. overlapping session windows are rejected;
12. repeated evaluation of identical dataset/grid is deterministic.

## 10. Explicit non-scope

L1-005 fixture implementation does not:

- execute or approve real D1 export;
- define NYSE/Nasdaq holiday calendars;
- repair or interpolate market data;
- expose read-only APIs;
- schedule imports;
- integrate the unified timeline.

`L1-003` remains the real-data gate. `X0-001` may begin only after fixture L1-005 acceptance under the current runtime plan.

## 11. Local verification boundary

Run:

```bash
uv run pytest -q analysis/tests/market_import/test_market_data_quality.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires focused tests, full regression, compileall success, and clean diff check.

## 12. Lane state

```text
L0-005 Accepted
L1-001 Accepted
L1-002 Accepted
L1-003 Blocked on separate SMOKE-007 change window
L1-004 Accepted — fixture path
L1-005 Provisional result — local verification pending
X0-001 waits for L1-005 fixture acceptance
```

## 13. Next action after acceptance

After L1-005 fixture acceptance, reconcile the X0-001 gate. Under the current WBS dependencies, I0-005, E0-007, N1-005, and O0-005 are already Accepted, so fixture L1-005 acceptance opens the implementation path for `X0-001 — unified timeline query`. Real-data promotion remains separately gated by L1-003.
