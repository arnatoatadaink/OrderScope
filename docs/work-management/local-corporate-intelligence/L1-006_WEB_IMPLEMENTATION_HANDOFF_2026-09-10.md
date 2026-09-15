# OrderScope — L1-006 Web Implementation Handoff

Status: **Accepted**
Date: 2026-09-10
Task: `L1-006`
Parent WBS: `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-004`, Accepted fixture-path `L1-005`

## 1. WBS completion target

Provide read-only localhost API routes:

```text
/imports
/coverage/latest
/datasets
/quality/latest
```

No mutation/job execution is added to HTTP.

## 2. Implementation

Changed:

- `analysis/app/orderscope_local/local_api/read_api.py`

Added focused tests:

- `analysis/tests/local_api/test_import_dataset_api.py`

`LocalReadSnapshot` now accepts immutable tuples of already-accepted market import state:

- `RawImportResult`
- `CanonicalBarDataset`
- `MarketDataQualityReport`

The API serializes these accepted descriptors only. It does not read raw SQL bytes, Parquet rows, provider responses, credentials, or unrestricted filesystem paths.

## 3. Route behavior

### `/imports`

Returns sanitized immutable raw-import catalog descriptors:

- status
- manifest ID
- SHA-256
- relative raw path
- registered timestamp

### `/datasets`

Returns canonical dataset descriptors:

- schema version
- manifest ID
- source artifact hash
- row count
- relative dataset path
- Parquet hash

No dataset body/rows are exposed.

### `/quality/latest`

Returns the latest accepted `MarketDataQualityReport` supplied by the snapshot builder, including issue metadata but no underlying data body.

L1-005's quality contract has no acceptance timestamp. Therefore the read API does **not** fabricate recency from manifest IDs. The snapshot builder owns accepted ordering and places its latest accepted report last.

### `/coverage/latest`

Derives the latest market-data coverage summary from the latest accepted quality report and matching dataset descriptor:

- dataset manifest ID
- row count
- symbols
- expected grid points
- issue count
- pass/fail
- matching dataset relative path when available
- Parquet SHA-256

If no accepted quality report exists, both latest endpoints return `null` state rather than fabricating coverage/quality.

## 4. Safety boundary

Preserved:

- literal `127.0.0.1` binding through the existing local API contract;
- GET-only/read-only HTTP;
- no import start, quality execution, scheduler start, retention mutation, provider calls, D1 action, or Worker mutation;
- no credentials/provider bodies/raw news bodies in responses;
- no arbitrary filesystem-path query interface.

`L1-003 / SMOKE-007` remains separately gated. L1-006 works with accepted fixture-path descriptors and does not imply real-D1 acceptance.

## 5. Focused acceptance cases

`analysis/tests/local_api/test_import_dataset_api.py` contains 7 L1-006-specific cases. The acceptance command also includes the existing read API regression tests.

## 6. Local verification evidence

User-reported local verification:

```text
focused API command -> 21 passed
full pytest suite   -> 468 passed
compileall          -> success / no errors
git diff --check    -> clean / no findings
```

The focused command includes the 7 L1-006-specific cases plus the existing `test_read_api.py` regression coverage.

## 7. Acceptance result

`L1-006` is **Accepted** for the fixture-path read API boundary.

This completes the L1 fixture-path read surface but does not complete `L1-003` real-D1 export, which remains separately gated behind `SMOKE-007`.
