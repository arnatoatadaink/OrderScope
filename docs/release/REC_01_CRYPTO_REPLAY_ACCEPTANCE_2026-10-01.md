# REC-01 — Crypto replay acceptance — 2026-10-01

Status: **ACCEPTED**

Branch:

```text
codex/post-v0-1-6-reconciliation-audit
```

Replay commit:

```text
f2b1bd24127814d5c025287f1c4f7186511c470f
```

## Scope

REC-01 selectively replayed the accepted v0.1.6 crypto-only package roots and focused tests onto the accepted UWBS-100 baseline without replacing shared later-generation files.

Included package roots:

```text
analysis/app/orderscope_local/crypto_archive/
analysis/app/orderscope_local/crypto_canary/
analysis/app/orderscope_local/crypto_context/
analysis/app/orderscope_local/crypto_derivatives/
analysis/app/orderscope_local/crypto_time/
```

Included focused test roots:

```text
analysis/tests/crypto_archive/
analysis/tests/crypto_canary/
analysis/tests/crypto_context/
analysis/tests/crypto_derivatives/
analysis/tests/crypto_time/
```

Deferred shared-file reconciliation remains REC-02 scope:

```text
analysis/app/orderscope_local/cli.py
analysis/app/orderscope_local/contracts/__init__.py
analysis/app/orderscope_local/cross_market/__init__.py
analysis/app/orderscope_local/integration/operator.py
```

## Local validation evidence

Executed on 2026-10-01 after switching to and fast-forwarding the reconciliation branch.

```text
uv run pytest -q analysis/tests/crypto_derivatives
62 passed in 2.59s

uv run pytest -q analysis/tests/crypto_canary
20 passed in 3.66s

uv run pytest -q analysis/tests/crypto_context
9 passed in 1.53s

uv run pytest -q analysis/tests/crypto_time
10 passed in 1.49s

uv run pytest -q analysis/tests/crypto_archive
10 passed in 1.01s

uv run pytest -q analysis/tests
1097 passed in 50.47s

uv run python -m compileall -q analysis/app
PASS (no output)

git diff --check
PASS (no output)
```

## Acceptance decision

```text
Selective crypto replay                    ACCEPTED
Focused crypto regressions                 ACCEPTED
Full Python regression                     ACCEPTED — 1097 passed
Compile validation                         ACCEPTED
Diff hygiene                               ACCEPTED
Shared-file reconciliation                 DEFERRED TO REC-02
UWBS-079 Stage B empirical recurrence      PENDING / EXPERIMENTAL
```

The 1097-test full regression confirms that the replayed v0.1.6 crypto packages coexist with the accepted UWBS-080..100 baseline at this checkpoint.

REC-01 is therefore closed as **Accepted**.
