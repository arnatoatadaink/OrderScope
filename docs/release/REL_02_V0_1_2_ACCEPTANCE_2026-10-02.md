# OrderScope — REL-02 v0.1.2 Exact-Boundary Acceptance — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Boundary

```text
version: v0.1.2
commit: f69c52bf574212d1506df81abc7b15694abb7922
message: Reconstruct v0.1.2 from frozen source manifest
```

This is the cumulative Macro/Carry release boundary reconstructed from the frozen source manifest.

## Exact-boundary validation

The operator checked out the exact boundary commit in detached HEAD state and ran the release gate against that tree.

Results:

```text
Python analysis tests   563 passed, 1 dependency deprecation warning
Worker tests            178 passed, 0 failed
Python compileall       PASS
git diff --check        PASS
TypeScript typecheck    PASS
working tree            clean
```

The warning is the existing Starlette/AnyIO `BlockingPortal` deprecation warning and is non-blocking.

## Decision

```text
REL-02          ACCEPTED
v0.1.2          TAG READY
boundary SHA    f69c52bf574212d1506df81abc7b15694abb7922
```

No production provider activation, deployment, D1 mutation authorization, or release tag creation is authorized by this acceptance record.
