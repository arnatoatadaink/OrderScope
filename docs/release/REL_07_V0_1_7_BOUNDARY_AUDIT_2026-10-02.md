# REL-07 — v0.1.7 Boundary Audit — 2026-10-02

Status: **RECONSTRUCTED CANDIDATE CREATED — ACCEPTANCE PENDING**
Release target: `v0.1.7`
Scope: `UWBS-080..086` Oil / Commodity / Cross-Asset

## 1. Decision summary

The historical UWBS-080..086 closeout commit is:

```text
33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
Close UWBS-086 shadow boundary in current tracker
```

This commit is a strict ancestor of current `main` and is the correct historical v0.1.7 feature-lane endpoint.

It is not by itself the final cumulative v0.1.7 release boundary because the accepted v0.1.6 Crypto Market Structure lane was reconstructed/replayed later during REC-01.

## 2. UWBS-086 acceptance evidence

Historical closeout evidence at `33ca0587...` records:

```text
shadow capacity bound focused tests:      10 passed
D1 capacity evidence focused tests:       10 passed
historical Canary evaluation tests:        7 passed
full Python regression:                  835 passed
compileall:                              PASS
git diff --check:                        PASS
```

Historical Canary was clean with zero false positives, false negatives, or regime mismatches. The accepted runtime boundary remains shadow-only; `WORKER_MODE=live` is excluded.

## 3. REC-01 replay source

Accepted replay source commit:

```text
f2b1bd24127814d5c025287f1c4f7186511c470f
Replay v0.1.6 crypto packages for REC-01
```

The REC-01 replay commit is additive: 4,251 additions and zero deletions. Its accepted package trees are therefore suitable for deterministic subtree grafting onto the historical v0.1.7 endpoint without rewriting the Oil / Commodity / Cross-Asset implementation.

## 4. Reconstructed cumulative candidate

A new cumulative Git tree was created by taking the historical `33ca0587...` tree and adding only the accepted REC-01 Crypto package/test subtrees:

```text
analysis/app/orderscope_local/crypto_archive
analysis/app/orderscope_local/crypto_canary
analysis/app/orderscope_local/crypto_context
analysis/app/orderscope_local/crypto_derivatives
analysis/app/orderscope_local/crypto_time
analysis/tests/crypto_archive
analysis/tests/crypto_canary
analysis/tests/crypto_context
analysis/tests/crypto_derivatives
analysis/tests/crypto_time
```

Created tree:

```text
f2945becd8ec5790d765b0a0e9063e5ca426fe93
```

Created candidate commit:

```text
c44372c4a3b23c4c90bf6950c447054904b28a19
Reconstruct cumulative v0.1.7 crypto + cross-asset boundary
parent: 33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
```

This reconstruction intentionally does not add Physical-SaaS (`UWBS-087..093`) or VIX / volatility (`UWBS-094..100`) package trees.

## 5. Reconstruction branch

Canonical staging branch:

```text
release/reconstructed-v0.1.7
```

The branch is to be advanced to `c44372c4...` and treated as the REL-07 candidate boundary. This does not change `main`.

## 6. REL-07 gate state

```text
Historical UWBS-080..086 endpoint verification: PASS
Ancestry to current main:                  PASS
Historical UWBS-086 acceptance evidence:   PASS
Direct-tag suitability of 33ca0587...:      FAIL (not cumulative)
REC-01 replay source classification:        PASS
Cumulative v0.1.7 candidate tree:           CREATED
Candidate commit:                           c44372c4...
Physical-SaaS / Volatility exclusion:       STRUCTURAL PASS by selected subtree set
Fresh/reconstructed release acceptance:     PENDING
v0.1.7 manifest finalization:                PENDING
v0.1.7 tag readiness:                        NOT READY
```

## 7. Remaining acceptance

The next gate is local validation of `release/reconstructed-v0.1.7` after it points to `c44372c4...`:

```text
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
npm test
npm run typecheck
```

Worker commands are included as cumulative release checks even though the REC-01 replay itself did not modify Worker code.

After clean validation:

1. write `V0_1_7_RELEASE_MANIFEST_2026-10-02.md`;
2. mark REL-07 Accepted;
3. mark `v0.1.7` annotated-tag creation READY;
4. advance CP to REL-08.

No provider activation, Worker/Cron mutation, D1 mutation, PB execution, automated trading action, or production security assertion is authorized by REL-07 reconstruction work.
