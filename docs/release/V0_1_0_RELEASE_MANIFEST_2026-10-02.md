# OrderScope v0.1.0 Release Manifest — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Semantic scope

`v0.1.0` is the original OrderScope WBS / Critical Path implementation baseline. It includes the original Local Corporate Intelligence foundation and accepted original formal work through the N1-006 real-data benchmark.

PB execution and later UWBS-derived capability lanes are excluded from this version.

## Boundary

```text
99b08a0b5fa1bec5921dc42e630c579a4e83c401
Accept N1-006 real-data benchmark
```

This boundary was identified by the historical reconstruction audit because it closes the final identified original-WBS benchmark immediately before later UWBS-originated operational/runtime extensions begin.

## Acceptance evidence

Historical functional acceptance at the boundary includes the N1-006 real-data benchmark with complete reviewed population and measured recall evidence.

A fresh exact-boundary release gate was executed on 2026-10-02 with detached HEAD at the boundary SHA.

```text
Python analysis tests     503 passed / 1 warning
Python compileall         PASS
Git diff check            PASS
Worker tests               94 passed / 0 failed
TypeScript typecheck      PASS
working tree              clean
```

Acceptance record:

`docs/release/REL_00_V0_1_0_ACCEPTANCE_2026-10-02.md`

## Release interpretation

```text
v0.1.0
  original WBS / CP baseline
  PB excluded
  later UWBS lanes excluded
  exact historical boundary validated
```

## Tag target

If an annotated `v0.1.0` tag is created, it should resolve to the accepted historical boundary:

```text
99b08a0b5fa1bec5921dc42e630c579a4e83c401
```

The documentation commits that record this later audit are not the product-code tag target.

## Decision

```text
VERSION          v0.1.0
REL              REL-00
ACCEPTANCE       ACCEPTED
TAG READINESS    READY
TAG CREATED      NO
```
