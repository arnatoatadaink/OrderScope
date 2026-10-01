# OrderScope v0.1.6 CP-16X acceptance plan — 2026-10-01

## Status

**Boundary acceptance pending local execution**

CP-16X is the final v0.1.6 release-boundary validation step after implementation of canonical UWBS-068..079.

## Acceptance objectives

Confirm that the reconstructed v0.1.6 crypto lane is internally consistent, regression-safe, and still respects the experimental boundaries documented during reconstruction.

## Required checks

### 1. Focused crypto suites

```bash
uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests/crypto_canary
uv run pytest -q analysis/tests/crypto_context
uv run pytest -q analysis/tests/crypto_time
uv run pytest -q analysis/tests/crypto_archive
```

### 2. Full Python regression

```bash
uv run pytest -q analysis/tests
```

### 3. Static/runtime syntax validation

```bash
uv run python -m compileall -q analysis/app
```

### 4. Diff hygiene

```bash
git diff --check
```

## Boundary assertions

Acceptance additionally requires review confirmation that:

- Fact / Derived Metric / Interpretation separation remains explicit;
- UTC / as-of semantics remain explicit;
- provider-specific assumptions are not silently generalized;
- cross-venue disagreement remains observable rather than silently averaged away;
- Position Map remains an estimate rather than a reconstructed ledger;
- liquidation side semantics remain distinct from aggressor trade side;
- NEAR Canary outputs remain descriptive QA/monitoring context rather than buy/sell signals;
- UWBS-079 recurrence remains experimental pending a real multi-week sample;
- later-version UWBS-084 work has not contaminated the v0.1.6 boundary.

## UWBS-079 Stage B

Stage B is tracked separately from CP-16X release acceptance.

The code path is accepted at Stage A, but empirical recurrence requires a real multi-week sample with materially different weekend regimes. v0.1.6 may ship this capability as experimental provided this limitation remains explicit.

## Release decision

If all required commands pass and the boundary assertions are confirmed, record:

```text
v0.1.6 CP-16X = Accepted
v0.1.6 crypto lane = Development release accepted
UWBS-079 Stage B = Experimental follow-up / empirical validation pending
```
