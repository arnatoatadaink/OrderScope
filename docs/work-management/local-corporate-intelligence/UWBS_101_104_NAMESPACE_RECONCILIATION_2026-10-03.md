# OrderScope — UWBS-101..104 Namespace Reconciliation

Date: 2026-10-03
Status: **CANONICAL NAMESPACE DECISION / FORMAL MAPPING CURRENT**
Scope: provisional UWBS identifiers above the accepted `UWBS-100` boundary

## 1. Decision

`UWBS-101`, `UWBS-102`, `UWBS-103`, and `UWBS-104` are frozen as **CONFLICT / LEGACY-ONLY** identifiers.

They must not be assigned to any new task and must not appear as canonical identifiers in new WBS/CP, implementation handoff, acceptance, release, or tracker documents.

Canonical replacement and formal allocation:

```text
UWBS-105 -> A0-018 -> v0.1.12
  Macro Release Surprise / Yen Carry Flow Observability

UWBS-106 -> C0-001 -> v0.1.11 REL-11A
  project/chain/wallet/contract registry + confirmed transfer Fact
UWBS-107 -> C0-002 -> v0.1.11 REL-11B
  abnormal-flow Derived Metrics + candidate state machine
UWBS-108 -> C0-003 -> v0.1.11 REL-11C
  market-context join with price/OI/funding/liquidation
UWBS-109 -> C0-004 -> v0.1.11 REL-11D
  historical exploit dataset + NEAR Intents replay
```

## 2. Collision provenance

Two independent planning lines used `UWBS-101` before either was incorporated into the canonical provisional-ID registry.

### Macro / Carry historical alias

Branch: `docs/uwbs-101-macro-carry-observability`
Historical file: `WBS_UNREFLECTED_TASK_BACKLOG_APPEND_UWBS-101_2026-10-01.md`
Historical alias: `UWBS-101`
Canonical replacement: `UWBS-105`
Formal WBS: `A0-018`
Release allocation: `v0.1.12`

The task covers PCE / Durable Goods official-release Facts, release surprise, U.S.-Japan 2Y spread and USDJPY transmission, plus carry BUILD / STABLE / COOLING interpretation before the existing carry-unwind states.

### Crypto On-chain historical aliases

Historical file: `WBS_UNREFLECTED_CRYPTO_ONCHAIN_SECURITY_EXTENSION_2026-10-02.md`
Historical aliases: `UWBS-101..104`
Canonical replacements: `UWBS-106..109`
Formal WBS: `C0-001..004`
Release allocation: `v0.1.11`

The lane covers confirmed on-chain transfer facts, abnormal-flow detection, derivatives/market confirmation, and historical exploit replay.

## 3. Legacy-to-canonical table

| Frozen legacy ID | Context discriminator | Canonical ID | Formal WBS | Canonical task |
|---|---|---|---|---|
| UWBS-101 | PCE / Durable Goods / official macro surprise / U.S.-Japan 2Y / USDJPY / yen carry | UWBS-105 | A0-018 | Macro Release Surprise / Yen Carry Flow Observability |
| UWBS-101 | wallet / contract / chain / confirmed transfer / on-chain registry | UWBS-106 | C0-001 | On-chain registry + transfer Fact |
| UWBS-102 | abnormal outflow / balance ratio / burst / candidate state | UWBS-107 | C0-002 | Abnormal-flow metrics + candidate state |
| UWBS-103 | price / OI / funding / liquidation / market confirmation | UWBS-108 | C0-003 | On-chain anomaly × market-context join |
| UWBS-104 | exploit history / incident replay / NEAR Intents | UWBS-109 | C0-004 | Historical exploit dataset + replay |

## 4. Reference-normalization rule

When an existing document references `UWBS-101..104`:

1. infer the intended lane only when surrounding text is sufficient;
2. replace active/current references with the canonical ID above;
3. preserve the old identifier as a historical alias where provenance matters;
4. if the surrounding text is insufficient, mark the reference `AMBIGUOUS — legacy UWBS-10x` and do not guess;
5. dated evidence may retain its original identifier, but current authority documents must point to this decision and use the canonical replacement.

## 5. Release planning effect

Current semantic allocation:

```text
v0.1.11  Crypto On-chain Event Intelligence
         C0-001..004 / UWBS-106..109

v0.1.12  Macro Release / Yen Carry Observability
         A0-018 / UWBS-105
```

Any prior `v0.1.11 = UWBS-101..104` statement is historical pre-reconciliation allocation and is superseded for current planning.

The detailed forward release authority is `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`.

## 6. Dependency effect

Canonical dependencies:

```text
Macro / Carry / v0.1.12
A0-003 + A0-004 + A0-013..016
        -> A0-018 / UWBS-105
        -> existing A0-005 carry-unwind interpretation path

Crypto On-chain / v0.1.11
C0-001 / UWBS-106
        -> C0-002 / UWBS-107
        -> C0-003 / UWBS-108
        -> C0-004 / UWBS-109
UWBS-068..079 -> C0-003 / C0-004
```

## 7. Frozen range rule

`UWBS-101..104` remain permanently unavailable for future canonical allocation. Their only permitted use is as quoted historical aliases accompanied by either a canonical replacement or an explicit ambiguity marker.

No implementation, provider activation, deployment, D1 mutation, secret change, automated trading action, Git tag creation, history rewrite, or force push is authorized by this document.
