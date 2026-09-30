# v0.1.6 UWBS-069 implementation progress — 2026-09-30

Status: **WEB IMPLEMENTATION CANDIDATE CREATED; LOCAL VALIDATION PENDING**

## Dependency base

UWBS-069 is implemented on top of accepted UWBS-068 source branch commit:

```text
UWBS-068 head = 716644a679f8f353d409e48ec06351dc38c2060e
```

Development branch:

```text
codex/uwbs-069-btc-relative-context
```

The branch is 5 commits ahead / 0 behind the UWBS-068 accepted source head.

## Implemented scope

```text
analysis/app/orderscope_local/crypto_context/
  __init__.py
  models.py
  metrics.py
  interpretation.py
analysis/tests/crypto_context/
  test_crypto_context.py
```

Implemented contracts and metrics:

- aligned immutable crypto return observations;
- explicit BTC/target pair alignment validation;
- BTC-adjusted residual return = target return - BTC return;
- same-direction crypto breadth relative to the configured BTC proxy;
- deterministic mean altcoin return;
- conservative BTC-relative Interpretation states:
  - `BTC_LED_SYNCHRONIZATION_CANDIDATE`
  - `ALTCOIN_RELATIVE_STRENGTH`
  - `ALTCOIN_RELATIVE_WEAKNESS`
  - `INSUFFICIENT_EVIDENCE`;
- Interpretation explicitly records `causal_status = candidate_only` and BTC as a configured proxy rather than an established causal leader.

No lagged-correlation estimator, regression beta, provider acquisition, weekend-window logic, institutional-flow source, liquidation cascade, or Canary fixture is included. Those remain later UWBS tasks / later validation.

## Candidate source commits

```text
a7f0d1dd0665128de6dad29b7f9f3ba3260e7b90  return/breadth contracts
6eeffe3396b301d8cb630608d9f2f4b8950234f5  deterministic BTC-relative metrics
03441d439682f90fe7f035451b0cb3bd4504a12e  conservative interpretation builder
adb2987e9119443841949dc4bccd7ef05c4689c2  public exports
56cd68aabd06326041acc8a37dc458f6cc3beb2f  focused tests
```

## Diff audit

Compared with UWBS-068 source head, only the new crypto-context package and its tests are added. No UWBS-070+, UWBS-084, provider activation, Worker/Cron, D1 or TypeScript changes are present.

## Focused test intent

The committed suite covers:

1. UTC/window validation;
2. BTC and target must be distinct and aligned;
3. BTC-adjusted residual calculation;
4. same-direction breadth;
5. zero-BTC-return breadth semantics;
6. mean altcoin return;
7. relative-strength interpretation without causal claim;
8. low breadth -> insufficient evidence;
9. invalid breadth rejection.

## Required local validation

```bash
git fetch origin codex/uwbs-069-btc-relative-context
git switch -C codex/uwbs-069-btc-relative-context \
  origin/codex/uwbs-069-btc-relative-context

uv run pytest -q analysis/tests/crypto_context
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app

git diff --check \
  716644a679f8f353d409e48ec06351dc38c2060e..HEAD
```

TypeScript tests/typecheck are not required unless a later change touches TypeScript/shared generated/build surfaces.

## Acceptance limit

UWBS-069 may be accepted when focused/full Python regression, compileall and diff check pass. Historical lag stability, BTC causality, empirical breadth thresholds and out-of-sample synchronization remain experimental and are not release blockers for the v0.1 development series, but must not be represented as Facts.
