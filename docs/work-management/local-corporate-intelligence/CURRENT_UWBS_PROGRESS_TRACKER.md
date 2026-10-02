# OrderScope — Current UWBS Progress Tracker

Status: **CURRENT UWBS OVERLAY**
Updated: 2026-10-02

This tracker is the current UWBS-specific overlay for canonical task progress. It supplements older integrated trackers that may predate the v0.1.6 reconstruction and post-v0.1.6 reconciliation.

Canonical ID meanings remain governed by `WBS_PROVISIONAL_ID_REGISTRY.md`.
Detailed v0.1.6 branch provenance is recorded in `UWBS_V0_1_6_BRANCH_RECONCILIATION_2026-10-02.md`.

## Status rule

A UWBS item is not downgraded to `Pending` merely because its original task branch is old or diverged. Use the newest accepted reconciliation evidence:

1. task branch implementation provenance;
2. local/CP acceptance evidence;
3. selective replay / semantic reconciliation evidence;
4. current `main` integration state.

## v0.1.6-era corrected status

| UWBS | Status | Implementation provenance | Acceptance / integration provenance |
|---|---|---|---|
| UWBS-062 | **Accepted / Integrated** | `theme/ontology.py` | REC-03 replay `9a40e29112e0cfae50828be7270cf1995ec53b97`; REC-03 acceptance `b3f18252f9ad3efdf17ea8c1c2ddea8dcf838861` |
| UWBS-063 | **Accepted / Integrated** | `theme/reaction.py` | REC-03 replay / acceptance |
| UWBS-064 | **Accepted / Integrated** | `theme/observation.py` | REC-03 replay / acceptance |
| UWBS-065 | **Accepted / Integrated** | `theme/state.py` | REC-03 replay / acceptance |
| UWBS-066 | **Accepted / Integrated** | `theme/calibration.py` | REC-03 replay / acceptance |
| UWBS-067 | **Accepted / Integrated** | `codex/uwbs-067-listing-compliance` @ `44e7a2d31c6ef5ebebafb77fbe44ac307625b014` | REC-03 selective replay / acceptance |
| UWBS-068 | **Accepted / Integrated** | `codex/uwbs-068-crypto-derivatives-contract` @ `716644a679f8f353d409e48ec06351dc38c2060e` | v0.1.6 CP-16X; REC-01 replay |
| UWBS-069 | **Accepted / Integrated** | `codex/uwbs-069-btc-relative-context` @ `56cd68aabd06326041acc8a37dc458f6cc3beb2f` | v0.1.6 CP-16X; current `crypto_context` package |
| UWBS-070 | **Accepted / Integrated planning evidence** | no dedicated task branch identified | CP-070A accepted in v0.1.6 progress reflection; source/provider survey task |
| UWBS-071 | **Accepted / Integrated** | `codex/uwbs-071-crypto-time-windows` @ `1cbcb9b65bbbea3b1ac251d614201d8d2ca86d5f` | v0.1.6 CP-16X; REC-01/current `crypto_time` |
| UWBS-072 | **Accepted / Integrated** | `codex/uwbs-072-near-btc-canary` @ `4ea346dfab96b1a2ba1e685bf6daba27341445a0` | v0.1.6 CP-16X; REC-01/current `crypto_canary` |
| UWBS-073 | **Accepted / Integrated** | `codex/uwbs-073-multivenue-adapters` @ `d602de71a93b8ac8c8877c0d0114d66553046555` | v0.1.6 CP-16X; REC-01 |
| UWBS-074 | **Accepted / Integrated** | `codex/uwbs-074-derivatives-archive` @ `4c34a8f36f1083f84d46a788f62b9e7b05ad4adc` | v0.1.6 CP-16X; REC-01/current `crypto_archive` |
| UWBS-075 | **Accepted / Integrated** | `codex/uwbs-075-liquidation-cascade` @ `aece57aa74fd89e9ca975668c6f00817aa442d25` | v0.1.6 CP-16X; REC-01 |
| UWBS-076 | **Accepted / Integrated** | `codex/uwbs-076-position-map-oi-retention` @ `a0cfe87e2f22fd470b97ca218959ef45eb668128` | v0.1.6 CP-16X; REC-01 |
| UWBS-077 | **Accepted / Integrated** | `codex/uwbs-077-cross-venue-qa` @ `1348ff64520fee5f0215591a985b36b6fb66e8e8` | v0.1.6 CP-16X; REC-01 |
| UWBS-078 | **Accepted / Integrated** | `codex/uwbs-078-near-futures-position-canary` @ `50d3b0697b8c6e07e4bab22c7faec11472154249` | v0.1.6 CP-16X; REC-01 |
| UWBS-079 Stage A | **Accepted / Integrated** | `codex/uwbs-079-weekend-rerisk-validation` @ `bf1a6294bf18ee2fad81a140e8a52b46b5f96c20` | v0.1.6 CP-16X; REC-01 |
| UWBS-079 Stage B | **Pending / Experimental** | longitudinal empirical-validation track | explicitly excluded from implementation blocker / validated-fact status |

## Reconstruction / reconciliation branch ledger

| Role | Branch | Head / key commit | Status |
|---|---|---|---|
| v0.1.6 reconstructed acceptance | `codex/v0-1-6-cp16x-acceptance` | `bfaf89c68daa656b7d75317f086458257cc94da9` | Accepted implementation boundary through UWBS-079 Stage A |
| cumulative post-v0.1.6 reconciliation | `codex/post-v0-1-6-reconciliation-audit` | `7734c2779b21ac9f6879dfa08e9def67c375f8a7` | REC-01..04 accepted / approved fast-forward line |
| crypto selective replay | same cumulative branch | `f2b1bd24127814d5c025287f1c4f7186511c470f` | REC-01 accepted scope |
| theme/listing selective replay | same cumulative branch | `9a40e29112e0cfae50828be7270cf1995ec53b97` | REC-03 implementation |
| non-crypto reconciliation acceptance | same cumulative branch | `b3f18252f9ad3efdf17ea8c1c2ddea8dcf838861` | REC-03 accepted |

## Validation evidence retained

v0.1.6 CP-16X:

```text
crypto_derivatives  62 passed
crypto_canary       20 passed
crypto_context       9 passed
crypto_time         10 passed
crypto_archive      10 passed
full analysis      746 passed, 1 warning
compileall          PASS
git diff --check    PASS
```

Post-v0.1.6 cumulative reconciliation:

```text
crypto_derivatives   62 passed
crypto_canary        20 passed
crypto_context        9 passed
crypto_time          10 passed
crypto_archive       10 passed
listing_compliance    9 passed
theme                 12 passed
full analysis       1118 passed
Worker               227 passed / 0 failed
compileall            PASS
git diff --check      PASS
npm typecheck         PASS
```

## Current correction

Previous progress interpretations that marked canonical UWBS-062..079 wholesale as unimplemented are obsolete.

Current interpretation:

```text
UWBS-062..067        ACCEPTED / INTEGRATED
UWBS-068..078        ACCEPTED / INTEGRATED
UWBS-079 Stage A     ACCEPTED / INTEGRATED
UWBS-079 Stage B     PENDING / EXPERIMENTAL
```

Future UWBS progress updates should include branch name, branch HEAD or representative implementation commit, acceptance commit/evidence, and current main integration state.
