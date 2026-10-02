# REL-05 / v0.1.5 Exact-Boundary Acceptance

Date: 2026-10-02
Status: ACCEPTED / TAG READY

## Boundary

- Version: v0.1.5
- Exact commit: `415de1f1dd42f70bd66992961cb43be7edba6ade`
- Commit subject: `Reconstruct v0.1.5 listing compliance boundary`
- Scope: cumulative reconstructed v0.1 lineage through UWBS-067 Listing Compliance / Earnings Repricing Canary.

## Exact-boundary validation

Validation was executed directly on the exact release boundary with a clean working tree.

- `uv run pytest -q analysis/tests` -> 635 passed, 1 warning
- `uv run python -m compileall -q analysis/app` -> PASS
- `git diff --check` -> PASS
- `npm test` -> 178 passed, 0 failed
- `npm run typecheck` -> PASS

The single Python warning is the pre-existing Starlette / AnyIO `BlockingPortal` deprecation warning and is non-blocking for this release boundary.

## Acceptance interpretation

This acceptance validates the reconstructed source boundary, cumulative regression surface, Worker regression surface, compileability, whitespace integrity, and TypeScript type safety for v0.1.5.

Listing-compliance and repricing-canary outputs remain analytical capabilities rather than universal exchange-rule guarantees. Empirical repricing thresholds and cross-exchange generalization remain subject to calibration and later empirical validation.

## Decision

REL-05 is Accepted. The exact boundary `415de1f1dd42f70bd66992961cb43be7edba6ade` is TAG READY as v0.1.5.
