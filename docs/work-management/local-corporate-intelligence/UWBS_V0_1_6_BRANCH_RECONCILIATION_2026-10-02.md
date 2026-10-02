# OrderScope — UWBS v0.1.6 branch reconciliation

Status: **CURRENT RECONCILIATION REFERENCE**
Date: 2026-10-02
Scope: canonical UWBS work implemented around the reconstructed v0.1.6 boundary and subsequently reconciled into `main`

## 1. Purpose

This record corrects UWBS progress interpretation where implementation existed on task-specific or reconstructed branches but was not visible from older current-tracker status text.

The status rule used here is:

1. canonical UWBS meaning comes from `WBS_PROVISIONAL_ID_REGISTRY.md`;
2. task-specific branch existence is implementation provenance, not by itself acceptance;
3. reconstructed v0.1.6 acceptance / REC acceptance is acceptance evidence;
4. current `main` package presence after reconciliation is the integration boundary;
5. empirical/research follow-up remains separate from implementation acceptance where explicitly stated.

## 2. Authoritative branch / commit boundaries

| Role | Branch / ref | Head / key commit | Meaning |
|---|---|---|---|
| reconstructed v0.1.6 acceptance | `codex/v0-1-6-cp16x-acceptance` | `bfaf89c68daa656b7d75317f086458257cc94da9` | Accepted crypto implementation boundary through UWBS-079 Stage A / CP-16X |
| cumulative reconciliation | `codex/post-v0-1-6-reconciliation-audit` | `7734c2779b21ac9f6879dfa08e9def67c375f8a7` | REC-01..04 accepted; approved fast-forward reconciliation line |
| REC-01 crypto replay | cumulative reconciliation branch | `f2b1bd24127814d5c025287f1c4f7186511c470f` | Replayed missing v0.1.6 crypto package roots |
| REC-03 non-crypto replay | cumulative reconciliation branch | `9a40e29112e0cfae50828be7270cf1995ec53b97` | Replayed missing `listing_compliance` and `theme` package roots |
| REC-03 acceptance | cumulative reconciliation branch | `b3f18252f9ad3efdf17ea8c1c2ddea8dcf838861` | Accepted non-crypto semantic-equivalence reconciliation |
| current integration target | `main` | inspect current `refs/heads/main`; reconciliation already integrated | Current authoritative code line |

The reconstructed branch must not be merged wholesale into current history. Its accepted missing deltas were selectively replayed and then regression-tested on the cumulative line.

## 3. Canonical UWBS status around v0.1.6

### AI-theme and listing-compliance lane

The current `main` tree contains `analysis/app/orderscope_local/theme/` with ontology, reaction, observation, state and calibration modules, and `analysis/app/orderscope_local/listing_compliance/`.

REC-03 explicitly accepted selective replay of the missing `theme` and `listing_compliance` roots, with focused validation of 12 theme tests and 9 listing-compliance tests plus full regression.

| UWBS | Canonical scope | Current status | Provenance / branch evidence | Main integration |
|---|---|---|---|---|
| UWBS-062 | AI / adjacent theme ontology and multi-theme exposure contract | **Accepted / integrated** | recovered as part of `theme` package via REC-03; implementation commit `9a40e291...` on `codex/post-v0-1-6-reconciliation-audit` | Yes |
| UWBS-063 | event × theme reaction-coefficient contract | **Accepted / integrated** | `theme/reaction.py`; REC-03 selective replay | Yes |
| UWBS-064 | cross-sectional theme reaction observation / confirmation | **Accepted / integrated** | `theme/observation.py`; REC-03 selective replay | Yes |
| UWBS-065 | theme activation / rotation / repricing state machine | **Accepted / integrated** | `theme/state.py`; REC-03 selective replay | Yes |
| UWBS-066 | historical calibration / Canary fixtures for theme reactions | **Accepted / integrated** | `theme/calibration.py`; REC-03 selective replay | Yes |
| UWBS-067 | LVWR listing-compliance / earnings-repricing Canary extension | **Accepted / integrated** | task branch `codex/uwbs-067-listing-compliance`, head `44e7a2d31c6ef5ebebafb77fbe44ac307625b014`; selectively replayed/accepted by REC-03 | Yes |

UWBS-067 therefore must not be classified as unimplemented merely because its original task branch diverges from current `main`.

### Crypto market-structure / derivatives lane

The v0.1.6 progress reflection records UWBS-068..078 as Accepted and UWBS-079 Stage A as Accepted. UWBS-079 Stage B remains Pending / Experimental and is not an implementation blocker.

| UWBS | Canonical scope | Current implementation status | Task-specific branch provenance | Task branch head | Current integration interpretation |
|---|---|---|---|---|---|
| UWBS-068 | crypto derivatives Fact / Derived Metric contract | **Accepted** | `codex/uwbs-068-crypto-derivatives-contract` | `716644a679f8f353d409e48ec06351dc38c2060e` | replayed by REC-01; present in current cumulative/main line |
| UWBS-069 | BTC macro-leader / altcoin relative-context model | **Accepted** | `codex/uwbs-069-btc-relative-context` | `56cd68aabd06326041acc8a37dc458f6cc3beb2f` | current `crypto_context` package present; accepted v0.1.6 boundary |
| UWBS-070 | BTC institutional-flow / market-structure source survey | **Accepted** | no dedicated `codex/uwbs-070-*` branch found in branch inventory | n/a | accepted by CP-070A / v0.1.6 progress reflection; document/research task rather than package-only evidence |
| UWBS-071 | 24/7 crypto time-window / weekend-liquidity contract | **Accepted** | `codex/uwbs-071-crypto-time-windows` | `1cbcb9b65bbbea3b1ac251d614201d8d2ca86d5f` | replayed/present as `crypto_time` |
| UWBS-072 | NEAR/BTC multi-layer Canary and false-positive suite | **Accepted** | `codex/uwbs-072-near-btc-canary` | `4ea346dfab96b1a2ba1e685bf6daba27341445a0` | replayed/present as `crypto_canary` |
| UWBS-073 | multi-venue futures/perpetual acquisition adapters | **Accepted** | `codex/uwbs-073-multivenue-adapters` | `d602de71a93b8ac8c8877c0d0114d66553046555` | replayed into current crypto derivatives package |
| UWBS-074 | durable derivatives snapshot archive / catch-up lifecycle | **Accepted** | `codex/uwbs-074-derivatives-archive` | `4c34a8f36f1083f84d46a788f62b9e7b05ad4adc` | replayed/present as `crypto_archive` |
| UWBS-075 | liquidation normalization / cascade metrics | **Accepted** | `codex/uwbs-075-liquidation-cascade` | `aece57aa74fd89e9ca975668c6f00817aa442d25` | replayed into current crypto derivatives package |
| UWBS-076 | price-zone OI retention / Position Map analysis | **Accepted** | `codex/uwbs-076-position-map-oi-retention` | `a0cfe87e2f22fd470b97ca218959ef45eb668128` | replayed into current crypto derivatives package |
| UWBS-077 | cross-venue divergence / data-quality guards | **Accepted** | `codex/uwbs-077-cross-venue-qa` | `1348ff64520fee5f0215591a985b36b6fb66e8e8` | replayed into current crypto derivatives package |
| UWBS-078 | futures-position tracking Canary for NEAR reference episode | **Accepted** | `codex/uwbs-078-near-futures-position-canary` | `50d3b0697b8c6e07e4bab22c7faec11472154249` | replayed into current crypto derivatives package |
| UWBS-079 Stage A | Pacific weekend handoff / weekday re-risking validator | **Accepted** | `codex/uwbs-079-weekend-rerisk-validation` | `bf1a6294bf18ee2fad81a140e8a52b46b5f96c20` | code/contract accepted and present in cumulative line |
| UWBS-079 Stage B | multi-week empirical recurrence validation | **Pending / Experimental** | longitudinal validation track, not a release implementation branch blocker | n/a | not complete; must remain outside Accepted empirical-fact status |

## 4. v0.1.6 acceptance evidence

The reconstructed v0.1.6 CP-16X acceptance recorded:

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

The later cumulative reconciliation recorded:

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

Therefore the current planning interpretation is not "UWBS-062..079 unimplemented". The implementation boundary has been recovered and reconciled, except for the explicitly separate UWBS-079 Stage B empirical study.

## 5. Branch-ledger rules for future progress tracking

Every future UWBS progress row should carry at least:

- canonical UWBS ID;
- scope/title;
- status (`Planned`, `Implemented`, `Accepted`, `Integrated`, `Experimental/Pending`, etc.);
- implementation branch name when one exists;
- implementation branch HEAD or representative implementation commit;
- acceptance branch / acceptance commit when different;
- current `main` integration state;
- acceptance evidence file / test evidence;
- residual research or runtime boundary that is intentionally not accepted.

A task-specific branch that is old/diverged must not automatically downgrade an accepted task if its implementation has been selectively replayed and accepted on a newer cumulative branch.

## 6. Corrected restart implication

For the v0.1.6-era lanes:

```text
UWBS-062..067        ACCEPTED / INTEGRATED after REC-03
UWBS-068..078        ACCEPTED / INTEGRATED after v0.1.6 + REC-01 reconciliation
UWBS-079 Stage A     ACCEPTED / INTEGRATED
UWBS-079 Stage B     PENDING / EXPERIMENTAL longitudinal validation
```

Accordingly, none of UWBS-062..078 should be selected as a fresh implementation task solely because an older tracker omitted their branch provenance.
