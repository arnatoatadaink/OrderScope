# AI Theme Decomposition / Event-Reaction Coefficient Design Report

Status: **Research / design input — not normative specification**  
Date: 2026-09-15  
Project: OrderScope / Stock Monitoring  
Related backlog: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`  
Related market-reaction report: `docs/work-management/local-corporate-intelligence/REPORT_TNON_CHPT_PRICE_REDISCOVERY_2026-09-11.md`

## 1. Purpose

This report decomposes the broad `AI` market theme into reusable subthemes and defines a candidate model for **event-dependent reaction coefficients**.

The key design decision is that a company should not be assigned only a static theme label such as `AI`. Instead, OrderScope should preserve:

1. the company's relatively stable **structural theme exposure**;
2. the current **news / event catalyst**;
3. an event-to-theme **reaction coefficient / sensitivity state**;
4. observed price / volume reaction;
5. a later interpretation of whether the market is actively repricing the theme.

This separation is required so that a theme can become temporarily dominant after a catalyst without rewriting the company's underlying business classification.

## 2. Executive summary

The broad AI theme should be decomposed into at least four sibling subthemes:

```text
AI
├─ AI_FOUNDATION      # compute / model / infrastructure
├─ AI_APPLICATION     # software / physical AI / domain deployment
├─ AI_SECURITY        # protection against AI-amplified attack / misuse
└─ AI_GOVERNANCE      # control / audit / policy / identity / compliance
```

`AI_SECURITY` and `AI_GOVERNANCE` should not be treated as anti-AI themes. Structurally they depend on AI adoption and complexity increasing. However, **market flows can temporarily make them behave as a counter-theme to AI growth / compute** when the catalyst is fear, safety concern, regulation, cyberattack, or doubts about unconstrained AI growth.

Therefore the correct model is:

```text
STRUCTURAL THEME EXPOSURE
        +
EVENT / NEWS CATALYST
        ↓
EVENT-THEME REACTION COEFFICIENT
        ↓
EXPECTED RELATIVE FLOW PRESSURE
        ↓
OBSERVED PRICE / VOLUME REACTION
        ↓
THEME REPRICING INTERPRETATION
```

The reaction coefficient is **not a raw Fact** and must not initially be a hard-coded numeric trading weight. It is a Derived Metric / Interpretation object whose magnitude must be calibrated from historical cases.

## 3. Why one `AI` bucket is no longer sufficient

A single AI category hides materially different economic drivers.

### 3.1 AI Foundation

Examples of exposure:

- accelerators / GPU / alternative compute;
- HBM / memory;
- datacenter power and cooling;
- high-speed networking / optical interconnect;
- model training / inference infrastructure.

Primary driver:

```text
more AI capability / more inference / more compute demand
    → more infrastructure demand
```

This is the closest category to the conventional `AI growth` trade.

### 3.2 AI Application

Examples:

- physical AI;
- robotics;
- autonomous systems;
- enterprise AI applications;
- vertical AI software;
- edge AI.

Primary driver:

```text
AI capability becomes usable
    → deployment into real workflows / physical systems
```

Physical AI belongs here. It is downstream of AI Foundation rather than a competing theme.

### 3.3 AI Security

Examples:

- endpoint / workload / cloud security;
- AI-agent security;
- model / prompt / inference protection;
- identity / access protection where AI increases attack surface;
- detection / response against AI-amplified attacks.

Primary driver:

```text
AI adoption / agent autonomy / attacker capability rises
    → attack surface and defensive complexity rise
    → security demand rises
```

This creates an important asymmetric behavior: AI Security can benefit from both **AI acceleration** and **fear of AI acceleration**.

### 3.4 AI Governance

Examples:

- AI policy / compliance;
- auditability;
- model risk management;
- identity / authorization / provenance;
- safety controls;
- enterprise governance layers.

Primary driver:

```text
AI becomes economically important or risky
    → organizations / regulators require stronger control
```

AI Governance is expected to react especially strongly to regulation, safety incidents, model misuse, legal exposure, and management concern about uncontrolled deployment.

## 4. Structural relationship: sibling themes, not simple opposites

The four categories should be modeled as sibling branches of an AI super-theme.

```text
AI_SUPER_THEME
   |
   +-- Foundation  : build capability
   +-- Application : deploy capability
   +-- Security    : protect capability and environment
   +-- Governance  : constrain / authorize / audit capability
```

The important distinction is:

- **structurally**: Security / Governance complement AI growth;
- **in market flow**: Security / Governance may temporarily oppose Foundation when investors rotate from `growth` to `risk control`.

Therefore OrderScope should not encode a permanent negative correlation between Foundation and Security / Governance.

Instead it should detect a **catalyst-dependent relative-flow regime**.

## 5. Reaction coefficient concept

### 5.1 Definition

For each event `E` and theme `T`, define a candidate object:

```text
EVENT_THEME_REACTION
  event_id
  theme_id
  direction
  strength_bucket
  evidence_count
  source_quality
  novelty
  breadth
  persistence_state
  observed_market_confirmation
```

`direction` should initially be categorical:

```text
STRONG_NEGATIVE
NEGATIVE
NEUTRAL_OR_UNKNOWN
POSITIVE
STRONG_POSITIVE
```

These labels are **provisional interpretation buckets**, not empirically calibrated numeric coefficients.

### 5.2 Why categorical first

A fixed numeric table such as `cyberattack = +0.8 security` would create false precision before historical calibration.

Initial implementation should therefore store:

```text
coefficient_state = POSITIVE / STRONG_POSITIVE / ...
confidence_state  = LOW / MEDIUM / HIGH
```

Only after historical validation should the project consider a normalized numeric coefficient.

## 6. Candidate event-to-theme reaction matrix

The following matrix is a **design hypothesis**, not measured historical output.

| Event / news class | AI Foundation | AI Application | AI Security | AI Governance |
|---|---|---|---|---|
| AI capability breakthrough | Strong positive | Positive | Positive | Positive |
| AI demand / capex acceleration | Strong positive | Positive | Positive | Neutral / positive |
| AI growth slowdown concern | Negative | Negative / mixed | Positive / mixed | Positive / mixed |
| Major cyberattack | Neutral / mixed | Neutral / mixed | Strong positive | Positive |
| AI-enabled cyberattack | Mixed | Mixed | Strong positive | Strong positive |
| AI safety incident / misuse | Negative / mixed | Negative / mixed | Positive | Strong positive |
| New AI regulation | Negative / mixed | Negative / mixed | Positive / mixed | Strong positive |
| Enterprise AI adoption acceleration | Positive | Strong positive | Positive | Positive |
| Autonomous-agent proliferation | Positive | Strong positive | Strong positive | Strong positive |
| Model commoditization / falling inference cost | Mixed | Positive | Positive | Positive / mixed |
| Compute supply constraint eases | Positive | Positive | Positive | Neutral |
| Severe AI capex contraction | Strong negative | Negative | Mixed | Mixed |

The matrix should be treated as a starting ontology for later validation, not as an executable trading table.

## 7. Additional reaction coefficients outside AI

The same mechanism should be generalized beyond AI.

A useful analogy is the defense / weapons theme.

```text
STRUCTURAL_THEME = DEFENSE_INDUSTRIAL
EVENT = WAR_ESCALATION / DEFENSE_BUDGET / PROCUREMENT / GEOPOLITICAL_RISK
    ↓
reaction coefficient becomes strongly positive
```

Likewise:

```text
STRUCTURAL_THEME = CYBERSECURITY
EVENT = MAJOR_CYBERATTACK / AI_ATTACK_CAPABILITY / SAFETY_CONCERN
    ↓
reaction coefficient becomes positive / strongly positive
```

and:

```text
STRUCTURAL_THEME = AI_GOVERNANCE
EVENT = AI_SAFETY_CONCERN / REGULATION / LIABILITY / CONTROL_FAILURE
    ↓
reaction coefficient becomes positive / strongly positive
```

This means the generic OrderScope abstraction should not be named specifically for AI. A reusable model is:

```text
THEME_EXPOSURE
  + EVENT_CLASS
  + EVENT_MAGNITUDE
  + COMPANY_RELEVANCE
  + CROSS_SECTIONAL_CONFIRMATION
  + MARKET_REACTION
  → THEME_REACTION_STATE
```

## 8. Important ambiguity: `Defense` must be split semantically

The word `defense` is overloaded and should not be used as one technical category.

Recommended identifiers:

```text
DEFENSE_INDUSTRIAL     # military / weapons / aerospace / procurement
CYBERSECURITY          # digital defense
AI_SECURITY            # AI-linked cybersecurity / model / agent protection
AI_GOVERNANCE          # control / audit / compliance / authorization
```

A military-defense company can also have `AI_APPLICATION` exposure if autonomous systems, targeting, sensing, or battlefield AI are economically meaningful.

Therefore theme membership should be many-to-many rather than exclusive.

Example:

```text
Company X
  DEFENSE_INDUSTRIAL = HIGH
  AI_APPLICATION     = MEDIUM
  AI_FOUNDATION      = LOW
```

A war catalyst may activate the first exposure strongly even when no new AI catalyst exists.

## 9. Proposed data model

### 9.1 Structural company-theme exposure

Candidate record:

```text
COMPANY_THEME_EXPOSURE
  company_id
  theme_id
  exposure_state
  evidence_refs[]
  effective_from
  effective_to
  accepted_at
```

`exposure_state` should initially use ordinal buckets such as:

```text
CORE
MATERIAL
SECONDARY
INCIDENTAL
UNKNOWN
```

These are classification states, not investment ratings.

### 9.2 Event-theme mapping

```text
EVENT_THEME_LINK
  event_id
  theme_id
  relation_type
  expected_direction
  expected_strength_bucket
  evidence_refs[]
  interpretation_version
```

Possible `relation_type` values:

```text
DEMAND_ACCELERATOR
RISK_ACCELERATOR
REGULATORY_ACCELERATOR
SUPPLY_RELIEF
SUPPLY_CONSTRAINT
ADOPTION_ACCELERATOR
ADOPTION_DECELERATOR
THREAT_ACCELERATOR
CONTROL_REQUIREMENT
```

### 9.3 Market confirmation

The expected reaction must remain separate from observed market behavior.

```text
THEME_MARKET_REACTION
  event_id
  theme_id
  benchmark_universe
  reaction_5m
  reaction_30m
  reaction_session
  reaction_after_hours
  reaction_next_premarket
  reaction_1d
  reaction_3d
  breadth_ratio
  abnormal_volume_state
  relative_return_state
  persistence_state
```

This reuses the same separation principle already proposed for catalyst-to-price rediscovery analysis.

## 10. Theme activation vs theme repricing

Two distinct states are required.

### 10.1 Theme activation

A news event makes an already-existing structural theme economically salient.

Example:

```text
major cyberattack
  → cybersecurity exposure becomes salient
  → multiple cybersecurity names receive abnormal buying
```

Candidate state:

```text
THEME_ACTIVATION_CANDIDATE
```

### 10.2 Theme repricing

The market begins assigning a persistently different valuation to the theme.

Requirements should eventually include:

- multi-name participation;
- abnormal volume;
- relative outperformance versus market / sector benchmark;
- persistence beyond the initial event window;
- survival of pullbacks / retests;
- repeated activation by subsequent related news.

Candidate state:

```text
THEME_REPRICING_ACTIVE
THEME_REPRICING_CONFIRMED_CANDIDATE
THEME_REPRICING_FAILED
```

No normative thresholds are defined in this report.

## 11. Cross-sectional confirmation is essential

A single company's price move should not be sufficient to infer a theme-level event.

For example, an AI-security theme activation should look for a basket response such as:

```text
AI_SECURITY event candidate
    ↓
multiple relevant companies move in the same direction
    + relative volume expansion
    + sector / peer outperformance
    + persistence into after-hours / next session
```

If only one name moves, OrderScope should first consider company-specific news, short positioning, low float, earnings, financing, or other idiosyncratic causes.

This is important for the SentinelOne-type case: the system should test whether the repricing is company-specific or part of a wider AI Security / Cybersecurity flow regime.

## 12. Counter-theme / rotation state

To represent the user's observed pattern without incorrectly declaring permanent opposition, add a temporary relationship state:

```text
THEME_ROTATION_RELATION
  source_theme
  destination_theme
  catalyst_event_id
  direction_state
  relative_flow_evidence
  start_time
  persistence_state
```

Example hypothesis:

```text
source_theme      = AI_FOUNDATION
 destination_theme = AI_SECURITY / AI_GOVERNANCE
 catalyst          = AI safety concern / growth concern
 relation          = RELATIVE_ROTATION
```

This does **not** mean AI Security is structurally negatively correlated with AI Foundation. It means the current catalyst caused relative capital reallocation.

## 13. Reaction-strength decomposition

A future numeric coefficient should be decomposable rather than stored as one opaque score.

Candidate components:

```text
structural_exposure
catalyst_relevance
catalyst_magnitude
source_quality
novelty
company_specificity
cross_sectional_breadth
observed_volume_confirmation
relative_price_confirmation
persistence
```

Conceptually:

```text
reaction_strength = f(
  structural_exposure,
  catalyst_relevance,
  catalyst_magnitude,
  breadth,
  observed_confirmation,
  persistence
)
```

No weights are assigned here. Any future numeric function must be calibrated from historical events and kept versioned.

## 14. Example event chains

### 14.1 War / defense-industrial

```text
WAR_ESCALATION Fact
  ↓
DEFENSE_INDUSTRIAL relevance = high
  ↓
procurement / replenishment expectation
  ↓
peer basket buying
  ↓
THEME_ACTIVATION_CANDIDATE
  ↓
if persistent across sessions / repeated contracts
  ↓
THEME_REPRICING_ACTIVE
```

### 14.2 Major cyberattack

```text
MAJOR_CYBERATTACK Fact
  ↓
CYBERSECURITY + AI_SECURITY relevance rises
  ↓
security-spend expectation
  ↓
peer basket relative strength / volume confirmation
  ↓
THEME_ACTIVATION_CANDIDATE
```

### 14.3 AI capability acceleration

```text
AI_CAPABILITY_BREAKTHROUGH Fact
  ↓
AI_FOUNDATION demand expectation rises
AI_APPLICATION opportunity set rises
AI_SECURITY threat surface rises
AI_GOVERNANCE control requirement may rise
  ↓
multiple themes can receive positive coefficients simultaneously
```

This is why a single event should support many theme links.

### 14.4 AI growth / safety concern

```text
AI_GROWTH_CONCERN or AI_SAFETY_CONCERN Fact
  ↓
AI_FOUNDATION expected reaction = negative / mixed
AI_APPLICATION expected reaction = negative / mixed
AI_SECURITY expected reaction = positive
AI_GOVERNANCE expected reaction = positive / strong positive
  ↓
possible cross-theme rotation
```

This is the clearest candidate for the recently observed "AI growth vs control/security" split.

## 15. Fact / Derived Metric / Interpretation boundaries

### Raw Fact

Examples:

- war declaration / escalation statement;
- procurement award;
- cyberattack disclosure;
- AI safety incident;
- regulatory proposal / enacted rule;
- company product / contract announcement;
- observed OHLCV / minute bars.

### Derived Metric

Examples:

- theme-basket return;
- relative return against benchmark;
- breadth ratio;
- abnormal volume ratio;
- multi-window reaction measurements;
- persistence duration.

### Interpretation

Examples:

- `THEME_ACTIVATION_CANDIDATE`;
- `THEME_ROTATION_RELATION`;
- `THEME_REPRICING_ACTIVE`;
- event-theme reaction strength bucket;
- `AI_SECURITY` receiving positive pressure from AI safety concern.

### Prediction

Examples:

- probability the theme remains bid for N sessions;
- expected next-session relative return;
- expected continuation of capital rotation.

Predictions must not be stored as Facts.

## 16. Candidate implementation packages

The design can be decomposed into future work as follows.

### Package A — Theme ontology

- add hierarchical theme IDs;
- support many-to-many company-theme exposure;
- distinguish `DEFENSE_INDUSTRIAL`, `CYBERSECURITY`, `AI_SECURITY`, and `AI_GOVERNANCE`;
- version exposure evidence.

### Package B — Event-theme reaction contract

- classify event type;
- link one event to multiple themes;
- assign provisional direction / strength buckets;
- retain evidence and interpretation version.

### Package C — Cross-sectional market confirmation

- define theme baskets;
- compute relative returns, breadth, volume expansion, and persistence;
- separate single-name reaction from theme-level reaction.

### Package D — Theme activation / rotation / repricing interpretation

- detect activation candidate;
- detect relative rotation between themes;
- detect persistent repricing candidate;
- link to existing price-discovery / valuation-regime work without collapsing the two concepts.

### Package E — Historical calibration

- collect historical event fixtures;
- estimate event-to-theme sensitivity;
- test false positives;
- only then consider numeric coefficients.

## 17. Candidate Canary / fixture families

At minimum the validation set should include:

- AI breakthrough with Foundation-led buying;
- enterprise AI-adoption news with Application-led buying;
- major cyberattack with Security-led buying;
- AI safety / regulation event with Governance / Security relative strength;
- war escalation with Defense Industrial relative strength;
- war de-escalation or procurement disappointment as a negative defense-theme case;
- cyberattack where cybersecurity stocks do **not** outperform, to test false activation;
- AI concern where all AI subthemes sell off together, to prevent forced counter-theme classification;
- single-company positive event with no peer confirmation, to prevent false theme-level inference;
- broad market rally where apparent theme strength is explained by beta rather than specific theme activation.

## 18. Design constraints

1. Do not infer capital flow as a raw Fact solely from price movement.
2. Do not assign a permanent opposition relationship between AI Foundation and AI Security / Governance.
3. Do not encode a numeric reaction coefficient before historical calibration.
4. Do not treat one security's move as proof of a theme repricing.
5. Preserve source / event / available / accepted timestamps.
6. Keep structural theme membership distinct from transient event activation.
7. Permit one company and one event to map to multiple themes.
8. Treat market confirmation as evidence for an Interpretation, not as proof of causality.

## 19. Proposed first-order ontology

```text
TECHNOLOGY
└─ AI
   ├─ AI_FOUNDATION
   │  ├─ COMPUTE
   │  ├─ MEMORY
   │  ├─ NETWORKING
   │  ├─ DATACENTER_INFRA
   │  └─ MODEL_INFRA
   ├─ AI_APPLICATION
   │  ├─ ENTERPRISE_AI
   │  ├─ PHYSICAL_AI
   │  ├─ ROBOTICS_AUTONOMY
   │  └─ EDGE_AI
   ├─ AI_SECURITY
   │  ├─ AI_CYBER_DEFENSE
   │  ├─ MODEL_SECURITY
   │  ├─ AGENT_SECURITY
   │  └─ IDENTITY_ACCESS
   └─ AI_GOVERNANCE
      ├─ AI_COMPLIANCE
      ├─ MODEL_RISK
      ├─ AUDIT_PROVENANCE
      └─ POLICY_CONTROL

DEFENSE_INDUSTRIAL
├─ WEAPONS
├─ AEROSPACE
├─ MUNITIONS
├─ ISR_SENSOR
└─ AUTONOMOUS_DEFENSE
```

Cross-links are expected. `AUTONOMOUS_DEFENSE`, for example, can simultaneously map to `DEFENSE_INDUSTRIAL` and `AI_APPLICATION / PHYSICAL_AI`.

## 20. Proposed planning outcome

The immediate planning conclusion is:

- decompose `AI` into Foundation / Application / Security / Governance;
- introduce generic event-to-theme reaction states;
- model temporary counter-theme behavior as **rotation**, not permanent opposition;
- use cross-sectional peer confirmation before declaring theme activation;
- keep coefficient strength categorical until historical calibration;
- generalize the same mechanism to Defense Industrial and other event-sensitive themes.

## 21. Unresolved items

- Historical thresholds for `POSITIVE` vs `STRONG_POSITIVE` are not yet defined.
- Theme-basket membership and rebalance rules are not yet defined.
- Security vs Governance overlap requires explicit precedence / multi-label rules.
- Whether `CYBERSECURITY` should sit outside AI with `AI_SECURITY` as a child/cross-link, or be duplicated under the AI ontology, requires schema design.
- No normative duration for `THEME_REPRICING_ACTIVE` or confirmation is defined.
- No numeric reaction coefficient or predictive probability is justified yet.
- SentinelOne / peer historical data should be used as a candidate recent fixture only after accepted market/news data are captured with reproducible timestamps.

## 22. Recommended next implementation step

Create WBS-unreflected tasks for:

1. theme ontology and many-to-many company exposure;
2. event-theme reaction contract;
3. cross-sectional theme-basket confirmation metrics;
4. theme activation / rotation / repricing interpretation;
5. historical calibration / Canary fixtures.

These should remain design / local-analysis work until the WBS formally incorporates them and accepted data fixtures establish calibration evidence.
