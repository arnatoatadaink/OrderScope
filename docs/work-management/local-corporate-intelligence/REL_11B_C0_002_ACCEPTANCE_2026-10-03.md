# OrderScope — REL-11B / C0-002 Acceptance — 2026-10-03

Status: **ACCEPTED / INTEGRATED**
Release: `v0.1.11`
Formal WBS: `C0-002`
Canonical source: `UWBS-107`
Integrated commit: `25a734313987635e97ee6c664d4506be1effb907`
Implementation branch: `feat/rel-11b-c0-002-abnormal-flow`

## Acceptance evidence

Repository-environment validation supplied on 2026-10-03:

```text
uv run pytest -q \
  analysis/tests/crypto_onchain/test_c0_001_registry.py \
  analysis/tests/crypto_onchain/test_c0_002_flow_metrics.py
19 passed in 1.63s

uv run pytest -q analysis/tests
1137 passed in 41.08s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no error output)
```

## Accepted capability

- deterministic 5m / 15m / 60m outbound windows;
- no-lookahead filtering on confirmed, available and accepted timestamps;
- USD notional completeness preserved instead of treating missing values as zero;
- balance-ratio, baseline-ratio and z-score metrics where valid;
- burst and destination metrics;
- deterministic `NORMAL`, `ELEVATED`, `ABNORMAL_FLOW_CANDIDATE`, and `UNKNOWN` states;
- alternative explanations retained separately as treasury movement, bridge rebalance, or unknown;
- abnormal-flow state does not imply exploit, theft, malicious intent, or confirmed security incident.

## Boundary retained

REL-11B does not implement market-context joins, exploit attribution, historical replay, provider activation, mempool monitoring, Worker/Cron/D1 mutation, or automated trading.

## Critical-path transition

```text
REL-11A / C0-001 / UWBS-106  ACCEPTED / INTEGRATED
REL-11B / C0-002 / UWBS-107  ACCEPTED / INTEGRATED
    -> REL-11C / C0-003 / UWBS-108  NEXT
```

Release-level cumulative `v0.1.11` acceptance remains deferred to `REL-11X`.
