# OrderScope v0.1.4 Release Manifest

Date: 2026-10-02
Status: ACCEPTED / TAG READY

## Release boundary

- Version: `v0.1.4`
- Exact commit: `a798622f839b836f8b60f52dd700b8fd87147991`
- Boundary description: reconstructed cumulative AI Theme release boundary (`UWBS-062..066`)

## Acceptance evidence

Exact-boundary validation executed on 2026-10-02:

- Python analysis suite: 626 passed, 1 non-blocking deprecation warning
- Python compileall: PASS
- `git diff --check`: PASS
- Worker test suite: 178 passed, 0 failed
- TypeScript typecheck: PASS
- Working tree: clean

## Release semantics

This release accepts the presence and structural correctness of the AI Theme capability at the reconstructed semantic-version boundary. It does not upgrade experimental analytical claims into calibrated or economically validated production claims.

Explicitly still experimental/unvalidated where previously documented:

- calibration quality
- false-positive rates
- persistence thresholds
- economic materiality
- profit attribution

## Release decision

`v0.1.4` is ACCEPTED and TAG READY at commit `a798622f839b836f8b60f52dd700b8fd87147991`.

Tag creation itself is a separate repository action and is not performed by this manifest.
