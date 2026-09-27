# UWBS-095 — Volatility Futures Term Structure

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**
Date: 2026-09-27

## Purpose

Derive source-lineaged volatility-futures term-structure metrics from UWBS-094 futures observations without converting them into ETP-return or fear-regime conclusions.

## DerivedMetric boundary

The implementation derives:

- front-second spread = second future minus front future;
- front-second ratio = second future / front future when front is non-zero;
- curve shape = `contango`, `backwardation`, or `flat` from the sign of the spread.

Input observations must:

- be explicit volatility futures;
- carry explicit maturity dates;
- have distinct record IDs;
- share the same observation timestamp;
- preserve record lineage.

The front and second contracts are selected by maturity, not caller order.

## Explicit exclusions

UWBS-095 does **not** assert:

- ETP roll yield;
- ETP decay or expected return;
- VIX spot convergence profit/loss;
- fear / risk-off regime;
- cross-asset causality.

Those require later DerivedMetric / Interpretation work with the appropriate product mechanics and evidence.

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this task.
