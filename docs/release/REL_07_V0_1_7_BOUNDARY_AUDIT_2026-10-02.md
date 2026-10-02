# REL-07 — v0.1.7 Boundary Audit — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Scope

`v0.1.7` is the cumulative release boundary for the accepted Oil / Commodity / Cross-Asset lane `UWBS-080..086`, including the accepted reconstructed v0.1.6 Crypto Market Structure replay as predecessor release content.

## Historical endpoint

The historical endpoint that closes UWBS-086 is:

```text
33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
Close UWBS-086 shadow boundary in current tracker
```

Ancestry check against the later main lineage showed the historical endpoint is a strict ancestor (`behind_by=0`). It is therefore the correct Oil / Commodity / Cross-Asset endpoint, but it is not itself a valid cumulative v0.1.7 tag target because it predates the later accepted REC-01 replay of reconstructed v0.1.6 Crypto Market Structure.

## Accepted predecessor replay

REC-01 replay source:

```text
f2b1bd24127814d5c025287f1c4f7186511c470f
Replay v0.1.6 crypto packages for REC-01
```

REL-07 imports only the Crypto source/test subtrees established by REC-01:

```text
analysis/app/orderscope_local/crypto_archive
analysis/app/orderscope_local/crypto_canary
analysis/app/orderscope_local/crypto_context
analysis/app/orderscope_local/crypto_derivatives
analysis/app/orderscope_local/crypto_time
analysis/tests/crypto_archive
analysis/tests/crypto_canary
analysis/tests/crypto_context
analysis/tests/crypto_derivatives
analysis/tests/crypto_time
```

## Reconstructed cumulative candidate

Reconstruction branch:

```text
release/reconstructed-v0.1.7
```

Exact code-bearing candidate validated by CI:

```text
4ec40a8279e5650f2faebb0cbf30aac0ddc77383
Reconstruct cumulative v0.1.7 with accepted REC-01 crypto replay
```

Reconstructed code tree:

```text
e0ee96e27caccebd4793c5c954ae4c23d0e11cc1
```

The earlier intermediate object `607db626...` is superseded and is not the accepted release candidate.

## Structural verification

Comparison from `33ca0587...` to `4ec40a82...` is forward-only and contains only:

1. selected REC-01 Crypto source/test content;
2. REL-07 release audit documentation.

The tested candidate does not include implementation trees for:

```text
UWBS-087..093  Physical-SaaS
UWBS-094..100  VIX / Cross-Asset Volatility
UWBS-101..104  Crypto On-chain Event Intelligence
```

Result: **PASS**.

## Exact-boundary CI validation

CI-only PR: `#15`

Workflow:

```text
REL-07 v0.1.7 validation
run id: 36952727896
checkout SHA: 4ec40a8279e5650f2faebb0cbf30aac0ddc77383
conclusion: success
```

Measured results:

```text
Crypto focused tests:    111 passed in 0.42s
Full Python regression:  946 passed in 4.42s
Python compileall:       PASS
Worker tests:            227 passed / 0 failed
Worker typecheck:         PASS
git diff --check:         PASS
```

Validation environment:

```text
Ubuntu 24.04
Python 3.13.15
Node 24.21.0
npm 11.19.0
uv 0.12.22
```

`npm ci` also reported four high-severity dependency audit findings. Installation and all release tests/typecheck still passed. This is recorded as a separate dependency-security observation and is not attributed to the reconstruction without separate analysis.

## Upstream acceptance retained

Historical UWBS-086 acceptance already recorded:

```text
shadow capacity bound focused tests: 10 passed
D1 capacity evidence focused tests:  10 passed
historical Canary evaluation tests:   7 passed
full Python regression:             835 passed
compileall:                         PASS
git diff --check:                   PASS
```

The new exact-boundary CI supersedes the need to rely only on that older aggregate result for REL-07.

## Manifest

Release manifest:

```text
docs/release/V0_1_7_RELEASE_MANIFEST_2026-10-02.md
```

The exact tested code-bearing commit is `4ec40a82...`. Manifest/audit updates after that test are documentation-only descendants and do not change the tested implementation tree.

## REL-07 gate state

```text
Historical UWBS-080..086 endpoint        PASS
Historical endpoint ancestry             PASS
Direct-tag suitability of 33ca0587       REJECTED AS NON-CUMULATIVE
Accepted REC-01 predecessor replay       PASS
Crypto-only subtree selection            PASS
Reconstruction candidate                 PASS
Later v0.1.8/v0.1.9 feature exclusion    PASS
Exact-boundary release acceptance        PASS
v0.1.7 release manifest                  COMPLETE
REL-07                                   ACCEPTED
v0.1.7 tag readiness                     READY
```

## Release boundary rule

The validated implementation boundary is `4ec40a8279e5650f2faebb0cbf30aac0ddc77383`. A tag may point to a documentation-only descendant containing the accepted audit/manifest only if comparison confirms no implementation, test, runtime, configuration or dependency content changed after the validated candidate. Any substantive change requires the acceptance suite to be rerun.

No provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this reconstruction.
