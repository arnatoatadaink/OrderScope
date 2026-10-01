# REC-01 — v0.1.6 crypto replay manifest — 2026-10-01

Status: **CLASSIFIED / READY FOR SELECTIVE REPLAY**

Base branch:

```text
codex/post-v0-1-6-reconciliation-audit
```

Baseline ancestry:

```text
main
  -> feat/uwbs-100-volatility-calibration
  -> codex/post-v0-1-6-reconciliation-audit
```

Source branch:

```text
codex/v0-1-6-cp16x-acceptance
```

## 1. Classification rule

The Git compare from the accepted UWBS-100 baseline to the reconstructed v0.1.6 branch shows the five crypto package roots and their focused tests as `added` on the reconstruction line.

They do not exist on the accepted UWBS-100 baseline and are not superseded by the later `orderscope_local/crypto/` BTC ETF-flow package. Therefore these paths are classified:

```text
RECONSTRUCTED_ONLY_REQUIRED
```

They may be replayed without replacing an existing same-path later implementation.

## 2. Code paths — RECONSTRUCTED_ONLY_REQUIRED

### crypto_archive

```text
analysis/app/orderscope_local/crypto_archive/__init__.py
analysis/app/orderscope_local/crypto_archive/archive.py
analysis/app/orderscope_local/crypto_archive/models.py
```

### crypto_canary

```text
analysis/app/orderscope_local/crypto_canary/__init__.py
analysis/app/orderscope_local/crypto_canary/evaluate.py
analysis/app/orderscope_local/crypto_canary/models.py
analysis/app/orderscope_local/crypto_canary/weekend_validation.py
```

### crypto_context

```text
analysis/app/orderscope_local/crypto_context/__init__.py
analysis/app/orderscope_local/crypto_context/interpretation.py
analysis/app/orderscope_local/crypto_context/metrics.py
analysis/app/orderscope_local/crypto_context/models.py
```

### crypto_derivatives

```text
analysis/app/orderscope_local/crypto_derivatives/__init__.py
analysis/app/orderscope_local/crypto_derivatives/adapters.py
analysis/app/orderscope_local/crypto_derivatives/cross_venue_qa.py
analysis/app/orderscope_local/crypto_derivatives/liquidation_metrics.py
analysis/app/orderscope_local/crypto_derivatives/liquidations.py
analysis/app/orderscope_local/crypto_derivatives/metrics.py
analysis/app/orderscope_local/crypto_derivatives/models.py
analysis/app/orderscope_local/crypto_derivatives/near_futures_canary.py
analysis/app/orderscope_local/crypto_derivatives/position_map.py
```

### crypto_time

```text
analysis/app/orderscope_local/crypto_time/__init__.py
analysis/app/orderscope_local/crypto_time/classify.py
analysis/app/orderscope_local/crypto_time/models.py
```

## 3. Focused tests — RECONSTRUCTED_ONLY_REQUIRED

```text
analysis/tests/crypto_archive/test_crypto_archive.py
analysis/tests/crypto_canary/test_crypto_canary.py
analysis/tests/crypto_canary/test_weekend_validation.py
analysis/tests/crypto_context/test_crypto_context.py
analysis/tests/crypto_derivatives/test_cross_venue_qa.py
analysis/tests/crypto_derivatives/test_crypto_derivative_adapters.py
analysis/tests/crypto_derivatives/test_crypto_derivatives.py
analysis/tests/crypto_derivatives/test_liquidation_cascade.py
analysis/tests/crypto_derivatives/test_near_futures_canary.py
analysis/tests/crypto_derivatives/test_position_map.py
analysis/tests/crypto_time/test_crypto_time.py
```

## 4. Different scope, do not conflate

The later baseline contains:

```text
analysis/app/orderscope_local/crypto/
analysis/tests/crypto/
```

This package is UWBS-084 BTC spot ETF-flow work. It is not a replacement for the v0.1.6 crypto market-structure packages above.

Classification:

```text
orderscope_local/crypto/             KEEP_LATER_ACCEPTED
orderscope_local/crypto_archive/     REPLAY_V0_1_6
orderscope_local/crypto_canary/      REPLAY_V0_1_6
orderscope_local/crypto_context/     REPLAY_V0_1_6
orderscope_local/crypto_derivatives/ REPLAY_V0_1_6
orderscope_local/crypto_time/        REPLAY_V0_1_6
```

## 5. Shared files — DO NOT COPY WHOLESALE

The following reconstruction-line paths also differ, but later accepted baseline versions exist or later work depends on them:

```text
analysis/app/orderscope_local/cli.py
analysis/app/orderscope_local/contracts/__init__.py
analysis/app/orderscope_local/cross_market/__init__.py
analysis/app/orderscope_local/integration/operator.py
```

Classification:

```text
CONFLICT_REQUIRES_MANUAL_RECONCILIATION
```

Required crypto imports/exports should be added to the later version only where needed. Do not replace the later file with the reconstructed file.

## 6. Other reconstructed paths

The compare also reports reconstructed macro/theme/listing/storage/Worker paths. These are not automatically included in REC-01 because later main contains extensive corresponding accepted work.

They require a separate semantic-equivalence audit before replay:

```text
REC-02 — shared contracts / cross-market / integration reconciliation
REC-03 — non-crypto reconstructed lane equivalence audit
REC-04 — release evidence and cumulative regression closeout
```

## 7. REC-01 acceptance target

After replaying only the paths listed in sections 2 and 3, run:

```text
uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests/crypto_canary
uv run pytest -q analysis/tests/crypto_context
uv run pytest -q analysis/tests/crypto_time
uv run pytest -q analysis/tests/crypto_archive
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

Expected result is preservation of both:

- accepted UWBS-080..100 baseline behavior;
- accepted v0.1.6 UWBS-068..079 crypto behavior.

No empirical UWBS-079 Stage B validation is required for REC-01.

## 8. Decision

```text
REC-01 classification: COMPLETE
Selective crypto package replay: READY
Direct whole-branch merge: PROHIBITED
Shared-file reconciliation: DEFERRED TO REC-02
```
