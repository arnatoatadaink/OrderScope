# v0.1.6 UWBS-068 implementation progress — 2026-09-30

Status: **WEB IMPLEMENTATION CANDIDATE CREATED; LOCAL VALIDATION PENDING**

## Parent boundary

```text
v0.1.5 = 415de1f1dd42f70bd66992961cb43be7edba6ade
```

## Development branch

```text
codex/uwbs-068-crypto-derivatives-contract
```

The branch is based directly on the accepted v0.1.5 synthetic boundary.

## Implemented scope

UWBS-068 now has a compact source-neutral Python contract:

```text
analysis/app/orderscope_local/crypto_derivatives/
  __init__.py
  models.py
  metrics.py
analysis/tests/crypto_derivatives/
  test_crypto_derivatives.py
```

Implemented observation contracts:

- `CryptoDerivativeObservation`
  - venue / instrument / contract / margin metadata;
  - observed / available / accepted UTC semantics;
  - OI in contracts/base/USD;
  - funding rate and interval;
  - mark/index price and explicit basis field;
  - derivatives volume;
  - source reference and revision;
  - explicit missing values retained as missing.
- `LiquidationObservation`
  - venue / instrument;
  - immutable time bucket;
  - long and short liquidation USD values kept separate;
  - optional event count;
  - source lineage.

Implemented deterministic metrics:

- `open_interest_delta_usd`
- `funding_delta`
- `basis_bps`
- `liquidation_imbalance`

No metric asserts trader identity, long-only capital inflow, institutional participation, or causality.

## Candidate source commits

```text
d8a549101ceda885e7dc67628dc8985654543891  contracts
06687d3f48d58329538d1cbfa6dda1c802438442  deterministic metrics
1061c291ef084013f7f77793f81f0631fdebb1f5  public exports
716644a679f8f353d409e48ec06351dc38c2060e  focused tests
```

## Diff audit

Compared with v0.1.5, the branch is 4 commits ahead / 0 behind and changes only:

```text
analysis/app/orderscope_local/crypto_derivatives/__init__.py
analysis/app/orderscope_local/crypto_derivatives/models.py
analysis/app/orderscope_local/crypto_derivatives/metrics.py
analysis/tests/crypto_derivatives/test_crypto_derivatives.py
```

No UWBS-069+ implementation, UWBS-084 BTC spot ETF code, provider activation, Worker/Cron change, D1 mutation, or TypeScript change is included.

## Focused test intent

The committed test suite covers:

1. partial/missing provider fields remain explicit;
2. UTC and observed/available/accepted ordering;
3. negative unsigned measures rejected;
4. empty observations rejected;
5. OI delta lineage and deterministic calculation;
6. venue/instrument series mixing rejected;
7. funding delta and basis calculation;
8. long/short liquidation values kept separate;
9. zero-liquidation bucket semantics;
10. invalid liquidation bucket/time/amount rejection.

The web connector cannot execute these tests. Local validation is required before acceptance.

## Local validation

```bash
git fetch origin codex/uwbs-068-crypto-derivatives-contract
git switch -C codex/uwbs-068-crypto-derivatives-contract \
  origin/codex/uwbs-068-crypto-derivatives-contract

uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app

git diff --check \
  415de1f1dd42f70bd66992961cb43be7edba6ade..HEAD
```

TypeScript tests/typecheck are not required unless later work changes TypeScript/shared generated/build surfaces.

## Acceptance limit

UWBS-068 may be accepted when focused/full Python regression, compileall and diff check pass.

The following remain outside UWBS-068 and must not be pulled forward:

- BTC leader/altcoin-relative interpretation (`UWBS-069`);
- institutional-flow/provider survey (`UWBS-070`);
- 24/7 session/window model (`UWBS-071`);
- NEAR/BTC Canary (`UWBS-072`);
- live/multi-venue adapters (`UWBS-073`);
- durable archive/catch-up (`UWBS-074`);
- cascade interpretation (`UWBS-075`);
- Position Map (`UWBS-076`);
- divergence/quality guards (`UWBS-077`);
- Canaries (`UWBS-078..079`);
- BTC spot ETF flow implementation (`UWBS-084`).
