# OrderScope — REL-11D / C0-004 Acceptance — 2026-10-03

Status: **ACCEPTED / INTEGRATED**
Release: `v0.1.11`
Formal WBS: `C0-004`
Canonical source: `UWBS-109`
Integrated commit: `bc174c797dfa5d2d4091e3c3987ad5f0676bb29b`
Implementation branch: `feat/rel-11d-c0-004-historical-replay`

## Acceptance evidence

Repository-environment validation supplied on 2026-10-03:

```text
uv run pytest -q \
  analysis/tests/crypto_onchain/test_c0_001_registry.py \
  analysis/tests/crypto_onchain/test_c0_002_flow_metrics.py \
  analysis/tests/crypto_onchain/test_c0_003_market_context.py \
  analysis/tests/crypto_onchain/test_c0_004_historical_replay.py
33 passed in 2.28s

uv run pytest -q analysis/tests
1151 passed in 41.91s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no error output)
```

## Accepted capability

- preserves first on-chain-detectable, first public, and first official timestamps separately;
- supports deterministic +15m/+1h/+6h/+24h/+48h/+5d/+30d replay windows;
- computes token, BTC and BTC-relative returns only from compatible accepted market observations;
- incomplete one-sided windows fail closed rather than synthesizing values;
- preserves source-record provenance;
- carries C0-003 market-structure phases into historical replay;
- preserves the NEAR Intents reference two-phase pattern as distinct deleveraging-candidate and new-short-candidate phases;
- keeps `causality = NOT_ESTABLISHED` and does not treat article-reported percentage moves as quantitative truth.

## Boundary retained

REL-11D does not establish exploit causality, malicious intent, incident attribution, provider activation, Worker/Cron/D1 mutation, mempool monitoring, or automated trading.

## Critical-path transition

```text
REL-11A / C0-001 / UWBS-106  ACCEPTED / INTEGRATED
REL-11B / C0-002 / UWBS-107  ACCEPTED / INTEGRATED
REL-11C / C0-003 / UWBS-108  ACCEPTED / INTEGRATED
REL-11D / C0-004 / UWBS-109  ACCEPTED / INTEGRATED
    -> REL-11X cumulative v0.1.11 acceptance  NEXT
```

`v0.1.11` is not yet TAG READY until REL-11X cumulative validation is accepted.
