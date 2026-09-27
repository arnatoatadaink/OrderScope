# UWBS-096 — VIX-linked ETP Roll / Decay Boundary

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**
Date: 2026-09-27

## Purpose

Separate three concepts that must not be conflated:

1. observed VIX-linked ETP price/NAV return;
2. VIX futures term-structure measurements;
3. an Interpretation that roll pressure may be a headwind/tailwind candidate.

## Accepted design boundary

Deterministic measurements are DerivedMetric values. A contango or backwardation observation alone is not a causal explanation for an ETP move.

The current implementation measures:

- ETP return;
- front/second futures spread;
- front/second futures ratio;
- directional roll pressure implied by the curve.

The assessment layer requires both ETP-return evidence and term-structure evidence. Contradicting evidence prevents a simple roll explanation.

## Explicit exclusions

UWBS-096 does not claim:

- that contango mechanically equals realized ETP decay over a chosen period;
- that every ETP decline in contango is caused by roll;
- that leverage, daily reset, fees, tracking error, spot-volatility shocks, or path dependency are negligible;
- a trading signal or expected return.

Those effects remain separate evidence or downstream interpretation work.

## Runtime boundary

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this task.
