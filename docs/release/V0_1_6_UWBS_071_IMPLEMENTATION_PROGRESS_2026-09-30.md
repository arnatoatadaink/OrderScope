# v0.1.6 UWBS-071 implementation progress — 2026-09-30

Status: **ACCEPTED**

## Dependency base

UWBS-071 is implemented on top of the accepted UWBS-069 source head:

```text
UWBS-069 head = 56cd68aabd06326041acc8a37dc458f6cc3beb2f
```

UWBS-070 is a source-survey/documentation task and therefore does not alter the code parent for this branch.

Development branch:

```text
codex/uwbs-071-crypto-time-windows
```

## Implemented scope

```text
analysis/app/orderscope_local/crypto_time/
  __init__.py
  models.py
  classify.py
analysis/tests/crypto_time/
  test_crypto_time.py
```

Implemented contracts:

- UTC-continuous crypto observation context;
- deterministic UTC date/hour classification;
- weekend versus weekday flag from UTC calendar only;
- configurable analysis windows that may overlap;
- conservative default analysis buckets for broad Asia/Europe/U.S. clock periods;
- wrapping analysis windows that cross UTC midnight;
- explicit traditional-market boundary context supplied by a caller/calendar source;
- provider-maintenance context as an explicit boundary type;
- no participant nationality, trader geography, or causal attribution fields.

## Semantic boundary

UWBS-071 deliberately does **not** infer CME reopen, cash-market open, DST shifts or holiday schedules from a timestamp alone.

```text
crypto timestamp -> deterministic UTC/day/window context
accepted calendar/provider evidence -> traditional-market boundary context
participant identity/geography -> not inferred
```

Region-named windows are analysis labels only. They do not assert who traded during the interval.

## Accepted source commits

```text
2373fd48b38d96d291edc5f54143b182ad983555  time-window contracts
4fd5e532f88189a193fa0f78a71579ef84207483  deterministic classifier/default windows
ed418ea0a44de65180ab73ed5dd5cfcfa1dfe20c  public exports
1cbcb9b65bbbea3b1ac251d614201d8d2ca86d5f  focused tests
```

## Local acceptance evidence

Executed locally on the development branch:

```text
focused Python: 10 passed
full Python: 663 passed, 1 warning
compileall: PASS
diff check: PASS
TypeScript: not required — Python-only diff
```

The single warning is the existing Starlette/AnyIO deprecation warning and is unrelated to UWBS-071.

## Diff audit

Compared with the accepted UWBS-069 source head, the branch changes only the new crypto-time package and its focused tests. No UWBS-072+, provider activation, Worker/Cron, D1, BTC spot ETF UWBS-084 or TypeScript changes are included.

## Acceptance conclusion

UWBS-071 is accepted for the v0.1.6 development series.

The following remain later work:

- NEAR/BTC multi-layer Canary (`UWBS-072`);
- live multi-venue adapters (`UWBS-073`);
- durable archive/catch-up (`UWBS-074`);
- liquidation/cascade metrics (`UWBS-075`);
- Position Map (`UWBS-076`);
- cross-venue divergence/data quality (`UWBS-077`);
- NEAR futures-position Canary (`UWBS-078`);
- Pacific weekend/re-risking validation (`UWBS-079`).
