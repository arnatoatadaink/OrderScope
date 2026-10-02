# REL-07 — v0.1.7 Boundary Audit — 2026-10-02

Status: **RECONSTRUCTION REQUIRED — HISTORICAL UWBS-080..086 BOUNDARY VERIFIED**
Release target: `v0.1.7`
Scope: `UWBS-080..086` Oil / Commodity / Cross-Asset

## 1. Decision summary

The historical UWBS-080..086 closeout commit is:

```text
33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
Close UWBS-086 shadow boundary in current tracker
```

This commit is a strict ancestor of current `main`:

```text
base:       33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
head:       main
status:     ahead
ahead_by:   94
behind_by:  0
merge_base: 33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
```

Therefore it is the correct **historical v0.1.7 feature-lane endpoint**.

It is **not** by itself the final cumulative v0.1.7 release boundary because the accepted v0.1.6 Crypto Market Structure lane was reconstructed/replayed later during REC-01. Tagging `33ca0587...` directly would produce a semantic v0.1.7 tree that omits the subsequently accepted cumulative v0.1.6 contents.

## 2. UWBS-086 acceptance evidence

Historical closeout evidence at `33ca0587...`:

`docs/work-management/local-corporate-intelligence/UWBS-086_FINAL_SHADOW_CAPACITY_ACCEPTANCE_2026-09-27.md`

Recorded verification:

```text
shadow capacity bound focused tests:      10 passed
D1 capacity evidence focused tests:       10 passed
historical Canary evaluation tests:        7 passed
full Python regression:                  835 passed
compileall:                              PASS
git diff --check:                        PASS
```

Historical Canary result:

```text
expected_regime:      risk_off
observed_regime:      risk_off
expected_alert:       true
observed_alert:       true
false positives:      0
false negatives:      0
regime mismatches:    0
historical clean:     true
```

Accepted runtime boundary remains shadow-only; `WORKER_MODE=live` is excluded.

## 3. Cumulative-release issue

Release versions are cumulative. The accepted sequence requires:

```text
accepted reconstructed v0.1.6 Crypto Market Structure
    +
accepted historical UWBS-080..086 Oil / Commodity / Cross-Asset
    =
reconstructed cumulative v0.1.7
```

The historical v0.1.7 endpoint predates REC-01 replay. Therefore ancestry alone is insufficient for final tagging.

## 4. Reconstruction choice

Selected reconstruction strategy:

1. preserve `33ca0587...` as the authoritative historical UWBS-080..086 endpoint;
2. reuse the accepted REC-01 Crypto replay package rather than redesigning UWBS-068..079;
3. build a dedicated reconstructed cumulative branch;
4. do not rewrite `main` or historical source commits;
5. run cumulative release acceptance against the reconstructed tree;
6. only then mark the v0.1.7 tag `READY`.

Staging branch created:

```text
release/reconstructed-v0.1.7
base: 33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
```

The base branch creation does not yet constitute cumulative acceptance; the accepted REC-01 Crypto replay still has to be applied/equivalence-verified on this branch.

## 5. REC-01 replay source

Accepted replay source commit:

```text
f2b1bd24127814d5c025287f1c4f7186511c470f
Replay v0.1.6 crypto packages for REC-01
```

REC-01 acceptance remains the authority for the reconstructed Crypto package contents. The replay must preserve the existing Fact / Derived Metric / Interpretation boundaries and must not promote UWBS-079 Stage B beyond its accepted state.

## 6. REL-07 gate state

```text
Historical UWBS-080..086 endpoint verification: PASS
Ancestry to current main:                  PASS
Historical UWBS-086 acceptance evidence:   PASS
Direct-tag suitability of 33ca0587...:      FAIL (not cumulative with reconstructed v0.1.6)
Reconstruction staging branch:              CREATED
Cumulative v0.1.7 release tree:             PENDING
Fresh/reconstructed release acceptance:     PENDING
v0.1.7 manifest finalization:                PENDING
v0.1.7 tag readiness:                        NOT READY
```

## 7. Next reconstruction step

```text
release/reconstructed-v0.1.7 @ 33ca0587...
  -> apply / reproduce accepted REC-01 v0.1.6 Crypto package replay
  -> verify no v0.1.8+ Physical-SaaS or v0.1.9+ Volatility scope is introduced
  -> run cumulative acceptance
  -> write final V0_1_7_RELEASE_MANIFEST
  -> mark REL-07 ACCEPTED / TAG READY
```

No provider activation, Worker/Cron mutation, D1 mutation, PB execution, automated trading action, or production security assertion is authorized by REL-07 reconstruction work.
