# UWBS-083 — Oil-down / Inflation-Growth Interpretation Boundary

Status: **WEB IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**

## Purpose

Classify bounded candidate interpretations around crude-price declines without collapsing one observed move into a causal conclusion.

## Interpretation candidates

- `oil_down_supply_relief_candidate`
- `oil_down_demand_weakness_candidate`
- `oil_down_inventory_build_candidate`
- `disinflation_support_candidate`
- `growth_risk_warning_candidate`

## Evidence classes

The assessment keeps independent record classes separate:

- crude price / return metrics;
- commodity fundamental metrics or Facts;
- commodity supply/logistics/geopolitical event Facts;
- macro metrics;
- contradicting evidence.

For `SUPPORT` / `PARTIAL`, a price signal is required and at least one independent non-price class must also be present. A single WTI/Brent move cannot establish a reason.

`CONTRADICT` requires explicit contradicting evidence. `UNKNOWN` carries no directional evidence.

## Candidate-specific guards

- supply-relief requires fundamental and/or event evidence;
- demand-weakness requires fundamental and/or macro evidence;
- inventory-build requires fundamental evidence;
- disinflation support requires macro evidence;
- growth-risk warning requires macro evidence.

## Non-goals

UWBS-083 does not:

- claim deterministic causality;
- infer exact barrels at risk;
- convert an event headline directly into price direction;
- classify portfolio Risk-On / Risk-Off;
- normalize BTC ETF flows;
- activate any live provider.

## Fact Store mapping

Results materialize as `Interpretation`, not `Fact`. Basis lineage preserves all supporting and contradicting record IDs.

Schema: `commodity-interpretation-v0.1`
Method: `commodity_interpretation_rule`

## Acceptance boundary

Run focused contract tests, full Python regression, compileall, and `git diff --check` locally. Public package export may be finalized after focused/full acceptance to avoid expanding the shared contract namespace before the new boundary is proven.
