# OrderScope v0.1.1 Release Manifest — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Release identity

```text
version: v0.1.1
boundary SHA: bada5bff803321427eb3c8eb1f3d159460ba5dd1
release gate: REL-01
```

## Scope

`v0.1.1` is the cumulative operational/runtime release boundary reconstructed from the frozen source manifest on top of the v0.1.0 baseline.

Canonical scope includes the operational/runtime UWBS lane associated with:

```text
UWBS-001..004
UWBS-016
UWBS-023..026
```

The release remains cumulative with v0.1.0 and preserves the historical source commits rather than rewriting them.

## Acceptance evidence

Exact-boundary validation on 2026-10-02:

```text
Python analysis tests   544 passed, 1 warning
Worker tests            178 passed / 0 failed
Python compileall       PASS
git diff --check        PASS
TypeScript typecheck    PASS
working tree            clean
```

The warning is the pre-existing Starlette / AnyIO deprecation warning and is non-blocking.

## Release classification

```text
functional/source acceptance   CONFIRMED
reconstructed boundary         CONFIRMED
exact-boundary validation      CONFIRMED
release manifest               CONFIRMED
tag-ready state                YES
```

## Explicit exclusions

This manifest does not authorize:

- production provider activation;
- Worker deployment;
- D1 mutation changes;
- secret/provider configuration changes;
- force push or history rewrite;
- Git tag creation by itself.

## Decision

```text
v0.1.1  ACCEPTED / TAG READY
```
