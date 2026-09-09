# OrderScope — L1-004 Web Implementation Handoff

Status: **Provisional result — fixture-path implementation complete / local test pending**
Date: 2026-09-09
Task: `L1-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L1-002`; real-data completion separately depends on `L1-003`

## 1. Local acceptance carried into this cycle

`L1-002` is Accepted from user-reported local evidence:

```text
storage migration tests -> 7 passed
focused L1-002 tests    -> 8 passed
full pytest suite       -> 368 passed
compileall              -> success
git diff --check        -> clean / no findings
```

## 2. WBS completion boundary

L1-004 must produce a deterministic-order canonical bar dataset while preserving bar/receipt provenance. This cycle implements the fixture path only. It does not claim real D1 completion while `L1-003` remains behind the separate SMOKE-007 change window.

## 3. Changed/added files

- `analysis/app/orderscope_local/market_import/canonical_bars.py`
- `analysis/app/orderscope_local/market_import/__init__.py`
- `analysis/tests/market_import/test_canonical_bar_dataset.py`

## 4. Input boundary

`generate_fixture_canonical_bars()` accepts an Accepted L1-001 `D1ExportManifest`, exact fixture artifact bytes, and a local dataset root.

Before parsing, it verifies:

```text
len(artifact) == manifest.byte_size
sha256(artifact) == manifest.sha256
```

The UTF-8 SQL fixture is loaded only into an isolated in-memory SQLite database. The manifest table must exist with the exact fixture-bar columns:

```text
symbol
bar_time
open
high
low
close
volume
receipt_time
```

No provider-specific D1 CLI JSON or credential field crosses this boundary.

## 5. Canonical bar normalization

Each bar is validated for:

- bounded canonical symbol;
- UTC bar/receipt timestamps;
- `bar_time` within the manifest half-open window;
- receipt time not earlier than bar time;
- finite non-negative OHLC values;
- valid OHLC envelope;
- non-negative integer volume.

Rows are sorted deterministically by:

```text
(symbol, bar_time, receipt_time)
```

Duplicate `(symbol, bar_time)` keys are rejected. Conflicting rows for the same key are also rejected rather than selecting a winner.

## 6. Parquet / provenance boundary

The output Parquet carries canonical values plus:

```text
source_manifest_id
source_artifact_sha256
source_environment
source_revision
```

The Arrow schema metadata records:

```text
orderscope_schema_version = canonical-bar-dataset-v0.1
```

Output path is content/manifest-addressed:

```text
canonical/<manifest_id>.parquet
```

The returned `CanonicalBarDataset` contains only schema/version, manifest identity, source artifact hash, row count, relative path, and Parquet SHA-256. It does not return raw SQL or parsed row objects.

## 7. Determinism / idempotency

Generating from the same manifest and artifact reproduces the same path, metadata, row order, and expected Parquet bytes in the same runtime/library version. If the target dataset path already exists with different bytes, generation fails closed rather than overwriting silently.

## 8. Focused fixtures encoded

The focused module currently collects 12 cases (8 test functions including a 4-case parametrization) covering:

1. deterministic ordering and source provenance columns;
2. same-input dataset identity/byte replay;
3. manifest size/hash and row-count enforcement;
4. exact fixture table schema / manifest table existence;
5. out-of-window, invalid OHLC, negative volume, and receipt-before-bar rejection;
6. duplicate/conflicting bar-key rejection;
7. existing-path tamper rejection;
8. absence of raw SQL/credential fields in result/Parquet schema.

## 9. Explicit non-scope

L1-004 fixture path does not:

- execute or approve the remote D1 export;
- claim real-data completion;
- define exchange session grids or holiday calendars;
- perform gap/conflict/session quality reporting;
- expose dataset APIs;
- schedule recurring generation.

`L1-005` owns market-data quality checks. `L1-003` remains the real D1 change-window gate.

## 10. Local verification boundary

Run:

```bash
uv run pytest -q analysis/tests/market_import/test_canonical_bar_dataset.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires focused fixture tests, full regression, compileall success, and clean diff check.

## 11. Lane state

```text
L0-005 Accepted
L1-001 Accepted
L1-002 Accepted
L1-003 Blocked on separate SMOKE-007 change window
L1-004 Provisional result — fixture path local test pending
L1-005 waits for L1-004 fixture acceptance
```

## 12. Next action after acceptance

Proceed to `L1-005 — market-data quality checks` on the fixture dataset. Keep real-D1 promotion separately gated by L1-003.
