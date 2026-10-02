# REL-00 — OrderScope v0.1.0 Exact-Boundary Acceptance — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Boundary

```text
version: v0.1.0
boundary: 99b08a0b5fa1bec5921dc42e630c579a4e83c401
commit: Accept N1-006 real-data benchmark
```

This release boundary represents the original WBS / CP baseline with PB execution excluded. PB / active-market validation is a later release lane and is not part of v0.1.0.

## Exact-boundary verification

The operator detached HEAD directly at the boundary SHA and verified a clean working tree before running the release gate.

```text
HEAD = 99b08a0b5fa1bec5921dc42e630c579a4e83c401
working tree = clean
```

Commands executed:

```bash
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
npm test
npm run typecheck
```

Results:

```text
Python analysis tests     503 passed / 1 dependency warning
Python compileall         PASS
Git diff check            PASS
Worker tests               94 passed / 0 failed
TypeScript typecheck      PASS
```

The warning was an existing Starlette/AnyIO deprecation warning and did not fail the suite.

## Acceptance decision

The exact historical boundary is independently executable and passes every test and static gate available at that commit.

```text
REL-00                    ACCEPTED
v0.1.0 exact boundary     ACCEPTED
release scope             original WBS / CP baseline
PB scope                  EXCLUDED
runtime mutation          NONE
TAG READINESS             READY
```

No provider mutation, D1 mutation, Worker deployment, tag creation, or history rewrite is authorized by this acceptance record.
