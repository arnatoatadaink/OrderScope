# v0.1.6 UWBS-074 implementation progress — 2026-10-01

Status: **ACCEPTED**

## Dependency base

UWBS-074 is implemented on top of accepted UWBS-073 source head:

```text
UWBS-073 head = d602de71a93b8ac8c8877c0d0114d66553046555
```

Development branch:

```text
codex/uwbs-074-derivatives-archive
```

Accepted source head:

```text
709db5b94e2d7adcea8ce5566da8e3028dd420ee
```

## Implemented scope

```text
analysis/app/orderscope_local/crypto_archive/
  __init__.py
  models.py
  archive.py
analysis/tests/crypto_archive/
  test_crypto_archive.py
```

Implemented archive semantics:

- deterministic canonical JSON envelope for `CryptoDerivativeObservation`;
- SHA-256 content hash for reproducibility;
- stable snapshot key scoped by venue / instrument / observed timestamp;
- idempotent identical replay detection;
- explicit revision replacement only when the incoming accepted record is not older;
- deterministic archive ordering;
- cadence-based missing-snapshot detection;
- adjacent missing points coalesced into catch-up windows;
- explicit catch-up lifecycle: `PENDING -> RUNNING -> COMPLETE` or `UNRECOVERABLE`;
- terminal catch-up states cannot be reopened silently.

## Validation history

The first local validation attempt failed:

```text
focused: 7 failed, 3 passed
full:    7 failed, 687 passed, 1 warning
```

Two independent defects were identified and corrected.

### Defect 1 — invalid test fixture chronology

The fixture defaulted to:

```text
observed_at  = t
available_at = t + 5s
accepted_at  = t + 1s
```

This violated the already-accepted UWBS-068 contract:

```text
observed_at <= available_at <= accepted_at
```

The default `accepted_offset` was corrected to `10` seconds. This was a test-fixture defect, not a relaxation of the UWBS-068 contract.

Fix commit:

```text
bda9950841403f948d386b0d005c4de03bb22f70  Fix UWBS-074 archive test observation timestamps
```

### Defect 2 — payload JSON incorrectly treated as a bounded identifier

`SnapshotEnvelope.__post_init__` reused the identifier validator `_text`, which limits strings to 256 characters, for `payload_json`. A canonical serialized derivatives snapshot is expected to exceed that length and is archive content, not an identifier.

The fix separates validation:

- identifiers / labels remain non-blank and <= 256 characters;
- `payload_json` must be a non-blank string but is not subject to the identifier length bound.

Storage-size limits remain a persistence/operational policy concern and are not silently imposed by the source-neutral archive contract.

Fix commit:

```text
709db5b94e2d7adcea8ce5566da8e3028dd420ee  Fix UWBS-074 payload validation
```

## Final local validation

The fixed branch passed all required acceptance checks:

```text
focused crypto_archive: 10 passed in 1.36s
full Python:             694 passed, 1 warning in 38.39s
compileall:              PASS (no output)
diff --check:            PASS (no output)
```

The remaining warning is the existing Starlette / anyio `BlockingPortal` deprecation warning and is unrelated to UWBS-074.

TypeScript tests/typecheck were not required because the UWBS-074 diff is Python-only.

## Semantic boundary

UWBS-074 defines lifecycle semantics only. It does not choose D1/R2/filesystem persistence or activate provider fetching.

```text
normalized snapshot
      ↓
canonical serialized envelope + hash
      ↓
archive idempotency / revision semantics
      ↓
missing-window detection
      ↓
catch-up lifecycle
```

Provider history limits remain source facts from UWBS-070/073 and must be handled operationally. If a historical window is beyond recoverable provider history it may be marked `UNRECOVERABLE`; the archive must not fabricate data.

## Source commits

Initial implementation:

```text
c6b920f7a68b894978b3c80d86014b1fa577eefe  archive/catch-up contracts
5f9f91447ba783d7c5f0a5006ff6148d8e80204d  archive/hash/gap lifecycle
c2522c822baf3ec74e36b4f481b834077e2eb649  public exports
52ce1425d499f3687adf954ef5ccc63b3d248306  focused tests
```

Validation fixes:

```text
bda9950841403f948d386b0d005c4de03bb22f70  fixture chronology fix
709db5b94e2d7adcea8ce5566da8e3028dd420ee  payload validation fix
```

## Diff audit

Compared with accepted UWBS-073 source head, changes remain limited to the new crypto-archive package and its focused tests. No D1 migration, Worker/Cron, network fetch, provider credential, liquidation acquisition, Position Map, UWBS-084 BTC ETF flow, or TypeScript changes are included.

## Acceptance decision

UWBS-074 is **Accepted**.

Physical persistence backend selection and scheduled catch-up execution remain operational integration work; UWBS-074 establishes the deterministic lifecycle contract required by later liquidation, position-map, and cross-venue quality work.
