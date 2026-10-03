# OrderScope — REL-11C / C0-003 Acceptance — 2026-10-03

Status: **ACCEPTED / INTEGRATED**
Release: `v0.1.11`
Formal WBS: `C0-003`
Canonical source: `UWBS-108`
Integrated commit: `a3223f09fec1c7efe7dba70a8a1cd14ddc76fc60`
Implementation branch: `feat/rel-11c-c0-003-market-context`

## Acceptance evidence

Repository-environment validation supplied on 2026-10-03:

```text
uv run pytest -q \
  analysis/tests/crypto_onchain/test_c0_001_registry.py \
  analysis/tests/crypto_onchain/test_c0_002_flow_metrics.py \
  analysis/tests/crypto_onchain/test_c0_003_market_context.py
26 passed in 2.18s

uv run pytest -q analysis/tests
1144 passed in 42.45s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no error output)
```

## Accepted capability

- joins C0-002 abnormal-flow evidence with accepted BTC-relative return evidence;
- reuses accepted derivatives observations for OI, funding and derivatives volume;
- reuses liquidation observations without redefining their source contract;
- preserves source-record provenance and event/context timestamps;
- distinguishes price-down + OI-down as a deleveraging candidate;
- distinguishes price-down + OI-up as a new-short candidate;
- returns mixed/insufficient when evidence does not support either pattern;
- explicitly retains `causality = NOT_ESTABLISHED`.

## Boundary retained

REL-11C does not establish causal security-incident attribution, exploit identity, historical incident timestamp truth, provider activation, Worker/Cron/D1 mutation, or automated trading.

## Critical-path transition

```text
REL-11A / C0-001 / UWBS-106  ACCEPTED / INTEGRATED
REL-11B / C0-002 / UWBS-107  ACCEPTED / INTEGRATED
REL-11C / C0-003 / UWBS-108  ACCEPTED / INTEGRATED
    -> REL-11D / C0-004 / UWBS-109  NEXT
```

Release-level cumulative `v0.1.11` acceptance remains deferred to `REL-11X`.
