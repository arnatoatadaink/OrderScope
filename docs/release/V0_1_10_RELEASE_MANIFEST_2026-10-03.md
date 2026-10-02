# v0.1.10 Release Manifest — 2026-10-03

## Status

**ACCEPTED / TAG READY**

This manifest does not create a Git tag.

## Boundary

- Version: `v0.1.10`
- Release theme: PB / active-market validation closeout
- Scope: `PB-00..PB-10`
- Boundary SHA: `c1e27d8367c490543e1d207f62d77f3bb5e8bc4e`
- Formal predecessor: `v0.1.9` boundary `fcfba651dbead9d035019e330f61986f5a1a60f7`
- Reconstruction property: one cumulative successor commit on the formal accepted v0.1.9 line, overlaying exactly the reviewed 16 PB closeout files.

## Validation evidence

| Check | Result |
|---|---|
| Exact SHA checkout | PASS |
| Clean working tree | PASS |
| Python analysis suite | 1097 passed |
| Python compileall | PASS |
| `git diff --check` | PASS |
| Worker tests | 228 passed / 0 failed |
| TypeScript typecheck | PASS |

## Lineage evidence

| Check | Result |
|---|---|
| Base | `fcfba651dbead9d035019e330f61986f5a1a60f7` |
| Head | `c1e27d8367c490543e1d207f62d77f3bb5e8bc4e` |
| Ahead / behind | 1 / 0 |
| Merge base | formal v0.1.9 boundary |
| Changed files | exactly 16 reviewed PB closeout files |

## Superseded candidate

`b0cd43ec4ddcce4bd64303bafb2891ebe23c0dcf` is **SUPERSEDED / NOT A TAG TARGET** because it was based on historical endpoint `8151d1c2727fd22b0e9f0222f589cee666c99ffc`, which diverges from the formal accepted cumulative v0.1.9 boundary.

## Version sequence

- `v0.1.9`: VIX / Cross-Asset Volatility, including `UWBS-094..100`
- `v0.1.10`: PB / active-market validation closeout, `PB-00..PB-10`
- `v0.1.11`: Crypto On-chain Event Intelligence, `UWBS-101..104`

## Explicit exclusions

This release acceptance does not authorize Git tag creation or push, production provider activation, Worker/Cron deployment, live D1 mutation, secrets or credential changes, automated trading, force push, or history rewrite.
