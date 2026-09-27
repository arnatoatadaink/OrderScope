# UWBS-081 — Local Acceptance

Status: **ACCEPTED**
Scope: structured commodity supply/fundamental acquisition
Branch: `l1-003-local-market-recovery`

## Accepted boundary

UWBS-081 establishes a provider-neutral observation boundary for directly observed petroleum fundamentals and an EIA API v2 normalization path.

Accepted measures:

- commercial stocks;
- Cushing stocks;
- Strategic Petroleum Reserve stocks;
- field production;
- refinery inputs;
- refinery utilization;
- imports;
- exports;
- product supplied.

`product_supplied` preserves source semantics and is not renamed to demand or consumption. Crude-oil product supplied remains representable as a source observation. Four-week averages, demand interpretation, supply-disruption classification and oil-price causal interpretation remain downstream work.

## Local acceptance evidence

```text
Commodity fundamental contract: 9 passed
EIA petroleum normalizer:        7 passed
Full Python regression:          725 passed
compileall:                      PASS
git diff --check:                PASS
```

Observed environment used for the immediately preceding accepted Python lane: Python 3.13.x under `uv run`.

## Acceptance decision

**UWBS-081 is ACCEPTED.**

No live provider activation, paid procurement, Worker/Cron mutation, D1 mutation or PB execution occurred during this task.

## Next dependency

Proceed to:

`UWBS-082 — commodity supply / shipping / geopolitical event taxonomy`

The next boundary must keep source-observed event facts separate from causal interpretation, severity scoring and cross-asset regime inference.
