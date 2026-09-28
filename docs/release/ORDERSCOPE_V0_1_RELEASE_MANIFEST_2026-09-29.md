# OrderScope v0.1 Release Manifest — 2026-09-29

Status: **VERSIONING IN PROGRESS — PB CLOSED, MAIN INTEGRATION PENDING**

## 1. Versioning rule

The v0.1 series is organized by functional boundary rather than by historical commit numbering.

- `v0.1.0`: original WBS / CP implementation baseline, excluding PB execution.
- `v0.1.1..v0.1.9`: UWBS-originated capability extensions grouped by lane.
- `v0.1.10`: PB / active-market validation closeout.

A version is taggable only when its implementation/acceptance boundary is identified by a stable commit and the release scope is not dependent on an unresolved acceptance condition.

Historical Git topology is not rewritten merely to make the version sequence visually linear. Where an older lane was incorporated into formal WBS before this release scheme existed, the release manifest records its logical ownership and a boundary SHA is reconstructed separately.

## 2. Version matrix

| Version | Functional boundary | Work package / UWBS | Current release state | Boundary SHA |
|---|---|---|---|---|
| v0.1.0 | Original WBS / CP baseline, PB excluded | L0/L1 foundation, X0/N1/W1/CS0/MR0 and original formal work | Boundary reconstruction required | TBD |
| v0.1.1 | Operational / runtime extensions | UWBS-001..004, 016, 023..026; incorporated into formal operational WBS | Logical scope accepted; boundary reconstruction required | TBD |
| v0.1.2 | Macro / carry context | UWBS-011..015 -> A0-003..007 | Logical scope incorporated; boundary reconstruction required | TBD |
| v0.1.3 | Cross-market / competitor / official macro adapters | UWBS-027..036 -> A0-008..017 | Logical scope incorporated; boundary reconstruction required | TBD |
| v0.1.4 | AI theme lane | UWBS-062..066 | Reserved; do not tag until acceptance is proven | — |
| v0.1.5 | Listing-compliance lane | UWBS-067 | Reserved; do not tag until acceptance is proven | — |
| v0.1.6 | Crypto market-structure lane | UWBS-068..079 | Reserved; do not tag until acceptance is proven | — |
| v0.1.7 | Oil / commodity / cross-asset | UWBS-080..086 | ACCEPTED / taggable | `33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d` |
| v0.1.8 | Physical-SaaS | UWBS-087..093 | ACCEPTED / taggable | `ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325` |
| v0.1.9 | VIX / cross-asset volatility | UWBS-094..100 | ACCEPTED / taggable | `8151d1c2727fd22b0e9f0222f589cee666c99ffc` |
| v0.1.10 | PB / active-market validation closeout | PB-00..PB-10 | CLOSED / ACCEPTED / taggable after integration | `b31e6caf06e885133183149c040d4774a02df23e` |

## 3. v0.1.10 PB boundary

The PB lane is complete through PB-10.

The six BTCUSD one-minute absences are not part of the PB completion condition after the 2026-09-29 reconciliation. They remain a separate data-quality follow-up and must not be used to reopen PB or block `v0.1.10`.

Governing reconciliation:

`docs/work-management/local-corporate-intelligence/L1-003_PB_FINAL_CLOSE_RECONCILIATION_2026-09-29.md`

This keeps the historical provider evidence intact while separating future BTCUSD recovery/absence-acknowledgement work from the completed PB lane.

## 4. Known hard release boundaries

### v0.1.7

Boundary: `33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d`

Meaning: oil / commodity / BTC ETF-flow / cross-asset regime lane accepted through UWBS-086 under the checked-in shadow-runtime capacity boundary. This does not imply unrestricted live-mode capacity acceptance.

### v0.1.8

Boundary: `ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325`

Meaning: Physical-SaaS lane closed through UWBS-093, including deployment lifecycle, milestone reconciliation, funnel/slippage, recurring-revenue quality, M&A overlay, applicability guard and Canary work.

### v0.1.9

Boundary: `8151d1c2727fd22b0e9f0222f589cee666c99ffc`

Meaning: volatility lane accepted through UWBS-100, including VIX contracts/term structure, BTC IV30, MSTR IV30, MSTR/BTC IV differential and historical calibration / false-positive / capacity evaluation.

### v0.1.10

Boundary: `b31e6caf06e885133183149c040d4774a02df23e`

Meaning: PB-00..PB-10 is administratively and semantically closed. The BTCUSD six-minute gap is carried outside PB as future data-quality work.

## 5. Main integration state

At manifest creation time, the repository's `main` branch has not yet been declared the complete v0.1-series integration point. Accepted work remains distributed across the UWBS and L1/PB branches.

Do not create a final `v0.1-series-complete` claim until:

1. the required accepted branches are integrated into the intended release branch/main without dropping accepted files;
2. the full regression/typecheck/compile checks appropriate to the integrated tree pass;
3. the version-boundary comparison confirms that release-specific documents do not accidentally change runtime semantics;
4. final annotated tags are created only for versions whose boundary SHAs are proven.

## 6. Pending versioning work

### Boundary reconstruction

Determine stable historical boundary SHAs for:

- `v0.1.0`
- `v0.1.1`
- `v0.1.2`
- `v0.1.3`

Do not invent these from dates alone. Reconstruct them from the repository DAG, acceptance records and incorporation commits.

### Reserved lanes

`v0.1.4..v0.1.6` remain reserved for canonical UWBS-062..079. They must not receive release tags merely because their IDs are registered.

### BTCUSD follow-up

The BTCUSD six-minute gap remains outside PB and outside `v0.1.10`. It should receive a separate future WBS/UWBS identity before additional implementation or mutation work.

## 7. Release interpretation

```text
v0.1.0      original system baseline (PB excluded)
v0.1.1-.3   incorporated operational / macro / cross-market extensions
v0.1.4-.6   reserved canonical lanes pending proven acceptance
v0.1.7-.9   accepted later analytical capability lanes
v0.1.10     PB active-market validation closeout
```

The next major product generation is expected to use `v0.2.x` for visualization / operator-UI infrastructure rather than silently extending the v0.1 backend/analysis series.
