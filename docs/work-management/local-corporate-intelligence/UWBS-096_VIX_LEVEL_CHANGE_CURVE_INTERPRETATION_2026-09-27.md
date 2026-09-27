# UWBS-096 — VIX level / change / curve interpretation contract

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**

## Canonical task identity

The canonical UWBS registry defines UWBS-096 as the VIX level/change/curve interpretation contract.  This document is the controlling implementation note for that task.

The VIX-linked ETP roll/decay module on the same branch is related supporting analysis only.  It is not the canonical task identity of UWBS-096.

## Canonical implementation

```text
analysis/app/orderscope_local/cross_market/vix_interpretation.py
analysis/tests/cross_market/test_vix_interpretation.py
```

The contract consumes already-grounded VIX level, point-change, percent-change, curve, and curve-transition evidence and materializes an Interpretation.  It does not create source Facts and it does not invent numerical fear thresholds.

Supported interpretation states:

```text
pressure_building_candidate
pressure_easing_candidate
curve_stress_persisting_candidate
mixed_volatility_candidate
unknown
```

Ratings:

```text
SUPPORT
PARTIAL
CONTRADICT
UNKNOWN
```

## Evidence guard

A SUPPORT result requires at least two independent VIX evidence classes.  PARTIAL requires at least one.  CONTRADICT requires explicit contradicting evidence.  UNKNOWN cannot carry directional evidence.

Curve-stress persistence specifically requires both a curve-level metric and a curve transition/persistence metric.  Record identifiers cannot be reused across evidence classes.

## Explicit exclusions

This task does not:

- calibrate a fixed VIX level threshold for fear or panic;
- substitute a VIX-linked ETF/ETN price for VIX;
- treat futures contango/backwardation as a spot VIX Fact;
- infer stock-market direction from volatility evidence;
- assert causal attribution from VIX alone.

Materialized output explicitly records `fixed_threshold_calibrated=false`.

## Auxiliary ETP roll analysis

The following files are supporting analysis on the same branch:

```text
analysis/app/orderscope_local/cross_market/volatility_etp_roll.py
analysis/tests/cross_market/test_volatility_etp_roll.py
```

They separate deterministic ETP return and futures-curve measurements from roll interpretation.  Negative roll pressure maps to a headwind candidate; positive roll pressure maps to a tailwind candidate; contradictory evidence blocks a simple roll explanation.

The earlier local result of `10 passed / 934 passed full regression` covered this auxiliary ETP-roll boundary before the canonical UWBS-096 interpretation contract was added.  It therefore does **not** constitute canonical UWBS-096 acceptance.

## Acceptance gate

Canonical UWBS-096 can be accepted only after all of the following pass on this branch:

```text
canonical VIX interpretation focused tests
auxiliary ETP roll focused tests
full Python regression
compileall
git diff --check
```

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this task.
