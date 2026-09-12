# R0 D1 Drain Local Acceptance — 2026-09-13

Status: **Accepted locally through R0-009**
Scope: D1 hot-store retention, bounded export/custody, acknowledgement/purge eligibility, and failure fixtures

## Boundary

This acceptance is local/fixture only. It does **not** authorize remote Cloudflare D1 export, deletion/purge, Worker deployment, Cron mutation, scheduler activation, or another live Canary window.

The accepted local sequence is:

```text
R0-006 retention contract
  -> R0-007 bounded export + custody
  -> R0-008 acknowledgement / purge-eligibility lifecycle
  -> R0-009 failure and recovery fixtures
```

`PURGED` remains outside the local acceptance boundary. The lifecycle may reach `PURGE_ELIGIBLE`; actual remote mutation requires a separately authorized change window and remote evidence.

## R0-006 — D1 retention contract

Accepted local contract:

- classifies reviewed D1 tables as current control, hot data, idempotency evidence, operational evidence, or unresolved blocker;
- current-control truth is never purge eligible;
- all non-control purge decisions require grace;
- custody acknowledgement, quality acceptance, replay horizon, and resolution are required according to table policy;
- unclassified tables fail closed.

Representative boundary:

```text
coverage_checkpoint      -> CURRENT_CONTROL -> never purge
normalized_bar           -> HOT_DATA -> custody + quality + grace
bar_acceptance_receipt   -> IDEMPOTENCY_EVIDENCE -> custody + quality + replay horizon + grace
bar_conflict             -> UNRESOLVED_BLOCKER -> custody + quality + replay horizon + resolution + grace
```

Implementation:

- `src/d1-retention.ts`
- `src/d1-retention.test.ts`

Acceptance evidence at the R0-006 boundary: focused 6 passed; full TypeScript 167 passed; full Python 537 passed; compileall succeeded.

## R0-007 — bounded export and custody

Accepted local/fixture behavior:

- only explicitly registered tables may be exported;
- export windows are explicit non-empty half-open UTC windows;
- rows are deterministically ordered and serialized as canonical UTF-8 NDJSON;
- existing `D1ExportManifest` remains the source artifact manifest;
- `D1CustodyManifest` binds source database identity, export manifest identity, and safe relative artifact placement;
- artifact byte size and SHA-256 must exactly match before custody is accepted;
- duplicate export of identical source/window content yields the same artifact and identities;
- unknown/unregistered tables fail closed;
- no remote Cloudflare D1 access or mutation is performed.

Implementation:

- `analysis/app/orderscope_local/storage/d1_custody.py`
- `analysis/app/orderscope_local/storage/d1_bounded_export.py`
- `analysis/tests/storage/test_d1_custody.py`
- `analysis/tests/storage/test_d1_bounded_export.py`

Measured acceptance evidence included focused 22 passed and full Python 551 passed with compileall success.

## R0-008 — acknowledgement and purge-eligibility lifecycle

Accepted local lifecycle:

```text
PLANNED
  -> EXPORTED
  -> HASH_VERIFIED
  -> IMPORTED
  -> QUALITY_ACCEPTED
  -> ACKNOWLEDGED
  -> GRACE
  -> PURGE_ELIGIBLE
  -> PURGED [remote-only; blocked locally]
```

Properties:

- skipped/reverse transitions fail closed;
- `QUALITY_ACCEPTED` and `ACKNOWLEDGED` establish their evidence only through lifecycle transitions;
- replay-horizon and conflict-resolution evidence are carried explicitly;
- R0-006 `evaluateD1PurgeEligibility` is reused rather than duplicating purge rules;
- `PURGED` cannot be reached through the local lifecycle API and requires separately authorized remote mutation evidence.

Implementation:

- `src/d1-drain-lifecycle.ts`
- `src/d1-drain-lifecycle.test.ts`

Measured acceptance evidence: focused 13/13 passed; full TypeScript 174/174 passed; TypeScript typecheck passed; full Python 551/551 passed; compileall succeeded.

## R0-009 — failure/recovery acceptance fixtures

Accepted failure boundaries cover:

- export failure does not fabricate a manifest;
- hash mismatch prevents custody acknowledgement;
- quality failure cannot advance to acknowledgement/purge eligibility;
- duplicate deterministic export preserves artifact/manifest/generation identity;
- local custody artifact remains readable after the fixture source rows are removed;
- current-control tables remain non-purgeable even if other evidence is present;
- failed purge attempts preserve the `PURGE_ELIGIBLE` state for a separately authorized retry;
- D1 query budget fails closed before issuing an over-budget statement.

Implementation includes:

- `src/r0-009-drain-failure.test.ts`
- `analysis/tests/storage/test_d1_drain_failure_fixture.py`

Initial R0-009 focused evidence: TypeScript 17/17 passed; Python storage-focused 18/18 passed; full Python 555/555 passed.

## Integration fixture hardening discovered during R0-009 acceptance

Two pre-existing non-deterministic integration-test conditions were exposed during full-suite acceptance and were treated as fixture defects rather than silently ignored.

### Lease-contention fixture

The original overlap fixture used a fixed 500 ms provider delay. Under full-suite load, the first scheduled tick could complete and release its lease before the second tick reached lease acquisition, producing `SUCCEEDED` instead of the intended `SKIPPED_LOCKED` observation.

The local fixture was hardened to use an explicit boolean release barrier. The first provider call remains blocked until the test has observed the second tick's locked outcome and explicitly releases the provider. This avoids a timing assumption and also avoids cross-request Promise resolution, which Miniflare rejects as unsafe.

Measured stability after repair: the targeted lease-contention test passed once immediately and then passed 5 additional consecutive runs (6/6 total).

### Provider-diagnostic sanitization fixture

The existing public-digest test rejected the bare substring `503`. The digest also contains a random scheduler `runId`, so an unrelated UUID containing the digits `503` could cause a false failure.

The fixture was narrowed to reject meaningful provider diagnostic material, including credentials, `upstream-provider-body`, and the diagnostic phrase `503 upstream-provider-body`, rather than the bare numeric substring.

Measured stability after repair: targeted provider-digest test passed 5/5 consecutive runs.

## Final measured acceptance

Final full-suite evidence after the fixture hardening:

```text
TypeScript full suite  -> 178 / 178 passed
TypeScript typecheck   -> passed
Python full suite      -> 555 / 555 passed
Python warnings        -> 2 existing dependency deprecation warnings
Python compileall      -> passed
```

The two Python warnings are the previously known FastAPI/Starlette/AnyIO test-client dependency deprecations and are not R0 drain failures.

## Disposition

- `R0-006`: **Accepted locally**
- `R0-007`: **Accepted locally / fixture bounded export + custody**
- `R0-008`: **Accepted locally through PURGE_ELIGIBLE**
- `R0-009`: **Accepted locally**
- remote D1 export/purge: **Not authorized**
- remote Worker/Cron mutation: **Not authorized**
- actual `PURGED` transition: **Blocked pending separately authorized remote change window**

Next planning work should use this document as the detailed acceptance record and keep remote activation/deletion gates separate from local contract completion.
