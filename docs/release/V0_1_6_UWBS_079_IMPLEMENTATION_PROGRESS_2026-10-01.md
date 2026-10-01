# v0.1.6 UWBS-079 Implementation Progress — 2026-10-01

## Status

**Implementation complete / local code validation pending / real multi-week evidence pending**

UWBS-079 implements the Pacific weekend handoff / weekday re-risking experimental validator defined by the canonical v0.1.6 crypto-lane audit.

## Canonical boundary

UWBS-079 is explicitly a validation task, not a causal model.

The implementation separates:

1. episode-level observations;
2. recurrence summary across independent weekends;
3. causal interpretation, which remains outside the accepted Fact/Derived Metric layer.

Time-window labels must not be interpreted as participant nationality. Repeated synchronization does not establish systematic, institutional, algorithmic, or AI-agent causality.

## CP-079A — Weekend handoff / re-risking experimental validator

Implemented in:

- `analysis/app/orderscope_local/crypto_canary/weekend_validation.py`

### Episode contract

`WeekendHandoffEpisode` records:

- UWBS-071 weekend time context
- subsequent weekday time context
- BTC return
- altcoin return
- synchronized breadth
- BTC-to-altcoin maximum lag in the research range `[-60, +60]` minutes
- spot-volume change
- derivatives-volume change
- open-interest change
- funding change
- liquidation imbalance
- 1h / 3h / 6h / 24h persistence
- explicit source references

The weekend observation must precede the weekday handoff and remain within a three-day transition window.

### Multi-week recurrence summary

`validate_weekend_rerisking()` produces:

- sample status
- positive / negative / flat BTC weekend counts
- same-direction BTC/altcoin fraction
- median synchronized breadth
- median maximum lag
- median spot / derivatives volume changes
- median OI / funding changes
- median liquidation imbalance
- median 1h / 3h / 6h / 24h persistence
- episode and source lineage
- `method_version="uwbs-079-v1"`

Default minimum independent-weekend sample is four.

Status semantics:

```text
< configured minimum weekends -> INSUFFICIENT_SAMPLE
>= configured minimum weekends -> EXPERIMENTAL
```

`EXPERIMENTAL` means only that the configured sample-size gate has been met. It does not mean statistical recurrence, predictiveness, or causality has been established.

## Test coverage added

`analysis/tests/crypto_canary/test_weekend_validation.py`

Coverage includes:

- single-weekend insufficient-sample behavior
- four independent weekends reaching experimental status
- BTC positive / negative / flat regime counts
- same-direction fraction
- median breadth / lag / volume / OI / funding / liquidation / persistence calculations
- invalid weekday/weekend classification rejection
- breadth range rejection
- lag research-range rejection
- duplicate episode rejection
- duplicate weekend-date rejection
- invalid minimum-sample rejection
- deterministic source-lineage deduplication

## Branch

- `codex/uwbs-079-weekend-rerisk-validation`

Accepted UWBS-078 base:

- `50d3b0697b8c6e07e4bab22c7faec11472154249`

## Acceptance stages

### Stage A — code acceptance

Run locally:

```bash
uv run pytest -q analysis/tests/crypto_canary/test_weekend_validation.py
uv run pytest -q analysis/tests/crypto_canary
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

### Stage B — empirical recurrence evidence

Canonical UWBS-079 requires a multi-week sample. Fixture tests alone cannot establish recurrence.

Before the recurrence claim is closed, populate independent weekend episodes that include at minimum a mix of:

- broad crypto risk-on weekends
- risk-off weekends
- BTC-flat weekends
- target-specific catalyst weekends
- no-material-event control weekends

The v0.1.6 development release may retain UWBS-079 as experimental if this evidence limitation remains explicit.
