# OrderScope — WBS-Unreflected Crypto On-chain Security Extension

Date: 2026-10-02
Updated: 2026-10-03 formal incorporation reconciliation
Status: **INCORPORATED / HISTORICAL PLANNING SOURCE — SUPERSEDED FOR EXECUTION**
Source report: `docs/work-management/local-corporate-intelligence/REPORT_CRYPTO_ONCHAIN_SECURITY_FLOW_AND_HACK_PRICE_IMPACT_2026-10-02.md`
Formal WBS: `docs/WORK_BREAKDOWN_CRYPTO_ONCHAIN_EVENT_INTELLIGENCE_2026-10-03.md`
Release allocation: `v0.1.11`

> This file preserves the original WBS-unreflected planning scope and namespace-remap provenance. Current implementation authority is the formal C0 WBS, the v0.1.11/v0.1.12 release plan, and the CURRENT CP.

The original draft used `UWBS-101..104`. Those identifiers are now **CONFLICT / FROZEN / LEGACY-ONLY**. Current canonical/formal mappings are:

| Historical alias | Canonical UWBS | Formal WBS | Task | Current disposition |
|---|---|---|---|---|
| UWBS-101 | UWBS-106 | C0-001 | Cross-chain project/wallet/contract registry + confirmed-transfer Fact | **Incorporated / implementation pending / REL-11A** |
| UWBS-102 | UWBS-107 | C0-002 | Abnormal on-chain flow Derived Metrics + candidate-state machine | **Incorporated / implementation pending / REL-11B** |
| UWBS-103 | UWBS-108 | C0-003 | On-chain anomaly × price/OI/funding/liquidation market-context join | **Incorporated / implementation pending / REL-11C** |
| UWBS-104 | UWBS-109 | C0-004 | Historical exploit price-impact dataset + NEAR Intents replay | **Incorporated / implementation pending / REL-11D** |

## Historical scope retained

### C0-001 / UWBS-106

Represent project-to-chain-to-wallet/contract relationships with evidence-backed roles; ingest confirmed transfers with event/accepted timestamps, tx hash, asset, amount, USD notional and provenance; retain unresolved relationships; never infer malicious intent from a transfer Fact.

Dependencies: common I0 provenance/idempotency boundaries and accepted crypto market-structure evidence.

### C0-002 / UWBS-107

Compute bounded 5m/15m/60m outflow, balance/baseline ratio or z-score where valid, burst/destination metrics, and bounded abnormal-flow candidate states. Preserve treasury movement, bridge rebalance and unknown alternatives rather than auto-promoting to a confirmed incident.

Dependency: C0-001 plus historical chain data/provider review.

### C0-003 / UWBS-108

Join exact on-chain event timing to token return, BTC-relative return, OI delta, funding, liquidation and available volume/CVD; distinguish price-down+OI-down deleveraging candidates from price-down+OI-up new-short candidates; preserve correlation vs causation.

Dependencies: C0-002 and accepted `UWBS-068..079` crypto market-structure observations.

### C0-004 / UWBS-109

Build reproducible incident/replay records with distinct first on-chain-detectable/public/official timestamps, consistent event-window returns, derivatives context, recovery state and false-positive handling. The NEAR Intents 2026-10-01 reference replay retains the ~17:00 JST price↓+OI↓ and ~22:00 JST price↓+OI↑ phases as the reference scenario to reproduce from accepted data.

Dependencies: C0-001..003, historical security/news evidence and accepted market history.

## Current release CP

```text
REL-11A  C0-001 / UWBS-106
  -> REL-11B  C0-002 / UWBS-107
  -> REL-11C  C0-003 / UWBS-108
  -> REL-11D  C0-004 / UWBS-109
  -> REL-11X  cumulative v0.1.11 acceptance / TAG READY decision
```

Accepted `UWBS-068..079` evidence feeds C0-003 and C0-004.

## Frozen legacy identifiers

`UWBS-101..104` must not be allocated to new work. Contextual historical mapping remains:

- wallet / chain / transfer context -> UWBS-106 / C0-001;
- abnormal-flow context -> UWBS-107 / C0-002;
- price/OI/funding/liquidation context -> UWBS-108 / C0-003;
- exploit/replay/NEAR Intents context -> UWBS-109 / C0-004;
- PCE / Durable Goods / US-Japan rates / USDJPY / carry context -> UWBS-105 / A0-018;
- insufficient context -> `AMBIGUOUS`.

## Research/data-source rule

Existing news is sufficient for incident discovery and qualitative labels but is not the quantitative price-impact source of truth. Preserve three evidence classes:

1. Security/news disclosure — incident identity, loss estimate, patch, compensation, recovery statements.
2. On-chain — transfer path, block-confirmed timing and wallet/component facts.
3. Market — price, BTC-relative return, OI, funding, liquidations and volume/CVD where available.

Article-reported percentage declines do not replace consistently computed event-window returns.

## Stage-B deferred extension

Mempool/pre-confirmation monitoring remains deferred until confirmed-transaction replay has acceptable false-positive behavior and provider/cost constraints are measured.

No live-provider activation, remote mutation, automated trading action, confirmed security-incident assertion, tag creation, history rewrite, or force push is authorized by this historical planning file.
