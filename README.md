# OrderScope

OrderScope is the Code of Truth repository for the Stock Monitoring Fact project.

## Current baseline

- Specification: `docs/CODE_OF_TRUTH_v0.1.md`
- Status: v0.1 baseline
- Target market: U.S. equities / U.S.-listed proxies
- Primary market data provider for PoC: Alpaca

## Principle

The system separates observed facts, derived metrics, interpretation, and prediction. Market data and derived artifacts are stored behind provider-independent contracts so that the data source can evolve without changing the analytical model.

## v0.1 implementation order

1. Freeze the exact initial Universe manifest (~100 tickers already selected by project decision).
2. Implement provider-independent bar ingestion with Alpaca as the first adapter.
3. Persist raw and normalized bars in UTC, with New York market-session classification.
4. Implement daily features and FFT/frequency features for 1D / 7D / 20D / 60D windows.
5. Add Fact / Derived Metric / Interpretation / Prediction separation to stored outputs.
6. Implement Regime evidence and decay rules.
7. Add tests for holidays, shortened sessions, gaps, and Extended Hours boundaries.

See `docs/CODE_OF_TRUTH_v0.1.md` for the normative specification.
