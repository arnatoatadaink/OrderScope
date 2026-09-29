# OrderScope v0.1 Release Lineage Reconstruction Execution Plan — 2026-09-29

Status: **RECONSTRUCTION BRANCH CREATED / DRY-RUN PLANNER CHECKED IN / APPLY NOT YET EXECUTED**

## 1. Goal

Build a clean cumulative release lineage from accepted historical implementation without rewriting or deleting the source-of-truth history.

The release lineage starts from the strongest current `v0.1.0` candidate:

```text
99b08a0b5fa1bec5921dc42e630c579a4e83c401
Accept N1-006 real-data benchmark
```

Release branch:

```text
release/reconstructed-v0.1
```

The source history remains untouched.

## 2. Release sequence

```text
v0.1.0  original WBS/CP baseline, PB excluded
   |
   v
v0.1.1  operational/runtime extensions
   |
   v
v0.1.2  macro/carry
   |
   v
v0.1.3  cross-market/competitor/macro adapters
```

Later accepted lanes and PB closeout will be integrated only after this first reconstruction segment is proven.

## 3. Source ownership

### v0.1.1

Logical ownership:

```text
UWBS-001..004
UWBS-016
UWBS-023..026
```

Formal IDs used by historical implementation may include:

```text
R0-001..009
W1-001
```

PB task IDs are explicitly excluded even where a historical operational document references PB dependencies.

### v0.1.2

Logical ownership:

```text
UWBS-011..015
A0-003..007
```

### v0.1.3

Logical ownership:

```text
UWBS-027..036
A0-008..017
```

## 4. Why reconstruction is required

The historical implementation order is not a clean release order.

Examples:

- UWBS-027 work began before UWBS-011 work.
- W1-001 final closeout occurred after substantial macro/cross-market work already existed.
- Tagging the original historical commits directly would therefore cause functional content from later logical versions to appear in earlier release tags.

The reconstructed branch solves this by replaying accepted source changes by functional ownership instead of historical wall-clock order.

## 5. Planner

Script:

```text
scripts/release/reconstruct_v0_1.py
```

Default behavior is dry-run only.

It:

1. scans all historical commits in topological order;
2. classifies source commits by version ownership using UWBS/formal-ID commit-message patterns;
3. rejects ambiguous cross-version classification;
4. excludes PB-labelled commits;
5. writes `var/release/v0.1-reconstruction-plan.json`;
6. prints the selected source commit inventory.

`--apply` is intentionally guarded and will only run when:

- current branch is exactly `release/reconstructed-v0.1`;
- working tree is clean;
- HEAD is still exactly the frozen `v0.1.0` base SHA.

Each logical version is replayed with `git cherry-pick --no-commit` and collapsed to one reconstruction checkpoint commit. Any cherry-pick conflict stops execution for review rather than auto-resolving semantic conflicts.

## 6. Required validation before apply

Before using `--apply`, review the dry-run plan for:

- missing implementation/test/export/acceptance commits;
- commits whose message lacks a mapped UWBS/formal ID;
- documentation-only commits that should or should not be carried;
- commits that combine changes belonging to more than one logical version;
- PB implementation/evidence accidentally selected through R0/W1 naming;
- revert pairs and superseded commits;
- merge commits whose diff should not be replayed directly.

A commit-message classifier is a discovery mechanism, not final proof of semantic ownership.

## 7. Post-version acceptance

After each reconstructed checkpoint:

```text
focused tests for the reconstructed lane
full regression
compile/typecheck as applicable
git diff --check
source-history comparison
PB-content exclusion audit
```

The resulting checkpoint SHA is the candidate tag boundary for that version.

## 8. No mutation of source history

This process must not:

- force-push historical branches;
- rewrite `main` during reconstruction;
- delete old acceptance commits;
- alter the PB closeout branch;
- claim new release tags before integrated-tree validation.

The reconstructed release lineage is an additional canonical release view derived from source-of-truth history.
