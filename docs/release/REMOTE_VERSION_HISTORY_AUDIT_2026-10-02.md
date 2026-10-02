# OrderScope — Remote Version History Audit — 2026-10-02

Status: **REMOTE / LOCAL RECONCILIATION CHECKPOINT — PB DIVERGENCE REVIEWED**
Date: 2026-10-02
Repository: `arnatoatadaink/OrderScope`

## 1. Purpose

This report records the GitHub-visible `v0.1.0` through `v0.1.9` history state and incorporates the local synchronization audit executed after `git fetch --all --prune --tags`.

A previous revision understated the remote reconstruction state for `v0.1.1..v0.1.5` because those boundaries are stored as sequential commits on the generic remote branch `release/reconstructed-v0.1`, rather than separate per-version branches. That finding is corrected here.

This revision additionally reconciles the divergent local `l1-003-local-market-recovery` PB line against its remote counterpart.

## 2. Remote reconstruction chain

Remote `release/reconstructed-v0.1` contains the cumulative semantic-version reconstruction checkpoints:

```text
v0.1.1  bada5bff803321427eb3c8eb1f3d159460ba5dd1
v0.1.2  f69c52bf574212d1506df81abc7b15694abb7922
v0.1.3  b4df4e911597d9f17bfa0a50b2057c24159dee9f
v0.1.4  a798622f839b836f8b60f52dd700b8fd87147991
v0.1.5  415de1f1dd42f70bd66992961cb43be7edba6ade
```

Remote also contains:

```text
v0.1.6 accepted development boundary
  bfaf89c68daa656b7d75317f086458257cc94da9

v0.1.7 accepted / tag-ready
  validated code: 4ec40a8279e5650f2faebb0cbf30aac0ddc77383
  doc-complete:   423929ae1ff3fd7431260ffdab09810dc7105aa0

v0.1.8 accepted / tag-ready
  validated code: 5069f81af63a554d0f2412f0309cc2244f95434e
  doc-complete:   d34d471b20d4f5be865b0414a42240ec7f3061d9

v0.1.9 accepted / tag-ready
  validated code: 530ae9087c53ced5f1c8261cf32d1e7687334943
  doc-complete:   fcfba651dbead9d035019e330f61986f5a1a60f7
```

No `v0.1.x` Git tags are currently visible on remote.

## 3. v0.1.0 historical boundary finding

Remote history contains a dedicated reconstruction study:

```text
2326164654007a1cbeb7363c8f2becddd8aa9390
Document v0.1.0-v0.1.3 boundary reconstruction findings
```

That study identifies the strongest clean existing-history candidate for `v0.1.0` as:

```text
99b08a0b5fa1bec5921dc42e630c579a4e83c401
Accept N1-006 real-data benchmark
```

Reason: it closes the final identified original-WBS real-data benchmark immediately before UWBS-originated Worker/runtime extension work begins. The reconstruction model explicitly defines `v0.1.0` as the original WBS/CP baseline **with PB excluded**.

Therefore the PB-10 local divergence is not required to define the `v0.1.0` source boundary. PB work belongs to the later active-market/PB closeout lane in the historical release model.

Current classification:

```text
v0.1.0 source boundary candidate = 99b08a0...
version-level exact acceptance/tag package = still to formalize
PB local divergence = not part of v0.1.0 source scope
```

## 4. Local PB branch divergence

Local branch state:

```text
l1-003-local-market-recovery
  ahead 5 / behind 7 versus origin/l1-003-local-market-recovery
merge base:
  16465e2af5faddccc8eeeb1a5af87c4d4f6ced40
```

Local-only commits:

```text
e0e4ff0 Record local PB-10 stop state and source evidence
07d5df2 Add bounded equity-only PB-10 continuation
9958cf1 Record PB-10 equity-only Phase B acceptance
21cc245 Record BTC Sunday market activity evidence
b6f1193 Record qualified PB close and BTC follow-up path
```

Remote-side successor commits after the same merge base include:

```text
a784a57 Add bounded equity-only PB-10 continuation
d17c295 Record PB-10 equity-only Phase B acceptance
58dba75 Record BTC Sunday market activity evidence
46976f3 Record qualified PB close and BTC follow-up path
b31e6ca Close PB lane and split BTCUSD gap follow-up
81c29e6 Add OrderScope v0.1 release manifest
2326164 Document v0.1.0-v0.1.3 boundary reconstruction findings
```

The four local commits after `e0e4ff0` correspond semantically to the first four remote commits above. The remote history subsequently adds stronger governance closeout and version-reconstruction documentation.

Conclusion:

```text
07d5df2 / 9958cf1 / 21cc245 / b6f1193
  -> superseded by equivalent remote-side commits
  -> do NOT merge/push the divergent local branch just to preserve these SHAs
```

## 5. Unique local evidence still not visible on the remote PB branch

The total local-side diff from the merge base contains 10 changed files. Seven are accounted for by the remote continuation/acceptance/Sunday-review/qualified-close sequence.

The remaining three files are associated with the initial local stop-state evidence commit `e0e4ff0`:

```text
docs/work-management/local-corporate-intelligence/L1-003_PB10_SEP28_PROVIDER_ABSENCE_READS.json
docs/work-management/local-corporate-intelligence/L1-003_PB10_SEP28_PARTIAL_WINDOW_HANDOFF.md
docs/work-management/local-corporate-intelligence/L1-003_PB10_SEP28_STOP_STATE.json
```

These artifacts are not present on the remote `l1-003-local-market-recovery` branch at the audited state.

They are raw/provenance evidence, not required to recreate the already-accepted remote PB continuation semantics. However, they should be preserved before local branch cleanup because later remote closeout documents state that historical provider evidence is retained.

Recommended treatment:

1. preserve the three files or the `e0e4ff0` commit on a non-release archival/audit branch;
2. do not merge the whole divergent local PB branch;
3. do not use these artifacts to redefine `v0.1.0`;
4. after preservation, the stale local PB branch may be retired separately.

## 6. Remote PB close state

Remote PB governance progressed beyond the local qualified-close state.

`46976f3` records:

```text
EQUITY-ONLY PHASE B ACCEPTED
WORKER SHADOW
BTCUSD six-minute gap remains separate follow-up
```

`b31e6ca` then supersedes the earlier five-symbol-open wording and states:

```text
PB-00..PB-10           CLOSED / ACCEPTED
PB lane                COMPLETE
BTCUSD six-minute gap  SEPARATE FOLLOW-UP / OUTSIDE PB
```

Thus the local PB branch is an earlier parallel line, not the current governance source of truth.

## 7. Current version-history classification

| Version | Remote boundary state | Acceptance/history state |
|---|---|---|
| `v0.1.0` | clean source candidate `99b08a0...` identified | exact version acceptance/manifest still needs final formalization |
| `v0.1.1` | `bada5bff...` | reconstructed remotely |
| `v0.1.2` | `f69c52bf...` | reconstructed remotely |
| `v0.1.3` | `b4df4e91...` | reconstructed remotely |
| `v0.1.4` | `a798622f...` | reconstructed remotely; separate local Theme provenance check remains |
| `v0.1.5` | `415de1f1...` | reconstructed remotely |
| `v0.1.6` | `bfaf89c6...` | accepted development boundary exists remotely |
| `v0.1.7` | `423929ae...` doc-complete | accepted / tag-ready |
| `v0.1.8` | `d34d471...` doc-complete | accepted / tag-ready |
| `v0.1.9` | `fcfba651...` doc-complete | accepted / tag-ready |

## 8. Remaining local-only history requiring review

After PB semantic reconciliation, the meaningful local-only history is reduced to two classes.

### A. PB raw evidence

```text
e0e4ff0
```

Preserve for provenance; do not merge the whole divergent branch.

### B. AI Theme provenance

```text
e018283 Implement candidate AI theme contracts and conservative observation flow
c4f50c0 Preserve event evidence in theme state assessments
```

Remote already has reconstructed `v0.1.4` at `a798622f...` and later REC-03 cumulative acceptance. These two commits require tree/patch equivalence review before deciding whether they are superseded or contain unique provenance worth archiving.

## 9. Recommended next actions

1. Preserve `e0e4ff0` evidence without merging the divergent PB line.
2. Verify the exact release-acceptance state of the `v0.1.1..v0.1.5` reconstructed commits (boundary exists does not automatically mean exact-boundary release tests were run at each commit).
3. Formalize `v0.1.0` around `99b08a0...` with the same manifest/acceptance discipline used for later versions.
4. Review the two local-only AI Theme commits against `a798622f...`.
5. Only after those checks decide which `v0.1.0..v0.1.6` boundaries are genuinely tag-ready.

Do not force-push or delete the local-only branches until the provenance preservation steps are complete.
