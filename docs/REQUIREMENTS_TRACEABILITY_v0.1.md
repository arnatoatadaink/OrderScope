# Stock Monitoring Fact v0.1 — Requirements Traceability Map

Status: derived, non-normative traceability artifact

## 1. Purpose

This document assigns stable requirement IDs to requirements already defined by the four Code of Truth v0.1 documents.

It does **not** create new requirements and does not override the source specifications. If this map disagrees with a Code of Truth document, the Code of Truth document is authoritative.

Authoritative source documents:

- `stock_monitoring_v0.1_spec.md` — parent specification
- `stock_monitoring_v0.1_universe_spec.md` — Universe reference specification
- `stock_monitoring_v0.1_regime_spec.md` — Regime reference specification
- `stock_monitoring_v0.1_provider_research.md` — Provider reference specification

Mermaid usage follows `MERMAID_CONVENTIONS.md`.

## 2. ID convention

Format:

`REQ-<DOMAIN>-<NNN>`

Domains:

| Domain | Meaning |
|---|---|
| SYS | system purpose / scope / temporal rules |
| UNI | Universe / classification / instrument cadence |
| MD | market-data acquisition and normalization |
| CAL | market session / calendar handling |
| FFT | frequency-domain market analysis |
| INT | corporate intelligence / event extraction |
| SRC | source tiers and official signals |
| SEC | SEC filings / fundamentals |
| REG | Regime engine |
| RET | raw-news retention |
| PROV | provider boundary / provider contracts |
| FACT | Fact model / persistence semantics |
| VER | v0.1 acceptance / verification requirement |

IDs describe requirement identity, not implementation ownership. A later architecture may satisfy one requirement with multiple components or one component may satisfy multiple requirements.

## 3. Requirement map

### 3.1 System scope

| ID | Requirement summary | Source |
|---|---|---|
| REQ-SYS-001 | Monitor the U.S. market continuously for changes in market, corporate, policy, filing, earnings, Regime, FFT and correlation information. | Parent §1 |
| REQ-SYS-002 | Record what changed as Fact; price prediction is not the primary purpose. | Parent §1 |
| REQ-SYS-003 | Support U.S.-listed equities and ETFs; Country Proxy instruments must be U.S.-listed ETFs. | Parent §2 |
| REQ-SYS-004 | Keep News / SEC / Official Signal acquisition event-driven. | Parent §2 |
| REQ-SYS-005 | Normalize internal timestamps to UTC, classify market time in `America/New_York`, and display in `Asia/Tokyo`. | Parent §4 |

### 3.2 Universe and classification

| ID | Requirement summary | Source |
|---|---|---|
| REQ-UNI-001 | Load an initially fixed Universe of approximately 100 instruments. | Parent §2; Universe §1, §7 |
| REQ-UNI-002 | Separate Universe membership from price acquisition cadence. | Universe §1 |
| REQ-UNI-003 | Support many-to-many Instrument ↔ Classification relationships. | Parent §3 |
| REQ-UNI-004 | Allow a company to belong to multiple Theme / Character / Regime classifications simultaneously. | Parent §3; Universe §1 |
| REQ-UNI-005 | Track company tickers for Regime by default; ETFs / Country Proxies are not Regime-tracked by default. | Universe §1 |
| REQ-UNI-006 | Use Tier A instruments at 1-minute price cadence. | Universe §2 |
| REQ-UNI-007 | Use Tier B instruments at 15-minute price cadence. | Universe §3 |
| REQ-UNI-008 | Use Tier C instruments at daily price cadence. | Universe §4 |
| REQ-UNI-009 | Do not automatically add instruments to the v0.1 Universe. | Universe §7 |
| REQ-UNI-010 | Instrument configuration must be capable of representing asset type, cadence, themes/roles and Regime-tracking behavior. | Universe §8 |

### 3.3 Market data

| ID | Requirement summary | Source |
|---|---|---|
| REQ-MD-001 | Access market data through `MarketDataProvider`; Core must not depend on provider-specific schemas. | Parent §4, §13 |
| REQ-MD-002 | Support OHLCV retrieval for U.S. stocks / ETFs. | Parent §4; Provider §9 |
| REQ-MD-003 | Support 1m / 15m / 1d bars. | Parent §2; Provider §9 |
| REQ-MD-004 | Support historical bars and latest bars. | Provider §9 |
| REQ-MD-005 | Support market-calendar retrieval through the market-data boundary. | Parent §4; Provider §9 |
| REQ-MD-006 | Normalize provider market timestamps to UTC before Core processing. | Parent §4; Provider §9 |
| REQ-MD-007 | Treat Alpaca as the v0.1 initial market-data candidate without coupling Core to Alpaca. | Parent §4; Provider §3 |

### 3.4 Session and calendar

| ID | Requirement summary | Source |
|---|---|---|
| REQ-CAL-001 | Distinguish Regular, Premarket and After-hours sessions. | Parent §6 |
| REQ-CAL-002 | Do not artificially interpolate market holidays into intraday time series. | Parent §6 |
| REQ-CAL-003 | Preserve Weekend / Holiday gaps as information for Daily-or-longer analysis. | Parent §6 |
| REQ-CAL-004 | Store only actual trading time for shortened sessions. | Parent §6 |
| REQ-CAL-005 | Separate shortened-session observations from normal-session baselines. | Parent §6 |

### 3.5 FFT / market analysis

| ID | Requirement summary | Source |
|---|---|---|
| REQ-FFT-001 | Provide analysis windows of 1, 7, 20 and 60 trading days. | Parent §5 |
| REQ-FFT-002 | Use log return as the primary FFT input. | Parent §5 |
| REQ-FFT-003 | Permit close, volatility and volume as auxiliary FFT-related inputs/features. | Parent §5 |
| REQ-FFT-004 | Apply the defined preprocessing chain: missing check → interval validation → log return → mean removal → optional detrend → Hann window → FFT → power spectrum. | Parent §5 |
| REQ-FFT-005 | Define Low / Mid / High frequency bands by period/frequency rather than price-change percentage. | Parent §5 |
| REQ-FFT-006 | Treat values such as 3% / 5% as amplitude-side features, not frequency-band boundaries. | Parent §5 |

### 3.6 Corporate intelligence

| ID | Requirement summary | Source |
|---|---|---|
| REQ-INT-001 | Ingest News, SEC Filing, Official Signal, Earnings, Segment Revenue, Major Contract, CAPEX, Financing, Partnership and M&A information. | Parent §7 |
| REQ-INT-002 | Convert external information through Event Extraction into Corporate Fact before Regime / Classification processing. | Parent §7 |
| REQ-INT-003 | Keep spoken/announced policy and implemented policy as separate Facts. | Parent §8 |

### 3.7 Source hierarchy and official signals

| ID | Requirement summary | Source |
|---|---|---|
| REQ-SRC-001 | Represent source tiers from Tier 0 official/government sources through Tier 5 general social sources. | Parent §8 |
| REQ-SRC-002 | Include the specified U.S. executive, Treasury, Federal Reserve, SEC and relevant Federal Agency official sources in Tier 0 monitoring. | Parent §8; Provider §7 |
| REQ-SRC-003 | Monitor official X accounts for Tier 0 actors/agencies when such official accounts exist. | Parent §8; Provider §7 |
| REQ-SRC-004 | Preserve original timestamp and a permanent source reference for Official Signal records. | Provider §9 |
| REQ-SRC-005 | Represent update/delete information for Official Signals when the upstream provider makes it available. | Provider §9 |

### 3.8 SEC and fundamentals

| ID | Requirement summary | Source |
|---|---|---|
| REQ-SEC-001 | Monitor SEC EDGAR directly for new filings. | Parent §9; Provider §6 |
| REQ-SEC-002 | Cover at least 8-K, 10-Q, 10-K, S-1, S-3, 424B*, DEF 14A, 13D, 13G and Form 4. | Parent §9 |
| REQ-SEC-003 | Detect filings by CIK and preserve accession number, form type, filing document and XBRL facts. | Provider §9 |
| REQ-SEC-004 | Extract quarterly segment revenue through a Fundamental Provider boundary. | Parent §9; Provider §9 |
| REQ-SEC-005 | Attempt segment fundamentals in the order Company Facts → XBRL Dimension → Filing Fallback. | Parent §9; Provider §6 |
| REQ-SEC-006 | Preserve fiscal period, source filing and segment identity/history for quarterly segment revenue. | Provider §9 |

### 3.9 Regime engine

| ID | Requirement summary | Source |
|---|---|---|
| REQ-REG-001 | Allow multiple Regimes to coexist for one company. | Parent §10; Regime §1 |
| REQ-REG-002 | Support `PROVISIONAL` and `REVENUE_BASED` Strength types. | Regime §2 |
| REQ-REG-003 | Assign Provisional strength 0.25 for emerging evidence, 0.50 for active preparation, and 0.75 for commercial evidence. | Parent §10; Regime §3 |
| REQ-REG-004 | Do not simply sum Evidence; base Provisional strength primarily on the strongest applicable Evidence. | Regime §3 |
| REQ-REG-005 | Transition to Revenue-based strength when individual quarterly segment revenue can be obtained. | Parent §10; Regime §4 |
| REQ-REG-006 | Compute `MA4_i` as the mean of the latest four quarterly revenues for segment `i`. | Regime §4 |
| REQ-REG-007 | Compute Revenue Strength as `MA4_i / MAX(MA4_all_segments)`. | Parent §10; Regime §4 |
| REQ-REG-008 | Compute Revenue Share separately as `MA4_i / SUM(MA4_all_segments)`. | Parent §10; Regime §4 |
| REQ-REG-009 | Preserve Latest Quarter Revenue separately for rapid-change detection. | Regime §4 |
| REQ-REG-010 | Store Evidence Confidence independently of Strength. | Regime §5 |
| REQ-REG-011 | Support statuses EMERGING, ACTIVE, COMMERCIAL, REVENUE_BASED, INACTIVE, REACTIVATING and STALE. | Regime §6 |
| REQ-REG-012 | Apply time decay only to Provisional Regimes. | Parent §11; Regime §7 |
| REQ-REG-013 | When no Supporting Evidence exists for one year, apply `strength × 0.5`; one year is fixed for v0.1. | Parent §11; Regime §7 |
| REQ-REG-014 | Do not time-decay Revenue-based Regimes. | Parent §11; Regime §7 |
| REQ-REG-015 | Preserve known contract `effective_from` / `effective_until` and do not decay solely because news is absent while the contract is being performed. | Regime §8 |
| REQ-REG-016 | For unknown contract duration, prioritize Quarterly Earnings, SEC, Segment Revenue and Management Disclosure for state evaluation. | Parent §11; Regime §8 |
| REQ-REG-017 | Do not immediately decay a contract solely because revenue has not yet been confirmed. | Regime §8 |
| REQ-REG-018 | Represent ongoing construction/conversion/preparation before revenue as `CONTRACT_AWAITING_REVENUE`. | Regime §8 |
| REQ-REG-019 | Set status to INACTIVE on explicit negative evidence such as cancellation, termination, withdrawal or abandonment. | Parent §11; Regime §9 |
| REQ-REG-020 | Never delete past Strength / Evidence when a Regime becomes inactive. | Regime §9 |
| REQ-REG-021 | Set an inactive/declining Regime to REACTIVATING when the specified positive evidence appears. | Parent §11; Regime §10 |
| REQ-REG-022 | Do not rewrite Revenue Strength from news alone. | Regime §10 |
| REQ-REG-023 | Move REACTIVATING toward ACTIVE / REVENUE_BASED only after revenue recovery is confirmed in a subsequent earnings result when revenue confirmation is required. | Parent §11; Regime §10 |
| REQ-REG-024 | Represent Regime change as Strength delta and store it as `COMPANY_REGIME_CHANGE` Fact. | Regime §11 |
| REQ-REG-025 | Preserve strategic relationships that are not represented by revenue as Fact / Relationship, without quantitatively defining `strategic_strength` in v0.1. | Parent §11; Regime §2, §12 |
| REQ-REG-026 | Preserve Regime history rather than overwriting previous states. | Regime §13 |

### 3.10 News retention

| ID | Requirement summary | Source |
|---|---|---|
| REQ-RET-001 | Delete successfully processed raw news body text after Fact extraction under normal conditions. | Parent §12 |
| REQ-RET-002 | Persist headline, publisher, URL, published/retrieved timestamps, ticker, event type, extracted facts and source hash. | Parent §12 |
| REQ-RET-003 | Retain raw body temporarily for extraction failure, ambiguity, conflicting information, pending verification or important Regime Evidence. | Parent §12 |
| REQ-RET-004 | Limit exceptional raw-body retention to a maximum of 30 days. | Parent §12 |

### 3.11 Provider boundary

| ID | Requirement summary | Source |
|---|---|---|
| REQ-PROV-001 | Core must depend only on provider contracts, not vendor-specific API schemas. | Parent §13; Provider §1 |
| REQ-PROV-002 | Define provider boundaries for Market Data, News, Filing, Fundamental and Official Signal. | Parent §13; Provider §1 |
| REQ-PROV-003 | News Provider must support ticker-filtered incremental retrieval and expose publication metadata, stable article ID and temporary body access. | Provider §9 |
| REQ-PROV-004 | Filing Provider must support CIK-based detection, accession, form, filing document and XBRL facts. | Provider §9 |
| REQ-PROV-005 | Fundamental Provider must provide quarterly segment revenue, fiscal period, source filing and segment identity/history. | Provider §9 |
| REQ-PROV-006 | Official Signal Provider must support incremental retrieval by source/account with original timestamp and durable source reference. | Provider §9 |
| REQ-PROV-007 | Provider pricing and commercial plan assumptions must be revalidated at contracting time. | Provider §1 |

### 3.12 Fact model

| ID | Requirement summary | Source |
|---|---|---|
| REQ-FACT-001 | Keep Fact, Derived Metric, Interpretation and Prediction distinct. | Parent §14 |
| REQ-FACT-002 | Support the v0.1 event types listed in the parent specification, including corporate, policy, Regime, correlation and reactivation events. | Parent §14 |
| REQ-FACT-003 | Persist Market, Corporate and Policy Facts to a common Store. | Parent §15 |

## 4. Acceptance / verification traceability

The parent specification's Definition of Done is represented as explicit verification IDs. These IDs describe what must be demonstrated; they do not prescribe a test framework.

| ID | Verification target | Primary requirement links |
|---|---|---|
| REQ-VER-001 | Approximately 100 instruments can be loaded from configuration. | REQ-UNI-001, REQ-UNI-010 |
| REQ-VER-002 | Market data is acquired according to per-instrument cadence. | REQ-UNI-006..008, REQ-MD-003 |
| REQ-VER-003 | Market-data provider can be replaced without changing Core domain behavior. | REQ-MD-001, REQ-PROV-001 |
| REQ-VER-004 | New SEC filings are detected. | REQ-SEC-001..003 |
| REQ-VER-005 | Segment revenue is extracted. | REQ-SEC-004..006 |
| REQ-VER-006 | MA4 Revenue Strength is calculated. | REQ-REG-006, REQ-REG-007 |
| REQ-VER-007 | Provisional Regime can be created from evidence. | REQ-REG-002..004 |
| REQ-VER-008 | One year without Supporting Evidence causes the v0.1 `×0.5` decay. | REQ-REG-012..014 |
| REQ-VER-009 | Negative Evidence causes INACTIVE state. | REQ-REG-019, REQ-REG-020 |
| REQ-VER-010 | Reactivation Signal can be generated and tracked. | REQ-REG-021..023 |
| REQ-VER-011 | Raw news body is deleted after successful Fact extraction and exception retention is bounded. | REQ-RET-001..004 |
| REQ-VER-012 | FFT processing is available for 1D / 7D / 20D / 60D windows. | REQ-FFT-001..006 |
| REQ-VER-013 | Market / Corporate / Policy Facts are stored in the common Store. | REQ-FACT-003 |
| REQ-VER-014 | Regime history can be reconstructed chronologically. | REQ-REG-020, REQ-REG-026 |

## 5. Cross-layer traceability model

```mermaid
flowchart LR
    COT[Code of Truth v0.1\n4 normative documents]
    REQ[Requirement IDs\nthis document]
    HLD[High-level design IDs\nHLD-*]
    DLD[Detailed design IDs\nDLD-*]
    VER[Verification\nREQ-VER-* / tests]

    COT -->|derived without changing semantics| REQ
    REQ -->|realized by| HLD
    HLD -->|implemented by| DLD
    DLD -->|verified by| VER
    VER -->|demonstrates| REQ
```

The next design layer should reference requirement IDs rather than relying on document proximity or repeated prose.

## 6. Known unresolved design questions

These are not silently resolved by this traceability map:

- Exact Low / Mid / High FFT period boundaries are not fixed in v0.1.
- Exact Core storage technology and schema are not fixed.
- Exact event-extraction model / pipeline is not fixed.
- Exact polling/streaming scheduling implementation is not fixed.
- Exact provider selected beyond the documented v0.1 candidates/adoptions is not expanded here.
- Exact handling of provider failure, retries, rate limiting and backfill is not defined by the current Code of Truth.
- Future Expected Realization Time / industry-specific decay belongs to v0.2+ research and is not a v0.1 requirement.
- `strategic_strength` remains intentionally non-quantified in v0.1.

These items should remain explicit design questions until a normative decision is made or a design can be selected without altering observable requirements.

## 7. Change policy

When Code of Truth v0.1 changes:

1. update the affected requirement summary/source mapping,
2. preserve an existing requirement ID when its semantic identity remains the same,
3. create a new ID when a genuinely new requirement is introduced,
4. do not reuse retired IDs for a different semantic requirement,
5. update downstream HLD / DLD / verification links in the same change when practical.

This document may be regenerated or reorganized, but stable IDs should be treated as durable traceability handles once implementation references them.
