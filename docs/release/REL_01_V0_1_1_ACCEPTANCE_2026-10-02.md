# OrderScope REL-01 — v0.1.1 Exact-Boundary Acceptance — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Boundary

```text
version: v0.1.1
boundary SHA: bada5bff803321427eb3c8eb1f3d159460ba5dd1
commit: Reconstruct v0.1.1 from frozen source manifest
```

This is the cumulative operational/runtime release boundary reconstructed from the frozen source manifest.

## Exact-boundary validation

The operator checked out the exact boundary in detached HEAD state and confirmed a clean working tree before executing the release gate.

Commands:

```bash
git switch --detach bada5bff803321427eb3c8eb1f3d159460ba5dd1
git rev-parse HEAD
git status --short
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
npm test
npm run typecheck
```

Observed results:

```text
HEAD                    bada5bff803321427eb3c8eb1f3d159460ba5dd1
working tree            clean
Python analysis tests   544 passed, 1 warning
compileall              PASS
git diff --check        PASS
Worker tests            178 passed / 0 failed
TypeScript typecheck    PASS
```

The single Python warning is the existing Starlette / AnyIO deprecation warning and is non-blocking.

## Decision

The reconstructed v0.1.1 boundary has now been exercised directly as a release candidate rather than inferred only from source-level acceptance history.

```text
REL-01       ACCEPTED
v0.1.1       TAG READY
```

No production provider activation, Worker deployment, D1 mutation authorization, branch rewrite, or tag creation is authorized by this document.
