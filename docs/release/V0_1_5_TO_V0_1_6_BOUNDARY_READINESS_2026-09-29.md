# v0.1.5–v0.1.6 boundary readiness — 2026-09-29

Status: **RESERVED; NO VERIFIED IMPLEMENTATION CLOSEOUT IN REVIEWED REFS**

The cumulative release line currently ends at reconstructed v0.1.3 (`b4df4e911597d9f17bfa0a50b2057c24159dee9f`). v0.1.4 is blocked by the separate AI Theme source audit. Neither v0.1.5 nor v0.1.6 can be inserted into that lineage until all preceding boundaries and their own source inventories are accepted.

## Canonical scope

Commit `cfc850c94738820f3b12e783791c9030edd216dc` created `WBS_PROVISIONAL_ID_REGISTRY.md` and resolves historical ID collisions:

| Version | Historical alias | Canonical ID | Scope |
| --- | --- | --- | --- |
| v0.1.5 | UWBS-035 | UWBS-067 | LVWR listing compliance and earnings repricing Canary |
| v0.1.6 | UWBS-036..047 | UWBS-068..079 | Crypto derivatives facts, BTC context, 24/7 windows, venue acquisition/archive, liquidation, OI/Position Map, data quality and Canaries |

Old UWBS-035/036 also label accepted v0.1.3 Cross-Market work; selecting commits by those aliases would contaminate a later boundary.

## Source candidates found

| Source SHA | Classification | Decision |
| --- | --- | --- |
| `1d158642f98ae57c2cd38ce76059b34b29426abb` | DESIGN_PROVENANCE_ONLY | LVWR price-rediscovery case; historical evidence only. |
| `d7eaffec4371a3594fcbc561cc1f2df5d136b059` | DESIGN_PROVENANCE_ONLY | Tracks the LVWR listing-compliance repricing task; no accepted fixture closeout. |
| `fc8a9a11d3690129619aa4a1825f08bd03d968c7` | DESIGN_PROVENANCE_ONLY | Futures position reading/derivatives collection report. |
| `4d842af1dd9165ee08aa05292f3fd8072ace15c3` | DESIGN_PROVENANCE_ONLY | Crypto futures position tracking backlog. |
| `1b5d2d27897cd5925fe81a5e3bbc9ab925453581` | DESIGN_PROVENANCE_ONLY | NEAR liquidation phase-transition report. |
| `cfc850c94738820f3b12e783791c9030edd216dc` | DOC_ONLY_OPTIONAL | Canonical ID registry; audit authority, not capability implementation. |

After refreshing origin refs, commit-subject searches found no implementation commits labeled UWBS-067..079. The reviewed origin/main planning backlog still marks the corresponding historical tasks pending, and the earlier version-boundary plan also reserves v0.1.5/v0.1.6 without verified closeout. These searches do not prove that no implementation exists anywhere; they establish that the currently reviewed evidence does not justify a release checkpoint.

## Gate before reconstruction

For each lane, identify implementation, tests, exports, fixes and acceptance commits by code behavior and paths, not solely by commit subject. Freeze a path-aware allowlist; check dependencies against the preceding reconstructed boundary; then run focused and full regression, typecheck/compile and diff checks. Until that evidence is present, do not create placeholder commits, tags or a later-version snapshot on `release/reconstructed-v0.1`.
