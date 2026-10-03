# OrderScope — Analyst / Cross-Market Post-100 WBS Addendum

Status: **FORMAL WBS ADDENDUM — CURRENT**
Date: 2026-10-03
Parent WBS: `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Canonical registry: `docs/work-management/local-corporate-intelligence/WBS_PROVISIONAL_ID_REGISTRY.md`
Namespace authority: `docs/work-management/local-corporate-intelligence/UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`

## 1. Purpose

Formally incorporate the post-100 Macro Release Surprise / Yen Carry Flow Observability capability without rewriting the accepted historical A0 task table.

The historical Macro/Carry foundation remains `A0-003..007` from `UWBS-011..015`. This addendum introduces one additional formal task only for the missing official-release / consensus / revision / event-window transmission layer.

`UWBS-101` is not used here. It is a frozen conflict/legacy-only identifier. The canonical provisional source is `UWBS-105`.

## 2. Formal incorporation

| Final WBS ID | Canonical source | Task | Completion condition | Dependency | State |
|---|---|---|---|---|---|
| A0-018 | UWBS-105 | Implement Macro Release Surprise / Yen Carry Flow Observability | Represent PCE and Durable Goods official-release observations with actual/consensus/prior/revision and release/reference timestamps; compute deterministic surprise and bounded no-lookahead event-window rate/FX deltas; expose `CARRY_BUILD`, `CARRY_STABLE`, and `CARRY_COOLING` as Interpretation around the existing carry-unwind path; preserve contradictory/missing evidence and never claim observed capital flow without an eligible direct flow source | A0-003 / A0-004 / A0-005 / A0-007; existing official/fallback macro adapters A0-013..016 | Incorporated / implementation pending |

## 3. Contract boundary

### Fact

Minimum official-release Fact fields include:

- release identity and observation/reference period;
- release timestamp / available timestamp / accepted timestamp;
- actual value;
- market consensus value when sourced;
- prior value and revision identity;
- unit and source provenance.

Initial release families:

- PCE headline/core MoM/YoY and compatible personal-income/consumption fields;
- Durable Goods headline, ex-transportation, core capital goods orders, and shipments when available.

### Derived Metric

Deterministic outputs may include:

- `actual - consensus` release surprise;
- U.S. 2Y / Japan 2Y / U.S.-Japan 2Y spread changes;
- spread velocity;
- bounded `30m / 2h / 1d` event-window deltas;
- USD/JPY and supported cross-JPY/risk-asset deltas.

No pre-release observation may be used as post-release confirmation, and stale/closed-market values remain missing/unknown.

### Interpretation

A0-018 may emit:

- `CARRY_BUILD`;
- `CARRY_STABLE`;
- `CARRY_COOLING`.

It reuses the existing `A0-005` / historical `UWBS-013` `CARRY_UNWIND_CANDIDATE` and `DELEVERAGING_REGIME` semantics rather than duplicating them.

A softer macro release plus lower U.S. 2Y plus narrower U.S.-Japan 2Y spread plus lower USD/JPY is not sufficient by itself to establish a carry unwind.

## 4. Acceptance conditions

A0-018 is Accepted only when:

1. official-release records preserve actual, consensus, prior/revision, time and source provenance;
2. surprise values are deterministic and unit-safe;
3. event-window deltas are reproducible and free of lookahead contamination;
4. missing consensus or incompatible market timing becomes UNKNOWN/lower confidence rather than guessed data;
5. contradictory evidence is retained;
6. `CARRY_UNWIND_CANDIDATE` still requires independent confirmation under A0-005 rules;
7. implementation tests cover false positives, stale/closed-market observations, revisions, missing consensus and contradictory evidence;
8. no live provider, Worker/Cron, remote D1, trading or paid procurement action is implicitly authorized.

## 5. Critical-path relation

```text
A0-003 Macro-Market Fact
   +
A0-004 rate/cross-country Derived Metrics
   +
A0-013..016 official/fallback source adapters
   |
   v
A0-018 Macro Release Surprise / Yen Carry Flow Observability
   |
   v
A0-005 existing CARRY_UNWIND_CANDIDATE / DELEVERAGING path
```

The historical provisional relation is therefore canonicalized as:

```text
UWBS-011 + UWBS-012 -> UWBS-105 -> UWBS-013
                         |
                         v
                      A0-018
```

## 6. Namespace rule

- `UWBS-105` is the only canonical provisional source ID for this task.
- Historical Macro-context references to the colliding `UWBS-101` map to `UWBS-105` when context is sufficient.
- `UWBS-101A/B/C` from historical planning are decomposition labels only and are not WBS IDs.
- Context-insufficient old references remain `AMBIGUOUS`.
