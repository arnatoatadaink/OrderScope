# OrderScope — N1-001 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `N1-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `I0-005`, Accepted `E0-001`

## 1. Local acceptance carried into this cycle

`N0-004` was promoted to Accepted from user-reported local evidence:

```text
focused N0-004 tests -> 8 passed
full pytest suite     -> 287 passed
git diff --check      -> clean / no findings
```

This completes the N0 News acquisition lane at the contract/fixture boundary.

## 2. WBS completion boundary

N1-001 freezes a versioned event taxonomy for deterministic News Fact extraction. The WBS explicitly calls out contract, CAPEX, financing, M&A, regulation, earnings, partnership, and major-customer events. The v0.1 taxonomy also includes product/service, supply-chain, leadership, and legal events so common corporate-news assertions have a bounded destination without using an untyped catch-all.

The taxonomy is semantic vocabulary only. It does not define extraction regexes, sentiment, impact scores, Regime strength, confidence thresholds, or prediction meaning.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/event_taxonomy.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_event_taxonomy.py`

## 4. Versioned taxonomy

Version:

```text
news-event-taxonomy-v0.1
```

Frozen event types:

1. `contract`
2. `capex`
3. `financing`
4. `m_and_a`
5. `regulation`
6. `earnings`
7. `partnership`
8. `major_customer`
9. `product_service`
10. `supply_chain`
11. `leadership`
12. `legal`

Every enum member must have exactly one immutable `EventTaxonomyEntry` containing a bounded definition and boundary note. Registry order is deterministic.

## 5. One assertion / one event type

A single explicit source assertion maps to one `NewsEventType`.

If one article explicitly establishes multiple independent events, for example:

```text
company raises debt financing
company commits proceeds to a new fabrication facility
```

N1-002 should emit separate financing and CAPEX Fact candidates rather than one multi-label Fact.

This preserves the accepted Fact Store rule that a Fact is one typed source-grounded assertion and prevents event labels from becoming an ambiguous tag bag.

## 6. Important taxonomy boundaries

### Contract vs partnership

- binding/awarded commercial or government agreement -> `contract`
- non-binding collaboration, alliance, integration, joint development -> `partnership`
- co-mention alone -> neither

### CAPEX vs financing

- capital spending commitment/action -> `capex`
- debt/equity/convertible/credit raising or refinancing -> `financing`
- financing does not imply CAPEX merely because management may later spend the proceeds

### M&A vs partnership

- ownership/control/business-asset transaction -> `m_and_a`
- strategic cooperation without ownership/control -> `partnership`

### Regulation vs legal

- government/regulator rule, approval, license, investigation, enforcement -> `regulation`
- private/non-regulatory lawsuit, judgment, settlement, formal legal proceeding -> `legal`

### Major customer

A named/material customer relationship requires explicit source linkage. Provider ticker tags, analyst speculation, or unnamed demand commentary cannot establish a major-customer event.

## 7. Earnings boundary

`earnings` is a News event category, not a replacement for the Accepted E0 domain contract.

N1 must not redefine:

- GAAP vs non-GAAP;
- fiscal-period identity;
- scheduled vs actual release time;
- earnings result metrics;
- source/evidence priority.

When a News extraction is promoted to detailed earnings Facts, the E0 contract remains authoritative.

## 8. Fact / Interpretation separation

The taxonomy intentionally does not include categories such as:

- bullish / bearish;
- positive / negative;
- strategic importance;
- high impact;
- regime change;
- expected price move.

Those are Interpretation/DerivedMetric/Prediction concerns and cannot be encoded as observed event types.

## 9. Focused fixtures encoded

The focused test module contains 10 tests covering:

1. frozen taxonomy version and required WBS categories;
2. every enum value defined exactly once;
3. deterministic immutable registry order;
4. contract/partnership boundary;
5. CAPEX/financing separation;
6. earnings delegation to E0 semantics;
7. regulation/legal enforcement boundary;
8. provider ticker tags cannot establish major-customer identity;
9. invalid/blank taxonomy entries rejected;
10. lookup requires the versioned enum rather than arbitrary strings.

## 10. Local verification evidence

User-reported local verification on 2026-09-09:

```text
focused N1-001 tests -> 10 passed
full pytest suite     -> 297 passed
git diff --check      -> clean / no findings
```

The acceptance evidence confirms the frozen taxonomy and its boundary fixtures against the current full local regression suite.

## 11. Explicit non-scope

N1-001 does not yet:

- classify article text;
- define regex/pattern extraction;
- consume temporary bodies;
- generate Facts or Evidence;
- set extraction confidence;
- resolve contradictions;
- choose or run an LLM;
- assign sentiment/impact/Regime labels.

N1-002 owns deterministic headline/metadata extraction. N1-003 owns body extraction provenance and evidence-span boundaries.

## 12. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Ready (N0-003 and N1-001 Accepted)
N1-003 waits for N1-002 (N0-004 already Accepted)
N1-004 waits for N1-003
N1-005 waits for N1-004
```

## 13. Next action

Proceed to `N1-002 — deterministic extraction baseline`. The implementation must use headline/metadata and explicit source language only, produce versioned Fact candidates with reciprocal Evidence, and leave absent amounts, counterparties, dates, or event kinds unknown rather than inferred.
