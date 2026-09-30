# OrderScope v0.1.5 local synthetic boundary handoff for Luna — 2026-09-30

Status: **READY FOR LOCAL EXECUTION**

## 1. Goal

Create one cumulative synthetic v0.1.5 release checkpoint from the accepted v0.1.4 boundary plus the four accepted UWBS-067 implementation commits. Preserve all source commits unchanged. Do not rewrite existing history, create a tag, or integrate `main` as a side effect.

## 2. Fixed inputs

Accepted parent boundary:

```text
v0.1.4 = a798622f839b836f8b60f52dd700b8fd87147991
```

Accepted UWBS-067 source commits, in order:

```text
5410f77247ba6ab774ba16a3add6e8ec15a4df48
e6fc865cb917c32669cf9fe8e5ffa5c47ef87229
0cfb1102a26e4cdb94300656c22d802bb97fb392
44e7a2d31c6ef5ebebafb77fbe44ac307625b014
```

Canonical scope:

```text
v0.1.5 = UWBS-067
lane   = Listing Compliance / Earnings Repricing Canary
```

Expected source-only paths:

```text
analysis/app/orderscope_local/listing_compliance/__init__.py
analysis/app/orderscope_local/listing_compliance/models.py
analysis/app/orderscope_local/listing_compliance/rules.py
analysis/tests/listing_compliance/test_listing_compliance.py
```

## 3. Acceptance evidence already recorded

Before synthetic-boundary construction, local validation has already passed:

```text
focused Python      9 passed
full Python         635 passed, 1 warning
compileall          PASS
diff check          PASS
TypeScript          not required; Python-only source surface
```

The warning is the existing Starlette `BlockingPortal` deprecation warning and is not a UWBS-067 failure.

Experimental limitations remain non-blocking:

- no universal delisting-probability model;
- no universal minimum-price or cure-duration threshold;
- no causal repricing attribution from price movement alone;
- no empirically calibrated repricing threshold.

## 4. Preflight — stop if any check fails

Run from the OrderScope repository root.

```bash
git fetch origin \
  release/reconstructed-v0.1 \
  release/reconstruction-tools \
  codex/uwbs-067-listing-compliance

git status --short
git rev-parse --show-toplevel
git rev-parse origin/release/reconstructed-v0.1
git rev-parse origin/codex/uwbs-067-listing-compliance
```

Expected remote reconstructed boundary before this task:

```text
a798622f839b836f8b60f52dd700b8fd87147991
```

STOP and report if:

- the worktree is dirty;
- `origin/release/reconstructed-v0.1` is not exactly the accepted v0.1.4 SHA above;
- any accepted source commit does not resolve;
- the source branch contains unrelated paths or v0.1.6+ work.

Do not reset, force-push, or auto-reconcile an unexpected remote boundary.

## 5. Preferred isolated worktree

Use an isolated worktree so the current development checkout is not disturbed.

```bash
WT=/tmp/orderscope-v0.1.5-boundary
rm -rf "$WT"

git worktree add --detach "$WT" a798622f839b836f8b60f52dd700b8fd87147991
cd "$WT"

git switch -c local/reconstruct-v0.1.5

git status --short
git rev-parse HEAD
```

Expected HEAD:

```text
a798622f839b836f8b60f52dd700b8fd87147991
```

If the branch name already exists locally, use a disposable unique name such as `local/reconstruct-v0.1.5-20260930`. Do not delete another worktree's active branch.

## 6. Replay the accepted source tree without preserving source commits as separate boundary commits

Apply all four source commits to the index/worktree with `--no-commit`:

```bash
git cherry-pick --no-commit \
  5410f77247ba6ab774ba16a3add6e8ec15a4df48 \
  e6fc865cb917c32669cf9fe8e5ffa5c47ef87229 \
  0cfb1102a26e4cdb94300656c22d802bb97fb392 \
  44e7a2d31c6ef5ebebafb77fbe44ac307625b014
```

Expected result: no conflict.

Immediately inspect:

```bash
git status --short
git diff --cached --stat
git diff --cached --name-only
```

Expected changed paths are only the four UWBS-067 paths listed in section 2.

STOP and report if:

- cherry-pick reports a conflict;
- an unrelated file is staged;
- a v0.1.6 Crypto path appears;
- any existing non-UWBS-067 source is unexpectedly modified.

If a conflict occurs, do not choose `ours`/`theirs` blindly. Record the conflicted paths and stop.

## 7. Validate the staged synthetic tree before commit

Run the focused suite first:

```bash
uv run pytest -q analysis/tests/listing_compliance
```

Expected:

```text
9 passed
```

Then full Python regression:

```bash
uv run pytest -q analysis/tests
```

Expected baseline from accepted candidate:

```text
635 passed
```

One pre-existing Starlette deprecation warning is acceptable if no new failure/warning class is introduced.

Then:

```bash
uv run python -m compileall -q analysis/app
git diff --check --cached
```

Both should return successfully with no error output.

TypeScript is not required because the accepted v0.1.5 diff is Python-only. If `git diff --cached --name-only` reveals any TypeScript, package, generated/shared-contract, root build or npm-related file, STOP and run the repository TypeScript acceptance suite before continuing.

## 8. Semantic acceptance check

Before committing, verify that the staged implementation still satisfies the accepted development boundary:

```text
Fact:
  explicit exchange/issuer listing-compliance evidence

Derived/structured state:
  deficiency / cure / regained / delisting lifecycle

Interpretation:
  listing-overhang removal / repricing assessment
```

Required invariants:

1. price recovery alone does not establish regained compliance;
2. listing evidence and earnings/company evidence remain separate lineage inputs;
3. no universal `$1` rule, rolling-window duration, or exchange-specific cure duration is promoted into a universal constant;
4. invalid cure/regained transitions remain rejected;
5. no future price target, trade action, or causal certainty is introduced.

If any of these are false, STOP and report instead of creating the boundary.

## 9. Create one synthetic v0.1.5 commit

Confirm staged changes only:

```bash
git status --short
```

Create exactly one commit:

```bash
git commit -m "Reconstruct v0.1.5 listing compliance boundary" \
  -m "Create the cumulative UWBS-067 Listing Compliance / Earnings Repricing Canary development boundary on top of accepted v0.1.4. Source commits remain preserved unchanged. Empirical repricing thresholds and universal exchange rules remain experimental/unvalidated."
```

Capture the new SHA:

```bash
V015_SHA=$(git rev-parse HEAD)
echo "$V015_SHA"
```

## 10. Verify parent and tree

The synthetic v0.1.5 commit must have exactly one parent: accepted v0.1.4.

```bash
git rev-parse HEAD^
git show --no-patch --format='%H%n%P%n%s' HEAD
```

Expected parent:

```text
a798622f839b836f8b60f52dd700b8fd87147991
```

Verify the cumulative diff:

```bash
git diff --stat a798622f839b836f8b60f52dd700b8fd87147991..HEAD
git diff --name-only a798622f839b836f8b60f52dd700b8fd87147991..HEAD
git diff --check a798622f839b836f8b60f52dd700b8fd87147991..HEAD
```

Expected paths: only the four UWBS-067 files.

Finally verify clean state:

```bash
git status --short
```

Expected: no output.

## 11. Update `release/reconstructed-v0.1`

Fetch once more immediately before push:

```bash
git fetch origin release/reconstructed-v0.1
REMOTE_BOUNDARY=$(git rev-parse origin/release/reconstructed-v0.1)
echo "$REMOTE_BOUNDARY"
```

It must still equal:

```text
a798622f839b836f8b60f52dd700b8fd87147991
```

If it changed, STOP. Do not force-push.

Push the synthetic commit as a fast-forward update:

```bash
git push origin HEAD:release/reconstructed-v0.1
```

Do not use `--force` or `--force-with-lease`.

## 12. Verify remote after push

```bash
git fetch origin release/reconstructed-v0.1
REMOTE_V015=$(git rev-parse origin/release/reconstructed-v0.1)
LOCAL_V015=$(git rev-parse HEAD)

printf 'local : %s\nremote: %s\n' "$LOCAL_V015" "$REMOTE_V015"
test "$LOCAL_V015" = "$REMOTE_V015"
```

Also inspect:

```bash
git log --oneline --decorate -5 origin/release/reconstructed-v0.1
```

Expected lineage tail:

```text
<v0.1.5 synthetic SHA>  Reconstruct v0.1.5 listing compliance boundary
 a798622f...             v0.1.4 synthetic boundary
 ...                     v0.1.3
```

## 13. Do not do these actions

Luna must NOT:

- create `v0.1.5` tag;
- merge to `main`;
- rewrite or squash historical source branches;
- delete accepted source commits;
- modify v0.1.6 readiness or Crypto implementation as part of this task;
- add historical calibration just to make the release look complete;
- force-push `release/reconstructed-v0.1`.

## 14. Documentation handoff after successful push

After the remote boundary is confirmed, report the synthetic SHA back to the coordinating session. The coordinating session can then update these release records with the final SHA:

```text
docs/release/V0_1_5_LISTING_COMPLIANCE_BOUNDARY_REPORT_2026-09-30.md
docs/release/V0_1_5_LISTING_COMPLIANCE_IMPLEMENTATION_PROGRESS_2026-09-30.md
docs/release/v0.1.5-replay-manifest.json
```

Do not invent the SHA in documentation before the commit exists.

## 15. Required final response format for Luna

Return exactly the essential execution evidence in this shape:

```text
v0.1.5 UWBS-067 synthetic boundary
parent: a798622f839b836f8b60f52dd700b8fd87147991
source commits:
- 5410f77247ba6ab774ba16a3add6e8ec15a4df48
- e6fc865cb917c32669cf9fe8e5ffa5c47ef87229
- 0cfb1102a26e4cdb94300656c22d802bb97fb392
- 44e7a2d31c6ef5ebebafb77fbe44ac307625b014
focused: 9 passed
full Python: <actual passed count and warnings>
compileall: PASS
diff check: PASS
TypeScript: not required — Python-only diff
synthetic boundary: <actual SHA>
remote release/reconstructed-v0.1: <actual SHA>
status: ACCEPTED / STOPPED
notes: <only if needed>
```

If stopped, include the exact failed command/condition and do not claim acceptance.
