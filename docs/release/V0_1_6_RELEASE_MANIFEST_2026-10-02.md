# OrderScope v0.1.6 Release Manifest — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Release boundary

```text
Version: v0.1.6
SHA:     bfaf89c68daa656b7d75317f086458257cc94da9
Title:   Reflect accepted v0.1.6 WBS and CP progress
```

Parent release boundary:

```text
v0.1.5 = 415de1f1dd42f70bd66992961cb43be7edba6ade
```

The v0.1.6 boundary is a direct cumulative successor of v0.1.5: 56 commits ahead, 0 behind, with v0.1.5 as the merge base.

## Functional scope

Crypto Market Structure / derivatives analysis lane:

- UWBS-068 through UWBS-079 Stage A
- crypto derivatives normalization and metrics
- multi-venue futures/perpetual adapters
- liquidation and cascade metrics
- OI / Position Map analysis
- cross-venue QA and divergence guards
- BTC-relative context and 24/7 time semantics
- NEAR/BTC and futures-position canaries
- durable crypto snapshot archive and catch-up lifecycle
- weekend handoff / weekday re-risking experimental validator code

## Explicit non-claim

UWBS-079 Stage B remains a research-validation track. This release does **not** claim that weekend-to-weekday recurrence, BTC-to-altcoin lead/lag, synchronized breadth, causal BTC leadership, participant geography, or universal weekend thresholds have been empirically validated.

## Exact-boundary validation

Validated on detached HEAD at `bfaf89c68daa656b7d75317f086458257cc94da9`:

```text
Python analysis tests   746 passed, 1 warning
Worker tests            178 passed / 0 failed
compileall              PASS
git diff --check        PASS
TypeScript typecheck    PASS
working tree            clean
```

The single Python warning is the known Starlette TestClient / AnyIO deprecation warning.

## Release decision

```text
implementation boundary   ACCEPTED
exact-boundary validation PASS
release manifest          COMPLETE
classification            TAG READY
```

Tag creation remains a separate explicit action and is not performed by this manifest.

Related records:

- `docs/release/V0_1_6_CP16X_ACCEPTANCE_2026-10-01.md`
- `docs/release/V0_1_6_PROGRESS_REFLECTION_2026-10-01.md`
- `docs/release/REL_06_V0_1_6_BOUNDARY_DECISION_2026-10-02.md`
- `docs/release/REL_06_V0_1_6_ACCEPTANCE_2026-10-02.md`
