# REC-02 — Shared-file reconciliation — 2026-10-01

Status: **ACCEPTED / NO CODE CHANGE REQUIRED**

Branch:

```text
codex/post-v0-1-6-reconciliation-audit
```

REC-01 acceptance:

```text
03772c1609045ad8413f78550840d9ded75f8982
```

## Scope

REC-02 reviewed the shared paths that differed between the reconstructed v0.1.6 lineage and the later accepted UWBS-100 baseline:

```text
analysis/app/orderscope_local/cli.py
analysis/app/orderscope_local/contracts/__init__.py
analysis/app/orderscope_local/cross_market/__init__.py
analysis/app/orderscope_local/integration/operator.py
```

The rule was to preserve later accepted behavior and add only missing v0.1.6 semantics actually required by the replayed crypto packages.

## Findings

### `integration/operator.py`

The current reconciliation branch and `codex/v0-1-6-cp16x-acceptance` use the same blob:

```text
e05031760e397f653bc84958638a31b1ac014b20
```

Classification:

```text
IDENTICAL — KEEP AS-IS
```

### `contracts/__init__.py`

The later accepted UWBS-100 baseline contains the v0.1.6 shared contract exports plus later contracts for capital structure, catalyst repricing, commodities, BTC ETF flow, cross-asset regimes, Physical-SaaS, and related accepted work.

The replayed crypto packages import their own package-local models/functions and do not require additional symbols to be added to the root contracts export surface.

Classification:

```text
LATER_ACCEPTED_SUPERSET — KEEP AS-IS
```

### `cross_market/__init__.py`

The later accepted version retains the v0.1.6 macro/cross-market exports and additionally exports later accepted A0 source-manifest, Alpaca daily, and validation surfaces.

No replayed crypto package requires a missing cross-market root export.

Classification:

```text
LATER_ACCEPTED_SUPERSET — KEEP AS-IS
```

### `cli.py`

The later accepted CLI preserves the v0.1.6 local commands while adding later accepted replay/deletion execution paths and temporary-news-store integration.

The replayed crypto packages do not introduce a CLI command requirement in UWBS-068..079 acceptance scope.

Classification:

```text
LATER_ACCEPTED_SUPERSET — KEEP AS-IS
```

## Regression evidence

REC-01 validation after selective crypto replay already exercised the cumulative codebase:

```text
crypto_derivatives  62 passed
crypto_canary       20 passed
crypto_context       9 passed
crypto_time         10 passed
crypto_archive      10 passed
full analysis     1097 passed
compileall           PASS
git diff --check     PASS
```

This provides executable evidence that no missing shared import/export is required for the replayed crypto packages at this boundary.

## Decision

```text
cli.py                         KEEP LATER ACCEPTED
contracts/__init__.py          KEEP LATER ACCEPTED
cross_market/__init__.py       KEEP LATER ACCEPTED
integration/operator.py        IDENTICAL
shared code edits              NONE
REC-02                         ACCEPTED
```

REC-02 is closed without source-code changes. The next gate is REC-03: semantic-equivalence audit for non-crypto reconstructed paths where later accepted implementations may supersede or overlap reconstructed v0.1.6 work.
