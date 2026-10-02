# OrderScope — v0.1.2 Release Manifest — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Version boundary

```text
version: v0.1.2
boundary commit: f69c52bf574212d1506df81abc7b15694abb7922
release gate: REL-02
```

## Scope

`v0.1.2` is the cumulative Macro/Carry release boundary reconstructed from the frozen source manifest on top of the previously reconstructed runtime/operational boundary.

## Acceptance evidence

Exact-boundary validation on 2026-10-02:

```text
Python analysis tests   563 passed, 1 warning
Worker tests            178 passed / 0 failed
compileall              PASS
git diff --check        PASS
npm run typecheck       PASS
working tree            clean
```

The only warning is the pre-existing Starlette/AnyIO deprecation warning.

## Release classification

```text
FUNCTIONAL SOURCE ACCEPTANCE   PRESENT
RECONSTRUCTED BOUNDARY         PRESENT
EXACT-BOUNDARY VALIDATION      PASSED
RELEASE STATUS                 ACCEPTED
TAG STATUS                     TAG READY
```

Actual Git tag creation remains a separate action.
