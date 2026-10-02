# REL-04 — v0.1.4 Exact Boundary Acceptance

Date: 2026-10-02
Status: ACCEPTED / TAG READY

## Exact boundary

- Version: `v0.1.4`
- Commit: `a798622f839b836f8b60f52dd700b8fd87147991`
- Commit subject: `Reconstruct v0.1.4 experimental AI Theme boundary`

## Validation results

Executed against the exact detached boundary commit with a clean working tree.

- `uv run pytest -q analysis/tests` → 626 passed, 1 warning
- `uv run python -m compileall -q analysis/app` → PASS
- `git diff --check` → PASS
- `npm test` → 178 passed, 0 failed
- `npm run typecheck` → PASS (`tsc --noEmit`)

The Python warning is the existing Starlette/AnyIO deprecation warning and is non-blocking for this release boundary.

## Scope note

This boundary is the reconstructed cumulative `v0.1.4` AI Theme release boundary. The AI Theme capability remains explicitly experimental and uncalibrated where documented: calibration, false-positive rates, persistence thresholds, economic materiality, and profit attribution are not claimed as empirically validated by this acceptance.

## Decision

REL-04 is accepted. The exact reconstructed `v0.1.4` boundary is release-valid and may be treated as TAG READY.
