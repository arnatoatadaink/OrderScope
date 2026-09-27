# A0-001 Implementation Acceptance — 2026-09-14

Status: **Accepted locally**
Scope: FX contradiction conditions for Cross-Market Rotation

## Accepted contract

A0-001 is implemented as a thin Cross-Market hypothesis contract over the accepted I0-005 Fact Store boundary.

Capital movement is represented only as an `Interpretation`; it is not promoted to `Fact`.

Accepted properties:

- source and destination regions remain explicit;
- proposed flow direction is explicit;
- support and contradiction Evidence references remain separate;
- `fx_direction_consistency` is one of `SUPPORT`, `NEUTRAL`, `CONTRADICT`, or `UNKNOWN`;
- confidence is ordinal (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`);
- FX contradiction blocks `HIGH` confidence in v0.1;
- an Evidence reference cannot simultaneously support and contradict the same hypothesis;
- observation windows are explicit non-empty half-open UTC windows;
- generation/acceptance times cannot run backward;
- the contract materializes into the accepted I0-005 `Interpretation` record rather than a new Fact type.

Implementation:

- `analysis/app/orderscope_local/contracts/cross_market.py`
- exports through `analysis/app/orderscope_local/contracts/__init__.py`

Acceptance evidence supplied by the local operator:

```text
focused A0-001 contract tests -> 8 passed in 0.62s
contracts regression suite    -> 88 passed in 1.17s
```

## Disposition

`A0-001`: **Accepted locally**.

This acceptance opens A0-002 validation work. It does not make A0-002 a serial blocker for the Core Corporate Intelligence path and does not authorize any remote mutation or live activation.
