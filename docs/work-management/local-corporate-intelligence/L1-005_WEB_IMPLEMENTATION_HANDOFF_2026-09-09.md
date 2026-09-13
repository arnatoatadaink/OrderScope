# OrderScope — L1-005 Web Implementation Handoff

Status: **Accepted — fixture-path local verification complete**
Date: 2026-09-09
Task: `L1-005`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted fixture-path `L1-004`

## 1. Local acceptance evidence

User-reported local verification:

```text
focused L1-005 tests -> 12 passed
full pytest suite    -> 391 passed
git diff --check     -> clean / no findings
```

The fixture-path completion condition is satisfied. Real D1 promotion remains independently gated by `L1-003` / `SMOKE-007`.

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

L1-005 intentionally does not embed an exchange holiday calendar or infer shortened sessions. Callers provide explicit UTC `SessionWindow` values with name/start/end/cadence. Windows are positive, cadence-aligned, and non-overlapping.

## 6. Gap / conflict / repair policy

- absent expected bar -> `missing_grid_point`;
- bar outside supplied grid -> `off_grid_point`;
- duplicate identity and conflicting identity are distinct issues;
- no interpolation, timestamp snapping, winner selection, or source rewrite occurs.

## 7. Dataset integrity / provenance

The quality pass rechecks persisted Parquet SHA-256, schema metadata, row count, `(symbol, bar_time)` identity, OHLCV, receipt ordering, and row-level manifest/artifact provenance.

## 8. Acceptance result

Focused tests **12 passed** and the full local suite **391 passed** with a clean `git diff --check`. L1-005 is therefore an Accepted downstream prerequisite for the fixture path.

## 9. Remaining external gate

`L1-003` remains separately Blocked on the approved remote D1 / `SMOKE-007` change window. Fixture acceptance must not be described as real-D1 acceptance.

## 10. Next action

The explicit `X0-001` dependencies are now satisfied on the fixture path:

```text
L1-005 Accepted
I0-005 Accepted
E0-007 Accepted
N1-005 Accepted
O0-005 Accepted
```

Proceed to `X0-001 — unified timeline query` while keeping real-data promotion separately gated by L1-003.
