# OrderScope — Crypto On-chain Event Intelligence Work Breakdown

Status: **FORMAL WBS EXTENSION — ACCEPTED / v0.1.11 TAG READY**
Date: 2026-10-03
Release target: `v0.1.11`
Validated cumulative target: `fce9a3a2e56783206d63dbcac0d8a65e50008c10`
Canonical registry: `docs/work-management/local-corporate-intelligence/WBS_PROVISIONAL_ID_REGISTRY.md`
Namespace authority: `docs/work-management/local-corporate-intelligence/UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`

## 1. Purpose

This WBS formally incorporates and now closes the Crypto On-chain Event Intelligence lane using canonical provisional IDs `UWBS-106..109`. Historical `UWBS-101..104` remain frozen as conflict/legacy-only.

The lane extends the accepted Crypto Market Structure layer `UWBS-068..079`. It does not authorize automated trading, live-provider activation, Worker/Cron mutation, D1 mutation, or security-incident attribution from abnormal transfers alone.

## 2. C0 — Crypto On-chain Event Intelligence

| Final WBS ID | Canonical source | Task | State |
|---|---|---|---|
| C0-001 | UWBS-106 | Cross-chain project / wallet / contract registry and confirmed-transfer Fact contract | **Accepted / Integrated** |
| C0-002 | UWBS-107 | Abnormal on-chain flow Derived Metrics and candidate-state machine | **Accepted / Integrated** |
| C0-003 | UWBS-108 | On-chain anomaly × market-context join | **Accepted / Integrated** |
| C0-004 | UWBS-109 | Historical exploit price-impact dataset and replay fixture | **Accepted / Integrated** |

## 3. Critical path completion

```text
C0-001 / UWBS-106  ACCEPTED
 -> C0-002 / UWBS-107  ACCEPTED
 -> C0-003 / UWBS-108  ACCEPTED
 -> C0-004 / UWBS-109  ACCEPTED
 -> REL-11X cumulative acceptance  ACCEPTED / TAG READY
```

Accepted evidence edges remain:

```text
UWBS-068..079 -> C0-003 / UWBS-108
UWBS-068..079 -> C0-004 / UWBS-109
```

## 4. Accepted layer boundaries

### C0-001 — Fact

- source-grounded chain/network and wallet/contract identity;
- evidence-backed project relationships with unresolved/disputed states preserved;
- confirmed-transfer identity/timing/provenance;
- no hack/exploit/theft/malicious attribution in a transfer Fact.

### C0-002 — Derived Metric / candidate interpretation

- deterministic 5m/15m/60m windows;
- balance/baseline ratio or z-score where valid;
- burst/destination metrics;
- treasury movement, bridge rebalance and unknown alternatives remain representable;
- missing required inputs fail closed or remain UNKNOWN.

### C0-003 — Market-context join

- BTC-relative return, OI, funding, liquidation and available volume context;
- price↓+OI↓ and price↓+OI↑ interpretations remain distinct;
- `causality = NOT_ESTABLISHED` is retained.

### C0-004 — Historical replay / QA

- first-on-chain-detectable, first-public and first-official timestamps remain distinct;
- +15m/+1h/+6h/+24h/+48h/+5d/+30d windows are reproducible;
- incomplete market inputs fail closed;
- NEAR Intents reference replay preserves separate market-structure phases without causal overclaim.

## 5. REL-11X cumulative acceptance evidence

```text
crypto_onchain                33 passed
crypto_context/derivatives/
archive/time/canary          111 passed
full analysis               1151 passed
compileall                   PASS
git diff --check             PASS
```

No shared Worker/runtime contracts were changed by C0-001..004, so Worker test/typecheck was not required for REL-11X.

## 6. Deferred scope

Mempool or pre-confirmation monitoring remains Stage B deferred until confirmed-transaction replay has acceptable false-positive behavior and provider/cost constraints are measured.

## 7. Release rule

- `UWBS-106..109` are the only canonical provisional source IDs for this WBS.
- `v0.1.11` is **ACCEPTED / TAG READY** at `fce9a3a2e56783206d63dbcac0d8a65e50008c10`.
- `TAG READY` does not authorize tag creation or push.
- next planned release work is `v0.1.12 REL-12A / A0-018 / UWBS-105`.
