# OrderScope — WBS-Unreflected VIX / Cross-Asset Volatility Extension

Date: 2026-09-27
Status: **Active WBS-unreflected planning extension**
Source report: `REPORT_VIX_CROSS_ASSET_VOLATILITY_OBSERVATION_2026-09-27.md`
Canonical provisional-ID range: `UWBS-094..100`

## 1. Purpose

This extension records the VIX / cross-asset volatility observation work without silently modifying the accepted normative WBS.

It follows the same Fact / Derived Metric / Interpretation separation used by the existing OrderScope cross-market lanes. It does not authorize provider activation, trading, remote mutation, paid procurement or normative alert thresholds.

## 2. WBS-unreflected tasks

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Dependencies / related work | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-094 | Survey volatility data sources and define source-neutral volatility instrument contract | Provider contracts / A0 / I0 | Select permissible candidate sources for VIX spot, VIX futures, BTC 30d IV and MSTR options/IV; record methodology, timestamps, history, terms, redistribution, cost and rate limits; define stable instrument/observation identities independent of vendor | Existing provider/terms gates; I0 timestamp/provenance rules; UWBS-015/A0 provider-survey pattern | Ready for WBS design | Pending |
| UWBS-095 | Implement VIX spot + F1/F2 observation and term-structure metrics | A0 / Volatility / Market Data | Persist VIX spot and first/second futures contract observations with expiry/provenance/quality state; calculate F1-spot basis and F2-F1 spread; expose contango/backwardation/flat/unknown using configurable definitions | UWBS-094; MarketDataProvider boundary; historical storage; Fact/Derived Metric separation | Needs decomposition | Pending |
| UWBS-096 | Define VIX level/change/curve interpretation contract | A0 / Volatility Interpretation / Regime | Define inspectable candidate states using level, point change, percentage change and curve transition/persistence; support SUPPORT/PARTIAL/CONTRADICT/UNKNOWN; prohibit ETF price substitution and fixed fear thresholds before calibration | UWBS-095; Regime semantics; UWBS-011..015 macro context where relevant | Needs decomposition | Pending |
| UWBS-097 | Implement BTC 30-day implied-volatility acquisition and normalization | Crypto Market Structure / Provider adapter | Persist source-grounded BTC 30d implied volatility with method/source/timestamp/quality/revision semantics; do not silently substitute realized volatility; expose source-neutral `BTC_IV_30D` identity | UWBS-094; crypto source work UWBS-068..079; provider/terms gates | Needs decomposition | Pending |
| UWBS-098 | Implement MSTR 30-day option-implied-volatility acquisition and normalization | Equity Options / Company Volatility | Persist or reproducibly derive MSTR 30d IV from accepted option data/provider output; freeze interpolation/convention before production; leave IV rank, percentile, skew and longer tenors optional until separately specified | UWBS-094; instrument identity/provenance; option-data provider decision | Needs decomposition | Pending |
| UWBS-099 | Define MSTR/BTC IV differential and cross-asset volatility interpretation | Cross-Market / Crypto-Equity / Derived Metrics | Compute tested `mstr_btc_iv_ratio` and `mstr_btc_iv_spread`; distinguish broad crypto-volatility evidence from MSTR-specific premium hypotheses; preserve contradiction/unknown evidence and avoid causal or directional claims | UWBS-097/098; Fact/Derived Metric/Interpretation boundary; MSTR/BTC market data | Ready for WBS design | Pending |
| UWBS-100 | Historical calibration, Canary/false-positive and Worker/D1 capacity acceptance | Cross-Market QA / Operations | Replay calm/correction/shock/recovery and MSTR/BTC divergence/control windows; compare thresholds vs percentile/z-score methods; measure false positives/lead-lag and actual collection/storage budget; produce evidence for cadence/threshold/provider decisions without live activation | UWBS-096/099; accepted historical data; Worker/D1 instrumentation; local analysis stack | Needs decomposition | Pending |

## 3. Proposed CP candidate

```text
UWBS-094
  +-> UWBS-095 -> UWBS-096
  +-> UWBS-097
  +-> UWBS-098

UWBS-097 + UWBS-098
  -> UWBS-099

UWBS-096 + UWBS-099
  -> UWBS-100
```

The provider/contract survey is the common prerequisite. Equity-VIX and BTC/MSTR-IV branches can then proceed independently until they converge at historical calibration.

## 4. Acceptance principles

- Spot VIX, VIX futures and VIX-linked ETFs are distinct instruments.
- Contango/backwardation is derived from futures observations; roll-decay behavior is not represented by spot VIX alone.
- BTC IV and MSTR IV are volatility measures, not price-direction signals.
- `mstr_btc_iv_ratio` / spread are Derived Metrics, not proof of company-specific fear.
- Missing/stale data must remain visible.
- No fixed numerical alert threshold is normative before UWBS-100 calibration.
- Provider licensing/cost is unresolved until UWBS-094.

## 5. Relationship to existing lanes

- Reuse A0 / macro Fact and Interpretation boundaries rather than creating a second cross-market framework.
- Reuse canonical crypto-market-structure lane `UWBS-068..079` where BTC source/time-window semantics overlap.
- Keep oil / Risk-On lane `UWBS-080..086` independent; volatility can later become evidence for cross-asset regime validation without being made a causal shortcut.
- MSTR option-IV work is company/equity-specific and must remain separable from BTC-wide volatility.

## 6. Non-authorization statement

This planning extension does not authorize live-provider activation, paid procurement, Worker/Cron mutation, remote D1 mutation, VIX/MSTR/BTC trading, or promotion of provisional thresholds into production Regime rules.
