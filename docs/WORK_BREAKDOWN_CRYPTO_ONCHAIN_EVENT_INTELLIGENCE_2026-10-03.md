# OrderScope — Crypto On-chain Event Intelligence Work Breakdown

Status: **FORMAL WBS EXTENSION — CURRENT**
Date: 2026-10-03
Release target: `v0.1.11`
Canonical registry: `docs/work-management/local-corporate-intelligence/WBS_PROVISIONAL_ID_REGISTRY.md`
Namespace authority: `docs/work-management/local-corporate-intelligence/UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`
Release namespace correction: `docs/release/V0_1_11_UWBS_NAMESPACE_CORRECTION_2026-10-03.md`

## 1. Purpose

Formally incorporate the Crypto On-chain Event Intelligence lane using collision-free canonical provisional IDs.

The historical provisional identifiers `UWBS-101..104` are frozen as conflict/legacy-only and are not valid for new implementation, CP, acceptance or handoff records. The canonical source range is `UWBS-106..109`.

This WBS extends the already accepted Crypto Market Structure layer `UWBS-068..079`. It does not authorize automated trading, malicious-intent attribution from transfer facts, live-provider activation, Worker/Cron mutation or remote D1 mutation.

## 2. C0 — Crypto On-chain Event Intelligence

| Final WBS ID | Canonical source | Task | Completion condition | Upstream dependency | Related accepted evidence | State |
|---|---|---|---|---|---|---|
| C0-001 | UWBS-106 | Define cross-chain project / wallet / contract registry and confirmed-transfer Fact contract | Represent project-to-chain-to-wallet/contract relationships with evidence-backed roles; preserve unresolved relationships; normalize confirmed transfer event/accepted timestamps, tx hash, asset, amount, USD notional and provenance; a transfer Fact never implies hack intent | I0 provenance/idempotency boundaries | Crypto Market Structure `UWBS-068..079` is related context but is not a blocking prerequisite for C0-001 | Incorporated / implementation pending |
| C0-002 | UWBS-107 | Implement abnormal on-chain flow Derived Metrics and candidate-state machine | Compute bounded 5m/15m/60m outflow, balance/baseline ratio or z-score where valid, burst/destination metrics; emit bounded abnormal-flow candidate states while preserving treasury movement, bridge rebalance and unknown alternatives | C0-001; historical chain data; provider/terms review | Existing crypto-market evidence may support fixtures but does not replace chain baselines | Incorporated / implementation pending |
| C0-003 | UWBS-108 | Join on-chain anomaly candidates with market-context confirmation | Correlate exact on-chain event timing with token return, BTC-relative return, OI delta, funding, liquidation and available volume/CVD; distinguish price-down+OI-down deleveraging candidate from price-down+OI-up new-short candidate; preserve correlation vs causation | C0-002; accepted Crypto Market Structure `UWBS-068..079` | `UWBS-068..079` supplies the market-context evidence boundary | Incorporated / implementation pending |
| C0-004 | UWBS-109 | Build historical exploit price-impact dataset and replay fixture | Store first on-chain-detectable/public/official timestamps separately; compute consistent +15m/+1h/+6h/+24h/+48h/+5d/+30d token/BTC-relative returns and available derivatives context; include reproducible NEAR Intents 2026-10-01 replay with the observed ~17:00 JST price↓+OI↓ and ~22:00 JST price↓+OI↑ phases | C0-001..003; accepted Crypto Market Structure `UWBS-068..079`; historical security/news evidence | Accepted market history supplies replay context | Incorporated / implementation pending |

## 3. Critical path

```text
C0-001 / UWBS-106
   |
   v
C0-002 / UWBS-107
   |
   v
C0-003 / UWBS-108
   |
   v
C0-004 / UWBS-109
   |
   v
REL-11X cumulative v0.1.11 acceptance
```

Additional evidence edges:

```text
UWBS-068..079 -> C0-003 / UWBS-108
UWBS-068..079 -> C0-004 / UWBS-109
```

`UWBS-068..079` is therefore not a blocking predecessor of C0-001/C0-002. It becomes a direct accepted dependency at the market-context and replay stages.

## 4. Layer boundary

### Fact layer — C0-001

Facts include only source-grounded identities, relationships and confirmed transfers. Required boundaries:

- chain/network identity;
- wallet/contract address identity;
- relationship role and evidence provenance;
- transaction hash/block-confirmed timing;
- asset/amount/USD notional when source-grounded;
- accepted timestamp and source identity;
- unresolved or disputed relationships retained explicitly.

No security-incident conclusion is stored as a transfer Fact.

### Derived Metric / Interpretation layer — C0-002

Abnormality is derived relative to explicit windows/baselines and must preserve alternative explanations. A large transfer does not auto-promote to a confirmed incident.

### Market-context layer — C0-003

The join is temporal and evidentiary. It may show patterns consistent with deleveraging or new short formation but must not convert correlation into causal incident attribution.

### Historical QA layer — C0-004

Article-reported percentage declines are not the quantitative source of truth. Event-window returns are computed consistently from accepted market data around source-grounded event timestamps.

## 5. Acceptance conditions

### C0-001

- deterministic address/component registry identity;
- provenance and unresolved relationships preserved;
- confirmed-transfer fields are reproducible;
- duplicate/update/conflict behavior is tested;
- transfer facts never imply malicious intent.

### C0-002

- bounded windows and baselines are deterministic;
- candidate state is separable from confirmed incident assertion;
- treasury / bridge-rebalance / unknown false positives remain representable;
- missing baseline data fails closed or remains UNKNOWN.

### C0-003

- joins use compatible as-of/event timing;
- price/OI/funding/liquidation signals preserve source and timestamp identity;
- price↓+OI↓ and price↓+OI↑ interpretations remain distinct;
- market confirmation remains evidence, not causal proof.

### C0-004

- incident timestamp classes are distinct;
- replay windows are reproducible;
- NEAR Intents reference replay is deterministic;
- false-positive and incomplete-data cases are covered;
- full regression / compileall / diff checks and affected Worker checks pass before release acceptance.

## 6. Deferred scope

Mempool or pre-confirmation monitoring remains Stage B deferred until confirmed-transaction replay has acceptable false-positive behavior and provider/cost constraints are measured.

## 7. Namespace and release rule

- `UWBS-106..109` are the only canonical provisional source IDs for this WBS.
- Historical Crypto-context references to old `UWBS-101..104` map respectively to `UWBS-106..109` when context is sufficient.
- Old `UWBS-101..104` remain frozen and may appear only as historical aliases/conflict documentation.
- `v0.1.11` scope is `C0-001..004` sourced from `UWBS-106..109`.
