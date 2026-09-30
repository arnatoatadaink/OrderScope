# v0.1.6 UWBS-074 implementation progress — 2026-10-01

Status: **LOCAL VALIDATION FAILED; FIX CANDIDATE PUSHED; RETEST REQUIRED**

## Dependency base

UWBS-074 is implemented on top of accepted UWBS-073 source head:

```text
UWBS-073 head = d602de71a93b8ac8c8877c0d0114d66553046555
```

Development branch:

```text
codex/uwbs-074-derivatives-archive
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

## First local validation result

The first local validation attempt failed:

```text
focused: 7 failed, 3 passed
full:    7 failed, 687 passed, 1 warning
```

Two independent defects were identified.

### Defect 1 — invalid test fixture chronology

The fixture defaulted to:

```text
observed_at  = t
available_at = t + 5s
accepted_at  = t + 1s
```

This violates the already-accepted UWBS-068 contract:

```text
observed_at <= available_at <= accepted_at
```

The default `accepted_offset` was corrected to `10` seconds. This is a test-fixture defect, not a relaxation of the UWBS-068 contract.

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

## Candidate source commits

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

Compared with accepted UWBS-073 source head, changes remain limited to the new crypto-archive package and its focused tests. No D1 migration, Worker/Cron, network fetch, provider credential, liquidation acquisition, Position Map, or TypeScript changes are included.

## Focused test intent

The committed suite covers:

1. deterministic/stable envelope hash;
2. stable snapshot-key scope;
3. insert + identical replay idempotency;
4. newer revision replacement;
5. older revision rejection;
6. coalesced missing-window detection;
7. no-gap behavior;
8. pending -> running -> complete lifecycle;
9. terminal unrecoverable state cannot reopen;
10. invalid cadence rejection.

## Required local revalidation

```bash
git fetch origin codex/uwbs-074-derivatives-archive
git switch -C codex/uwbs-074-derivatives-archive \
  origin/codex/uwbs-074-derivatives-archive

uv run pytest -q analysis/tests/crypto_archive
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app

git diff --check \
  d602de71a93b8ac8c8877c0d0114d66553046555..HEAD
```

TypeScript tests/typecheck are not required unless later work touches TypeScript/shared generated/build surfaces.

## Acceptance limit

UWBS-074 is **not accepted yet**. It may be accepted only after the focused/full Python regression, compileall and diff check pass on the fixed branch.

Physical persistence backend selection and scheduled catch-up execution remain operational integration work; UWBS-074 establishes the deterministic lifecycle contract needed before those decisions.
