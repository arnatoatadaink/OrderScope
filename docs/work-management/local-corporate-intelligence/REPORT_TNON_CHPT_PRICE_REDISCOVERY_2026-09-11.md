# TNON / CHPT Price Rediscovery Comparative Report

Status: **Research / design input — not normative specification**
Date: 2026-09-11
Symbols: `TNON`, `CHPT`
Related TNON report: `docs/work-management/local-corporate-intelligence/REPORT_TNON_CONVERTIBLE_DEBT_REPAYMENT_CASE_2026-09-11.md`
Related backlog: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`

## 1. Purpose

This report compares two recent sharp repricing cases to define a reusable OrderScope distinction between a transient price spike and a genuine market price rediscovery process.

- `CHPT`: operating / fundamental revaluation after fiscal Q2 2027 results.
- `TNON`: capital-structure revaluation after removal of discounted convertible-note overhang.

The cases are deliberately not treated as identical. They share a market-reaction pattern class, while the underlying catalyst class differs.

## 2. Executive summary

`CHPT` is the stronger current reference case for **confirmed price rediscovery**. Its September 3 repricing was followed by several sessions in which price remained materially above the September 2 pre-event close.

`TNON` is a useful reference case for **delayed / conflicted price discovery**. The positive September 9 capital-structure catalyst was followed by a sharply negative regular session, then a large positive move after-hours / the following session. This is evidence of delayed repricing, but the durability of the new equilibrium requires more observation than CHPT.

The reusable model should therefore separate:

```text
CATALYST
  ↓
INITIAL_REACTION
  ↓
PRICE_DISCOVERY
  ↓
NEW_EQUILIBRIUM_CANDIDATE
  ↓
PRICE_REDISCOVERY_CONFIRMED or PRICE_SPIKE_REJECTED
```

A large percentage gain alone must not establish `PRICE_REDISCOVERY_CONFIRMED`.

## 3. CHPT — fundamental revaluation reference case

### 3.1 Catalyst facts

ChargePoint reported fiscal Q2 2027 results on September 2, 2026. Company-reported highlights included:

- revenue of `$116M`, up 18% year-over-year and above guidance;
- subscription revenue of `$44M`, up 10% year-over-year;
- GAAP gross margin of 36%;
- non-GAAP gross margin of 38%;
- non-GAAP adjusted EBITDA loss of `$4.8M`, improved from a `$22.1M` loss in the prior-year period.

Sources:
- ChargePoint IR: https://investors.chargepoint.com/news/news-details/2026/ChargePoint-Reports-Second-Quarter-Fiscal-Year-2027-Financial-Results/default.aspx
- SEC 8-K: https://www.sec.gov/Archives/edgar/data/1777393/000177739326000061/chpt-20260902.htm

### 3.2 Daily market reaction

Observed daily prices show a clear regime shift around the event:

| Date | Close | Daily change | Volume |
|---|---:|---:|---:|
| 2026-09-02 | `$5.19` | `-2.08%` | `1.63M` |
| 2026-09-03 | `$9.08` | `+74.95%` | `44.12M` |
| 2026-09-04 | `$9.89` | `+8.92%` | `13.30M` |
| 2026-09-08 | `$9.37` | `-5.26%` | `5.36M` |
| 2026-09-09 | `$8.95` | `-4.48%` | `2.26M` |
| 2026-09-10 | `$9.00` | `+0.56%` | `1.39M` |

Source:
- StockAnalysis historical data: https://stockanalysis.com/stocks/chpt/history/

The important signal is not just the September 3 peak. By September 10, CHPT still traded around `$9`, far above the September 2 close of `$5.19`. That persistence is consistent with a new equilibrium range being accepted by the market.

### 3.3 Interpretation

Candidate classification:

```text
catalyst_class = FUNDAMENTAL_REVALUATION
initial_reaction = STRONGLY_POSITIVE
volume_expansion = EXTREME
new_equilibrium_candidate = ~9 USD region
persistence = MULTI_SESSION
price_rediscovery_state = CONFIRMED_CANDIDATE
```

`CONFIRMED_CANDIDATE` is intentionally softer than an unconditional long-term fair-value claim. Market price acceptance for several sessions does not prove fundamental intrinsic value.

## 4. TNON — capital-structure revaluation / delayed repricing reference case

### 4.1 Catalyst facts

On September 9, 2026, Tenon Medical announced full early repayment of outstanding original issue discount senior convertible promissory notes originally issued with aggregate principal of approximately `$5.16M`, ahead of their September 11 maturity. The company explicitly stated that repayment eliminated the potential conversion of the notes into common shares at a discount to market prices.

Sources:
- ACCESS Newswire: https://www.accessnewswire.com/newsroom/en/education/tenon-medical-announces-early-repayment-of-its-convertible-notes-1218400
- SEC 8-K: https://www.sec.gov/Archives/edgar/data/1560293/000121390026098232/ea0304884-8k_tenon.htm

### 4.2 Market reaction

September 9 regular-session data:

| Date | Open | High | Low | Close | Change | Volume |
|---|---:|---:|---:|---:|---:|---:|
| 2026-09-08 | `$3.58` | `$3.60` | `$3.18` | `$3.36` | `-9.68%` | `~0.386M` |
| 2026-09-09 | `$3.44` | `$3.67` | `$2.40` | `$2.44` | `-27.38%` | `~12.72M` |
| 2026-09-10 | `$4.20` | `$5.77` | `$4.00` | `$5.20` | `+113.12%` | `~100.85M` |

Sources:
- StockAnalysis / September 9: https://stockanalysis.com/stocks/tnon/history/
- Investing.com / September 10 daily record: https://jp.investing.com/equities/tenon-medical-historical-data

StockAnalysis also recorded an after-hours September 9 price near `$3.02`, approximately `+23.77%` from the regular close. This establishes that the positive repricing began after a regular session that had moved strongly against the catalyst direction.

### 4.3 Interpretation

Candidate classification:

```text
catalyst_class = CAPITAL_STRUCTURE_REVALUATION
fundamental_direction = POSITIVE
regular_session_reaction = STRONGLY_NEGATIVE
after_hours_reaction = POSITIVE
next_regular_session_reaction = STRONGLY_POSITIVE
volume_expansion = EXTREME
reaction_latency = DELAYED / CROSS_SESSION
price_rediscovery_state = ACTIVE_CANDIDATE
```

TNON should not yet be treated as equivalent to CHPT's persistence case. A single following-session doubling can still be dominated by micro-cap liquidity, short positioning, warrant / float effects, or temporary speculative flow.

## 5. What the two cases have in common

Both cases show that a catalyst can invalidate the market's previous pricing assumptions and force a search for a new balance between buyers and sellers.

The reusable sequence is:

```text
OLD_EQUILIBRIUM
  ↓
MATERIAL CATALYST
  ↓
HIGH VOLUME / HIGH VOLATILITY
  ↓
MULTIPLE CANDIDATE PRICE LEVELS
  ↓
RETEST / ACCEPTANCE / REJECTION
  ↓
NEW EQUILIBRIUM CANDIDATE
```

The key analytical object is not the highest traded price. It is the price region that attracts sustained volume and survives subsequent retests.

## 6. What is different

| Dimension | CHPT | TNON |
|---|---|---|
| Catalyst class | Fundamental / operating performance | Capital structure / dilution-overhang removal |
| Prior pricing assumption affected | Growth, margin, cash-burn trajectory | Dilution / discounted conversion risk |
| First major reaction | Immediate large positive repricing | Regular-session negative divergence, then delayed positive repricing |
| Persistence evidence as of 2026-09-11 | Several sessions near the new higher range | Limited; large next-session move requires further persistence test |
| Liquidity / micro-cap distortion risk | Material but lower | High |
| Best reference use | Confirmed rediscovery pattern | Delayed rediscovery / catalyst-price divergence pattern |

## 7. Proposed OrderScope state model

### 7.1 Reaction states

```text
NO_REACTION
PARTIAL_REACTION
DIRECTIONAL_REACTION
CATALYST_PRICE_DIVERGENCE
DELAYED_REPRICING
```

### 7.2 Price-discovery states

```text
PRICE_SPIKE
PRICE_DISCOVERY_ACTIVE
NEW_EQUILIBRIUM_CANDIDATE
PRICE_REDISCOVERY_CONFIRMED
PRICE_REDISCOVERY_FAILED
```

These should be Derived Metric / Interpretation states, not raw Facts.

## 8. Candidate measurements

For each material catalyst, persist fixed-window market observations:

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
- event price;
- event-session VWAP;
- peak and trough;
- volume ratio against rolling baseline;
- realized volatility ratio;
- high-volume price region;
- pullback depth from event peak;
- retest level and result;
- time spent above / below candidate equilibrium;
- number of sessions maintaining the new range.

The thresholds for these metrics must be learned / validated; they are not defined by the TNON and CHPT examples alone.

## 9. Spike vs rediscovery acceptance concept

A first provisional distinction is:

```text
PRICE_SPIKE
  large instantaneous move
  + weak persistence
  + rapid return toward old range

PRICE_REDISCOVERY
  material catalyst
  + abnormal participation / volume
  + old range invalidated
  + candidate higher/lower range survives retest
  + persistence across defined observation windows
```

A percentage threshold alone is insufficient. For example, both a +80% one-hour pump that fully reverses and CHPT's multi-session repricing can exhibit a similar maximum percentage change while representing different states.

## 10. Proposed hierarchy

```text
VALUATION_REGIME_CHANGE
  └─ PRICE_DISCOVERY
       ├─ FUNDAMENTAL_REVALUATION
       │    └─ CHPT reference fixture
       ├─ CAPITAL_STRUCTURE_REVALUATION
       │    └─ TNON reference fixture
       ├─ M&A_REVALUATION
       ├─ REGULATORY_REVALUATION
       └─ BUSINESS_REGIME_REVALUATION
```

This hierarchy should remain linked to, but distinct from, `COMPANY_REGIME_CHANGE`. A market repricing can occur without a durable business-regime change, and a business-regime change can exist before the market fully reprices it.

## 11. Proposed derived event contracts

Candidate interpretation objects:

```text
CATALYST_PRICE_DIVERGENCE
  catalyst_direction
  expected_strength_bucket
  observed_return_window
  observed_volume_ratio
  conflicting_known_events[]

PRICE_DISCOVERY_EVENT
  old_equilibrium
  event_timestamp
  catalyst_class
  peak_price
  pullback_low
  high_volume_price_region
  new_equilibrium_candidate
  equilibrium_duration
  retest_status
  confirmation_state
```

`expected_strength_bucket` must be derived from explicit evidence and calibrated historically. It must not silently encode discretionary analyst conviction as Fact.

## 12. Canary / fixture use

Recommended reference fixtures:

### CHPT fixture

Expected behaviors:

- detect material earnings / operating catalyst;
- detect extreme volume and price displacement;
- recognize persistence above the old range across subsequent sessions;
- classify as a fundamental-revaluation price-rediscovery candidate.

### TNON fixture

Expected behaviors:

- detect confirmed capital-structure catalyst;
- identify same-session price direction conflict;
- create `CATALYST_PRICE_DIVERGENCE` rather than automatically invalidating the catalyst;
- observe after-hours / next-session reversal;
- classify `DELAYED_REPRICING` and `PRICE_DISCOVERY_ACTIVE`;
- withhold durable rediscovery confirmation until persistence criteria are satisfied.

## 13. Failure / false-positive cases required

The implementation must include cases where:

- a positive headline is followed by a durable negative repricing because another stronger negative event exists;
- a micro-cap stock spikes on low float and fully retraces;
- an earnings beat creates only a temporary gap that closes;
- a dilution-overhang removal is offset by a replacement financing with comparable or greater dilution;
- market-wide movement explains most of the apparent repricing;
- price remains high for one session but fails the multi-session persistence criterion.

## 14. WBS-unreflected work linkage

This report is the source document for backlog items covering:

- catalyst-to-market-reaction observation windows;
- `CATALYST_PRICE_DIVERGENCE` / `DELAYED_REPRICING` interpretation;
- price-spike vs price-rediscovery state model;
- valuation-regime linkage while preserving separation from `COMPANY_REGIME_CHANGE`;
- CHPT / TNON Canary fixtures and historical threshold validation.

See the `Capital structure / catalyst and price-discovery expansion` section added to `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`.

## 15. Unresolved items

- No normative duration / number-of-sessions threshold for `PRICE_REDISCOVERY_CONFIRMED` is established yet.
- Intraday high-volume price-node calculations require the project's minute-bar dataset; daily OHLCV alone is insufficient.
- Expected catalyst strength requires calibration against historical events before it can be used as a systematic signal.
- TNON's longer-duration equilibrium remains unconfirmed as of this report date.
