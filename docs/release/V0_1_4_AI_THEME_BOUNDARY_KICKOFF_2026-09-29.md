# OrderScope v0.1.4 AI Theme Boundary Kickoff — 2026-09-29

Status: **KICKOFF / SOURCE-INVENTORY AUDIT REQUIRED BEFORE REPLAY**

## 1. Purpose

Begin reconstruction of the next clean cumulative release boundary after the accepted `v0.1.0..v0.1.3` lineage.

Accepted reconstructed parent:

```text
v0.1.0  99b08a0b5fa1bec5921dc42e630c579a4e83c401
v0.1.1  bada5bff803321427eb3c8eb1f3d159460ba5dd1
v0.1.2  f69c52bf574212d1506df81abc7b15694abb7922
v0.1.3  b4df4e911597d9f17bfa0a50b2057c24159dee9f
```

`v0.1.4` is the AI Theme lane. The release-boundary plan assigns the canonical release scope to:

```text
UWBS-062..066
```

No tag is authorized by this kickoff report. The goal is to determine the exact accepted source inventory and reconstruct a pure cumulative `v0.1.4` snapshot on top of reconstructed `v0.1.3`.

## 2. Historical numbering conflict that must be resolved first

The earliest checked-in AI-theme design material used the provisional identifiers:

```text
UWBS-030..034
```

The design covered:

```text
AI theme ontology / multi-theme exposure
  -> event × theme reaction coefficient
  -> cross-sectional theme reaction observation
  -> theme activation / rotation / repricing interpretation
  -> historical calibration / Canary fixtures
```

Those provisional identifiers later collide with the accepted v0.1.3 Cross-Market lane, where `UWBS-030..036` became canonical for repricing-state and official macro adapters.

Therefore **the old AI-theme `UWBS-030..034` labels must never be replayed into v0.1.4 merely by identifier matching**.

The first v0.1.4 audit task is to establish the permanent mapping:

```text
historical AI provisional ID
  -> canonical UWBS-062..066 ID
  -> source implementation/test/export/acceptance commits
```

The original design/backlog commits remain historical evidence; they do not override the final canonical numbering.

## 3. Historical source material already identified

At minimum the source-history audit must include:

- `26212936cd2e0ac148e328f22bf58fe7ee59e6ce`
  - `docs: add AI theme decomposition and reaction coefficient design report`
- `49523f52a50136d5d8301d30b1345cfcd9f88aea`
  - `docs: add AI theme decomposition reaction coefficient backlog`

The backlog material explicitly defines the AI decomposition and its initial dependency chain, but at that point uses the now-conflicting provisional IDs.

These two commits are **design/provenance inputs**, not proof that the complete v0.1.4 implementation was accepted.

## 4. Canonical v0.1.4 functional boundary

The intended functional boundary is the AI Theme capability lane represented by canonical `UWBS-062..066`.

The expected logical structure to verify against the final WBS/backlog records is:

```text
AI theme ontology / structural exposure
  -> event × theme relationship model
  -> cross-sectional reaction observation
  -> activation / rotation / repricing interpretation
  -> calibration / Canary / false-positive validation
```

Key semantic rules inherited from the original design:

- a company may have multiple AI/adjacent theme exposures;
- structural exposure is distinct from temporary market narrative;
- `AI_SECURITY` and `AI_GOVERNANCE` are not permanent anti-AI themes;
- news/event observations remain source-grounded evidence;
- reaction coefficients are Derived Metric / Interpretation, not Facts;
- no fixed numeric coefficient is normative without historical calibration;
- single-stock movement does not by itself prove a theme-level reaction;
- theme activation, theme rotation and persistent theme repricing are distinct states;
- adjacent themes such as `DEFENSE_INDUSTRIAL` may overlap AI application exposure but remain separate identities.

## 5. Required source inventory

Before any replay, build an explicit allowlist manifest for `v0.1.4`.

For every candidate source commit classify it as exactly one of:

```text
MUST_REPLAY_IMPLEMENTATION
MUST_REPLAY_TEST
MUST_REPLAY_EXPORT
MUST_REPLAY_ACCEPTANCE_CONTENT
DESIGN_PROVENANCE_ONLY
DOC_ONLY_OPTIONAL
SHARED_PREREQUISITE
SUPERSEDED_OR_REVERTED
OTHER_VERSION
MIXED_COMMIT_REQUIRES_PATH_SPLIT
```

Do not use commit-message regex as final ownership proof.

The audit must identify:

1. the commit where `UWBS-062..066` became canonical;
2. all implementation commits owned by those tasks;
3. required test/fix commits that make the accepted behavior pass;
4. package/export commits needed to expose the accepted capability;
5. acceptance commits or documents that prove the boundary;
6. shared prerequisites already present in reconstructed v0.1.3;
7. mixed commits containing both AI-theme and unrelated later-lane changes;
8. provisional `UWBS-030..034` documents that should remain source-history evidence only.

## 6. Dependency audit against reconstructed v0.1.3

The reconstructed parent already contains Cross-Market primitives and must be treated as the only release parent for v0.1.4.

Verify whether the AI Theme implementation depends on accepted v0.1.3 components such as:

- market relationship/context contracts;
- market reaction interpretations;
- relative repricing metrics/state;
- macro context/adapters;
- shared Fact / Derived Metric / Interpretation provenance rules.

If a candidate AI commit historically depended on unrelated later work, replay only the path-level AI change or introduce an explicit shared prerequisite after semantic review. Do not import a future release lane solely to satisfy Git context.

## 7. Reconstruction rule

The target lineage is cumulative:

```text
b4df4e911597d9f17bfa0a50b2057c24159dee9f
  reconstructed v0.1.3
        |
        v
<new synthetic v0.1.4 commit>
  AI Theme / UWBS-062..066 only
```

Recommended process:

1. freeze `release/reconstructed-v0.1` at accepted v0.1.3;
2. audit and freeze the v0.1.4 source allowlist;
3. replay source commits with `--no-commit` or path-specific application;
4. stop on semantic conflicts;
5. never resolve a conflict by blindly taking `ours` or `theirs`;
6. collapse the accepted v0.1.4 content to one synthetic checkpoint commit;
7. record `source SHA -> reconstructed boundary/path decision` permanently;
8. run focused and full acceptance before push/tag.

## 8. Acceptance gates

A candidate v0.1.4 boundary is accepted only when all applicable gates pass:

```text
[ ] canonical UWBS-062..066 mapping proven
[ ] provisional UWBS-030..034 collision fully documented
[ ] explicit frozen source allowlist reviewed
[ ] no v0.1.5+ capability accidentally included
[ ] no PB execution evidence included
[ ] no live provider/runtime mutation evidence included merely for context
[ ] focused AI-theme tests PASS
[ ] full Python regression PASS
[ ] TypeScript regression PASS where affected
[ ] typecheck PASS
[ ] Python compileall PASS
[ ] git diff --check PASS
[ ] package/export surface contains only accepted v0.1.4 additions
[ ] reconstructed v0.1.3 -> v0.1.4 diff reviewed
[ ] synthetic boundary SHA recorded
```

## 9. Expected audit outputs

Before replay, produce or update the following artifacts:

```text
docs/release/V0_1_4_AI_THEME_SOURCE_INVENTORY_2026-09-29.md
docs/release/v0.1.4-replay-manifest.json
```

The source inventory should contain:

- canonical ID mapping;
- source commit SHA;
- source commit role;
- changed paths;
- replay decision;
- dependency/prerequisite;
- conflict/path-split notes;
- acceptance evidence.

The JSON manifest should be fail-closed and must not permit apply while any candidate remains unclassified.

## 10. Completion condition for the v0.1.4 reconstruction task

The v0.1.4 reconstruction is complete when:

```text
reconstructed v0.1.3
  + canonical AI Theme UWBS-062..066 accepted content
  = one clean cumulative synthetic v0.1.4 boundary
```

and the boundary passes the acceptance gates above.

Tag creation and integration into `main` remain separate later gates.

## 11. Immediate next action

Perform the canonical-ID/source-history audit in this order:

```text
A. find the remap/incorporation record that assigns AI Theme to UWBS-062..066
B. enumerate all 062..066 implementation/test/export/acceptance commits
C. connect any older provisional 030..034 AI commits to the canonical IDs
D. remove design-only / superseded / unrelated commits
E. identify shared prerequisites already covered by v0.1.3
F. freeze v0.1.4 source inventory and replay manifest
G. rehearse replay on an isolated worktree
```

Do not begin `--apply` before A–F are complete.
