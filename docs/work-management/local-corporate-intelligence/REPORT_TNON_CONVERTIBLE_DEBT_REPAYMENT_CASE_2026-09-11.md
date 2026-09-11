# TNON Convertible Debt Repayment Case Report

Status: **Research / design input — not normative specification**
Date: 2026-09-11
Symbol: `TNON` / Tenon Medical, Inc.
Related backlog: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`

## 1. Purpose

This report reconstructs the Tenon Medical (`TNON`) convertible-debt lifecycle that culminated in the September 9, 2026 early repayment announcement. The purpose is to identify which parts could have been detected before the price move, which sources provide actionable timing, and which reusable Fact / Derived Metric / Interpretation concepts should be considered for OrderScope.

This report intentionally separates observed Facts from derived interpretations and predictions.

## 2. Executive summary

The TNON event was not merely a positive news headline. It was the resolution of a previously observable capital-structure risk.

The chain was:

1. March 11, 2026: issuance of approximately `$5.16M` aggregate principal of 20% OID senior convertible promissory notes.
2. The notes were due September 11, 2026, optionally extendable to December 11, 2026.
3. Conversion became available after the six-month anniversary at 80% of a reference VWAP, creating discounted-conversion / dilution overhang.
4. August 27-31, 2026: TNON raised approximately `$3.0M` in a private placement; the filing explicitly stated that proceeds were intended in part for repayment of certain debt.
5. September 9, 2026 at 08:30 ET: ACCESS Newswire published the company's announcement that the notes had been repaid in full, ahead of maturity.
6. The SEC 8-K subsequently confirmed the event and attached the same press release.

The important design conclusion is that OrderScope could have placed TNON into an elevated capital-event attention state before September 9 by combining maturity proximity, conversion eligibility, outstanding discounted convertible debt, and a new financing whose stated use included debt repayment.

## 3. Observed event timeline

| Date / time | Observed event | Classification |
|---|---|---|
| 2026-03-11 | Senior convertible notes issued; aggregate principal about `$5.16M` | Capital instrument creation |
| 2026-03 onward | 20% OID structure; maturity 2026-09-11, optional extension to 2026-12-11 | Contract terms |
| Six-month anniversary | Conversion eligibility begins at 80% of the prior three trading-day VWAP, subject to note terms | Dilution-risk activation window |
| 2026-08-27 | Securities purchase agreement for August private placement | Financing announced |
| 2026-08-31 | Private placement closed; gross proceeds about `$2,999,405`; stated use included repayment of certain debt | Financing closed / repayment capacity increased |
| 2026-09-09 08:30 ET | ACCESS Newswire: full early repayment of outstanding convertible notes | Discovery / company release |
| 2026-09-09 | SEC 8-K Item 8.01 confirms full repayment ahead of 2026-09-11 maturity | Tier-1 confirmation |

## 4. Primary-source facts

### 4.1 Convertible-note terms

The March filing states that the notes had a September 11, 2026 maturity date, extendable at the company's option to December 11, 2026. After the six-month anniversary, the notes were convertible at 80% of the VWAP for the prior three trading days, subject to adjustment. Early prepayment was at 102.5% of principal, and the company was required to prepay an amount equal to 15% of net proceeds from securities financings.

Source:
- SEC: https://www.sec.gov/Archives/edgar/data/1560293/000121390026093926/ea0303435-8ka1_tenon.htm

### 4.2 August 2026 private placement

The August 31 8-K states that the company closed a private placement for gross proceeds of approximately `$2,999,404.59`. It issued pre-funded warrants for up to 597,610 shares and Series A warrants for up to 1,058,517 shares, with the Series A exercise price at `$5.02`. The company explicitly stated that net proceeds were intended for repayment of certain debt, working capital, and general corporate purposes.

Sources:
- SEC 8-K: https://www.sec.gov/Archives/edgar/data/1560293/000121390026095686/ea0303883-8k_tenon.htm
- SEC exhibit / closing release: https://www.sec.gov/Archives/edgar/data/1560293/000121390026095686/ea030388301ex99-2.htm

### 4.3 Full repayment

On September 9, TNON announced that it had repaid in full its outstanding original issue discount senior convertible promissory notes, originally issued with aggregate principal of approximately `$5.16M`, ahead of the September 11 maturity date. The release explicitly described elimination of the potential for conversion into common stock at a discount to market prices.

Sources:
- ACCESS Newswire, 2026-09-09 08:30 ET: https://www.accessnewswire.com/newsroom/en/education/tenon-medical-announces-early-repayment-of-its-convertible-notes-1218400
- SEC 8-K: https://www.sec.gov/Archives/edgar/data/1560293/000121390026098232/ea0304884-8k_tenon.htm
- SEC Exhibit 99.1: https://www.sec.gov/Archives/edgar/data/1560293/000121390026098232/ea030488401ex99-1.htm

## 5. What was knowable before the announcement

The following items were observable Facts before September 9:

- a material convertible debt instrument existed;
- maturity was near;
- conversion eligibility was also near / beginning;
- conversion pricing was at a discount to a recent market VWAP;
- a new financing had closed eleven days before maturity;
- the stated use of the financing explicitly included repayment of certain debt.

Therefore OrderScope could reasonably create a high-priority **resolution window** without predicting a specific outcome.

A valid interpretation would be:

```text
DEBT_RESOLUTION_WINDOW
  instrument = senior_convertible_note
  maturity_distance_days <= 30
  discounted_conversion_risk = true
  recent_financing = true
  use_of_proceeds_contains_debt_repayment = true
```

This does **not** justify a Fact such as `FULL_REPAYMENT_EXPECTED=true`. Repayment, extension, refinancing, partial repayment, or conversion remained possible until confirmed.

## 6. Source and latency implications

The company release appeared on ACCESS Newswire at 08:30 ET. The SEC filing followed as the stronger confirmation source. The design implication is a two-layer model:

```text
Discovery source
  company IR / ACCESS / Business Wire / PR Newswire / GlobeNewswire
        ↓
Candidate event
        ↓
Tier-1 confirmation
  SEC / issuer filing / official notice
```

The SEC path remains suitable as the factual system of record, but relying on SEC alone can add latency for pre-market catalysts.

## 7. Proposed reusable Fact model

Candidate raw / normalized Facts:

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

Candidate derived / interpretation concepts:

```text
DILUTION_OVERHANG_CREATED
DILUTION_OVERHANG_REDUCED
CONVERTIBLE_NOTE_DILUTION_OVERHANG_REMOVED
DEBT_RESOLUTION_WINDOW
CAPITAL_STRUCTURE_REGIME_CHANGE
```

`DILUTION_RISK_REMOVED` is too broad for TNON because the August financing itself introduced pre-funded and Series A warrant exposure. The correct interpretation is narrower: the convertible-note dilution overhang was removed while other potential dilution instruments remained.

## 8. Proposed state transition for the TNON case

```text
SENIOR_CONVERTIBLE_NOTE
ACTIVE
  ↓
MATURITY_NEAR + CONVERSION_WINDOW_NEAR
  ↓
RECENT_FINANCING / DEBT-REPAYMENT USE OF PROCEEDS
  ↓
DEBT_RESOLUTION_WINDOW = HIGH ATTENTION
  ↓
FULL_REPAYMENT CONFIRMED
  ↓
CONVERTIBLE_NOTE_DILUTION_OVERHANG_REMOVED
```

A higher-level interpretation may then record a capital-structure regime transition, while retaining warrant exposure separately.

## 9. Candidate attention rule

The following is a **planning heuristic, not an empirically validated model**:

```text
+2 maturity <= 30 days
+2 conversion eligibility <= 30 days
+2 discounted conversion mechanism exists
+2 stated use of recent financing includes debt repayment
+1 new financing closed
+1 instrument size is material relative to company capital structure
```

A threshold may promote the issuer to `CAPITAL_EVENT_ATTENTION=HIGH`. Threshold values require historical backtesting before becoming normative.

## 10. Required safeguards

1. Do not infer that financing proceeds were actually used for a specific debt until an explicit source confirms it.
2. Do not equate original aggregate principal with final cash repayment amount unless confirmed.
3. Do not interpret removal of one convertible instrument as removal of all dilution risk.
4. Preserve event time, available time, accepted time, source, accession / document identity, and instrument identity.
5. Keep Fact, Derived Metric, Interpretation, and Prediction boundaries explicit.

## 11. Design implications for OrderScope

The reusable capability is broader than TNON:

- monitor outstanding capital instruments as stateful objects rather than isolated news items;
- schedule maturity / conversion-window attention from disclosed contractual dates;
- connect new financings to existing debt instruments without asserting repayment until confirmed;
- treat early repayment, conversion, extension, refinancing, and maturity as state transitions;
- combine newswire discovery with SEC confirmation;
- pass confirmed capital-structure events to the market-reaction / price-discovery layer.

## 12. WBS-unreflected work linkage

This report is the source document for the proposed backlog work covering:

- capital-instrument lifecycle and maturity / conversion-window monitoring;
- financing-to-debt-resolution attention logic;
- dilution-overhang state and capital-structure regime transitions;
- TNON fixture / Canary acceptance case.

See the `Capital structure / catalyst and price-discovery expansion` section added to `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`.

## 13. Unresolved items

- Exact final cash amount paid to retire the notes has not been established from the cited September 9 release alone.
- The contribution of the August financing to the eventual repayment is not proven solely by the stated use-of-proceeds language.
- Historical precision / recall of the proposed attention heuristic is unknown.
- Newswire provider licensing, API terms, cost, and retention constraints require separate provider review.
