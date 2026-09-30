# v0.1.6 UWBS-073 implementation progress — 2026-10-01

Status: **WEB IMPLEMENTATION CANDIDATE CREATED; LOCAL VALIDATION PENDING**

## Dependency base

UWBS-073 is implemented on top of accepted UWBS-072 source head:

```text
UWBS-072 head = 4ea346dfab96b1a2ba1e685bf6daba27341445a0
```

Development branch:

```text
codex/uwbs-073-multivenue-adapters
```

The branch is 3 commits ahead / 0 behind the accepted UWBS-072 code head.

## Implemented scope

```text
analysis/app/orderscope_local/crypto_derivatives/adapters.py
analysis/app/orderscope_local/crypto_derivatives/__init__.py
analysis/tests/crypto_derivatives/test_crypto_derivative_adapters.py
```

Provider payload adapters are provided for:

- Binance COIN-M current open interest;
- Bybit V5 derivatives ticker rows;
- OKX joined public-market snapshots;
- Hyperliquid perpetual asset context.

All adapters normalize into the existing UWBS-068 `CryptoDerivativeObservation` contract.

## Semantic boundary

UWBS-073 intentionally contains **no network I/O**.

```text
provider raw/public payload
        ↓
provider-specific adapter
        ↓
CryptoDerivativeObservation
```

The following are excluded:

- HTTP/WebSocket clients;
- credentials/API-key handling;
- provider activation;
- retries/rate-limit scheduling;
- Worker/Cron changes;
- archive/persistence lifecycle (`UWBS-074`);
- liquidation event acquisition (`UWBS-075`);
- position-map analysis (`UWBS-076`).

Missing provider fields remain explicit `None`; adapters do not fabricate values. Hyperliquid OI USD is derived only when both observed base OI and mark price are present. Bybit inverse OI is not mislabeled as base-asset OI. Mark/index basis is a deterministic subtraction only when both values exist.

## Provider schema notes used by this implementation

- Binance COIN-M current OI exposes `symbol`, `openInterest`, `contractType`, and `time`; historical OI has separate semantics and remains outside this adapter.
- Bybit V5 ticker exposes mark/index price, OI size/value, funding rate, turnover and basis-related fields; linear/inverse category controls margin semantics.
- OKX derivatives data is split across public endpoints, so this adapter accepts a caller-joined snapshot while preserving missing fields.
- Hyperliquid asset context exposes funding, OI, mark/oracle price, and notional volume context suitable for source-neutral normalization.

## Candidate source commits

```text
de1ed4da22b152f37abb0cc462bacc9fbcc32c8d  provider adapters
52c77bb09523473f1cf2f4409a76998e0630f6e2  public exports
d602de71a93b8ac8c8877c0d0114d66553046555  focused tests
```

## Diff audit

Compared with accepted UWBS-072 source head, only the UWBS-073 adapter surface and focused tests are changed. No provider activation, Worker/Cron, D1, archive, liquidation stream, UWBS-084 BTC ETF flow, or TypeScript changes are present.

## Focused test intent

The committed suite covers:

1. Binance perpetual OI normalization;
2. Binance dated future classification;
3. Bybit linear OI/funding/basis normalization;
4. Bybit inverse OI unit guard;
5. Bybit unknown-category rejection;
6. OKX missing-field preservation;
7. OKX joined OI/funding/mark/index normalization;
8. Hyperliquid base OI -> USD OI derivation only with mark price;
9. Hyperliquid no fabricated USD OI without mark;
10. invalid numeric provider field rejection;
11. adapter layer contains no network/credential contract.

## Required local validation

```bash
git fetch origin codex/uwbs-073-multivenue-adapters
git switch -C codex/uwbs-073-multivenue-adapters \
  origin/codex/uwbs-073-multivenue-adapters

uv run pytest -q analysis/tests/crypto_derivatives/test_crypto_derivative_adapters.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app

git diff --check \
  4ea346dfab96b1a2ba1e685bf6daba27341445a0..HEAD
```

TypeScript tests/typecheck are not required unless later work touches TypeScript/shared generated/build surfaces.

## Acceptance limit

UWBS-073 may be accepted when focused/full Python regression, compileall and diff check pass.

Live fetch behavior and provider outage/rate-limit handling are deliberately deferred to operational integration after source contracts and archive semantics are stable.
