# v0.1.6 UWBS-074 implementation progress — 2026-10-01

Status: **WEB IMPLEMENTATION CANDIDATE CREATED; LOCAL VALIDATION PENDING**

## Dependency base

UWBS-074 is implemented on top of accepted UWBS-073 source head:

```text
UWBS-073 head = d602de71a93b8ac8c8877c0d0114d66553046555
```

Development branch:

```text
codex/uwbs-074-derivatives-archive
```

The branch is 4 commits ahead / 0 behind the accepted UWBS-073 code head.

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

```text
c6b920f7a68b894978b3c80d86014b1fa577eefe  archive/catch-up contracts
5f9f91447ba783d7c5f0a5006ff6148d8e80204d  archive/hash/gap lifecycle
c2522c822baf3ec74e36b4f481b834077e2eb649  public exports
52ce1425d499f3687adf954ef5ccc63b3d248306  focused tests
```

## Diff audit

Compared with accepted UWBS-073 source head, only the new crypto-archive package and its focused tests are added. No D1 migration, Worker/Cron, network fetch, provider credential, liquidation acquisition, Position Map, or TypeScript changes are included.

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

## Required local validation

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

UWBS-074 may be accepted when focused/full Python regression, compileall and diff check pass.

Physical persistence backend selection and scheduled catch-up execution remain operational integration work; UWBS-074 establishes the deterministic lifecycle contract needed before those decisions.
