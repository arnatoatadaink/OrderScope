# v0.1.10 Release Manifest — 2026-10-03

## Status

**ACCEPTED / TAG READY**

This manifest does not create a Git tag.

## Boundary

- Version: `v0.1.10`
- Release theme: PB / active-market validation closeout
- Scope: `PB-00..PB-10`
- Boundary SHA: `b0cd43ec4ddcce4bd64303bafb2891ebe23c0dcf`
- Predecessor: `v0.1.9` boundary `8151d1c2727fd22b0e9f0222f589cee666c99ffc`
- Reconstruction property: cumulative successor of `v0.1.9`; historical PB closeout evidence replayed onto the accepted semantic-version chain.

## Validation evidence

| Check | Result |
|---|---|
| Exact SHA checkout | PASS |
| Clean working tree | PASS |
| Python analysis suite | 986 passed |
| Python compileall | PASS |
| `git diff --check` | PASS |
| Worker tests | 228 passed / 0 failed |
| TypeScript typecheck | PASS |

## Scope boundary

`v0.1.10` closes the PB / active-market validation lane. It is intentionally separated from the next planned semantic release:

- `v0.1.9`: VIX / Cross-Asset Volatility, including `UWBS-094..100`
- `v0.1.10`: PB / active-market validation closeout, `PB-00..PB-10`
- `v0.1.11`: Crypto On-chain Event Intelligence, `UWBS-101..104`

## Explicit exclusions

This release acceptance does not authorize:

- creation or push of the `v0.1.10` Git tag;
- production provider activation;
- Worker/Cron deployment;
- live D1 mutation;
- secrets or credential changes;
- automated trading or trading mutations;
- force push or history rewrite.
