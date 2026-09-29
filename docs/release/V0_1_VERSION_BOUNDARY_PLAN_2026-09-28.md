# OrderScope v0.1 Version Boundary Plan — 2026-09-28

Status: **ACTIVE VERSION-BOUNDARY PLAN — RECONSTRUCTION IN PROGRESS**

> This document reconstructs the intended role of the missing `V0_1_VERSION_BOUNDARY_PLAN_2026-09-28.md` using the checked-in release manifest, boundary-reconstruction report, replay manifest, and the current reconstruction findings as source-of-truth.
>
> Historical implementation branches remain immutable. This plan defines logical release boundaries and the rules for constructing a clean cumulative release lineage.

## 1. Purpose

Define the functional boundaries for the OrderScope `v0.1.x` series so that each version can be interpreted consistently even though the historical implementation order is interleaved.

The release model is functional rather than chronological:

```text
v0.1.0  Original WBS / CP baseline, PB excluded
v0.1.1  Operational / Runtime
v0.1.2  Macro / Carry
v0.1.3  Cross-Market / Official Macro Adapters
v0.1.4  AI Theme
v0.1.5  Listing Compliance
v0.1.6  Crypto Market Structure
v0.1.7  Oil / Commodity / Cross-Asset
v0.1.8  Physical-SaaS
v0.1.9  VIX / Cross-Asset Volatility
v0.1.10 PB / Active-Market Validation Closeout
```

The intended successor generation is `v0.2.x`, beginning with visualization/operator-UI infrastructure rather than continuing to extend the v0.1 backend/analysis series indefinitely.

## 2. Version-boundary rules

A version boundary is accepted only when all of the following are true:

1. the functional scope is explicit;
2. implementation and required regression/fix commits are identified;
3. acceptance evidence exists for the scope being claimed;
4. unresolved future work is explicitly outside the version boundary;
5. the release snapshot does not accidentally include later logical-version functionality;
6. full regression / compile / typecheck / `git diff --check` appropriate to the snapshot pass;
7. the boundary SHA belongs to the clean reconstructed release lineage or is otherwise proven to be a pure historical boundary.

Historical source commits are evidence and must not be rewritten merely to create a prettier version graph.

## 3. Release-lineage policy

Because the original implementation order is interleaved, the clean release lineage is built separately from the historical source-of-truth branches.

```text
historical source branches
        |
        | immutable implementation / test / acceptance evidence
        v
release/reconstruction-tools
        |
        | frozen replay manifest + reconstruction tooling
        v
release/reconstructed-v0.1
        |
        +-- v0.1.0 historical clean base
        +-- v0.1.1 synthetic cumulative checkpoint
        +-- v0.1.2 synthetic cumulative checkpoint
        +-- v0.1.3 synthetic cumulative checkpoint
        +-- later accepted lanes integrated only after verification
```

Each synthetic checkpoint is a release identity. It does not replace the historical implementation SHA references contained in task-specific evidence.

## 4. Version matrix

| Version | Functional boundary | Canonical work scope | Boundary state | Boundary / source reference |
|---|---|---|---|---|
| `v0.1.0` | Original WBS / CP baseline, PB excluded | W0/L0/L1/I0/S0/E0/N0/N1/O0/X0 original baseline | **Clean historical boundary found** | `99b08a0b5fa1bec5921dc42e630c579a4e83c401` |
| `v0.1.1` | Operational / runtime extensions | UWBS-001..004, UWBS-016, UWBS-023..026; R0-001..009; W1 runtime capability | **Reconstructed; local acceptance passed** | `bada5bff803321427eb3c8eb1f3d159460ba5dd1` |
| `v0.1.2` | Macro / carry context | UWBS-011..015 -> A0-003..007 | **Reconstructed; local acceptance passed** | `f69c52bf574212d1506df81abc7b15694abb7922` |
| `v0.1.3` | Cross-market / competitor / official macro adapters | UWBS-027..036 -> A0-008..017 | **Reconstructed; local acceptance passed** | `b4df4e911597d9f17bfa0a50b2057c24159dee9f` |
| `v0.1.4` | AI theme lane | UWBS-062..066 | **Blocked: no accepted implementation inventory** | `V0_1_4_AI_THEME_SOURCE_INVENTORY_2026-09-29.md` |
| `v0.1.5` | Listing-compliance lane | UWBS-067 | **Reserved: design/backlog only in reviewed history** | `V0_1_5_TO_V0_1_6_BOUNDARY_READINESS_2026-09-29.md` |
| `v0.1.6` | Crypto market-structure lane | UWBS-068..079 | **Reserved: design/backlog only in reviewed history** | `V0_1_5_TO_V0_1_6_BOUNDARY_READINESS_2026-09-29.md` |
| `v0.1.7` | Oil / commodity / cross-asset | UWBS-080..086 | **Accepted / taggable after integration validation** | `33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d` |
| `v0.1.8` | Physical-SaaS | UWBS-087..093 | **Accepted / taggable after integration validation** | `ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325` |
| `v0.1.9` | VIX / cross-asset volatility | UWBS-094..100 | **Accepted / taggable after integration validation** | `8151d1c2727fd22b0e9f0222f589cee666c99ffc` |
| `v0.1.10` | PB / active-market validation closeout | PB-00..PB-10 | **Closed / Accepted; integrate after prior release lineage is stable** | PB close reconciliation boundary `b31e6caf06e885133183149c040d4774a02df23e` |

## 5. v0.1.0 boundary

The strongest historical boundary is:

```text
99b08a0b5fa1bec5921dc42e630c579a4e83c401
Accept N1-006 real-data benchmark
```

This commit is immediately before the first UWBS-originated W1 incorporation and therefore provides a naturally clean original-WBS baseline.

Interpretation:

- original WBS/CP functionality is included;
- PB execution is excluded;
- later R0/W1 operational extensions are excluded;
- later macro/cross-market lanes are excluded.

This SHA is the frozen starting point of `release/reconstructed-v0.1`.

## 6. v0.1.1 reconstructed boundary

The dependency inventory was repaired and accepted. The cumulative synthetic
boundary is `bada5bff803321427eb3c8eb1f3d159460ba5dd1`. The exact source
allowlist and conflict decisions are in `v0.1-replay-manifest.json` and
`V0_1_REPLAY_INVENTORY_AUDIT_2026-09-29.md`.

### Historical first replay blocker (resolved)

The following records the first replay attempt. Its proposed next steps were
completed during reconstruction and no longer describe the current branch state.

The first replay started from the clean `v0.1.0` base and stopped at:

```text
a54da090083de20495687c8f217e3a5fd693aba1
Integrate Packet D run evidence into live scheduler
```

with a semantic conflict in:

```text
src/worker.ts
```

### Interpretation of the conflict

The conflict must not be resolved by choosing either side blindly.

`a54da09...` is not merely live-operation evidence. It connects scheduler run evidence into the Worker execution path and therefore represents real runtime capability.

The conflict shows that the initial v0.1.1 replay manifest omitted historical runtime prerequisites that had modified `worker.ts` before Packet D integration.

At minimum, W1-002 implementation work has been identified as relevant prerequisite material, including:

```text
9a5fa8b07eab46d7103f609b490ae7daeff13970
Batch market persistence and repair Stage B budgets
```

The remediation sequence at that time was:

1. abort/reset the failed replay back to `99b08a0...`;
2. audit W1-002..W1-007 implementation/test/fix commits;
3. include only runtime prerequisites required by the accepted v0.1.1 capability boundary;
4. exclude live activation/rollback episodes and unrelated operational evidence;
5. regenerate/freeze the v0.1.1 source inventory;
6. rerun dry-run and `--apply` from the clean base.

## 7. v0.1.2 boundary

Canonical scope:

```text
UWBS-011 -> A0-003
UWBS-012 -> A0-004
UWBS-013 -> A0-005
UWBS-014 -> A0-006
UWBS-015 -> A0-007
```

The corrected source inventory is frozen in:

```text
docs/release/v0.1-replay-manifest.json
```

The historical implementation cannot be tagged directly as a pure `v0.1.2` because part of the future `v0.1.3` lane was implemented first.

The accepted cumulative boundary on reconstructed v0.1.1 is
`f69c52bf574212d1506df81abc7b15694abb7922`.

## 8. v0.1.3 boundary

Canonical scope:

```text
UWBS-027 -> A0-008
UWBS-028 -> A0-009
UWBS-029 -> A0-010
UWBS-030 -> A0-011
UWBS-031 -> A0-012
UWBS-032 -> A0-013
UWBS-033 -> A0-014
UWBS-034 -> A0-015
UWBS-035 -> A0-016
UWBS-036 -> A0-017
```

Historical final acceptance includes:

```text
0a02add6777745fd65cc0800fd232f745401c583
Accept UWBS-035 and UWBS-036 macro source adapters
```

However the historical line is not a pure release boundary because UWBS-027..031 began before the v0.1.2 lane.

The accepted cumulative boundary on reconstructed v0.1.2 is
`b4df4e911597d9f17bfa0a50b2057c24159dee9f`.

## 9. Reserved versions v0.1.4..v0.1.6

These numbers remain intentionally reserved:

```text
v0.1.4  UWBS-062..066  AI theme
v0.1.5  UWBS-067       Listing compliance
v0.1.6  UWBS-068..079  Crypto market structure
```

The v0.1.4 source audit confirms the canonical ID mapping but finds no accepted
implementation inventory. The v0.1.5–v0.1.6 readiness audit finds design/backlog
source without a verified implementation closeout. No synthetic checkpoint has
been added beyond v0.1.3.

A registered UWBS ID or branch is not sufficient for a release tag.

Tagging requires proven implementation/acceptance boundaries and integrated-tree validation.

Do not renumber later accepted lanes merely to avoid these gaps. Stable logical ownership is more important than contiguous early tagging.

## 10. Known accepted later boundaries

### v0.1.7 — Oil / commodity / cross-asset

Historical accepted boundary:

```text
33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
```

Scope closes UWBS-080..086, including historical replay/capacity work under the accepted shadow-runtime boundary.

### v0.1.8 — Physical-SaaS

Historical accepted boundary:

```text
ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325
```

Scope closes UWBS-087..093.

### v0.1.9 — VIX / cross-asset volatility

Historical accepted boundary:

```text
8151d1c2727fd22b0e9f0222f589cee666c99ffc
```

Scope closes UWBS-094..100, including VIX, BTC IV30, MSTR IV30, MSTR/BTC IV differential and historical calibration.

These SHAs identify accepted historical lane boundaries. Final release tags should still be placed only after the reconstructed cumulative lineage has integrated and validated the corresponding content.

## 11. v0.1.10 PB boundary

PB is closed through PB-10.

PB close reconciliation boundary:

```text
b31e6caf06e885133183149c040d4774a02df23e
```

The six reproducible BTCUSD one-minute absences are explicitly outside the PB completion condition.

They remain a separate future data-quality task with two acceptable resolution families:

1. genuine same-logical-variant provider recovery; or
2. a BTC-specific reproducible provider-absence acknowledgement with frozen evidence and guards.

The gap must not reopen PB and must not block `v0.1.10`.

Synthetic zero-volume OHLC bars are prohibited as a substitute for source evidence.

## 12. Tagging policy

Do not tag directly from branch names or dates.

Tag only after a version has:

```text
frozen functional scope
        +
frozen source inventory
        +
clean cumulative reconstructed checkpoint
        +
focused tests
        +
full regression
        +
compile/typecheck
        +
git diff --check
        +
source-history comparison
        +
PB/future-scope exclusion audit
```

Recommended tags are annotated tags on the accepted reconstructed checkpoint commits.

The old implementation SHAs remain historical evidence and should not be rewritten to point at reconstructed releases.

## 13. Main integration policy

`main` must not be declared the complete v0.1-series integration point merely because individual accepted branches exist.

Before final main integration:

1. complete the reconstructed release lineage;
2. verify that each cumulative checkpoint contains all prior-version functionality;
3. integrate later accepted lanes in intended version order;
4. ensure reserved v0.1.4..v0.1.6 are either accepted or explicitly remain untagged/reserved;
5. integrate PB closeout without pulling the BTCUSD future follow-up into PB scope;
6. run the full repository regression/typecheck/compile acceptance suite;
7. compare the integrated tree against accepted branch contents to detect dropped files or unintended runtime changes;
8. only then move main / create final release tags.

## 14. Reconstruction tooling and governing documents

Primary operational references:

```text
docs/release/V0_1_0_TO_V0_1_3_BOUNDARY_RECONSTRUCTION_2026-09-29.md
docs/release/V0_1_RECONSTRUCTION_EXECUTION_PLAN_2026-09-29.md
docs/release/V0_1_REPLAY_LOCAL_ACCEPTANCE_RUNBOOK_2026-09-29.md
docs/release/v0.1-replay-manifest.json
docs/release/ORDERSCOPE_V0_1_RELEASE_MANIFEST_2026-09-29.md
scripts/release/reconstruct_v0_1.py
```

Branch ownership at the time of this plan:

```text
l1-003-local-market-recovery
  - release manifest
  - v0.1.0..v0.1.3 boundary reconstruction report

release/reconstruction-tools
  - reconstruction execution plan
  - replay acceptance runbook
  - frozen replay manifest
  - reconstruction script

release/reconstructed-v0.1
  - clean cumulative release snapshots only
```

## 15. Current checkpoint summary

```text
v0.1.0
  CLEAN BASE
  99b08a0b5fa1bec5921dc42e630c579a4e83c401

v0.1.1
  RECONSTRUCTION PAUSED
  blocker: missing W1 runtime prerequisite inventory
  observed conflict: a54da09... / src/worker.ts

v0.1.2
  SOURCE INVENTORY FROZEN
  waits for accepted reconstructed v0.1.1

v0.1.3
  SOURCE INVENTORY FROZEN
  waits for accepted reconstructed v0.1.2

v0.1.4..v0.1.6
  RESERVED / NOT TAGGABLE YET

v0.1.7..v0.1.9
  HISTORICAL ACCEPTED BOUNDARIES KNOWN
  cumulative release integration still required

v0.1.10
  PB CLOSED / ACCEPTED
  BTCUSD six-minute gap is separate future work
```

## 16. No-op / safety statement

This plan does not itself:

- rewrite historical branches;
- move `main`;
- create or move tags;
- authorize live Worker activation;
- authorize remote D1 mutation;
- reopen PB;
- authorize synthetic market data;
- resolve the current `src/worker.ts` replay conflict manually.

All mutation remains gated by the reconstruction runbook and local acceptance checks.
