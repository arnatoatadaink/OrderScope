# TNON / CHPT / LVWR / AMBR Price Rediscovery Comparative Report

Status: **Research / design input — not normative specification**
Date: 2026-09-11
Symbols: `TNON`, `CHPT`, `LVWR`, `AMBR`
Related TNON report: `docs/work-management/local-corporate-intelligence/REPORT_TNON_CONVERTIBLE_DEBT_REPAYMENT_CASE_2026-09-11.md`
Related backlog: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`

## 1. Purpose

This report compares two recent sharp repricing cases to define a reusable OrderScope distinction between a transient price spike and a genuine market price rediscovery process.

- `CHPT`: operating / fundamental revaluation after fiscal Q2 2027 results.
- `TNON`: capital-structure revaluation after removal of discounted convertible-note overhang.
- `LVWR`: earnings-led repricing that also removed an exchange minimum-price compliance overhang.

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

## 14. LVWR — earnings repricing plus listing-compliance overhang removal

### 14.1 Catalyst and listing-compliance facts

LiveWire Group provides a useful third case because the market catalyst and the exchange-compliance state were related but not identical events.

On July 23, 2026, LiveWire disclosed that NYSE had notified the company that it was below the continued-listing minimum share-price criterion after its average closing price over a consecutive 30-trading-day period fell below $1.00. This was a compliance deficiency with a cure period, not an immediate delisting event.

The company also reported Q2 2026 results on July 23. Company-reported highlights included revenue of approximately $9.1M, up 55% year-over-year, while operating and net losses remained substantial. The following session produced an exceptionally large positive repricing.

On August 3, 2026, NYSE notified LiveWire that it had regained compliance based on the 30-trading-day average closing price through July 31; LiveWire publicly announced the regained-compliance status on August 10.

Sources:

- SEC / July 23 listing-compliance disclosure: https://www.sec.gov/Archives/edgar/data/1898795/000189879526000078/lvwr-20260723.htm
- LiveWire Q2 2026 results: https://investor.livewire.com/news-events-1/news/news-details/2026/LiveWire-Group-Inc--Reports-2026-Second-Quarter-Financial-Results/default.aspx
- LiveWire regained-compliance announcement: https://investor.livewire.com/news-events-1/news/news-details/2026/LiveWire-Group-Regains-Compliance-with-NYSE-Continued-Listing-Standards/default.aspx

### 14.2 Event-chain interpretation

The important modeling distinction is:

```text
LISTING_COMPLIANCE_DEFICIENCY
  + EARNINGS_CATALYST
        ↓
LARGE POSITIVE REPRICING
        ↓
30-DAY AVERAGE PRICE RECOVERS
        ↓
LISTING_COMPLIANCE_RESTORED
        ↓
POST-EVENT PRICE_DISCOVERY
```

The July 23 earnings release is the primary observed market catalyst. Regaining NYSE compliance was a later consequence of the sustained price recovery and should not be modeled as though the September move were caused by a new "30th-day delisting event."

For OrderScope, the source-grounded states should therefore remain separate:

```text
EXCHANGE_LISTING_DEFICIENCY
EXCHANGE_LISTING_CURE_WINDOW
EXCHANGE_LISTING_COMPLIANCE_RESTORED
```

from the market interpretation states:

```text
PRICE_DISCOVERY_ACTIVE
NEW_EQUILIBRIUM_CANDIDATE
PRICE_REDISCOVERY_CONFIRMED / FAILED
```

### 14.3 September follow-through

By mid-September, LVWR again showed a multi-session rise with expanding participation, including a sharp September 17 move. No new exchange-compliance event was identified that explains this move as a fresh delisting-avoidance catalyst.

The current interpretation is therefore:

```text
July:
  earnings catalyst
  + listing-risk overhang
  -> large repricing
  -> compliance restoration

August:
  post-event range formation / equilibrium search

September:
  renewed momentum inside the post-July repricing regime
  -> possible continuation of price discovery
  -> not a distinct delisting event on current evidence
```

This distinction matters because a mechanical date count after the original notice can create a false causal label. The relevant NYSE rule uses the rolling 30-trading-day average and the company had already disclosed restored compliance in August.

### 14.4 Reusable design lesson

LVWR extends the existing CHPT/TNON model with an event-chain where a market repricing changes a regulatory/listing state.

Candidate representation:

```text
source facts:
  earnings_event
  exchange_listing_deficiency
  exchange_listing_compliance_restored

derived observations:
  abnormal_return
  abnormal_volume
  rolling_average_price_recovery
  persistence_above_old_range

interpretation:
  PRICE_DISCOVERY_ACTIVE
  LISTING_OVERHANG_REMOVED
  NEW_EQUILIBRIUM_CANDIDATE
```

`LISTING_OVERHANG_REMOVED` must remain an Interpretation derived from an explicit exchange-compliance restoration Fact. It must not be inferred only because the share price temporarily trades above $1.

### 14.5 Canary / false-positive requirements

A future LVWR fixture should verify that the system can:

- ingest the exchange deficiency notice as a distinct Fact;
- ingest the earnings catalyst independently;
- observe the large post-earnings repricing;
- ingest the later explicit NYSE compliance-restoration notice;
- avoid creating a second "delisting avoided" event from a calendar-count coincidence;
- distinguish a September momentum continuation from a new listing-compliance catalyst;
- reject false positives where price briefly exceeds $1 but the required rolling-average criterion or explicit restoration evidence is absent.

Dependencies should reuse `UWBS-020` and `UWBS-021` rather than creating a second market-reaction framework.

## 15. WBS-unreflected work linkage

This report is the source document for backlog items covering:

- catalyst-to-market-reaction observation windows;
- `CATALYST_PRICE_DIVERGENCE` / `DELAYED_REPRICING` interpretation;
- price-spike vs price-rediscovery state model;
- valuation-regime linkage while preserving separation from `COMPANY_REGIME_CHANGE`;
- CHPT / TNON Canary fixtures and historical threshold validation;
- LVWR listing-compliance / earnings-repricing chain and false-causality rejection fixture.

See the `Capital structure / catalyst and price-discovery expansion` section added to `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`.

## 16. Unresolved items

- No normative duration / number-of-sessions threshold for `PRICE_REDISCOVERY_CONFIRMED` is established yet.
- Intraday high-volume price-node calculations require the project's minute-bar dataset; daily OHLCV alone is insufficient.
- Expected catalyst strength requires calibration against historical events before it can be used as a systematic signal.
- TNON's longer-duration equilibrium remains unconfirmed as of this report date.

## 17. AMBR — delayed stair-step repricing and cross-theme acceleration hypothesis

### 17.1 Observed structure

The user-provided September 9–18 15-minute chart and September 18 one-minute chart show a stair-step repricing pattern rather than a single isolated vertical spike. The stock repeatedly formed balance at progressively higher price levels instead of immediately returning to the prior range. This makes AMBR useful as a candidate example of delayed / stair-step price rediscovery.

### 17.2 September 18 acceleration — HYPOTHESIS

A working hypothesis is that the September 18 acceleration was amplified by the convergence of: (1) reduced incremental rate / inflation anxiety and broader risk-on recovery, (2) a sharp BTCUSD move and associated inflow into crypto-linked equities, (3) renewed AI / growth demand, and (4) AMBR's own company-specific AI-agent / earnings repricing already in progress.

Classification: **HYPOTHESIS — causal attribution unconfirmed; verification value high.**

This should not be stored as an observed Fact. It is stronger than UNKNOWN because the mechanism is specific, coherent, and falsifiable, and there is contemporaneous cross-market evidence consistent with it. It remains below confirmed interpretation because the available evidence does not establish how much of AMBR's September 18 buying came from crypto flow, AI / growth flow, macro risk-on flow, or company-specific repricing.

Candidate causal chain:

    company-specific repricing already active
      + BTCUSD / crypto-equity risk-on flow
      + AI / growth risk-on flow
      + macro anxiety easing at the margin
      -> theme convergence around AMBR
      -> participation / liquidity expansion
      -> September 18 price-discovery acceleration

### 17.3 Why HYPOTHESIS rather than UNKNOWN

Use HYPOTHESIS when a causal explanation has enough supporting observations to justify an explicit test and can be disproved by contrary data. Use UNKNOWN when the causal mechanism itself is not sufficiently specified or evidence is too sparse to define a meaningful falsification test. AMBR currently satisfies the first condition.

### 17.4 Required validation

- Align AMBR, BTCUSD, major crypto-equity proxies such as COIN / MSTR, and a broad AI / growth proxy on one- to five-minute bars for September 18.
- Test lead / lag around major return and volume bursts rather than relying on same-session correlation.
- Decompose AMBR returns against broad-market, growth, and crypto factors and inspect the residual repricing.
- Check whether AMBR repeatedly follows the proposed external drivers, or whether AMBR moves first.
- Promote, narrow, or reject the hypothesis only after at least one explicit disconfirmation test.

Possible status outcomes:

- SUPPORTED: repeated external-driver lead plus subsequent AMBR response, while a material company-specific residual remains.
- PARTIALLY_SUPPORTED: common risk-on timing exists but AMBR's company-specific repricing explains most of the move.
- REJECTED: AMBR systematically leads the proposed drivers or no repeatable lead / lag relationship is found.

### 17.5 Reusable OrderScope lesson

AMBR adds a theme-convergence case to the price-rediscovery framework. The source-grounded corporate, macro, sector-theme, and cross-asset observations should remain separate from the analyst-generated causal hypothesis. A future OrderScope interpretation object can link those Facts into a THEME_CONVERGENCE_HYPOTHESIS without promoting the causal edge itself to Fact.
