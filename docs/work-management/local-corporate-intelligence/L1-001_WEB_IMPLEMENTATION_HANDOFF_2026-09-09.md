# OrderScope — L1-001 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `L1-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-005`

## 1. Local acceptance evidence

User-reported local verification after the Web implementation:

```text
focused L1-001 tests -> 8 passed
full pytest suite    -> 360 passed
git diff --check     -> clean / no findings
```

The L0-005 dependency was already Accepted before this cycle.

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

L1-002 uses this identity and the artifact SHA-256 to make fixture/raw-dump registration idempotent; L1-001 itself does not persist anything.

## 7. Storage-neutral serialization

`to_record()` emits scalar-only values (`str` / `int`) suitable for the accepted storage-neutral contract style.

`decode_d1_export_manifest()` requires the exact v0.1 field set, restores UTC timestamps, reconstructs the immutable manifest, and verifies the supplied `manifest_id`.

## 8. Acceptance conclusion

The WBS completion condition is satisfied and L1-001 is safe as a downstream prerequisite.

Lane state after acceptance:

```text
L0-005 Accepted
L1-001 Accepted
L1-002 Provisional result — Web implementation complete / local test pending
L1-003 Blocked on separate SMOKE-007 change window
L1-004 waits for L1-002 acceptance
L1-005 waits for L1-004
```
