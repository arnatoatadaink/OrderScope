# REL-07 — v0.1.7 Boundary Audit — 2026-10-02

Status: **RECONSTRUCTION CANDIDATE CREATED / ACCEPTANCE PENDING**

## Scope

`v0.1.7` is the cumulative release boundary for the accepted Oil / Commodity / Cross-Asset lane `UWBS-080..086`, including the accepted reconstructed v0.1.6 Crypto Market Structure replay as its predecessor release content.

## Historical endpoint

The historical endpoint that closes UWBS-086 is:

```text
33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
Close UWBS-086 shadow boundary in current tracker
```

Git ancestry check against the later main lineage showed:

```text
base:      33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
status:    ahead
behind_by: 0
```

This is therefore the correct historical Oil / Commodity / Cross-Asset endpoint, but it is not itself a valid cumulative v0.1.7 tag target because it predates the later accepted REC-01 replay of the reconstructed v0.1.6 Crypto Market Structure lane.

## Accepted predecessor replay

REC-01 replay source:

```text
f2b1bd24127814d5c025287f1c4f7186511c470f
Replay v0.1.6 crypto packages for REC-01
```

The replay commit adds the accepted Crypto Market Structure packages and tests. For REL-07 reconstruction, only the ten Crypto source/test subtrees introduced by REC-01 are transplanted; later Physical-SaaS and Volatility trees present elsewhere in the REC-01 parent lineage are not imported.

Imported source trees:

```text
analysis/app/orderscope_local/crypto_archive
analysis/app/orderscope_local/crypto_canary
analysis/app/orderscope_local/crypto_context
analysis/app/orderscope_local/crypto_derivatives
analysis/app/orderscope_local/crypto_time
```

Imported test trees:

```text
analysis/tests/crypto_archive
analysis/tests/crypto_canary
analysis/tests/crypto_context
analysis/tests/crypto_derivatives
analysis/tests/crypto_time
```

## Reconstruction candidate

Reconstruction branch:

```text
release/reconstructed-v0.1.7
```

Candidate cumulative commit:

```text
607db626a5ac355e5717332ca50ae859615a8f12
Reconstruct cumulative v0.1.7 with accepted REC-01 crypto replay
```

Candidate base tree before replay overlay:

```text
6538ae1ef214b7436c9b8992ef31da07dd025112
```

Candidate reconstructed tree:

```text
f2945becd8ec5790d765b0a0e9063e5ca426fe93
```

## Evidence already accepted upstream

Historical UWBS-086 acceptance recorded:

```text
shadow capacity bound focused tests: 10 passed
D1 capacity evidence focused tests:  10 passed
historical Canary evaluation tests:   7 passed
full Python regression:             835 passed
compileall:                         PASS
git diff --check:                   PASS
```

REC-01 crypto replay was separately accepted during the post-v0.1.6 reconciliation. These are upstream acceptance records, not a substitute for the final exact-boundary release test required by REL-07.

## REL-07 gate state

```text
Historical UWBS-080..086 endpoint        PASS
Historical endpoint ancestry             PASS
Direct-tag suitability of 33ca0587       FAIL / intentionally rejected
Accepted REC-01 replay source identified PASS
Crypto-only subtree selection            PASS
Reconstruction candidate created         PASS
Later v0.1.8/v0.1.9 feature exclusion    VERIFY NEXT
Exact-boundary release acceptance        PENDING
v0.1.7 release manifest                  PENDING
Tag readiness                            NOT READY
```

## Next gate

1. move `release/reconstructed-v0.1.7` to candidate `607db626...` by non-forced fast-forward;
2. compare against historical endpoint and prove only the selected Crypto replay plus REL-07 audit artifacts are added;
3. prove Physical-SaaS `UWBS-087..093` and Volatility `UWBS-094..100` implementation trees are absent from the candidate;
4. run or obtain exact-boundary release acceptance evidence;
5. write the v0.1.7 release manifest and only then mark the tag boundary READY.

No provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this reconstruction.