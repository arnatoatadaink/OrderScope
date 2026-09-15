# OrderScope — D1 Hot-Store Drain Lifecycle Design

Status: **Design proposal — WBS/CP unreflected**
Date: 2026-09-12
Scope: Cloudflare Worker/D1 → Local analysis server retention, export, verification, purge
Target branch: `docs/mermaid-conventions-v0.1`

## 1. Decision summary

Adopt a two-tier data-lifecycle boundary:

- Cloudflare Worker/D1 is the **hot operational store** for bounded acquisition, idempotency, checkpoint/cursor state, recent canonical data, short-term operational evidence, and retry/recovery control.
- The local analysis server is the **long-term analytical history store** for immutable exports, canonical Parquet datasets, catalog/manifest state, quality evidence, Fact/Derived Metric/Interpretation analysis, and historical replay inputs.

D1 should not become the long-term analytical warehouse. Historical data that has crossed a verified export boundary should become eligible for bounded purge after an explicit grace period, while control-state records required for continued acquisition must remain in D1.

The intended lifecycle is:

```text
Provider
  -> Worker acquisition
  -> D1 hot data/state
  -> bounded incremental export
  -> local immutable raw archive
  -> manifest/hash verification
  -> local import + quality acceptance
  -> export acknowledgement
  -> grace period
  -> bounded D1 purge
```

This proposal extends the existing L1 export/import path and PX0 retention/recovery work. It does not authorize remote D1 mutation, live Worker activation, or an unbounded delete operation.

## 2. Existing baseline

The current design already contains the following pieces:

- `L1-001`: D1 export manifest contract with source environment/revision, bounded start/end time, table, row count, size, and SHA-256.
- `L1-002`: immutable fixture/raw import with hash-based idempotency.
- `L1-003`: separately gated real D1 export window, including pause/export/resume/catch-up semantics.
- `L1-004`: deterministic canonical Parquet generation with provenance retention.
- `L1-005`: market-data quality validation.
- `L1-006`: local read-only import/dataset/quality API.
- `I0-003`: provider/source cursor/checkpoint ownership.
- `UWBS-003/PX0-003`: retention and bounded-reprocessing operator path.
- `UWBS-004/PX0-004`: reproducible backup/restore and restore drill.
- Packet D / `UWBS-002`: durable run evidence and restart/recovery boundary.

The missing design is the explicit **Export → Verify → Acknowledge → Grace → Purge** lifecycle that connects those pieces while keeping D1 lightweight.

## 3. Storage-role boundary

### 3.1 D1 — hot operational store

D1 should retain only data needed for near-term acquisition and operational recovery.

Recommended classes:

| Class | Examples | Retention intent |
|---|---|---|
| Current control state | checkpoints, cursors, current lease rows, schema/migrations | retain; not drained as historical data |
| Hot acquired data | normalized market bars, News metadata/query membership | short bounded retention after verified export |
| Acceptance/idempotency evidence | bar acceptance receipts, duplicate/update/conflict linkage | retain through replay/grace boundary; then archive/purge according to policy |
| Operational evidence | scheduler run/job evidence, attempts, digests | medium retention sufficient for incident/restart analysis |
| Exception/conflict state | unresolved conflicts, failed/retryable state, retention blockers | retain until explicitly resolved/archived |

A time-based retention/lookback configuration must not be interpreted as proof that older rows were safely exported or can be deleted.

### 3.2 Local analysis server — long-term history

The local side should own long-term retained analytical history:

```text
immutable raw export
  -> verified export manifest
  -> catalog registration
  -> deterministic Parquet/canonical dataset
  -> quality result
  -> Fact / Derived Metric / Interpretation / Prediction consumers
```

Local history must preserve enough provenance to trace every retained record back to source environment, export generation, bounded window, source table/provider, hash, and accepted local dataset revision.

## 4. Incremental export boundary

Do not repeatedly download all historical D1 rows once the system is in steady state.

Export must be bounded by explicit half-open windows:

```text
[startInclusive, endExclusive)
```

Possible window policies include:

- fixed UTC blocks;
- market-session boundaries (`PRE`, `REGULAR`, `AFTER`);
- close/finalization-aware market windows;
- source-specific bounded windows for News/official data.

The exact cadence is configuration/policy, not a Fact-model constant.

Each export generation should record at minimum:

- export ID / generation;
- source environment and D1 database identity;
- schema/migration revision;
- table/source/provider;
- `startInclusive` / `endExclusive`;
- extraction time;
- row count;
- byte size where available;
- SHA-256 or equivalent content hash;
- first/last source identity/timestamp where useful;
- local destination reference;
- verification/import status.

## 5. Export acknowledgement state machine

Historical D1 rows become purge-eligible only after the local side proves successful custody.

Proposed state machine:

```text
PLANNED
  -> EXPORTED
  -> HASH_VERIFIED
  -> IMPORTED
  -> QUALITY_ACCEPTED
  -> ACKNOWLEDGED
  -> GRACE
  -> PURGE_ELIGIBLE
  -> PURGED
```

Failure/exception paths should include at least:

```text
EXPORT_FAILED
HASH_MISMATCH
IMPORT_FAILED
QUALITY_BLOCKED
PURGE_FAILED
```

No failure state may advance the purge boundary.

## 6. Purge safety gates

Do not implement `download succeeded -> delete immediately`.

A bounded D1 data window is purge-eligible only if all required gates are satisfied. Minimum policy:

```text
exported == true
hash_verified == true
local_imported == true
quality_accepted == true
export_acknowledged == true
checkpoint/control boundary is safely beyond the exported window where applicable
grace_period_elapsed == true
no unresolved retention blocker/conflict references the candidate rows
```

Deletion must always be bounded by explicit table/source/time/identity predicates. No `delete all old data` operation should exist without a concrete reviewed retention plan.

The operator must be able to run a dry-run that reports candidate row count/window before mutation.

## 7. Checkpoint and control-state rules

`I0-003` remains the source of truth for provider/source acquisition progress.

The following must **not** be inferred from local archive state alone:

- current acquisition cursor;
- latest complete-through boundary;
- retry-not-before state;
- current lease ownership;
- current schema/migration readiness.

Archive success must not delete the live checkpoint merely because equivalent historical data exists locally.

For restart/recovery, use:

- D1 checkpoint/cursor for acquisition truth;
- durable run/job evidence for what execution occurred;
- export manifest/ack state for historical custody;
- local catalog/hash/quality evidence for analytical-retention truth.

These are related but not interchangeable sources of truth.

## 8. Recommended retention classes

Initial values should remain configurable and non-normative until measured in Canary/full-v0.1 operation.

Suggested policy classes:

| Data class | Initial design intent |
|---|---|
| Minute/market canonical rows in D1 | short hot window; export frequently; purge after ACK + grace |
| News metadata/query membership | short-to-medium hot window; preserve enough for duplicate/retry observation |
| News body | not a Worker durable baseline; successful temporary content deleted after extraction; exceptions bounded by existing max-retention policy |
| Acceptance receipts | keep through export/replay grace; archive enough provenance before purge |
| Conflicts / unresolved exceptions | retain until resolved or explicitly archived |
| scheduler run/job evidence | medium window such as days/weeks, then archive/purge by operations policy |
| digest history | bounded operational window |
| checkpoints/cursors/current lease | persistent current state; not historical drain targets |
| schema/migrations/config identity | persistent |

Do not freeze durations such as `24h`, `7d`, or `30d` from this report alone. Use measured D1 size, rows read/written, incident-response needs, and replay requirements to set policy.

## 9. D1 read/write cost implications

This lifecycle is intended to reduce both D1 retained size and repeated historical scans.

Key rules:

1. Prefer indexed bounded-window export queries over full-table scans.
2. Store export high-water marks/ack state so already-exported historical ranges are not repeatedly scanned.
3. Index retention/recovery predicates such as status/time where the measured query plan justifies it.
4. Purge in bounded batches so one maintenance run cannot consume the entire invocation D1 budget.
5. Count export/ack/purge operations in the same operational budget model rather than treating maintenance as free.
6. Measure actual D1 metadata (`rows_read`, `rows_written` where available) separately from OrderScope invocation statement budgeting.

The Worker should remain optimized for acquisition correctness and bounded operation, not historical analytical querying.

## 10. Failure semantics

### Local analysis server unavailable

- Worker acquisition may continue while D1 retention headroom remains.
- Export backlog becomes visible.
- Purge does not advance.
- An explicit threshold may later block or degrade acquisition if retention headroom becomes unsafe; that threshold requires separate design/acceptance.

### Export succeeded but local verification failed

- keep D1 source rows;
- mark generation failed/blocked;
- allow bounded retry;
- do not silently create a new purge watermark.

### Local import succeeded but D1 purge failed

- local copy remains valid;
- D1 rows remain duplicates until bounded purge retry;
- idempotent purge should make retry safe.

### D1 row changed after export

Where mutable/update semantics exist, the export contract must detect revisions or use immutable identity/revision semantics. A prior ACK must not hide a later accepted revision.

## 11. Operator and automation boundary

Initial implementation should be operator-controlled / CLI-oriented.

Required capabilities should eventually include:

- inspect export backlog;
- plan bounded export;
- execute bounded export;
- verify hash/row count;
- register local import/quality acceptance;
- acknowledge a generation;
- dry-run purge candidates;
- execute bounded purge;
- retry failed export/purge;
- inspect retained control-state separately from purge candidates.

Do not expose arbitrary retention mutation or replay through a public HTTP endpoint.

Automatic scheduled drain may be introduced only after the bounded CLI path is accepted and recovery behavior is proven.

## 12. Relationship to Packet D/E/F

- **Packet D / UWBS-002** supplies durable run/job evidence and safe restart semantics. It should not become archive/checkpoint truth.
- **Packet E / UWBS-003** should be expanded during WBS design from a generic retention CLI into the operator boundary for bounded export/ack/purge/replay actions.
- **Packet F / UWBS-004** remains backup/restore. An export archive is not automatically a complete disaster-recovery backup; backup generations must include the metadata/catalog/schema required for restoration.

This report therefore adds missing lifecycle tasks rather than declaring UWBS-003/004 covered.

## 13. Proposed WBS-unreflected decomposition

### UWBS-023 — Define D1 hot-store / local-history retention contract

Define data classes, authoritative stores, purge eligibility, retention blockers, and configurable retention/grace policy without treating `ACQUISITION_RETENTION_MINUTES` as automatic deletion proof.

### UWBS-024 — Implement bounded incremental D1 export and custody manifest

Implement source/table/time-bounded export with generation ID, row count, hash, schema/source revision, idempotent retry, and local immutable destination registration. Avoid steady-state full-history scans.

### UWBS-025 — Implement export acknowledgement and bounded D1 purge lifecycle

Implement the explicit verification/ACK/grace state machine and operator dry-run/execute purge. Purge only ACKed bounded data and never acquisition control truth.

### UWBS-026 — Add drain lifecycle acceptance/operations tests

Test Local unavailable, export retry, hash mismatch, import/quality block, duplicate export, update after export, purge retry, checkpoint preservation, stale/unresolved retention blocker, and bounded-budget behavior.

## 14. Acceptance direction

The design should not be considered production-ready until fixtures prove at least:

1. no source row is purged before verified local custody;
2. repeated export is idempotent;
3. hash mismatch blocks ACK/purge;
4. a locally accepted generation survives D1 purge and remains queryable through the local dataset/catalog path;
5. checkpoint/cursor truth survives historical purge;
6. an unavailable local server grows backlog rather than deleting data;
7. purge retry is bounded and idempotent;
8. updated/revised records after an earlier export are not lost;
9. retention/backlog state is observable;
10. backup/restore remains separately testable from normal drain/archive operation.

## 15. Non-goals

This proposal does not:

- authorize `L1-003` real-D1 export without its gate;
- authorize live Worker mutation;
- define a permanent retention duration;
- turn Local archive state into acquisition checkpoint truth;
- make R2 or another cloud archive mandatory;
- treat export as equivalent to full backup;
- add unbounded replay or purge;
- change Fact / Derived Metric / Interpretation / Prediction boundaries.

## 16. Planning conclusion

The target architecture should be:

```text
Cloudflare Worker + D1
  = low-latency bounded acquisition + recent hot state + operational control

Local analysis server
  = durable historical custody + Parquet/catalog + quality + analysis
```

The missing engineering boundary is not another generic retention timer. It is a verifiable custody transfer protocol:

```text
Export -> Verify -> Import/Quality -> Acknowledge -> Grace -> Purge
```

Formal WBS/CP incorporation should decompose this protocol while preserving `I0-003` checkpoint ownership, Packet D restart evidence, UWBS-003 operator mutation boundaries, and UWBS-004 backup/restore responsibilities.
