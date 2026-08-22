# OrderScope Code of Truth v0.1

Status: **Baseline / fixed for implementation**

This document is the normative v0.1 specification for the Stock Monitoring Fact project. Items marked **Unresolved** are intentionally not inferred or completed.

## 1. Scope

OrderScope monitors U.S. equities and U.S.-listed proxies and records market observations as facts before applying interpretation or prediction.

The v0.1 goal is not autonomous trading. The goal is to establish a reproducible observation, normalization, feature, and regime-evidence pipeline that can later support higher-level analysis.

## 2. Information layers

Every stored analytical output MUST identify one of the following layers:

1. **Fact** — directly observed or externally reported information.
2. **Derived Metric** — deterministic transformation of facts, such as returns, realized volatility, frequency-domain power, or gap metrics.
3. **Interpretation** — a model or rule-based reading of facts/metrics.
4. **Prediction** — forward-looking estimate or scenario.

Interpretation and Prediction MUST NOT overwrite or masquerade as Fact.

## 3. Initial Universe

- The initial Universe is fixed at approximately 100 U.S. equities / U.S.-listed proxies selected during v0.1 design.
- Universe membership is configuration, not an automatically changing discovery result.
- Real-time minute bars are not required for every symbol merely because it is in the Universe.
- Universe membership and data-acquisition cadence are separate concerns.

### Unresolved

The exact ~100 ticker manifest has not yet been transcribed into this repository. It MUST be added verbatim from the previously approved list; no ticker may be guessed or substituted.

## 4. Market-data provider strategy

Provider order for v0.1 and future migration:

1. **Alpaca** — first implementation / PoC source.
2. **Tiingo** — retained as a future alternative / secondary candidate.
3. **Massive** — candidate for full-scale / production operation when higher-grade coverage and operational requirements justify it.

The analytical pipeline MUST depend on a provider-independent contract rather than provider-native response structures.

## 5. Time and session normalization

- Persist timestamps in UTC.
- Preserve sufficient metadata to classify observations in `America/New_York` market time.
- Session classification MUST distinguish at least:
  - Regular Trading Hours (RTH)
  - Extended Hours (ETH), when available
  - market holiday
  - shortened / early-close session
  - non-trading gap / missing data
- Exchange calendars MUST be used rather than assuming every weekday is a full session.

Holiday and shortened-session boundaries MUST NOT be treated as ordinary missing bars.

## 6. Price-analysis windows

The baseline analytical windows are:

- **1D** — intraday / single-session behavior
- **7D** — short multi-session behavior
- **20D** — approximately one trading month
- **60D** — approximately one trading quarter

Longer windows may be introduced later, but they are not required by v0.1.

Daily and Weekly analysis may span overnight, weekend, and holiday boundaries. These boundaries are semantically meaningful gaps and MUST be represented explicitly rather than interpolated into fictitious continuous trading.

## 7. Frequency-domain analysis

FFT / spectral analysis is part of the derived-metric layer.

### Baseline requirements

- Run only on normalized and quality-checked price-derived series.
- Store the source window, sample cadence, preprocessing method, and normalization with every spectral result.
- Spectral bands are expressed by temporal frequency / period, not by price-return magnitude.
- A 3% or 5% price move MUST NOT be used as the Low/Mid/High FFT band boundary.

### Initial band interpretation

For a window containing enough samples, band labels SHOULD represent oscillation period relative to the analysis window:

- **High frequency** — short-lived oscillation / microstructure-scale movement
- **Mid frequency** — intermediate swing structure
- **Low frequency** — slow trend / broad cycle component

Exact cutoff frequencies are implementation parameters and MUST be versioned with the feature definition rather than hard-coded as universal market truths.

## 8. Price-move thresholds

Percentage thresholds such as 3% and 5% may be useful as separate event / amplitude features, but they are not FFT frequency boundaries.

If implemented, they belong to Derived Metrics or event detection and MUST state the reference basis, e.g. previous close, session open, rolling baseline, or local extremum.

## 9. Regime evidence model

A Regime represents a persistent explanatory state supported by evidence such as research, preparation, invention, contract activity, construction, sales realization, or related external developments.

Regime MUST NOT be treated as permanently valid merely because it was once established.

### v0.1 decay rule

- Initial baseline: **if no relevant update exists for one year, multiply the Regime evidence weight by 0.5**.
- This is the fixed v0.1 default and may be refined in a later version.

### Evidence that changes a Regime

- Supporting follow-up evidence can refresh or strengthen it.
- Explicitly contradictory evidence can weaken or invalidate it before the time-decay condition.
- A materially reversed external condition may terminate the Regime irrespective of age.

## 10. Domain-sensitive decay

A single decay duration is recognized as an approximation.

Future versions SHOULD adjust expected persistence using domain-specific elapsed-time costs, including examples such as:

- research / investigation
- preparation
- invention / development
- contract execution
- sales realization
- data-center or other physical construction

AI may compress research, design, software, and preparation timelines, while construction and other physical-capital activities can remain constrained by materially longer lead times.

These domain-specific duration models are **not fixed in v0.1**. The one-year `×0.5` rule remains the baseline until a later specification supersedes it.

## 11. Contracts with unknown duration

When a contract's duration or economic realization period is unknown:

- do not invent a contract-end date;
- begin judging decay / realization against evidence visible in financial results, especially revenue realization in company reporting;
- later contradictory or cancellation evidence can override this heuristic.

The mapping between a contract and reported revenue MUST retain provenance and uncertainty when the linkage is not explicit.

## 12. Provenance

Every Fact SHOULD retain, when applicable:

- source/provider
- source identifier or URL
- observation / publication timestamp
- ingestion timestamp
- symbol / entity identifiers
- raw value or normalized value
- normalization version
- confidence / quality flags where the source is ambiguous

Derived Metrics MUST reference the underlying facts or data range used to compute them.

## 13. Missing data and discontinuities

The pipeline MUST distinguish:

- expected market closure
- early close
- provider outage
- symbol halt
- unavailable ETH data
- genuine absence of observations

The implementation MUST NOT silently interpolate across these categories before analysis.

## 14. Provider-independent bar contract

The normalized bar representation SHOULD include at least:

- symbol
- timestamp UTC
- market-session classification
- open
- high
- low
- close
- volume
- source/provider
- source quality/status metadata

Provider-specific fields may be retained separately but MUST NOT be required by downstream core analysis.

## 15. v0.1 implementation sequence

1. Add the exact approved Universe manifest.
2. Implement a provider abstraction and Alpaca adapter.
3. Implement UTC normalization plus New York session/calendar classification.
4. Persist raw and normalized bars separately or with equivalent lineage.
5. Implement deterministic daily features.
6. Implement 1D / 7D / 20D / 60D spectral features.
7. Implement explicit Fact / Derived Metric / Interpretation / Prediction typing.
8. Implement Regime evidence records and the one-year `×0.5` baseline decay.
9. Add handling/tests for holidays, early closes, overnight/weekend gaps, missing data, and ETH boundaries.
10. Add contract-revenue realization evidence support without inventing unknown contract periods.

## 16. Acceptance criteria for v0.1

v0.1 implementation is considered conformant when:

- downstream analysis can switch market-data providers without changing its core bar contract;
- no holiday or early-close session is silently classified as ordinary missing data;
- FFT bands are based on temporal frequency rather than price percentage amplitude;
- all non-observed analytical values are typed as Derived Metric, Interpretation, or Prediction;
- Regime evidence decays by `×0.5` after one year without relevant update under the baseline rule;
- unknown contract duration is not fabricated;
- the exact approved Universe is stored as a version-controlled manifest.

## 17. Explicitly unresolved for post-v0.1 work

- Exact domain-specific Regime half-lives and duration-estimation model.
- Rules for quantifying supporting versus contradictory Regime evidence.
- Exact FFT Low/Mid/High cutoffs per sampling cadence/window.
- Exact real-time/minute-bar acquisition policy per Universe member.
- Production migration threshold from Alpaca to Tiingo or Massive.
- Exact linkage model between contract evidence and reported revenue.
- The exact approved ~100 ticker manifest, pending transcription into the repository.
