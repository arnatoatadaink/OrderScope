# OrderScope v0.1.4 Local Release Execution Handoff — Luna

Status: **READY FOR LOCAL EXECUTION**
Date: 2026-09-30
Target: `v0.1.4 AI Theme — Experimental / Uncalibrated`

## 1. Goal

Create one clean cumulative synthetic `v0.1.4` boundary on top of the accepted reconstructed `v0.1.3` boundary, verify the resulting tree locally, then push only the final accepted release boundary to `release/reconstructed-v0.1`.

This is an **experimental development release**. Historical market calibration is intentionally non-blocking for v0.1.4, but the release must clearly record that theme-confirmation thresholds, false-positive rate, persistence criteria, economic materiality, and profit attribution are not yet validated on accepted historical market cases.

## 2. Fixed release inputs

Accepted parent boundary:

```text
v0.1.3 = b4df4e911597d9f17bfa0a50b2057c24159dee9f
```

Accepted v0.1.4 source commits:

```text
e018283549ccbb74ff5309fc4fe0b4addb91fa0d
c4f50c0878e001e8d6b031bf7f15ef188e3d4453
```

Logical scope:

```text
UWBS-062  AI / adjacent theme ontology and structural exposure
UWBS-063  Event × theme categorical reaction hypothesis
UWBS-064  Cross-sectional theme reaction observation
UWBS-065  Theme activation / rotation / repricing interpretation
UWBS-066  Historical-case classification / calibration summary contract
```

Do not infer v0.1.4 ownership from historical aliases `UWBS-030..034`; those IDs overlap the accepted v0.1.3 Cross-Market lane. The canonical v0.1.4 IDs are `UWBS-062..066`.

## 3. Release policy

v0.1.4 is accepted as:

```text
Experimental / Uncalibrated
```

Accepted now:

- theme ontology and many-to-many theme exposure contract;
- event × theme categorical hypothesis contract;
- basket-relative reaction observation;
- conservative activation / rotation / repricing interpretation states;
- calibration-case classification and descriptive summary contract;
- regression behavior covered by current tests.

Explicitly not validated yet:

- historical empirical confirmation thresholds;
- false-positive rate on accepted historical samples;
- persistence thresholds;
- economic materiality interpretation;
- profit attribution;
- accepted company-theme registry population;
- historically calibrated event × theme numeric coefficients.

These are follow-up work and must be preserved in release notes, but they do not block this development release.

## 4. Required remote documents

Before starting, refresh the tooling branch and confirm these exist:

```text
docs/release/V0_1_4_AI_THEME_BOUNDARY_REPORT_2026-09-30.md
docs/release/V0_1_4_AI_THEME_SOURCE_INVENTORY_2026-09-29.md
docs/release/V0_1_4_AI_THEME_IMPLEMENTATION_PROGRESS_2026-09-30.md
docs/release/V0_1_4_AI_THEME_EVIDENCE_MATURITY_EXTENSION_2026-09-30.md
docs/release/v0.1.4-replay-manifest.json
```

`v0.1.4-replay-manifest.json` is the release authority for the two accepted source commits.

## 5. Local preparation

Run from the canonical WSL checkout.

```bash
cd /home/y/projects/codex_work/OrderScope

git fetch origin \
  release/reconstruction-tools \
  release/reconstructed-v0.1 \
  codex/uwbs-062-066-ai-theme

git status --short
```

Expected:

```text
(no output)
```

If the canonical checkout is dirty, stop and inspect the changes. Do not delete or reset unrelated work automatically.

Refresh the tooling branch:

```bash
git switch -C release/reconstruction-tools origin/release/reconstruction-tools

git rev-parse HEAD
git status --short
```

The exact tooling HEAD may advance; a clean worktree is the hard requirement.

## 6. Create isolated release worktree

Do not perform the replay in the tooling checkout.

First synchronize the local release branch to the current remote accepted boundary:

```bash
git branch -f release/reconstructed-v0.1 origin/release/reconstructed-v0.1
```

Check its current remote boundary:

```bash
git rev-parse release/reconstructed-v0.1
```

Expected before v0.1.4 replay:

```text
b4df4e911597d9f17bfa0a50b2057c24159dee9f
```

If it is not this SHA, stop and inspect the remote branch before continuing. Do not force it backward.

Create a sibling worktree:

```bash
rm -rf ../OrderScope-release-v0.1.4

git worktree add \
  ../OrderScope-release-v0.1.4 \
  release/reconstructed-v0.1
```

Verify:

```bash
git -C ../OrderScope-release-v0.1.4 rev-parse HEAD
git -C ../OrderScope-release-v0.1.4 status --short
```

Expected:

```text
b4df4e911597d9f17bfa0a50b2057c24159dee9f
```

and no status output.

## 7. Replay the accepted v0.1.4 source

Use `--no-commit` so the version boundary remains one synthetic cumulative checkpoint.

```bash
git -C ../OrderScope-release-v0.1.4 cherry-pick --no-commit \
  e018283549ccbb74ff5309fc4fe0b4addb91fa0d

git -C ../OrderScope-release-v0.1.4 cherry-pick --no-commit \
  c4f50c0878e001e8d6b031bf7f15ef188e3d4453
```

If either command conflicts:

1. stop;
2. do not choose `ours` or `theirs` blindly;
3. record the source SHA and conflicting paths;
4. compare the conflict against `b4df4e91...` and the source commit;
5. abort the replay if ownership is ambiguous.

Abort command if required:

```bash
git -C ../OrderScope-release-v0.1.4 cherry-pick --abort || true
```

A conflict is a review condition, not a reason to improvise a release tree.

## 8. Verify intended diff before tests

The expected new runtime/test surface is limited to the AI Theme Python package and tests.

Inspect:

```bash
git -C ../OrderScope-release-v0.1.4 status --short

git -C ../OrderScope-release-v0.1.4 diff --stat \
  b4df4e911597d9f17bfa0a50b2057c24159dee9f

git -C ../OrderScope-release-v0.1.4 diff --name-only \
  b4df4e911597d9f17bfa0a50b2057c24159dee9f
```

Expected primary paths:

```text
analysis/app/orderscope_local/theme/
analysis/tests/theme/test_theme.py
```

If unrelated PB, Worker live-operation, remote D1 mutation, v0.1.5+, or unexpected TypeScript/runtime files appear, stop and inspect before proceeding.

## 9. Focused tests

Run the AI Theme tests first:

```bash
cd ../OrderScope-release-v0.1.4

uv run pytest -q analysis/tests/theme/test_theme.py
```

Expected baseline from the development candidate:

```text
12 passed
```

A different pass count is not automatically a failure if the test file has legitimately changed, but any failure blocks the release.

## 10. Full local acceptance

Run the complete Python regression:

```bash
uv run pytest -q analysis/tests
```

Previous candidate baseline:

```text
626 passed, 2 warnings
```

Hard requirement: zero failures.

Compile check:

```bash
uv run python -m compileall -q analysis/app
```

Expected: exit code 0 and no error output.

Diff check:

```bash
git diff --check \
  b4df4e911597d9f17bfa0a50b2057c24159dee9f
```

Expected: no output.

TypeScript sources were not changed by the accepted candidate. A full TypeScript rerun is optional for this v0.1.4 boundary if the actual diff confirms no TypeScript file changed. If any TypeScript file changed unexpectedly, run the checked-in repository commands before acceptance:

```bash
npm test
npm run typecheck
```

and require both to pass.

## 11. Experimental-release semantic review

Before committing, confirm all of the following:

```text
[ ] Theme states remain Interpretation/Derived Metric outputs, not raw Facts.
[ ] No hard-coded historically unvalidated numeric event×theme coefficient was introduced.
[ ] Single-stock movement alone is not promoted to confirmed theme activation.
[ ] Missing volume/evidence remains conservative rather than inferred.
[ ] Source event evidence is retained in Interpretation lineage.
[ ] Release notes state that historical calibration is incomplete.
[ ] Economic materiality and profit attribution are not claimed as implemented validation.
```

## 12. Create one synthetic v0.1.4 checkpoint

Check the staged tree:

```bash
git status --short
```

Then create one cumulative boundary commit:

```bash
git add -A

git commit -m "Reconstruct v0.1.4 experimental AI Theme boundary" \
  -m "Release UWBS-062..066 as an experimental uncalibrated analytical capability. Historical calibration, false-positive rates, persistence thresholds, economic materiality and profit attribution remain explicitly unvalidated follow-up work."
```

Record the new SHA:

```bash
git rev-parse HEAD
```

Define it locally for the remainder of the checks:

```bash
V014_SHA=$(git rev-parse HEAD)
echo "$V014_SHA"
```

## 13. Post-commit verification

Require a clean worktree:

```bash
git status --short
```

Expected: no output.

Verify the release DAG:

```bash
git log --oneline --decorate -6
```

Expected shape:

```text
<V014_SHA> Reconstruct v0.1.4 experimental AI Theme boundary
b4df4e91    Reconstruct v0.1.3 from frozen source manifest
f69c52bf    Reconstruct v0.1.2 from frozen source manifest
bada5bff    Reconstruct v0.1.1 from frozen source manifest
...
```

Verify parent exactly:

```bash
git rev-parse HEAD^
```

Expected:

```text
b4df4e911597d9f17bfa0a50b2057c24159dee9f
```

## 14. Push only after acceptance

Push the reconstructed release branch:

```bash
git push origin release/reconstructed-v0.1
```

Do not create a tag and do not merge `main` as part of this step unless separately instructed.

## 15. Update release documentation after push

Return to the tooling checkout:

```bash
cd /home/y/projects/codex_work/OrderScope
git switch release/reconstruction-tools
git pull --ff-only origin release/reconstruction-tools
```

Update at minimum:

```text
docs/release/V0_1_4_AI_THEME_BOUNDARY_REPORT_2026-09-30.md
docs/release/V0_1_VERSION_BOUNDARY_PLAN_2026-09-28.md
```

Record:

```text
v0.1.4 = <V014_SHA>
status = EXPERIMENTAL / UNCALIBRATED ACCEPTED
```

Preserve these caveats verbatim in substance:

```text
Historical empirical confirmation thresholds are not validated.
False-positive rate is not validated on accepted historical samples.
Persistence criteria are provisional.
Economic materiality is not validated.
Profit attribution is not implemented as an accepted validation layer.
```

Do not rewrite the historical source SHAs. The synthetic SHA is a release-boundary identity, not a replacement for source implementation evidence.

## 16. Evidence Maturity follow-up — not part of this boundary

The next AI Theme extension is intentionally separated from v0.1.4 release acceptance.

Target conceptual model:

```text
NEWS
  -> NARRATIVE
  -> COMMERCIAL_EVIDENCE
  -> RECURRING_EVIDENCE
  -> PROFIT_ATTRIBUTED
```

Interpretation axes:

```text
Theme Exposure
× Evidence Maturity
× Economic Materiality
× Persistence
```

Do not infer malicious intent from promotional AI announcements. Prefer evidence-state labels such as:

```text
PROMOTIONAL_ONLY
UNVERIFIED_COMMERCIAL_CLAIM
NO_REVENUE_EVIDENCE
NO_REPEAT_EVIDENCE
ECONOMIC_MATERIALITY_UNKNOWN
```

Detailed design authority:

```text
docs/release/V0_1_4_AI_THEME_EVIDENCE_MATURITY_EXTENSION_2026-09-30.md
```

This follow-up should be assigned a later WBS/UWBS identity and must not silently change the semantic meaning of the accepted experimental v0.1.4 boundary.

## 17. Stop conditions for Luna

Stop and report instead of repairing automatically if any of these occur:

- remote `release/reconstructed-v0.1` no longer points at `b4df4e91...` before replay;
- either accepted source commit does not resolve;
- cherry-pick conflict occurs;
- unexpected unrelated runtime paths appear in the diff;
- any focused or full regression test fails;
- compileall or diff check fails;
- TypeScript changed unexpectedly and its regression/typecheck fails;
- parent of the final synthetic commit is not exactly `b4df4e91...`;
- push is rejected because the remote branch advanced.

When stopping, report the exact command, exit result, SHA/path involved, and `git status --short`. Do not reset or force-push without a separate review.

## 18. Acceptance report format for Luna

After successful execution, report only the relevant facts in this form:

```text
v0.1.4 LOCAL RELEASE ACCEPTANCE

parent: b4df4e911597d9f17bfa0a50b2057c24159dee9f
source commits:
- e018283549ccbb74ff5309fc4fe0b4addb91fa0d
- c4f50c0878e001e8d6b031bf7f15ef188e3d4453

focused tests: <result>
full Python: <result>
compileall: PASS/FAIL
diff check: PASS/FAIL
TypeScript changed: yes/no
TypeScript tests/typecheck: <result or not required>

v0.1.4 boundary: <new SHA>
parent verification: PASS/FAIL
worktree clean: yes/no
remote push: PASS/FAIL

release classification:
EXPERIMENTAL / UNCALIBRATED ACCEPTED

non-blocking follow-up:
historical calibration / false-positive validation / evidence maturity / economic materiality / profit attribution
```

If every hard gate passes, v0.1.4 can be treated as complete for the development release line and work can proceed to the next planned version boundary.
