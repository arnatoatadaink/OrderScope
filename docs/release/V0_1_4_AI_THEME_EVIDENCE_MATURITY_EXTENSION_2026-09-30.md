# v0.1.4 AI Theme Evidence Maturity Extension — 2026-09-30

Status: **DESIGN ACCEPTED FOR POST-v0.1.4 ITERATION; NOT REQUIRED FOR EXPERIMENTAL v0.1.4 RELEASE**

## 1. Purpose

AI Theme relevance must not be interpreted as proof of realized economic value.
This extension separates thematic association from the maturity and materiality of the supporting business evidence.

The core model is:

```text
Theme Exposure
× Evidence Maturity
× Economic Materiality
× Persistence
```

These axes are intentionally independent.

## 2. Evidence maturity ladder

```text
NEWS
  -> NARRATIVE
  -> COMMERCIAL_EVIDENCE
  -> RECURRING_EVIDENCE
  -> PROFIT_ATTRIBUTED
```

### NEWS

First-party or accepted-source announcement that establishes a possible AI relationship.
Examples include:

- partnership announcement;
- startup support program;
- memorandum of understanding;
- proof of concept;
- planned deployment;
- product launch;
- announced customer relationship without disclosed economics.

This level establishes thematic relevance only. It must not imply revenue, recurring value, or profitability.

### NARRATIVE

Theme relevance inferred from surrounding market structure or business context rather than realized company-specific economics.
Examples include:

- sector-wide AI capex expectations;
- regulatory or policy changes;
- peer adoption;
- supply-chain positioning;
- market narrative that could benefit or harm the company.

Narrative evidence belongs to Interpretation and must not be stored as realized commercial Fact.

### COMMERCIAL_EVIDENCE

Explicit source-grounded evidence of realized commercial activity.
Examples include:

- signed contract with explicit scope;
- purchase order;
- disclosed recognized revenue;
- explicit paying-customer deployment;
- backlog or booking attributable to the AI-related product/service.

Where value is not disclosed, materiality remains UNKNOWN.

### RECURRING_EVIDENCE

Commercial evidence repeats across a later reporting or contract cycle.
Examples include:

- contribution confirmed in a second earnings report;
- renewal;
- expanded order;
- recurring subscription contribution;
- repeated segment growth attributable to the theme.

One-off commercial evidence must not automatically advance to this level.

### PROFIT_ATTRIBUTED

Theme-linked economics can be connected to profitability or cash generation with explicit evidence.
Preferred measures include:

- gross profit contribution;
- operating profit contribution;
- contribution margin;
- free-cash-flow contribution.

Revenue share alone is insufficient to claim profit attribution.

## 3. Economic materiality

Maintain a separate materiality dimension, for example:

```text
UNKNOWN
IMMATERIAL
EMERGING
MATERIAL
CORE
```

The exact quantitative thresholds must be calibrated by sector and accounting availability rather than hard-coded globally.

Possible later metrics include:

```text
AI revenue / total revenue
AI gross profit / total gross profit
AI operating profit / total operating profit
AI FCF / total FCF
AI bookings / total bookings
AI backlog / total backlog
```

Do not infer gross-profit attribution from revenue share when margins differ materially across segments.

## 4. Persistence

Persistence should remain separate from evidence maturity.
Suggested states:

```text
UNCONFIRMED
ONE_PERIOD
REPEATED
MULTI_PERIOD
STRUCTURAL
```

A repeated news cycle without repeated economics must not count as recurring commercial evidence.

## 5. Promotional / weakly supported AI claims

Do not infer fraud, manipulation or deceptive intent without evidence.
Represent observable uncertainty instead.

Suggested classifications:

```text
PROMOTIONAL_ONLY
UNVERIFIED_COMMERCIAL_CLAIM
NO_REVENUE_EVIDENCE
NO_REPEAT_EVIDENCE
ECONOMIC_MATERIALITY_UNKNOWN
CUSTOMER_IDENTITY_UNVERIFIED
CONTRACT_VALUE_UNDISCLOSED
```

These labels describe the evidence state, not intent.

## 6. Upgrade and downgrade rules

Evidence maturity must be monotonic only when supported by new evidence. A company may be downgraded if previously accepted evidence is corrected, terminated or shown to have been misunderstood.

Examples:

```text
NEWS -> COMMERCIAL_EVIDENCE
```

requires a later explicit contract/order/revenue Fact.

```text
COMMERCIAL_EVIDENCE -> RECURRING_EVIDENCE
```

requires a second independent period or renewal/expansion event.

```text
RECURRING_EVIDENCE -> PROFIT_ATTRIBUTED
```

requires explicit profit/cash-flow attribution, not merely continued revenue.

## 7. Theme interaction

The same company can hold several AI themes with different evidence maturity.

Example:

```text
AI_FOUNDATION:
  maturity = RECURRING_EVIDENCE
  materiality = MATERIAL

AI_APPLICATION:
  maturity = NEWS
  materiality = UNKNOWN
```

Theme-level scores must therefore be keyed by both company and theme identity.

## 8. Historical calibration interaction

Historical market calibration remains useful but is orthogonal to evidence maturity.

A first-day NEWS event may create a large market reaction even though economic materiality is unknown.
Conversely, a company may reach PROFIT_ATTRIBUTED with little short-term price reaction because the market already priced the economics earlier.

Therefore do not use price reaction alone to promote evidence maturity.

## 9. Proposed implementation sequence

Recommended future tasks:

1. define EvidenceMaturity and EconomicMateriality contracts;
2. add company-theme evidence records with provenance;
3. support explicit upgrade/downgrade transitions;
4. add recurring-evidence detection across reporting periods;
5. add profit-attribution records using segment / management disclosure evidence;
6. connect but do not collapse these states into AI Theme market-reaction Interpretation;
7. build Canary cases for promotional-only, one-off commercial, recurring commercial and profit-attributed companies.

## 10. Release relationship

This extension is **not a blocker** for the experimental v0.1.4 release.

v0.1.4 may ship with:

```text
AI Theme — Experimental / Uncalibrated
```

while this maturity layer is implemented and refined in a subsequent v0.1.x iteration.

All downstream reports using v0.1.4 should continue to distinguish thematic relevance from proven commercial and profit contribution.
