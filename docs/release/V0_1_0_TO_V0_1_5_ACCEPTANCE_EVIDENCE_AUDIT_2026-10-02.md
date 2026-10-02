# OrderScope — v0.1.0..v0.1.5 Acceptance Evidence Audit — 2026-10-02

Status: **BOUNDARIES IDENTIFIED / EXACT-BOUNDARY RELEASE VALIDATION INCOMPLETE**

## 1. Purpose

This audit distinguishes three separate questions for `v0.1.0` through `v0.1.5`:

1. does a functional/source acceptance record exist;
2. does a reconstructed semantic-version boundary commit exist;
3. was that exact reconstructed SHA independently exercised as a release boundary with a complete regression gate.

A reconstruction commit containing accepted source material is not automatically equivalent to an exact-boundary release acceptance run.

## 2. Boundary inventory

```text
v0.1.0 source candidate
  99b08a0b5fa1bec5921dc42e630c579a4e83c401
  Accept N1-006 real-data benchmark

v0.1.1 reconstructed boundary
  bada5bff803321427eb3c8eb1f3d159460ba5dd1

v0.1.2 reconstructed boundary
  f69c52bf574212d1506df81abc7b15694abb7922

v0.1.3 reconstructed boundary
  b4df4e911597d9f17bfa0a50b2057c24159dee9f

v0.1.4 reconstructed boundary
  a798622f839b836f8b60f52dd700b8fd87147991

v0.1.5 reconstructed boundary
  415de1f1dd42f70bd66992961cb43be7edba6ade
```

`v0.1.1..v0.1.5` are cumulative commits on remote branch `release/reconstructed-v0.1`.

## 3. v0.1.0 acceptance evidence

The boundary reconstruction study identifies `99b08a0...` as the strongest clean historical boundary immediately before UWBS-originated Worker/runtime extension work begins.

The commit itself is an acceptance commit (`Accept N1-006 real-data benchmark`) and records:

```text
645 / 645 review candidates explicitly reviewed
51 matched
594 unrelated
0 unresolved
4 / 4 frozen reference events discovered
recall 1.0000
misattribution 0
focused tests 19
full Python 503
compileall PASS
git diff --check PASS
```

This is strong source-boundary acceptance evidence for the original WBS/CP baseline.

However, no dedicated semantic-version release manifest / exact-boundary CI record for `v0.1.0` has yet been established in the reconstructed release process.

Classification:

```text
source acceptance evidence     PASS
clean source boundary          PASS
exact release-boundary suite   NOT YET RECORDED
release manifest               NOT YET COMPLETE
tag readiness                  NOT READY
```

PB-10 is not part of `v0.1.0` under the adopted release model.

## 4. v0.1.1 acceptance evidence

`bada5bff...` reconstructs the cumulative operational/runtime boundary from frozen accepted source material.

The reconstructed tree contains historical task-level acceptance records, including operational/Worker evidence such as:

```text
focused scheduler-registration 4 / 4
full TypeScript                161 / 161
typecheck                      PASS
Wrangler deploy --dry-run      PASS
full Python                    537 / 537
compileall                     PASS
git diff --check               PASS
```

and later scheduler/capacity verification including:

```text
focused scheduler/capacity/orchestration 33 passed
full TypeScript                         124 passed
typecheck                               PASS
Wrangler type generation                PASS
Wrangler deploy dry-run/build            PASS
git diff --check                         PASS
```

These records prove the source functionality had acceptance evidence.

But GitHub currently reports no PR-triggered workflow run and no combined commit status for the exact reconstructed SHA `bada5bff...`.

Classification:

```text
functional/source acceptance   PASS
reconstructed boundary         PASS
exact reconstructed-SHA gate   NOT PROVEN
manifest                       NOT COMPLETE
TAG READY                      NO
```

## 5. v0.1.2 acceptance evidence

`f69c52bf...` reconstructs the cumulative Macro/Carry lane (`UWBS-011..015`) on top of reconstructed `v0.1.1`.

The commit carries implementation and tests from accepted source work, but the reconstruction commit itself is a reconstruction checkpoint rather than an acceptance commit.

No PR-triggered workflow run or combined commit status is recorded for the exact SHA.

Classification:

```text
accepted source material       PRESENT
reconstructed boundary         PASS
exact reconstructed-SHA gate   NOT PROVEN
manifest                       NOT COMPLETE
TAG READY                      NO
```

## 6. v0.1.3 acceptance evidence

`b4df4e91...` reconstructs the cumulative cross-market / competitor / official macro adapter lane (`UWBS-027..036`) on top of reconstructed `v0.1.2`.

The commit contains the source implementation/test material, but it is not itself an exact-boundary acceptance commit.

No PR-triggered workflow run or combined commit status is recorded for the exact SHA.

Classification:

```text
accepted source material       PRESENT
reconstructed boundary         PASS
exact reconstructed-SHA gate   NOT PROVEN
manifest                       NOT COMPLETE
TAG READY                      NO
```

## 7. v0.1.4 acceptance evidence

`a798622f...` reconstructs `UWBS-062..066` as the experimental AI Theme boundary.

The reconstruction explicitly preserves conservative semantics and keeps calibration / false-positive / persistence / materiality questions unvalidated rather than inventing thresholds.

Later REC-03 / REC-04 cumulative reconciliation proves the recovered Theme package in the current accepted cumulative tree:

```text
theme focused       12 passed
full analysis     1118 passed
Worker             227 passed / 0 failed
compileall           PASS
git diff --check     PASS
npm typecheck        PASS
```

This proves the recovered Theme functionality is accepted in the later cumulative tree.

It does **not** prove that exact reconstructed SHA `a798622f...` was independently exercised as a release boundary. GitHub currently shows no PR-triggered workflow run and no combined commit status for that SHA.

Two local-only Theme commits (`e018283`, `c4f50c0`) remain a provenance/equivalence check. Their absence from current remote refs prevents remote-only proof of patch identity.

Classification:

```text
feature acceptance             PASS via later cumulative reconciliation
reconstructed boundary         PASS
exact reconstructed-SHA gate   NOT PROVEN
local provenance equivalence   PENDING
manifest                       NOT COMPLETE
TAG READY                      NO
```

## 8. v0.1.5 acceptance evidence

`415de1f1...` reconstructs the cumulative `UWBS-067` Listing Compliance / Earnings Repricing Canary boundary on top of reconstructed `v0.1.4`.

Later REC-03 / REC-04 cumulative reconciliation proves the recovered listing package:

```text
listing_compliance    9 passed
full analysis      1118 passed
Worker              227 passed / 0 failed
compileall            PASS
git diff --check      PASS
npm typecheck         PASS
```

Again, this is later cumulative validation rather than a direct exact-boundary run of `415de1f1...`.

GitHub currently shows no PR-triggered workflow run and no combined commit status for the exact reconstructed SHA.

Classification:

```text
feature acceptance             PASS via later cumulative reconciliation
reconstructed boundary         PASS
exact reconstructed-SHA gate   NOT PROVEN
manifest                       NOT COMPLETE
TAG READY                      NO
```

## 9. Current acceptance matrix

| Version | Boundary identified | Functional/source acceptance | Exact-boundary validation | Manifest | Current release classification |
|---|---|---|---|---|---|
| `v0.1.0` | Yes: `99b08a0...` | **PASS** | **Missing release-level rerun** | Missing | **NOT TAG READY** |
| `v0.1.1` | Yes: `bada5bff...` | **PASS** | **Not proven on reconstructed SHA** | Missing | **NOT TAG READY** |
| `v0.1.2` | Yes: `f69c52bf...` | Source material accepted | **Not proven on reconstructed SHA** | Missing | **NOT TAG READY** |
| `v0.1.3` | Yes: `b4df4e91...` | Source material accepted | **Not proven on reconstructed SHA** | Missing | **NOT TAG READY** |
| `v0.1.4` | Yes: `a798622f...` | **PASS via REC cumulative validation** | **Not proven on reconstructed SHA** | Missing | **NOT TAG READY** |
| `v0.1.5` | Yes: `415de1f1...` | **PASS via REC cumulative validation** | **Not proven on reconstructed SHA** | Missing | **NOT TAG READY** |

The remaining problem is therefore no longer missing reconstruction commits. It is **release acceptance normalization**.

## 10. Required exact-boundary gate

For each release boundary, run the same disciplined validation style used for REL-07 through REL-09.

Minimum common gate:

```bash
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
npm test
npm run typecheck
```

Where the historical boundary predates one side of the runtime/tooling tree, a command that is structurally unavailable at that boundary must be marked `NOT APPLICABLE` with evidence; it must not be silently counted as PASS.

Focused suites should be added per version scope:

```text
v0.1.0  original WBS / N1 final acceptance-relevant tests
v0.1.1  operational / scheduler / Worker / retention-replay tests
v0.1.2  macro/carry tests
v0.1.3  cross-market / relationship / repricing / official adapter tests
v0.1.4  theme tests
v0.1.5  listing_compliance tests
```

## 11. Proposed closeout order

```text
REL-00  validate 99b08a0... and write v0.1.0 manifest
  -> REL-01 validate bada5bff... and write v0.1.1 manifest
  -> REL-02 validate f69c52bf... and write v0.1.2 manifest
  -> REL-03 validate b4df4e91... and write v0.1.3 manifest
  -> REL-04 validate a798622f... and write v0.1.4 manifest
  -> REL-05 validate 415de1f1... and write v0.1.5 manifest
  -> REL-06 reconcile/validate cumulative v0.1.6 successor boundary
```

Only after these exact-boundary gates should annotated `v0.1.0..v0.1.6` tags be considered.

## 12. Current decision

```text
v0.1.0..v0.1.5 reconstruction commits  FOUND
source/feature acceptance evidence       FOUND
exact-boundary release acceptance        INCOMPLETE
semantic Git tags                        NOT AUTHORIZED YET
```

No runtime/provider mutation, history rewrite, force push, or tag creation is authorized by this audit.
