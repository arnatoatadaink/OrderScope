# OrderScope — Analyst / Cross-Market Post-100 WBS Addendum

Status: **FORMAL WBS ADDENDUM — CURRENT**
Date: 2026-10-03
Release target: `v0.1.12`
Parent WBS: `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Canonical registry: `docs/work-management/local-corporate-intelligence/WBS_PROVISIONAL_ID_REGISTRY.md`
Namespace authority: `docs/work-management/local-corporate-intelligence/UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`
Release plan: `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`

## 1. Purpose

Formally incorporate the post-100 Macro Release Surprise / Yen Carry Flow Observability capability without rewriting the accepted historical A0 task table.

The historical Macro/Carry foundation remains `A0-003..007` from `UWBS-011..015`, with official/fallback source adapters `A0-013..016`. This addendum introduces one additional formal task only for the missing official-release / consensus / revision / event-window transmission layer.

`UWBS-101` is not used here. It is a frozen conflict/legacy-only identifier. The canonical provisional source is `UWBS-105`.

Release allocation is fixed for current planning as:

```text
v0.1.12 -> A0-018 / UWBS-105
```

## 2. Formal incorporation

| Final WBS ID | Canonical source | Release | Task | Completion condition | Upstream dependency | Downstream integration | State |
|---|---|---|---|---|---|---|---|
| A0-018 | UWBS-105 | v0.1.12 | Implement Macro Release Surprise / Yen Carry Flow Observability | Represent PCE and Durable Goods official-release observations with actual/consensus/prior/revision and release/reference timestamps; compute deterministic surprise and bounded no-lookahead event-window rate/FX deltas; expose `CARRY_BUILD`, `CARRY_STABLE`, and `CARRY_COOLING` as Interpretation around the existing carry-unwind path; preserve contradictory/missing evidence and never claim observed capital flow without an eligible direct flow source | A0-003 / A0-004 / A0-007; existing official/fallback macro adapters A0-013..016 | Existing A0-005 carry-unwind / deleveraging interpretation path | Incorporated / v0.1.12 implementation pending |

A0-005 is intentionally **downstream** of A0-018 for this extension. It is not a prerequisite for implementing the release/surprise/event-window layer.

## 3. Release implementation decomposition

`A0-018` remains one formal WBS task. Implementation/acceptance is divided into release CP units rather than creating artificial new WBS IDs.

```text
REL-12A  Macro release Fact / consensus / revision contract
REL-12B  Surprise + event-window rate/FX transmission
REL-12C  Carry BUILD / STABLE / COOLING integration
REL-12D  Historical fixture / false-positive / revision validation
REL-12X  Cumulative v0.1.12 acceptance / TAG READY decision
```

### REL-12A

Initial release families:

- PCE headline/core MoM/YoY and compatible personal-income/consumption fields;
- Durable Goods headline, ex-transportation, core capital-goods orders and shipments where source-grounded.

Required Fact boundary:

- release identity;
- observation/reference period;
- release / available / accepted timestamps;
- actual;
- consensus when sourced;
- prior and revision identity;
- units and provenance.

### REL-12B

Deterministic outputs include:

- `actual - consensus` surprise;
- U.S. 2Y / Japan 2Y / U.S.-Japan 2Y spread changes;
- spread velocity;
- bounded `30m / 2h / 1d` event-window deltas;
- USD/JPY and eligible cross-JPY / risk-asset confirmation context.

No pre-release observation may be used as post-release confirmation. Stale/closed-market values remain UNKNOWN.

### REL-12C

A0-018 may emit:

- `CARRY_BUILD`;
- `CARRY_STABLE`;
- `CARRY_COOLING`.

It reuses the existing `A0-005` `CARRY_UNWIND_CANDIDATE` and `DELEVERAGING_REGIME` semantics rather than duplicating them.

A softer macro release + lower U.S. 2Y + narrower U.S.-Japan 2Y spread + lower USD/JPY is not sufficient by itself to establish a carry unwind.

### REL-12D

Historical validation must cover:

- revisions;
- missing consensus;
- stale/closed-market observations;
- contradictory FX/rate signals;
- false-positive carry-cooling cases;
- no-lookahead event-window reconstruction.

## 4. Acceptance conditions

A0-018 / v0.1.12 is Accepted only when:

1. official-release records preserve actual, consensus, prior/revision, time and source provenance;
2. surprise values are deterministic and unit-safe;
3. event-window deltas are reproducible and free of lookahead contamination;
4. missing consensus or incompatible market timing becomes UNKNOWN/lower confidence rather than guessed data;
5. contradictory evidence is retained;
6. `CARRY_UNWIND_CANDIDATE` still requires independent confirmation under A0-005 rules;
7. focused and historical-validation tests cover false positives, stale/closed-market observations, revisions, missing consensus and contradictory evidence;
8. affected Macro/Cross-Market regression passes;
9. full Python regression, compileall and `git diff --check` pass;
10. no live provider, Worker/Cron, remote D1, trading or paid procurement action is implicitly authorized.

## 5. Critical-path relation

```text
A0-003 Macro-Market Fact
   +
A0-004 rate/cross-country Derived Metrics
   +
A0-007 source-selection contract
   +
A0-013..016 official/fallback source adapters
   |
   v
REL-12A -> REL-12B -> REL-12C
                         |
                         v
A0-005 existing CARRY_UNWIND_CANDIDATE / DELEVERAGING path
                         |
                         v
REL-12D -> REL-12X
```

The historical provisional relation is canonicalized as:

```text
UWBS-011 + UWBS-012 -> UWBS-105 -> UWBS-013
                         |
                         v
                      A0-018
```

## 6. Namespace rule

- `UWBS-105` is the only canonical provisional source ID for this task.
- Historical Macro-context references to colliding `UWBS-101` map to `UWBS-105` when context is sufficient.
- `UWBS-101A/B/C` from historical planning are decomposition labels only and are not WBS IDs.
- Context-insufficient old references remain `AMBIGUOUS`.
