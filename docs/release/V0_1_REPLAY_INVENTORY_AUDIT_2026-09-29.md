# v0.1 replay inventory and boundary audit — 2026-09-29

Status: **LOCAL v0.1.1–v0.1.3 BOUNDARIES ACCEPTED**

## Source and release identities

The historical source commits remain unchanged. The separate `release/reconstructed-v0.1` branch contains three cumulative synthetic boundaries above the frozen v0.1.0 base:

| Boundary | Commit | Accepted content |
| --- | --- | --- |
| v0.1.0 | `99b08a0b5fa1bec5921dc42e630c579a4e83c401` | Historical WBS/CP baseline |
| v0.1.1 | `bada5bff803321427eb3c8eb1f3d159460ba5dd1` | Operational/runtime extensions |
| v0.1.2 | `f69c52bf574212d1506df81abc7b15694abb7922` | Macro/carry |
| v0.1.3 | `b4df4e911597d9f17bfa0a50b2057c24159dee9f` | Cross-market, competitor, and official macro adapters |

The corrected `v0.1-replay-manifest.json` records 63, 12, and 42 historical source commits for these three boundaries, respectively. The original frozen inventory had 50, 12, and 39. Its omissions and replay conflicts were audited before acceptance.

## Inventory and conflict resolution

- v0.1.1 adds the missing W1 runtime dependency chain, the R0 local D1 export fixture, and the local acceptance test fix. The historical progress tracker and remote custody ACK test were excluded because they contain operational episodes outside this release boundary.
- v0.1.2 takes the macro/carry source and tests. Package exports were limited to that boundary; historical package initializers already contained later v0.1.3 exports.
- v0.1.3 adds the A0-002 shared validation prerequisite needed by relative repricing. Package exports combine accepted v0.1.2 and v0.1.3 symbols without provisional unrelated A0-002 exports.
- Manual cherry-pick conflict decisions were path-specific. No entire historical tracker or operational document was taken merely to make a conflict disappear. The manifest's `manual_resolution_notes` record the source-level decisions.
- PB-00..PB-10 work, live Worker activation, remote D1 mutation, and remote custody episodes were excluded from these release boundaries.

The interrupted first replay was preserved under `/tmp/orderscope-replay-interrupted-20260929/` during investigation. That path is diagnostic evidence, not an input to the accepted boundaries.

## Local acceptance

| Boundary | Python regression | TypeScript regression | Typecheck | Python compileall | Diff check |
| --- | ---: | ---: | --- | --- | --- |
| v0.1.1 | 544 passed | 178 passed | PASS | PASS | PASS |
| v0.1.2 | 563 passed | 178 passed | PASS | PASS | PASS |
| v0.1.3 | 614 passed | 178 passed | PASS | PASS | PASS |

The v0.1.3 Python suite was rerun after the final package export correction. TypeScript sources did not change after its full suite and typecheck passed. Python compileall and the staged diff check passed after the export correction. The temporary `node_modules` junction used for the target worktree's TypeScript tests was removed before commit.

These commits are candidate release boundaries. Tags and integration into `main` remain later gates under the version boundary plan.
