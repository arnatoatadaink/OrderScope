# OrderScope — WBS-Unreflected Crypto On-chain Security Extension

Date: 2026-10-02
Status: Active planning extension — not yet incorporated into normative WBS/CP
Source report: `docs/work-management/local-corporate-intelligence/REPORT_CRYPTO_ONCHAIN_SECURITY_FLOW_AND_HACK_PRICE_IMPACT_2026-10-02.md`

This extension follows the append-only WBS-unreflected planning model. It reserves provisional IDs after the currently observed UWBS-100 boundary. The IDs below are tracking IDs only until formal WBS/CP incorporation.

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Dependencies / related work | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-101 | Define cross-chain protocol wallet/component registry and on-chain transfer Fact contract | Crypto On-chain / I0 / Registry | Represent project-to-chain-to-wallet/contract relationships with evidence-backed roles; ingest confirmed transfers with event/accepted timestamps, tx hash, asset, amount, USD notional and provenance; allow unresolved relationships; do not infer hack intent from transfer facts | Existing I0 provenance/idempotency boundaries; crypto market-structure work UWBS-068..079 | Ready for WBS design | Pending |
| UWBS-102 | Implement abnormal on-chain flow Derived Metrics and candidate-state machine | Crypto On-chain Derived Metrics / Interpretation | Compute bounded 5m/15m/60m outflow, balance ratio, baseline ratio/z-score, burst/destination metrics; emit `ONCHAIN_ABNORMAL_FLOW_CANDIDATE/CONFIRMED` and alternative treasury/bridge-rebalance/unknown states without auto-promoting to confirmed security incident | UWBS-101; historical chain data; provider/terms review | Ready for WBS design | Pending |
| UWBS-103 | Join on-chain anomaly candidates with price/OI/funding/liquidation market confirmation | Crypto Market Structure / Event Intelligence | Correlate exact on-chain event timestamps with token return, BTC-relative return, OI delta, funding, liquidation and available CVD/volume; distinguish price-down+OI-down deleveraging candidate from price-down+OI-up new-short candidate; preserve correlation vs causation boundary | UWBS-102; existing crypto derivatives/market structure observations UWBS-068..079 | Ready for WBS design | Pending |
| UWBS-104 | Build historical crypto exploit price-impact dataset and NEAR Intents replay fixture | Crypto Historical Research / QA | Create reproducible incident records containing first malicious/on-chain-detectable/public/official timestamps, loss/TVL/market-cap ratios, patch/compensation/recovery state, +15m/+1h/+6h/+24h/+48h/+5d/+30d token and BTC-relative returns, OI/funding/liquidation, and recovery duration; replay NEAR Intents 2026-10-01 including ~17:00 JST price↓+OI↓ and ~22:00 JST price↓+OI↑ phases | UWBS-101..103; historical news/security reports; accepted crypto market history | Ready for WBS design | Pending |

## Proposed CP candidate

```text
UWBS-101
  -> UWBS-102
  -> UWBS-103
  -> UWBS-104

existing crypto market structure UWBS-068..079
  +-> UWBS-103
  +-> UWBS-104
```

## Research/data-source rule

Existing news is sufficient for incident discovery and qualitative labels, but is not sufficient as the quantitative price-impact source of truth.

Use three source classes:

1. Security/news disclosure layer — incident identity, loss estimate, patch, compensation, recovery statements.
2. On-chain layer — first malicious transaction, transfer path, block-confirmed timing and wallet/component facts.
3. Market layer — price, BTC-relative return, OI, funding, liquidations and volume/CVD where available.

The historical model must not use article-reported percentage declines as a substitute for consistently computed event-window returns.

## Stage-B deferred extension

Mempool/pre-confirmation monitoring is intentionally deferred until confirmed-transaction replay has acceptable false-positive behavior and provider/cost constraints are measured.

No live-provider activation, remote mutation, automated trading action, or security-incident assertion is authorized by this planning extension.
