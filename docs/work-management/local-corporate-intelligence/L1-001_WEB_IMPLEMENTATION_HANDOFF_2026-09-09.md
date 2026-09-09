# OrderScope — L1-001 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `L1-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-005`

## 1. Local acceptance carried into this cycle

GitHub HEAD `2fd726b9ae40f16aaca836e0661d7f53c4b0a045` contains the user-completed L0-005 SQLite migration foundation.

User-reported local acceptance evidence:

```text
focused L0-005 tests -> 7 passed
full pytest suite    -> 352 passed
compileall           -> success
git diff --check     -> clean
upstream diff        -> 0 / 0
```

The branch commit also updates the authoritative tracker to mark L0-005 Accepted and L1-001 Ready.

## 2. WBS completion boundary

L1-001 defines the immutable D1 export manifest contract. The manifest schema includes:

- source environment;
- source revision;
- half-open UTC start/end time;
- exported table name;
- row count;
- byte size;
- exact SHA-256 of the exported artifact.

It does not perform export, import, SQL parsing, remote D1 mutation, or market-data quality checks.

## 3. Changed/added files

- `analysis/app/orderscope_local/market_import/__init__.py`
- `analysis/app/orderscope_local/market_import/d1_manifest.py`
- `analysis/tests/market_import/test_d1_export_manifest.py`

## 4. Versioned manifest contract

Schema version:

```text
d1-export-manifest-v0.1
```

`D1ExportManifest` is immutable and provider-neutral at the local Core boundary.

Fields:

```text
source_environment
source_revision
window_start
window_end
table_name
row_count
byte_size
sha256
schema_version
```

The contract intentionally does not contain raw SQL rows, D1 CLI output, credentials, provider response payloads, or local filesystem paths.

## 5. Window semantics

`window_start` and `window_end` must both be UTC-aware instants and define a non-empty half-open interval:

```text
[window_start, window_end)
```

No timezone coercion or inferred local time is performed.

## 6. Artifact identity / idempotency handoff

`manifest_id` is a deterministic SHA-256 identity derived from all normalized manifest fields, including the exported artifact SHA-256.

Repeated registration of the exact same manifest reproduces the same ID. A changed artifact hash, source revision, window, table, row count, or size changes the manifest identity.

L1-002 may use this identity and the artifact SHA-256 to make fixture/raw-dump registration idempotent; L1-001 itself does not persist anything.

## 7. Storage-neutral serialization

`to_record()` emits scalar-only values (`str` / `int`) suitable for the accepted storage-neutral contract style.

`decode_d1_export_manifest()`:

- requires the exact v0.1 field set;
- restores UTC timestamps;
- reconstructs the immutable manifest;
- verifies that the supplied `manifest_id` matches reconstructed content.

Unknown extra fields such as local `path` are rejected rather than silently accepted.

## 8. Validation boundary

The contract rejects:

- empty/reversed windows;
- non-UTC timestamps;
- invalid table identifiers;
- blank/unbounded source environment or revision;
- negative or boolean row/byte counts;
- uppercase, malformed, or non-64-character SHA-256 values;
- missing/extra serialized fields;
- manifest identity tampering.

## 9. Focused fixtures encoded

The focused module currently contains 8 tests covering:

1. required manifest fields and half-open window;
2. deterministic manifest identity and artifact-hash sensitivity;
3. scalar-only record round-trip and identity verification;
4. empty/reversed/non-UTC window rejection;
5. strict environment/revision/table/hash validation;
6. non-negative integer count/size validation;
7. missing/extra/wrong-typed record rejection;
8. explicit absence of rows/SQL/path/credentials/API-key fields.

## 10. Explicit non-scope

L1-001 does not:

- execute a D1 export;
- approve or run the `SMOKE-007` change window;
- read SQL dump rows;
- persist imported raw data;
- create Parquet datasets;
- perform OHLCV/session/gap quality checks;
- expose an API.

`L1-002` owns fixture dump import/idempotent registration. `L1-003` remains the separately gated real D1 export. `L1-004/L1-005` own canonical dataset and market-data quality.

## 11. Local verification boundary

Before promoting L1-001 to Accepted, run:

```bash
uv run pytest -q analysis/tests/market_import/test_d1_export_manifest.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires focused tests, full regression, compileall success, and clean diff check.

## 12. Lane state

```text
L0-005 Accepted
L1-001 Provisional result — local test pending
L1-002 waits for L1-001 acceptance
L1-003 Blocked on separate SMOKE-007 change window
L1-004 waits for L1-002 fixture path
L1-005 waits for L1-004
```

## 13. Next action after acceptance

After L1-001 acceptance, proceed to `L1-002 — fixture dump importer`: register a small SQL fixture as immutable raw data, verify the manifest/artifact hash, and make reimport of the same hash idempotent without treating the real D1 export gate as a blocker.
