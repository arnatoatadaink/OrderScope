# v0.1.6 UWBS-072 implementation progress — 2026-09-30

Status: **ACCEPTED**

## Dependency base

UWBS-072 is implemented on top of accepted UWBS-071 source head:

```text
UWBS-071 head = 1cbcb9b65bbbea3b1ac251d614201d8d2ca86d5f
```

Development branch:

```text
codex/uwbs-072-near-btc-canary
```

The branch is 4 commits ahead / 0 behind the accepted UWBS-071 code head.

## Implemented scope

```text
analysis/app/orderscope_local/crypto_canary/
  __init__.py
  models.py
  evaluate.py
analysis/tests/crypto_canary/
  test_crypto_canary.py
```

The Canary combines explicit layer states for:

- BTC directional context;
- NEAR directional context;
- BTC-relative strength;
- derivatives positioning;
- liquidation context;
- weekend-liquidity context;
- target-specific catalyst context.

Candidate outputs:

- `MULTI_LAYER_CONFIRMATION_CANDIDATE`
- `BTC_ONLY_MOVE`
- `NEAR_IDIOSYNCRATIC_MOVE`
- `LIQUIDATION_ONLY_AMPLIFICATION`
- `WEEKEND_THIN_LIQUIDITY_CANDIDATE`
- `CONFLICTING_EVIDENCE`
- `INSUFFICIENT_EVIDENCE`

All outputs remain Interpretation candidates with `causal_status = candidate_only`.

## False-positive boundary

UWBS-072 explicitly rejects the following shortcuts:

```text
BTC move alone                 -> not target confirmation
NEAR move without BTC          -> idiosyncratic candidate
liquidation alone              -> not new directional positioning
weekend context alone          -> not macro confirmation
contradicting layer            -> conflicting evidence
missing core layers            -> insufficient evidence
```

No trader identity, participant nationality, institution attribution, or deterministic BTC causality is emitted.

## Candidate source commits

```text
1902b89cd4ea3269f10456d3a292b54bd788bced  canary contracts
c98458b26144158d08a74be1e57277c0d9fd641c  conservative evaluator
00b82180931dc61fd40cf18b632a9244bc9c476f  public exports
4ea346dfab96b1a2ba1e685bf6daba27341445a0  focused tests
```

## Acceptance evidence

Local validation completed successfully:

```text
focused crypto_canary: 10 passed
full Python regression: 673 passed, 1 warning
compileall: PASS
diff check: PASS
TypeScript: not required — Python-only diff
```

The single warning is the existing Starlette / AnyIO deprecation warning from `starlette/testclient.py` and is not introduced by UWBS-072.

## Diff audit

Compared with accepted UWBS-071 source head, only the new crypto-canary package and its focused tests are added. No UWBS-073+, provider activation, Worker/Cron, D1, UWBS-084 BTC ETF flow, or TypeScript changes are included.

## Acceptance effect

UWBS-072 is accepted for the v0.1.6 development series.

This task intentionally does not freeze thresholds from the September NEAR episode as universal constants. Historical real-data replay remains experimental and will be strengthened by UWBS-073..079 acquisition/archive/quality work.

Next task:

```text
UWBS-073 — Implement multi-venue futures/perpetual acquisition adapters
```
