# OrderScope v0.1.8 Release Manifest — 2026-10-02

Status: **REL-08 ACCEPTED / TAG READY**

## Release identity

```text
version: v0.1.8
scope: Physical-SaaS
UWBS: UWBS-087..093
predecessor boundary: 423929ae1ff3fd7431260ffdab09810dc7105aa0
historical lane endpoint: ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325
exact tested code candidate: 5069f81af63a554d0f2412f0309cc2244f95434e
```

## Reconstruction rule

The accepted cumulative v0.1.7 boundary is used as the parent. The historical delta from the v0.1.7 Oil / Commodity endpoint through the Physical-SaaS closeout was verified to contain only UWBS-087..093 implementation, tests, tracker updates and acceptance/design documentation. That Physical-SaaS delta was overlaid onto the accepted cumulative v0.1.7 boundary.

No UWBS-094..100 Volatility implementation and no UWBS-101..104 On-chain Event Intelligence implementation is included.

## Exact-boundary validation

```text
workflow: REL-08 v0.1.8 validation
run id: 36953356715
CI PR: #16
checkout SHA: 5069f81af63a554d0f2412f0309cc2244f95434e
conclusion: SUCCESS
```

Measured results:

```text
Physical-SaaS focused tests: 69 passed in 0.19s
Full Python regression:      1015 passed in 3.53s
Python compileall:           PASS
Worker tests:                227 passed / 0 failed
Worker typecheck:            PASS
git diff --check:            PASS
```

Validation environment:

```text
Ubuntu 24.04.5
Python 3.13.15
Node 24.21.0
npm 11.19.0
uv 0.12.22
```

`npm ci` reported four high-severity audit findings, matching the already recorded dependency-security observation from REL-07. Installation and all release gates passed. This remains a separate dependency-maintenance/security item unless separately promoted to a release blocker.

## REL-08 decision

```text
Accepted v0.1.7 predecessor: PASS
Historical Physical-SaaS endpoint: PASS
Physical-SaaS-only reconstruction: PASS
Later-feature exclusion: PASS
Exact-boundary CI: PASS
REL-08: ACCEPTED
v0.1.8 tag readiness: READY
```

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or automated trading action is authorized by this release reconstruction.
