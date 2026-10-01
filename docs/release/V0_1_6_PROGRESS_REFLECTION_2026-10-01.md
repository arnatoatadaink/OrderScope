# OrderScope v0.1.6 Progress Reflection — 2026-10-01

Status: **DEVELOPMENT RELEASE ACCEPTED / UWBS-079 STAGE B EXPERIMENTAL PENDING**

## 1. Summary

The canonical v0.1.6 crypto lane (`UWBS-068..079`) has completed its implementation boundary and CP-16X regression acceptance.

The development-release boundary is accepted. The only remaining research item is the empirical multi-week recurrence validation for UWBS-079 Stage B. That residual item does not block the v0.1.6 development release because its hypothesis-validation status is explicitly separated from implementation acceptance.

## 2. Canonical UWBS progress

| UWBS | Scope | Current status |
| --- | --- | --- |
| UWBS-068 | Crypto derivatives Fact / Derived Metric contract | **Accepted** |
| UWBS-069 | BTC macro-leader / altcoin relative-context model | **Accepted** |
| UWBS-070 | BTC institutional-flow / market-structure source survey | **Accepted** |
| UWBS-071 | 24/7 crypto time-window / weekend-liquidity contract | **Accepted** |
| UWBS-072 | NEAR/BTC multi-layer Canary and false-positive suite | **Accepted** |
| UWBS-073 | Multi-venue futures/perpetual acquisition adapters | **Accepted** |
| UWBS-074 | Durable derivatives snapshot archive / catch-up lifecycle | **Accepted** |
| UWBS-075 | Liquidation normalization / cascade metrics | **Accepted** |
| UWBS-076 | Price-zone OI retention / Position Map analysis | **Accepted** |
| UWBS-077 | Cross-venue divergence / data-quality guards | **Accepted** |
| UWBS-078 | Futures-position tracking Canary for NEAR reference episode | **Accepted** |
| UWBS-079 Stage A | Pacific weekend handoff / weekday re-risking implementation | **Accepted** |
| UWBS-079 Stage B | Multi-week empirical recurrence validation | **Pending / Experimental** |

## 3. CP progress

| CP | Scope | Status |
| --- | --- | --- |
| CP-068A | Crypto derivatives core contracts | **Accepted** |
| CP-071A | 24/7 / weekend time-window contract | **Accepted** |
| CP-069A | BTC-relative context metrics | **Accepted** |
| CP-070A | Source/provider survey closeout | **Accepted** |
| CP-073A | Normalized multi-venue adapter interface | **Accepted** |
| CP-073B | Offline fixture adapters / venue normalization | **Accepted** |
| CP-074A | Snapshot archive contract | **Accepted** |
| CP-074B | Gap/catch-up lifecycle | **Accepted** |
| CP-075A | Liquidation normalization | **Accepted** |
| CP-075B | Cascade / imbalance metrics | **Accepted** |
| CP-076A | Position Map / OI retention metrics | **Accepted** |
| CP-077A | Cross-venue quality / divergence guards | **Accepted** |
| CP-072A | NEAR/BTC multi-layer Canary | **Accepted** |
| CP-078A | Futures-position NEAR Canary | **Accepted** |
| CP-079A | Weekend handoff / re-risking experimental validator | **Accepted (code / Stage A)** |
| CP-16X | Full regression + v0.1.6 boundary acceptance | **Accepted** |

## 4. Final acceptance evidence

CP-16X was validated locally on 2026-10-01.

```text
uv run pytest -q analysis/tests/crypto_derivatives
62 passed in 2.66s

uv run pytest -q analysis/tests/crypto_canary
20 passed in 1.84s

uv run pytest -q analysis/tests/crypto_context
9 passed in 1.82s

uv run pytest -q analysis/tests/crypto_time
10 passed in 1.04s

uv run pytest -q analysis/tests/crypto_archive
10 passed in 1.00s

uv run pytest -q analysis/tests
746 passed, 1 warning in 33.78s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The one warning is the existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not a v0.1.6 blocker.

## 5. Release boundary decision

```text
v0.1.6 implementation boundary          ACCEPTED
canonical UWBS-068..078                 ACCEPTED
UWBS-079 Stage A code/contract          ACCEPTED
CP-16X full regression                  ACCEPTED
UWBS-079 Stage B empirical recurrence   PENDING / EXPERIMENTAL
```

The development release must not represent UWBS-079 Stage B hypotheses as validated facts.

Specifically, the following remain unvalidated recurrence hypotheses:

- stable weekend-to-weekday re-risking recurrence;
- stable BTC-to-altcoin lead/lag structure;
- stable synchronized breadth;
- causal BTC leadership;
- participant geography inferred from regional time windows;
- universal weekend thresholds.

## 6. UWBS-079 Stage B follow-up track

Stage B should remain outside the critical path for subsequent implementation work.

Required future evidence:

- multiple independent weekends;
- risk-on, risk-off, BTC-flat and local-catalyst controls;
- predeclared comparison universe;
- weekend/weekday handoff windows using accepted UWBS-071 time semantics;
- BTC/altcoin returns and breadth;
- lag/correlation measures;
- spot and derivatives volume confirmation;
- OI / funding / liquidation context;
- 1h / 3h / 6h / 24h persistence;
- explicit alternative-explanation tracking.

Until sufficient independent samples are available, status remains `EXPERIMENTAL` rather than `VALIDATED_RECURRENCE`.

## 7. Current handoff

v0.1.6 is no longer the active implementation bottleneck.

Next planning work may proceed to the next canonical lane / UWBS sequence while UWBS-079 Stage B remains as a longitudinal validation track.

Acceptance evidence record:

- `docs/release/V0_1_6_CP16X_ACCEPTANCE_2026-10-01.md`

This progress reflection is the current v0.1.6 status reference for WBS/CP planning after CP-16X acceptance.
