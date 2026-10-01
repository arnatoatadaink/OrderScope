# REC-04 — Cumulative acceptance plan — 2026-10-01

Status: **READY FOR FINAL LOCAL VALIDATION**

Branch:

```text
codex/post-v0-1-6-reconciliation-audit
```

Prerequisites:

```text
REC-01  ACCEPTED
REC-02  ACCEPTED
REC-03  ACCEPTED
```

## Purpose

REC-04 is the final cumulative validation gate after reconstructing the accepted v0.1.6 lineage onto the later UWBS-080..100 baseline.

The goal is not to re-prove empirical hypotheses. The goal is to prove that the cumulative code line remains executable and regression-safe across:

- v0.1.6 crypto packages;
- restored listing-compliance and theme packages;
- later UWBS-080..100 analysis work;
- Worker/news/scheduler runtime;
- Python and TypeScript static checks.

## Required local validation

Run exactly:

```bash
git fetch origin
git switch codex/post-v0-1-6-reconciliation-audit
git pull --ff-only origin codex/post-v0-1-6-reconciliation-audit

uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests/crypto_canary
uv run pytest -q analysis/tests/crypto_context
uv run pytest -q analysis/tests/crypto_time
uv run pytest -q analysis/tests/crypto_archive
uv run pytest -q analysis/tests/listing_compliance
uv run pytest -q analysis/tests/theme

uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check

npm test
npm run typecheck
```

## Acceptance criteria

REC-04 is Accepted only if all of the following hold:

1. all focused suites pass;
2. full Python regression passes with no failures;
3. compileall passes;
4. git diff --check passes;
5. npm test passes with zero failures;
6. npm run typecheck passes;
7. no new blocking warning or regression appears.

Existing non-blocking Starlette/AnyIO deprecation warnings, if unchanged, do not block acceptance.

## Release-boundary interpretation

If REC-04 passes:

```text
UWBS-068..079 crypto reconstruction  preserved
UWBS-080..100 accepted baseline      preserved
listing_compliance                   restored
Theme model                          restored
Worker/news/scheduler                preserved
cumulative reconstruction            ACCEPTED
```

UWBS-079 Stage B remains experimental/pending and is not converted into a validated recurrence claim by this acceptance.

No merge to main or release tag is authorized by REC-04 alone; those remain a separate integration decision.
