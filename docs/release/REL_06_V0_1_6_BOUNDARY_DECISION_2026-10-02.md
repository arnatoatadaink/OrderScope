# REL-06 — v0.1.6 boundary decision — 2026-10-02

Status: **BOUNDARY RESOLVED / EXACT-BOUNDARY VALIDATION PENDING**

## Decision

The canonical `v0.1.6` release-boundary candidate is:

```text
bfaf89c68daa656b7d75317f086458257cc94da9
Reflect accepted v0.1.6 WBS and CP progress
```

## Lineage evidence

The accepted `v0.1.5` boundary is:

```text
415de1f1dd42f70bd66992961cb43be7edba6ade
Reconstruct v0.1.5 listing compliance boundary
```

GitHub commit comparison from `v0.1.5` to the selected `v0.1.6` candidate reports:

```text
status      ahead
ahead_by    56
behind_by   0
merge_base  415de1f1dd42f70bd66992961cb43be7edba6ade
```

Therefore `bfaf89c...` is a direct cumulative successor of the accepted reconstructed `v0.1.5` boundary rather than an unrelated or divergent reconstruction.

The file delta is confined to the v0.1.6 crypto implementation lane and its release evidence:

- `analysis/app/orderscope_local/crypto_archive/**`
- `analysis/app/orderscope_local/crypto_canary/**`
- `analysis/app/orderscope_local/crypto_context/**`
- `analysis/app/orderscope_local/crypto_derivatives/**`
- `analysis/app/orderscope_local/crypto_time/**`
- matching `analysis/tests/crypto_*` suites
- `docs/release/V0_1_6_*` acceptance/progress documents

This matches the planned v0.1.6 scope (`UWBS-068..079`).

## Existing acceptance evidence

Commit `bfaf89c...` records the v0.1.6 development release as accepted, including CP-16X evidence:

```text
crypto_derivatives  62 passed
crypto_canary       20 passed
crypto_context       9 passed
crypto_time         10 passed
crypto_archive      10 passed
full analysis      746 passed, 1 warning
compileall           PASS
git diff --check     PASS
```

`UWBS-079 Stage B` remains `Pending / Experimental` and is explicitly non-blocking for the implementation release. The release must not represent Stage-B recurrence hypotheses as validated facts.

## Why REC-04 is not the v0.1.6 tag boundary

`REC_04_CUMULATIVE_ACCEPTANCE_2026-10-01.md` validates a later cumulative reconciliation branch that already contains:

- accepted `UWBS-080..100` baseline work;
- replayed v0.1.6 crypto packages;
- replayed `theme` and `listing_compliance` packages;
- later Worker/news/storage/scheduler and cross-market implementations.

That branch is a valid later cumulative regression boundary, but it is too broad to represent the historical semantic boundary of `v0.1.6`.

Similarly, main replay commits such as `f2b1bd24127814d5c025287f1c4f7186511c470f` are reconciliation/integration commits, not the original semantic release endpoint.

## REL-06 acceptance gate

Before `v0.1.6` is promoted to `TAG READY`, run the common exact-boundary validation on `bfaf89c...`:

```bash
git switch --detach bfaf89c68daa656b7d75317f086458257cc94da9

git rev-parse HEAD
git status --short

uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
npm test
npm run typecheck
```

Expected historical Python baseline is approximately `746 passed, 1 warning`. Worker test count must be recorded from the exact boundary rather than inferred from a later reconciliation branch.

## Current classification

```text
v0.1.6 boundary SHA     RESOLVED -> bfaf89c68daa656b7d75317f086458257cc94da9
lineage from v0.1.5     PASS
scope isolation         PASS
historical CP-16X       ACCEPTED
exact-boundary rerun    PENDING
release classification  NOT YET TAG READY
```
