# OrderScope — REL-11X / v0.1.11 Cumulative Acceptance Plan — 2026-10-03

Status: **CURRENT / VALIDATION PENDING**
Release: `v0.1.11`
Scope: cumulative acceptance of `C0-001..004 / UWBS-106..109`

## Accepted prerequisites

```text
REL-11A / C0-001 / UWBS-106  ACCEPTED / INTEGRATED
REL-11B / C0-002 / UWBS-107  ACCEPTED / INTEGRATED
REL-11C / C0-003 / UWBS-108  ACCEPTED / INTEGRATED
REL-11D / C0-004 / UWBS-109  ACCEPTED / INTEGRATED
```

## Cumulative validation gate

Run on current `main` after pulling the integrated REL-11D code.

### 1. On-chain focused cumulative suite

```bash
uv run pytest -q analysis/tests/crypto_onchain
```

### 2. Affected accepted crypto-market-structure regression

```bash
uv run pytest -q \
  analysis/tests/crypto_context \
  analysis/tests/crypto_derivatives \
  analysis/tests/crypto_archive \
  analysis/tests/crypto_time \
  analysis/tests/crypto_canary
```

If one of these directories is absent in the checked-out tree, report that fact rather than substituting an unrelated path.

### 3. Full Python regression

```bash
uv run pytest -q analysis/tests
```

### 4. Static repository checks

```bash
uv run python -m compileall -q analysis/app
git diff --check
```

Worker tests/typecheck are required only when shared Worker/runtime contracts are changed. `C0-001..004` currently modify only the local analysis package and tests, so no Worker gate is added unless the final main diff shows shared runtime changes.

## Acceptance conditions

REL-11X may be accepted only when:

- all C0 focused tests pass;
- affected accepted crypto-context / derivatives / archive / time / canary tests pass;
- full analysis regression passes;
- compileall and diff checks pass;
- no look-ahead regression is introduced;
- first on-chain/public/official timestamps remain distinct;
- abnormal-flow candidate remains distinct from confirmed incident attribution;
- market-context interpretation keeps `causality = NOT_ESTABLISHED`;
- incomplete historical windows remain explicit rather than synthesized.

## Release-state rule

Passing REL-11X permits `v0.1.11` to move to **ACCEPTED / TAG READY** and advances the current feature restart to `v0.1.12 REL-12A / A0-018 / UWBS-105`.

`TAG READY` does not authorize creating or pushing a Git tag. Tag creation remains separately authorization-bound.
