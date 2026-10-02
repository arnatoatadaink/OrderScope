# REL-07 — v0.1.7 Boundary Audit — 2026-10-02

Status: **RECONSTRUCTED CANDIDATE CREATED — LOCAL ACCEPTANCE PENDING**
Release target: `v0.1.7`
Scope: `UWBS-080..086` Oil / Commodity / Cross-Asset

## 1. Historical boundary

Historical UWBS-080..086 closeout:

```text
33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
Close UWBS-086 shadow boundary in current tracker
```

This commit is a strict ancestor of current `main` and is the correct historical v0.1.7 feature-lane endpoint. It is not directly taggable as cumulative v0.1.7 because it predates the later accepted REC-01 replay of the reconstructed v0.1.6 Crypto Market Structure lane.

## 2. Historical UWBS-086 acceptance

Recorded at the historical endpoint:

```text
shadow capacity bound focused tests:      10 passed
D1 capacity evidence focused tests:       10 passed
historical Canary evaluation tests:        7 passed
full Python regression:                  835 passed
compileall:                              PASS
git diff --check:                        PASS
```

Historical Canary: zero false positives, zero false negatives, zero regime mismatches. Accepted runtime remains shadow-only; live-mode capacity is excluded.

## 3. REC-01 replay source

Accepted replay source:

```text
f2b1bd24127814d5c025287f1c4f7186511c470f
Replay v0.1.6 crypto packages for REC-01
```

The source replay is additive: 4,251 additions, zero deletions.

## 4. Reconstructed cumulative candidate

The historical v0.1.7 tree was combined with the exact accepted REC-01 Crypto package/test subtree objects.

Tree:

```text
f2945becd8ec5790d765b0a0e9063e5ca426fe93
```

Candidate commit:

```text
c44372c4a3b23c4c90bf6950c447054904b28a19
Reconstruct cumulative v0.1.7 crypto + cross-asset boundary
parent: 33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
```

Candidate branch:

```text
release/reconstructed-v0.1.7-candidate
```

The earlier `release/reconstructed-v0.1.7` staging branch is preserved and is not force-updated.

## 5. Structural equivalence result

Comparison `33ca0587... -> c44372c4...`:

```text
status:     ahead
ahead_by:   1
behind_by:  0
merge_base: 33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
```

Changed files are exactly the accepted Crypto replay package/test files: 34 added files, no modified/deleted files.

Added application package trees:

```text
analysis/app/orderscope_local/crypto_archive
analysis/app/orderscope_local/crypto_canary
analysis/app/orderscope_local/crypto_context
analysis/app/orderscope_local/crypto_derivatives
analysis/app/orderscope_local/crypto_time
```

Added test package trees:

```text
analysis/tests/crypto_archive
analysis/tests/crypto_canary
analysis/tests/crypto_context
analysis/tests/crypto_derivatives
analysis/tests/crypto_time
```

Because the tree was built using the accepted REC-01 subtree SHAs, file contents are object-identical to the accepted replay source for these packages.

No Physical-SaaS (`UWBS-087..093`) or VIX / volatility (`UWBS-094..100`) package is introduced by the reconstruction commit.

## 6. REL-07 gate state

```text
Historical UWBS-080..086 endpoint:         PASS
Ancestry to main:                          PASS
Historical UWBS-086 acceptance:            PASS
Direct-tag 33ca0587 suitability:            FAIL — not cumulative
REC-01 source classification:               PASS
Cumulative candidate construction:          PASS
Crypto replay structural equivalence:       PASS
v0.1.8/v0.1.9 scope exclusion:              PASS
Fresh local cumulative test acceptance:     PENDING
v0.1.7 manifest finalization:                PENDING
v0.1.7 tag readiness:                        NOT READY
```

## 7. Required local acceptance

GitHub Actions workflows are not present in this repository and the assistant runtime has no outbound GitHub network access, so executable tests must be run in the user's existing local clone.

Run from the OrderScope repository:

```bash
git fetch origin
git switch release/reconstructed-v0.1.7-candidate
git pull --ff-only origin release/reconstructed-v0.1.7-candidate

git rev-parse HEAD
# expected: c44372c4a3b23c4c90bf6950c447054904b28a19

uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check

npm test
npm run typecheck
```

If all checks pass, REL-07 can proceed immediately to release-manifest finalization and `v0.1.7` tag-ready acceptance.

No provider activation, Worker/Cron mutation, D1 mutation, PB execution, automated trading action, or production security assertion is authorized by REL-07 reconstruction work.
