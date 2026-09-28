# WBS / CP Unreflected Backlog

This document records research and implementation candidates that have been identified but are not yet assigned to the formal OrderScope WBS/CP.

## UWBS-VALUATION-001 — Sector / Company Valuation Baseline

- Status: Unreflected / research proposal
- Added: 2026-09-28
- Priority market: United States
- Secondary market: Japan
- Report: `docs/reports/VALUATION_BASELINE_SECTOR_MULTIPLES_REPORT_2026-09-28.md`

### Goal

Establish market, sector/industry and company historical valuation baselines from P/B, P/E, forward P/E, EV/EBITDA, EV/Sales, ROE, ROIC and related metrics. Use relative valuation and historical distributions to improve catalyst interpretation, sector-move decomposition and price-rediscovery analysis.

### Proposed scope before formal CP assignment

- US sector/industry taxonomy and ticker mapping.
- US point-in-time fundamentals source benchmark and normalization.
- Internal historical sector/industry multiple distributions.
- Company historical premium/discount versus sector/industry.
- Relative P/B, relative P/E, percentiles and Z-scores.
- Sector-specific primary valuation metric selection.
- Low/Base/High valuation reference bands.
- Catalyst pre/post valuation snapshots.
- Backtest against known catalyst / price-rediscovery cases.
- Japan adapter using the same normalized schema with Japan-specific sources.

### Source policy

US primary implementation:

- SEC EDGAR/XBRL Company Facts for authoritative raw issuer fundamentals.
- Existing OrderScope market-data provider layer for price/market observations.
- NYU Stern / Damodaran industry datasets as research and aggregate-validation references.

Japan secondary implementation:

- JPX industry P/E/P/B statistics for authoritative sector aggregate validation.
- J-Quants and/or EDINET to be benchmarked for company-level point-in-time fundamentals and filing history.

### Planning gate

Do not assign formal CP numbers until the following are decided:

1. canonical US taxonomy;
2. point-in-time historical fundamentals provider/retention strategy;
3. aggregation rules including negative earnings/equity and outliers;
4. initial history window;
5. valuation-band calibration/backtest acceptance criteria.
