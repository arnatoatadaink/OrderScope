# OrderScope v0.1 reconstructed release — local acceptance runbook

Status: **PRE-APPLY / LOCAL REPLAY REVIEW REQUIRED**
Date: 2026-09-29

## Purpose

This runbook validates the frozen source-of-truth replay manifest before any reconstructed release checkpoint is pushed or tagged.

The source Git history is immutable. `release/reconstructed-v0.1` is a separate cumulative release lineage starting from the original WBS/CP baseline:

```text
v0.1.0 = 99b08a0b5fa1bec5921dc42e630c579a4e83c401
```

The tooling and manifest remain on `release/reconstruction-tools` so that release snapshots are not contaminated by reconstruction-only files.

## 1. Refresh both release branches

From the canonical WSL checkout:

```bash
git fetch origin \
  release/reconstruction-tools \
  release/reconstructed-v0.1

git switch -C release/reconstruction-tools origin/release/reconstruction-tools
```

Confirm the tooling branch is clean:

```bash
git status --short
git rev-parse HEAD
```

## 2. Create an isolated target worktree

Use a sibling path outside the canonical checkout:

```bash
git branch -f release/reconstructed-v0.1 origin/release/reconstructed-v0.1
rm -rf ../OrderScope-release-v0.1
git worktree add ../OrderScope-release-v0.1 release/reconstructed-v0.1
```

Verify the target is still the frozen v0.1.0 base:

```bash
git -C ../OrderScope-release-v0.1 rev-parse HEAD
# expected:
# 99b08a0b5fa1bec5921dc42e630c579a4e83c401

git -C ../OrderScope-release-v0.1 status --short
```

Do not continue if HEAD differs or the worktree is dirty.

## 3. Manifest dry-run

Run the reconstruction planner from the tooling checkout while targeting the isolated worktree:

```bash
python3 scripts/release/reconstruct_v0_1.py \
  --target-worktree ../OrderScope-release-v0.1
```

Expected current behavior:

- all source SHAs resolve;
- no duplicate source SHA is reported;
- no PB-labelled source commit is accepted;
- v0.1.1, v0.1.2 and v0.1.3 inventories are printed;
- `--apply` remains blocked while manifest status is `ready_for_local_replay_review`.

Any SHA-resolution or PB-boundary failure is a hard rejection.

## 4. Review the frozen source inventory

Primary manifest:

```text
docs/release/v0.1-replay-manifest.json
```

Review rules:

1. no PB-00..PB-10 execution evidence in v0.1.0..v0.1.3;
2. no remote D1 mutation episode merely because it supplied acceptance evidence;
3. no live Worker activation/rollback episode merely because it followed a capability implementation;
4. fixes required by accepted local tests remain included;
5. revert pairs and superseded remote-operation commits remain only in immutable source history;
6. v0.1.1 contains W1-001 non-live capability, including the actual implementation commit `a0b018971f8e23cb526ad9fb7453d679e1e1ed9b`;
7. Packet B/C regression coverage and the R0-001 Node ESM test-import fix are included.

## 5. Enable replay only after dry-run review

After the dry-run inventory is accepted, update only the manifest statuses:

```text
ready_for_local_replay_review -> ready_for_replay
```

for v0.1.1, v0.1.2 and v0.1.3.

Do not otherwise reorder or add source commits at the same time as this status transition.

Pull the status-only manifest commit locally, then rerun the dry-run command. It must end with:

```text
dry-run validated; manifest is eligible for --apply
```

## 6. Apply reconstruction

Only after the previous gate passes:

```bash
python3 scripts/release/reconstruct_v0_1.py \
  --target-worktree ../OrderScope-release-v0.1 \
  --apply
```

The script must create exactly three synthetic cumulative checkpoint commits:

```text
v0.1.0 historical base
  -> Reconstruct v0.1.1 from frozen source manifest
  -> Reconstruct v0.1.2 from frozen source manifest
  -> Reconstruct v0.1.3 from frozen source manifest
```

If a cherry-pick conflict occurs, stop. Do not resolve it by choosing either side blindly. Record the conflicting source SHA and paths and review whether the conflict represents:

- a missing prerequisite commit;
- an intentionally excluded operational episode;
- a later fix that must be replayed earlier;
- or a true semantic overlap between version scopes.

## 7. Post-replay verification

Before pushing the reconstructed branch, run from the target worktree:

```bash
git status --short
git log --oneline --decorate -8

git diff --check 99b08a0b5fa1bec5921dc42e630c579a4e83c401..HEAD

uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app

npm test --prefix .
npm run typecheck --prefix .
```

If the repository's current package scripts require a narrower Worker command, use the checked-in package.json as authority and record the exact command/output rather than substituting an assumed command.

Acceptance requires:

- clean worktree;
- no conflict residue;
- Python regression PASS;
- Python compileall PASS;
- Worker/TypeScript tests PASS under checked-in scripts;
- typecheck PASS;
- `git diff --check` PASS.

## 8. Record reconstructed boundaries

After acceptance, record the new synthetic SHAs as:

```text
v0.1.0 = 99b08a0b5fa1bec5921dc42e630c579a4e83c401
v0.1.1 = <new synthetic SHA>
v0.1.2 = <new synthetic SHA>
v0.1.3 = <new synthetic SHA>
```

Do not replace the historical source SHAs in task-specific evidence. The new SHAs are release-boundary identities, not replacements for original implementation/acceptance evidence.

## 9. Push boundary

Only after all checks pass:

```bash
git -C ../OrderScope-release-v0.1 push origin release/reconstructed-v0.1
```

Tags and main integration remain separate later gates.

## 10. Current non-goals

This runbook does not:

- rewrite existing branches;
- rewrite commit author/committer identity;
- tag v0.1.x yet;
- merge into main;
- reconstruct reserved v0.1.4..v0.1.6;
- move PB/BTCUSD follow-up into v0.1.0..v0.1.3;
- authorize remote runtime mutation.
