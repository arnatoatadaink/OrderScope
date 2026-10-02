# OrderScope v0.1.7 Release Manifest — 2026-10-02

Status: **REL-07 ACCEPTED / TAG READY**

## Release identity

```text
version: v0.1.7
scope: Oil / Commodity / Cross-Asset
UWBS: UWBS-080..086
reconstruction branch: release/reconstructed-v0.1.7
historical lane endpoint: 33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d
accepted predecessor replay: f2b1bd24127814d5c025287f1c4f7186511c470f
exact tested code candidate: 4ec40a8279e5650f2faebb0cbf30aac0ddc77383
```

## Reconstruction rule

The historical UWBS-080..086 endpoint predates the accepted post-v0.1.6 REC-01 replay. It is therefore not tagged directly.

The cumulative v0.1.7 tree is reconstructed by retaining the historical Oil / Commodity / Cross-Asset endpoint and overlaying only the accepted REC-01 Crypto source/test subtrees required to preserve cumulative v0.1.6 content.

No Physical-SaaS `UWBS-087..093` implementation tree and no Volatility `UWBS-094..100` implementation tree is included in the tested v0.1.7 candidate.

## Exact-boundary validation

GitHub Actions validation:

```text
workflow: REL-07 v0.1.7 validation
run id: 36952727896
CI PR: #15
checkout SHA: 4ec40a8279e5650f2faebb0cbf30aac0ddc77383
conclusion: SUCCESS
```

Measured results:

```text
Crypto focused tests: 111 passed in 0.42s
Full Python regression: 946 passed in 4.42s
Python compileall: PASS
Worker tests: 227 passed / 0 failed
Worker typecheck: PASS
git diff --check: PASS
```

Environment evidence from the CI run:

```text
runner: ubuntu-24.04
Python: 3.13.15
Node: 24.21.0
npm: 11.19.0
uv: 0.12.22
```

## Structural exclusion check

Comparison of historical endpoint `33ca0587...` to tested candidate `4ec40a82...` is a forward-only lineage (`behind_by=0`). The changed implementation/test paths are limited to the selected REC-01 Crypto replay subtrees plus REL-07 release documentation.

Explicitly excluded from the tested release boundary:

```text
UWBS-087..093 Physical-SaaS implementation
UWBS-094..100 VIX / Cross-Asset Volatility implementation
UWBS-101..104 Crypto On-chain Event Intelligence
```

## Existing dependency observation

`npm ci` reported four high-severity audit findings. The install completed and all Worker tests/typecheck passed. This manifest records the observation but does not classify it as introduced by the v0.1.7 reconstruction; dependency-audit remediation remains a separate maintenance/security task unless separately promoted to a release blocker.

## Runtime exclusions

This release acceptance does not newly authorize:

- production provider activation;
- Worker/Cron runtime mutation;
- D1 mutation beyond already accepted boundaries;
- PB execution;
- paid procurement;
- automated trading action;
- `WORKER_MODE=live` capacity acceptance beyond previously recorded scope.

## REL-07 decision

```text
Historical lane endpoint: PASS
Cumulative predecessor preservation: PASS
Later-feature exclusion: PASS
Exact-boundary CI: PASS
Release manifest: COMPLETE
REL-07: ACCEPTED
v0.1.7 tag readiness: READY
```

The exact code-bearing candidate validated by CI is `4ec40a8279e5650f2faebb0cbf30aac0ddc77383`. Release-document commits created after this validation must remain documentation-only descendants; otherwise the acceptance suite must be rerun before tagging.
