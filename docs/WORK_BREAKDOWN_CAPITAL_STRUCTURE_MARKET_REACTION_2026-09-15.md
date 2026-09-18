# OrderScope — Capital Structure / Market Reaction Work Breakdown

Status: non-normative execution backlog extension
Date: 2026-09-15
Parent: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Normative spec: `stock_monitoring_v0.1_spec.md`
Source reports:
- `work-management/local-corporate-intelligence/REPORT_TNON_CONVERTIBLE_DEBT_REPAYMENT_CASE_2026-09-11.md`
- `work-management/local-corporate-intelligence/REPORT_TNON_CHPT_PRICE_REDISCOVERY_2026-09-11.md`

## 1. Purpose

Formally incorporate the previously WBS-unreflected TNON / CHPT work while preserving the project boundary between source-grounded capital-structure Facts and price/volume-derived market-reaction interpretations.

This WBS does not turn the TNON or CHPT examples into predictive rules. It does not establish fixed percentage, duration, session-count, or attention-score thresholds. It does not authorize live provider activation, Worker/Cron mutation, remote D1 mutation, or trading actions.

## 2. CS0 — Capital Structure lifecycle

| ID | Source | Task | Completion condition | Dependency |
|---|---|---|---|---|
| CS0-001 | UWBS-017 | Define stateful Capital Instrument / Convertible Debt lifecycle contract | Represent issuance, outstanding state, maturity, optional extension, conversion-window opening, conversion formula, mandatory/optional prepayment, partial/full repayment, refinancing, conversion and termination as historical state transitions; preserve instrument identity, terms, event/available/accepted times and source provenance | I0-002/004/005; S0 filing records; N1 discovery path |
| CS0-002 | UWBS-018 | Implement maturity/conversion-window Attention and financing-to-debt-resolution linkage | Derive bounded attention from disclosed contractual dates; connect recent financing and explicit use-of-proceeds debt-repayment language to outstanding instruments without asserting repayment before confirmation; expose `DEBT_RESOLUTION_WINDOW` only as Interpretation; keep thresholds configurable/non-normative until validated | CS0-001; scheduler/calendar primitives; SEC/IR/news acquisition |
| CS0-003 | UWBS-019 | Model dilution-overhang and capital-structure regime transitions | Distinguish instrument-specific overhang creation/reduction/removal from company-wide dilution risk; retain replacement warrants/pre-funded warrants separately; support evidence-backed `CONVERTIBLE_NOTE_DILUTION_OVERHANG_REMOVED` and higher-level capital-structure regime interpretation without converting it directly into a price prediction | CS0-001/002; I0 Fact/Derived Metric/Interpretation separation; Regime model |

### 2.1 CS0 boundaries

Raw/normalized Facts may include:

```text
CAPITAL_INSTRUMENT_CREATED
CAPITAL_INSTRUMENT_TERMS_CHANGED
CAPITAL_INSTRUMENT_MATURES_SOON
CAPITAL_INSTRUMENT_CONVERSION_WINDOW_OPEN
FINANCING_ANNOUNCED
FINANCING_CLOSED
DEBT_PREPAYMENT_REQUIRED
DEBT_PARTIALLY_REPAID
DEBT_FULLY_REPAID
```

Derived/Interpretation concepts may include:

```text
DILUTION_OVERHANG_CREATED
DILUTION_OVERHANG_REDUCED
CONVERTIBLE_NOTE_DILUTION_OVERHANG_REMOVED
DEBT_RESOLUTION_WINDOW
CAPITAL_STRUCTURE_REGIME_CHANGE
```

Safeguards:
- Do not infer actual debt repayment from stated use of proceeds alone.
- Do not equate original principal with final cash settlement unless a source establishes it.
- Do not treat removal of one convertible instrument as removal of all dilution risk.
- Preserve event, available, accepted, source/accession/document and instrument identities.
- Newswire discovery may precede SEC/issuer confirmation, but the discovery/confirmation states must remain distinct.

## 3. MR0 — Catalyst / Market Reaction / Price Rediscovery

| ID | Source | Task | Completion condition | Dependency |
|---|---|---|---|---|
| MR0-001 | UWBS-020 | Define catalyst-to-market-reaction observation contract | For material source-grounded catalysts, persist fixed-window returns, volume/volatility ratios and session-aware observations across premarket, regular, after-hours and subsequent sessions; preserve catalyst identity; OHLCV response must not be treated as proof of causation | L1 market bars/session model; I0 history; accepted event taxonomy; CS0/S0/E0/N1 catalyst sources |
| MR0-002 | UWBS-021 | Define Price Discovery / Catalyst-Price Divergence interpretation state machine | Distinguish `NO_REACTION`, `PARTIAL_REACTION`, `DIRECTIONAL_REACTION`, `CATALYST_PRICE_DIVERGENCE`, `DELAYED_REPRICING`, `PRICE_SPIKE`, `PRICE_DISCOVERY_ACTIVE`, `NEW_EQUILIBRIUM_CANDIDATE`, `PRICE_REDISCOVERY_CONFIRMED`, and `PRICE_REDISCOVERY_FAILED`; base confirmation on persistence/retest/participation rather than peak percentage alone; keep `VALUATION_REGIME_CHANGE` distinct from `COMPANY_REGIME_CHANGE` | MR0-001; Fact/Derived Metric/Interpretation boundary; Regime specification |
| MR0-003 | UWBS-022 | TNON / CHPT capital-event and price-rediscovery Canary fixtures | Reproduce TNON maturity/conversion-window → financing/debt-resolution evidence → full repayment → instrument-specific overhang removal → same-session divergence → delayed repricing, and CHPT earnings catalyst → extreme participation → multi-session higher-range persistence; include false positives for low-float spike/retrace, offsetting dilution, stronger conflicting news, market-wide movement and one-session persistence failure | CS0-001..003; MR0-001/002; historical minute/daily bars; permitted source snapshots |

### 3.1 MR0 observation fields

Candidate fixed windows:

```text
reaction_5m
reaction_30m
reaction_1h
reaction_session_close
reaction_after_hours
reaction_next_premarket
reaction_next_open
reaction_next_close
reaction_3d
reaction_5d
```

Candidate market-structure measurements:
- old equilibrium reference range;
- event price and event-session VWAP;
- peak/trough;
- volume ratio to rolling baseline;
- realized-volatility ratio;
- high-volume price region;
- pullback depth from event peak;
- retest level/result;
- time above/below candidate equilibrium;
- sessions maintaining the candidate range.

These fields define what may be measured. They do not define normative thresholds.

### 3.2 Spike vs rediscovery boundary

The intended separation is qualitative until historical calibration exists:

```text
PRICE_SPIKE
  = large displacement + weak persistence + return toward old range

PRICE_REDISCOVERY
  = material catalyst + abnormal participation + invalidation of old range
    + candidate range survives retest + persistence across reviewed windows
```

A large percentage move by itself is insufficient for `PRICE_REDISCOVERY_CONFIRMED`.

## 4. Dependency graph

```text
I0-002/004/005 + S0/N1
        ↓
     CS0-001
        ↓
     CS0-002
        ↓
     CS0-003
        │
        ├──────────────┐
        ↓              │
     MR0-001 ← E0/N1/market bars
        ↓              │
     MR0-002            │
        ↓              │
     MR0-003 ←──────────┘
```

`CS0` may proceed independently from live market availability because its core acceptance can be fixture/source-history based. `MR0-001/002` deterministic calculations and historical replay may also proceed while markets are closed. Any completion condition that later requires fresh post-catalyst session behavior remains market-day gated.

## 5. Execution order

1. Implement/review `CS0-001` state/history contract.
2. Add `CS0-002` bounded attention/linkage without predictive repayment claims.
3. Add `CS0-003` instrument-specific dilution-overhang transitions.
4. Implement `MR0-001` deterministic catalyst/market observation contract.
5. Implement `MR0-002` interpretation state machine with no fixed numeric threshold.
6. Build `MR0-003` TNON/CHPT + false-positive fixtures.
7. Only after historical validation, decide whether any numeric thresholds or minimum persistence windows deserve a separate calibration task.

## 6. Definition of Done

### CS0
- Capital instruments are stateful historical objects, not isolated headlines.
- Maturity/conversion/extension/repayment/refinancing/conversion states are source-traceable.
- Financing use-of-proceeds creates Evidence/attention, not an unconfirmed repayment Fact.
- Replacement warrants and other dilution exposure remain separately represented.
- Instrument-specific overhang removal is not silently promoted to company-wide dilution removal.

### MR0
- Every market-reaction record is linked to a source-grounded catalyst identity.
- Fixed observation windows are deterministic and session-aware.
- Market movement is Derived Metric / Interpretation, not causal Fact.
- Price spike, divergence, delayed repricing and persistent rediscovery are distinguishable.
- Canary fixtures include contradictory/confounding cases and withhold confirmation when persistence evidence is insufficient.
- `VALUATION_REGIME_CHANGE` remains distinct from `COMPANY_REGIME_CHANGE`.

## 7. Market-day / change-control boundary

May proceed while U.S. markets are closed:
- schema/type design;
- fixture construction;
- historical SEC/IR/news linkage;
- historical minute/daily replay;
- deterministic observation calculations;
- state-machine tests;
- WBS/CP documentation.

Market-day gated only when a specific acceptance condition requires fresh active-session evidence.

Separately gated regardless of market state:
- live provider activation;
- Worker/Cron deployment or mutation;
- remote D1 mutation;
- purge;
- trading or automatic portfolio actions.

## 8. UWBS incorporation map

| UWBS ID | Final WBS ID | Disposition |
|---|---|---|
| UWBS-017 | CS0-001 | Incorporated |
| UWBS-018 | CS0-002 | Incorporated |
| UWBS-019 | CS0-003 | Incorporated |
| UWBS-020 | MR0-001 | Incorporated |
| UWBS-021 | MR0-002 | Incorporated |
| UWBS-022 | MR0-003 | Incorporated |

## 9. Unresolved planning questions

- Historical precision/recall of the `DEBT_RESOLUTION_WINDOW` attention heuristic is not yet measured.
- No normative duration or session-count threshold for `PRICE_REDISCOVERY_CONFIRMED` exists.
- Intraday high-volume price-node calculations require minute bars; daily OHLCV is insufficient.
- Expected catalyst-strength calibration remains future work.
- Newswire licensing/API/retention constraints remain provider-contract work and are not solved by this WBS.
