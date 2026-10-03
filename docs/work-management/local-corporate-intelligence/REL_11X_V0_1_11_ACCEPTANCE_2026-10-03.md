# OrderScope — REL-11X / v0.1.11 Cumulative Acceptance — 2026-10-03

Status: **ACCEPTED / TAG READY**
Release: `v0.1.11`
Scope: `C0-001..C0-004 / UWBS-106..109`
Validated cumulative target: `fce9a3a2e56783206d63dbcac0d8a65e50008c10`

## Acceptance evidence

Repository-environment validation supplied on 2026-10-03 against `main` at the target above:

```text
uv run pytest -q analysis/tests/crypto_onchain
33 passed in 2.63s

uv run pytest -q \
  analysis/tests/crypto_context \
  analysis/tests/crypto_derivatives \
  analysis/tests/crypto_archive \
  analysis/tests/crypto_time \
  analysis/tests/crypto_canary
111 passed in 3.26s

uv run pytest -q analysis/tests
1151 passed in 42.03s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no error output)
```

No shared Worker/runtime contracts were changed by C0-001..004, so Worker test/typecheck was not added as a REL-11X gate.

## Accepted capability boundary

- `C0-001 / UWBS-106`: cross-chain project / wallet / contract registry and confirmed-transfer Fact contract;
- `C0-002 / UWBS-107`: deterministic 5m/15m/60m abnormal-flow Derived Metrics and candidate state;
- `C0-003 / UWBS-108`: on-chain anomaly × BTC-relative / OI / funding / liquidation market-context join;
- `C0-004 / UWBS-109`: historical replay with distinct first-on-chain/public/official timestamps and +15m/+1h/+6h/+24h/+48h/+5d/+30d windows.

The accepted lane retains these safety/evidence boundaries:

- abnormal transfer does not imply exploit, theft, malicious intent or confirmed incident;
- market context may produce deleveraging/new-short candidates but does not establish causality;
- missing replay inputs fail closed rather than being guessed;
- historical article-reported percentage moves do not replace consistently computed market returns.

## Release transition

```text
v0.1.11  C0-001..004 / UWBS-106..109  ACCEPTED / TAG READY

NEXT:
v0.1.12 REL-12A / A0-018 / UWBS-105
```

`TAG READY` is evidence only. Creation or push of a Git tag remains unauthorized until explicitly requested.
