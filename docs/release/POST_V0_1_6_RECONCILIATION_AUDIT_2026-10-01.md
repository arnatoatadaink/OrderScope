# OrderScope post-v0.1.6 reconciliation audit — 2026-10-01

Status: **AUDIT COMPLETE / RECONCILIATION REQUIRED**

## 1. Purpose

Determine the safe cumulative integration path after the reconstructed v0.1.6 crypto-lane acceptance while preserving the later accepted UWBS-080..100 implementation line.

This audit does not merge branches, rewrite history, activate providers, mutate Worker/D1 state, or authorize PB runtime work.

## 2. Authoritative boundaries inspected

### Reconstructed v0.1.6 acceptance line

Branch:

```text
codex/v0-1-6-cp16x-acceptance
```

Current accepted head before this audit:

```text
bfaf89c68daa656b7d75317f086458257cc94da9
```

It contains the accepted reconstructed v0.1.6 crypto lane through canonical UWBS-079 Stage A and CP-16X.

### Later implementation line

Repository `main` currently points to:

```text
b18d9b10ab3c6067d0f721551559898d447343cc
```

This line contains accepted implementation through UWBS-097.

### UWBS-098..100 continuation line

Branch:

```text
feat/uwbs-100-volatility-calibration
```

Current head:

```text
40a3cc1e3d7231bf0c1b49e0bd8a5aa5335af0ba
```

It is exactly 13 commits ahead of `main`, zero behind, and contains accepted UWBS-098, UWBS-099 and UWBS-100 plus the v0.1.x release-boundary plan.

## 3. Git topology result

### main vs reconstructed v0.1.6

```text
status: diverged
v0.1.6 ahead of main: 61 commits
v0.1.6 behind main:    743 commits
merge base:            99b08a0b5fa1bec5921dc42e630c579a4e83c401
```

Therefore a direct branch merge is not a safe default operation.

The two lines represent different historical reconstruction paths. The reconstructed branch includes accepted v0.1.x components replayed from an older synthetic boundary while `main` continued accumulating the historical implementation stream.

### main vs UWBS-100 feature

```text
status: ahead
feature ahead of main: 13 commits
feature behind main:   0 commits
base:                  b18d9b10ab3c6067d0f721551559898d447343cc
```

This is a clean continuation relationship. UWBS-098..100 should therefore be treated as later accepted work waiting for integration, not as reconstruction input to be discarded.

## 4. Canonical accepted task state

Current accepted task interpretation:

```text
UWBS-068..079  reconstructed v0.1.6 crypto lane      ACCEPTED
UWBS-080..086  oil / commodity / cross-asset lane    ACCEPTED
UWBS-087..093  Physical-SaaS lane                    ACCEPTED
UWBS-094..097  volatility lane, integrated in main   ACCEPTED
UWBS-098..100  volatility continuation feature       ACCEPTED / NOT YET IN MAIN
```

UWBS-079 Stage B remains an experimental multi-week empirical-validation track and is not an implementation blocker.

## 5. Why direct merge is unsafe

The v0.1.6 reconstruction branch and the later main line both contain paths such as:

```text
analysis/app/orderscope_local/cli.py
analysis/app/orderscope_local/contracts/__init__.py
analysis/app/orderscope_local/cross_market/__init__.py
analysis/app/orderscope_local/integration/operator.py
analysis/app/orderscope_local/storage/*
```

They also contain overlapping conceptual modules that were independently introduced or replayed on different histories.

A merge may therefore produce one of four classes of problem:

1. textual conflicts in shared package/export files;
2. duplicate semantic implementation under different package paths;
3. silent replacement of a later accepted implementation by a reconstructed earlier variant;
4. test success with incorrect release provenance or duplicated contracts.

Accordingly, conflict count alone is not a sufficient acceptance criterion.

## 6. Selected cumulative baseline

The safe baseline for the next reconciliation phase is:

```text
feat/uwbs-100-volatility-calibration
```

because it is a strict descendant of current `main` and preserves accepted UWBS-080..100 work.

Audit branch created from that baseline:

```text
codex/post-v0-1-6-reconciliation-audit
```

The reconstruction branch is treated as a source of accepted missing deltas, not as the branch that should replace the later line wholesale.

## 7. Required reconciliation method

Use a **selective replay / semantic reconciliation** strategy.

### Phase R1 — inventory reconstructed-only artifacts

Compare the v0.1.6 branch against the later baseline and classify each changed path as:

- `ALREADY_PRESENT_EQUIVALENT`
- `ALREADY_PRESENT_LATER_VERSION`
- `RECONSTRUCTED_ONLY_REQUIRED`
- `DOC_EVIDENCE_ONLY`
- `CONFLICT_REQUIRES_MANUAL_RECONCILIATION`

Do not replay files classified as equivalent or superseded.

### Phase R2 — prioritize v0.1.6 crypto-specific package roots

The most likely reconstructed-only required roots are:

```text
analysis/app/orderscope_local/crypto_archive/
analysis/app/orderscope_local/crypto_canary/
analysis/app/orderscope_local/crypto_context/
analysis/app/orderscope_local/crypto_derivatives/
analysis/app/orderscope_local/crypto_time/

analysis/tests/crypto_archive/
analysis/tests/crypto_canary/
analysis/tests/crypto_context/
analysis/tests/crypto_derivatives/
analysis/tests/crypto_time/
```

These must be checked against later `orderscope_local/crypto/` work. The latter contains UWBS-084 BTC ETF flow and is a different canonical scope; package-name proximity must not be treated as equivalence.

### Phase R3 — reconcile shared export/integration files manually

Files such as:

```text
analysis/app/orderscope_local/cli.py
analysis/app/orderscope_local/contracts/__init__.py
analysis/app/orderscope_local/cross_market/__init__.py
analysis/app/orderscope_local/integration/operator.py
```

must not be copied wholesale from the reconstruction branch. Required symbols should be added to the later baseline while preserving all later accepted exports and behavior.

### Phase R4 — replay acceptance/release evidence

The following v0.1.6 evidence should be retained on the cumulative line after code reconciliation:

```text
docs/release/V0_1_6_*_2026-10-01.md
```

Historical audit/planning documents remain evidence and must not be rewritten to pretend they were originally created on the later line.

### Phase R5 — full cumulative acceptance

After selective replay, run at minimum:

```text
uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests/crypto_canary
uv run pytest -q analysis/tests/crypto_context
uv run pytest -q analysis/tests/crypto_time
uv run pytest -q analysis/tests/crypto_archive
uv run pytest -q analysis/tests/cross_market/test_mstr_iv30.py
uv run pytest -q analysis/tests/cross_market/test_mstr_btc_iv30.py
uv run pytest -q analysis/tests/cross_market/test_volatility_calibration.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

Worker/TypeScript regression should also be rerun if reconciliation touches `src/`, migrations, worker configuration, or shared runtime integration files.

## 8. Non-goals

This reconciliation does not:

- re-run already accepted empirical studies merely because history is reorganized;
- activate UWBS-079 Stage B;
- alter PB-09/PB-10 authorization;
- replace accepted later implementations with older reconstructed variants;
- rewrite historical commits;
- force squash/merge policy before semantic equivalence is proven.

## 9. Decision

```text
Direct merge reconstructed v0.1.6 -> main:              NO
Discard later main/UWBS-080..100 line:                  NO
Use UWBS-100 feature as cumulative reconciliation base: YES
Selective replay of reconstructed missing artifacts:    YES
Full cumulative regression after replay:                REQUIRED
```

## 10. Immediate next task

Create a file-level reconciliation manifest for the reconstructed v0.1.6 delta, beginning with the five crypto package roots and their focused tests.

The first implementation objective is not another UWBS item. It is:

```text
REC-01 — classify and replay reconstructed v0.1.6 crypto-only artifacts onto the accepted UWBS-100 baseline
```

Only after REC-01 is accepted should shared export/integration files be reconciled and a new cumulative release boundary be declared.
