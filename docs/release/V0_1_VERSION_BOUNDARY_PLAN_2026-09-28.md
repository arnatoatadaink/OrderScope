# OrderScope v0.1.x Version Boundary Plan

Status: **PROPOSED RELEASE / TAGGING PLAN — PB CLOSE REQUIRED BEFORE FINALIZATION**
Date: 2026-09-28
Branch reviewed: `feat/uwbs-100-volatility-calibration`

## 1. Purpose

Define a stable version history for the current OrderScope implementation before the final merge to `main`.

The original WBS / Critical Path implementation is treated as the `v0.1.0` baseline. Later WBS-unreflected work is grouped into coherent `v0.1.n` feature increments by functional lane rather than by individual commit.

This document separates:

1. **logical version boundary** — the intended functional contents of a version;
2. **taggable commit boundary** — a repository commit that can safely represent the completed lane;
3. **reserved boundary** — a logical version number whose UWBS work is registered but does not yet have a verified accepted implementation closeout on the reviewed branch.

Do not create a release tag for a reserved boundary merely because the UWBS IDs exist in the registry.

## 2. Release-line rule

```text
v0.1.0  Original WBS / CP baseline, finalized after PB close
v0.1.1  Operational / runtime UWBS incorporation
v0.1.2  Macro / Carry
v0.1.3  Cross-market / competitor / official macro adapters
v0.1.4  AI Theme
v0.1.5  Listing Compliance
v0.1.6  Crypto Market Structure
v0.1.7  Oil / Commodity / Cross-Asset
v0.1.8  Physical-SaaS
v0.1.9  VIX / Cross-Asset Volatility
```

`v0.1.n` is cumulative when used as an actual release tag. A later version includes all earlier content that is already present in its ancestor history.

## 3. Version boundary matrix

| Version | Functional scope | UWBS scope | Boundary state | Candidate boundary commit | Tag action |
|---|---|---|---|---|---|
| `v0.1.0` | Original WBS / CP baseline + final PB closure | Original WBS packages; PB-00..PB-10 | **PENDING PB CLOSE** | **TBD: final PB close commit** | Tag only after PB-09/PB-10 acceptance and full regression |
| `v0.1.1` | Operational / runtime extensions incorporated into formal R0/W1 work | UWBS-001..004, UWBS-016, UWBS-023..026 | **LOGICAL / ALREADY INCORPORATED** | Historical work is already interleaved with baseline; exact standalone cumulative tag boundary requires history reconstruction | Prefer release-manifest attribution; do not force a misleading historical tag |
| `v0.1.2` | Macro / Carry contracts, metrics, interpretation, validation, source survey | UWBS-011..015 -> A0-003..007 | **LOGICAL / ALREADY INCORPORATED** | Historical work already incorporated into formal A0 WBS | Prefer release-manifest attribution |
| `v0.1.3` | Competitor divergence, relative repricing and official/fallback macro adapters | UWBS-027..036 -> A0-008..017 | **LOGICAL / ALREADY INCORPORATED** | Historical work already incorporated into formal A0 WBS | Prefer release-manifest attribution |
| `v0.1.4` | AI-theme ontology, event/theme coefficients, cross-sectional reaction, theme-state calibration | UWBS-062..066 | **RESERVED — NO VERIFIED CLOSEOUT IN REVIEWED BRANCH** | none | Do not tag until implemented/accepted or explicitly deferred from v0.1 release line |
| `v0.1.5` | Listing-compliance / earnings-repricing Canary | UWBS-067 | **RESERVED — NO VERIFIED CLOSEOUT IN REVIEWED BRANCH** | none | Do not tag until implemented/accepted or explicitly deferred |
| `v0.1.6` | Crypto derivatives / market structure / weekend / OI / liquidation / venue divergence | UWBS-068..079 | **RESERVED — NO VERIFIED CLOSEOUT IN REVIEWED BRANCH** | none | Do not tag until implemented/accepted or explicitly deferred |
| `v0.1.7` | Oil, commodity fundamentals/events, BTC ETF flow, cross-asset regime, historical Canary and shadow capacity | UWBS-080..086 | **TAGGABLE ACCEPTED BOUNDARY** | `33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d` — Close UWBS-086 shadow boundary in current tracker | Candidate tag after ancestry verification against chosen release branch |
| `v0.1.8` | Physical-SaaS lifecycle, milestone reconciliation, funnel/slippage, financial quality, M&A overlay, applicability guard, Powerfleet Canary | UWBS-087..093 | **TAGGABLE ACCEPTED BOUNDARY** | `ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325` — Close Physical-SaaS lane through UWBS-093 | Candidate tag after ancestry verification |
| `v0.1.9` | VIX spot/futures term structure, VIX interpretation, BTC IV30, MSTR IV30, IV differential, historical calibration/false-positive/capacity acceptance | UWBS-094..100 | **TAGGABLE ACCEPTED BOUNDARY** | `8151d1c2727fd22b0e9f0222f589cee666c99ffc` — Accept UWBS-100 volatility calibration | Current final UWBS candidate boundary |

## 4. Important interpretation of v0.1.0

`v0.1.0` is the **product baseline**, not the date at which every historical commit first existed.

The repository has accumulated some UWBS-derived work before the PB lane was finally closed. Therefore the final PB-close commit may already contain later UWBS implementations in its physical Git tree.

For release documentation, `v0.1.0` means:

- the original WBS / CP acceptance boundary;
- market-dependent PB validation completed and safely closed;
- core L0/L1/X0/N1/W1/CS0/MR0 and original A0 expectations preserved;
- no claim that later UWBS feature lanes were conceptually part of the original scope.

If a byte-for-byte historical `v0.1.0` tree excluding every later UWBS change is required, it must be reconstructed on a dedicated release branch. Do not rewrite published history merely to obtain that shape.

## 5. Version explanations and acceptance focus

### v0.1.0 — Original OrderScope baseline

Purpose: establish the first reproducible system baseline defined by the original WBS and Critical Path.

Primary capabilities:

- local corporate-intelligence foundation;
- normalized Fact / Evidence / Derived Metric boundaries;
- market-history collection, local recovery and gap handling;
- Worker/D1 integration foundation;
- market-reaction and corporate-signal paths;
- fixture / historical / real-data validation paths;
- PB active-session execution and safe close.

Release gate:

- PB-09 accepted;
- PB-10 accepted / safe closed;
- Python full regression pass;
- Worker/runtime tests pass;
- TypeScript typecheck pass where applicable;
- `compileall` pass;
- `git diff --check` pass;
- D1 migration/runtime configuration reviewed;
- no unexpected live/provider/secret change;
- current WBS/CP/tracker reconciled.

### v0.1.1 — Operational / runtime extension

Purpose: harden the operational behavior around the original baseline.

Scope attribution:

- UWBS-001..004;
- UWBS-016;
- UWBS-023..026.

These tasks have already been incorporated into formal runtime/operational WBS IDs. Treat this version primarily as a release-manifest boundary unless a clean historical cumulative commit can be demonstrated.

Review focus:

- custody and retry behavior;
- Worker/D1 operational boundaries;
- evidence retention;
- failure handling / fail-closed behavior;
- cost and read/write semantics;
- restart safety.

### v0.1.2 — Macro / Carry

Purpose: add reusable non-price macro context without converting inference into Fact.

Scope attribution:

- UWBS-011..015 -> A0-003..007.

Primary capabilities:

- policy/market rates and sovereign-yield Facts;
- rate-curve and cross-country Derived Metrics;
- USD/JPY and yield-delta context;
- carry-unwind / deleveraging Interpretation contracts;
- macro stress validation fixtures;
- structured macro source survey.

Review focus:

- tenor and unit identity;
- observation/release/accepted timestamps;
- revision behavior;
- UNKNOWN propagation;
- capital movement remains Interpretation, not Fact.

### v0.1.3 — Cross-market / competitor / official macro adapters

Purpose: move from generic macro context to reusable relative-repricing and source-adapter infrastructure.

Scope attribution:

- UWBS-027..036 -> A0-008..017.

Primary capabilities:

- leader / competitor / substitute relationships;
- relative overshoot / mean-reversion metrics;
- macro-pressure / latent-catalyst interpretation;
- repricing-state extension;
- CBRS divergence Canary;
- U.S. Treasury / NY Fed / BOJ-MOF / FRED-ALFRED adapters;
- CFTC positioning evidence.

Review focus:

- adapters fail closed;
- revision/source lineage preserved;
- fallback never silently changes source semantics;
- positioning is not mislabeled as fund flow;
- price/volume does not identify institutional buyers.

### v0.1.4 — AI Theme

Purpose: model events and market reactions across an AI/adjacent-theme graph rather than treating every related stock as one homogeneous theme.

Reserved scope:

- UWBS-062..066.

Expected capabilities:

- multi-theme ontology;
- event x theme reaction coefficients;
- cross-sectional confirmation;
- theme activation / rotation / repricing state;
- historical calibration and Canary.

Current release state: **reserved, not taggable from the reviewed branch**.

### v0.1.5 — Listing Compliance

Purpose: separate exchange-listing compliance events from price repricing and earnings reactions.

Reserved scope:

- UWBS-067.

Expected capabilities:

- compliance-notice Fact handling;
- deadline/effective-state context;
- recovery/compliance outcome;
- LVWR reference Canary;
- no automatic equation of notice with actual delisting.

Current release state: **reserved, not taggable from the reviewed branch**.

### v0.1.6 — Crypto Market Structure

Purpose: provide 24/7 crypto market-structure evidence and derivatives context beneath later cross-asset interpretation.

Reserved scope:

- UWBS-068..079.

Expected capabilities:

- crypto derivatives Facts / Derived Metrics;
- BTC leader/alt context;
- futures/perpetual multi-venue adapters;
- durable snapshot/catch-up lifecycle;
- liquidation and price-zone OI analysis;
- venue divergence/data-quality guards;
- NEAR reference Canary;
- Pacific weekend/weekday handoff analysis.

Current release state: **reserved, not taggable from the reviewed branch**.

### v0.1.7 — Oil / Commodity / Cross-Asset

Purpose: add direct commodity evidence and cross-asset regime analysis.

Accepted scope:

- UWBS-080..086.

Primary capabilities:

- WTI / Brent source-neutral contracts;
- commodity fundamental acquisition selection;
- supply/shipping/geopolitical event taxonomy;
- oil-down inflation/growth interpretation;
- BTC ETF-flow normalization;
- Risk-On / Crypto Risk-On regime contract;
- historical Canary;
- Worker/D1 capacity assessment.

Boundary commit:

`33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d`

Important limitation: accepted runtime boundary is shadow/canary capacity. It does **not** by itself authorize live acquisition mode.

### v0.1.8 — Physical-SaaS

Purpose: model physical deployment businesses where commercial progress, deployment, billing, ARR and recognized revenue occur at different lifecycle stages.

Accepted scope:

- UWBS-087..093.

Primary capabilities:

- deployment-lifecycle Fact contract;
- operational milestone reconciliation;
- deployment-funnel Derived Metrics and slippage;
- recurring-revenue / cash-conversion / deleveraging model;
- M&A integration evidence overlay;
- applicability guard;
- Powerfleet lifecycle Canary / false-positive suite.

Boundary commit:

`ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325`

Review focus: never conflate backlog/bookings/deployment/connected base/billing/ARR/revenue.

### v0.1.9 — VIX / Cross-Asset Volatility

Purpose: establish explicit volatility observations and calibration without turning implied volatility into a directional signal.

Accepted scope:

- UWBS-094..100.

Primary capabilities:

- source-neutral volatility-instrument contract;
- VIX spot and F1/F2 term structure;
- contango/backwardation/curve interpretation;
- BTC IV30;
- MSTR IV30;
- MSTR/BTC IV differential;
- historical calibration;
- threshold / percentile / z-score comparison;
- Canary confusion-matrix and lead/lag evaluation;
- capacity assessment integration.

Boundary commit:

`8151d1c2727fd22b0e9f0222f589cee666c99ffc`

Latest UWBS-100 local acceptance evidence:

```text
focused:           13 passed
full analysis:    986 passed
compileall:       PASS
git diff --check: PASS
```

Review focus: IV and VIX remain volatility evidence; no automatic directional, causal or trading interpretation.

## 6. Legacy unassigned UWBS IDs

The following valid legacy IDs are not assigned to the release sequence above until their incorporation/closeout is explicitly reconciled:

```text
UWBS-005..010
UWBS-017..022
```

Do not silently insert them into an already tagged historical version. Once their final disposition is known, either:

- document them as covered/deferred with no release increment; or
- allocate `v0.1.10+` if they introduce accepted functionality.

## 7. Main-integration procedure after PB close

Recommended order:

```text
1. Complete PB-09 active-session validation.
2. Complete PB-10 bounded execution / safe close.
3. Run full repository acceptance suite.
4. Reconcile CURRENT tracker + Critical Path + UWBS closeout state.
5. Record final PB-close commit SHA as v0.1.0 product-baseline evidence.
6. Verify ancestry of the accepted UWBS lane boundaries.
7. Decide disposition of reserved v0.1.4..v0.1.6.
8. Produce release notes / version manifest.
9. Integrate final accepted head to main by fast-forward or reviewed merge.
10. Create annotated tags only for boundaries that correspond to real accepted commit states.
```

Do not rewrite historical commits solely to make the semantic-version sequence visually contiguous.

## 8. Final tag recommendation

Two valid strategies exist.

### Strategy A — Evidence-preserving (recommended)

Use `v0.1.0` for the post-PB product baseline, then tag only later/independently meaningful accepted boundaries whose ancestry and semantics are valid. Keep `v0.1.1..v0.1.6` as release-manifest logical versions until/unless reconstructed cleanly.

This preserves the real development history.

### Strategy B — Reconstructed release branch

Create a dedicated release branch from the original WBS baseline and replay accepted UWBS lanes in desired semantic order, producing exact `v0.1.0..v0.1.9` cumulative trees.

Use this only if byte-level reproducibility of every intermediate version is worth the extra risk and review cost. Do not rewrite `main` history.

For OrderScope, **Strategy A is preferred**.
