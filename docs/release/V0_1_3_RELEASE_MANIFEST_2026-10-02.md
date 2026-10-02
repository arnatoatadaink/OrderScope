# OrderScope v0.1.3 Release Manifest

Date: 2026-10-02
Status: ACCEPTED / TAG READY

## Exact boundary

- Version: `v0.1.3`
- Commit: `b4df4e911597d9f17bfa0a50b2057c24159dee9f`
- Subject: `Reconstruct v0.1.3 from frozen source manifest`

## Release scope

`v0.1.3` is the cumulative reconstructed boundary for the cross-market / competitor / official macro adapter layer following the accepted `v0.1.2` Macro/Carry boundary.

## Exact-boundary validation

Validated on 2026-10-02 at the exact boundary commit:

- Python analysis tests: `614 passed, 1 warning`
- Worker tests: `178 passed, 0 failed`
- Python compileall: PASS
- `git diff --check`: PASS
- TypeScript typecheck: PASS
- Working tree: clean

The warning is the existing Starlette / AnyIO `BlockingPortal` deprecation warning and is non-blocking.

## Acceptance record

See:

- `docs/release/REL_03_V0_1_3_ACCEPTANCE_2026-10-02.md`
- `docs/release/V0_1_0_TO_V0_1_5_ACCEPTANCE_EVIDENCE_AUDIT_2026-10-02.md`

## Tag posture

`v0.1.3` is TAG READY. No Git tag is created by this manifest itself.
