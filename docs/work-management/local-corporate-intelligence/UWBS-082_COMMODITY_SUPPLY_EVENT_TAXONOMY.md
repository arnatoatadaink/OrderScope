# UWBS-082 — Commodity Supply / Shipping / Geopolitical Event Taxonomy

Status: **WEB IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**
Scope: source-observed commodity supply/logistics/geopolitical event Facts
Branch: `l1-003-local-market-recovery`

## Purpose

Freeze a provider-neutral taxonomy for source-observed commodity events before adding causal interpretation.

This boundary records **what a source says happened or was announced**. It must not infer:

- barrels at risk;
- severity score;
- bullish/bearish oil direction;
- inflation/growth impact;
- risk-on/risk-off regime;
- probability that the event causes a future price move.

Those belong to UWBS-083 and later interpretation layers.

## Event kinds

Physical supply / processing:

- `upstream_outage`
- `refinery_outage`
- `pipeline_disruption`

Logistics / maritime:

- `port_disruption`
- `shipping_route_disruption`
- `maritime_security_incident`
- `blockade_or_closure`

Policy / geopolitical:

- `sanctions_action`
- `export_restriction`
- `import_restriction`
- `strategic_release`
- `production_policy_action`
- `armed_conflict`

## Lifecycle state

Lifecycle is source state, not severity:

- `reported`
- `announced`
- `active`
- `resolved`
- `cancelled`

## Identity rules

- every event has `subject_ref` and `geography_ref`;
- pipeline/refinery disruption requires `asset_ref`;
- shipping-route disruption and blockade/closure require `route_ref`;
- sanctions/import/export/production-policy action requires `actor_ref`;
- `effective_start` / `effective_end` preserve source precision and may be absent;
- source-grounded Facts require Evidence references under the existing Fact Store invariant.

## Materialization

`CommoditySupplyEventObservation.to_fact()` emits:

```text
schema_version = commodity-supply-event-observation-v0.1
fact_type      = commodity_event.<event_kind>
assertion_kind = observation
```

The Fact value preserves only source-observed taxonomy/lifecycle/identity references. It contains no directional market interpretation.

## Acceptance boundary

Focused acceptance should cover:

1. basic Fact materialization;
2. pipeline asset identity guard;
3. shipping route identity guard;
4. policy actor identity guard;
5. effective interval ordering;
6. lifecycle vocabulary excludes severity/direction;
7. taxonomy excludes price-direction, barrels-at-risk and risk-regime labels;
8. full Python regression;
9. compileall;
10. `git diff --check`.

No live provider activation or runtime mutation is part of UWBS-082.
