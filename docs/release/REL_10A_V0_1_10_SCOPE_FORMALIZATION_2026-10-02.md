# REL-10A — v0.1.10 Scope Formalization — 2026-10-02

Status: **ACCEPTED**
Release target: `v0.1.10`
Package: **Crypto On-chain Event Intelligence**

## 1. Decision

The approved v0.1.10 implementation scope is fixed as:

```text
v0.1.10 = UWBS-101..104
```

Release ordering dependency is satisfied by accepted/tag-ready REL-09 (`v0.1.9`).

## 2. Ordered implementation lane

```text
UWBS-101
  Cross-chain protocol wallet/component registry
  + confirmed on-chain transfer Fact contract
    |
    v
UWBS-102
  Abnormal on-chain flow Derived Metrics
  + candidate-state machine
    |
    v
UWBS-103
  Join on-chain anomaly with price / OI / funding / liquidation confirmation
    |
    v
UWBS-104
  Historical exploit price-impact dataset
  + NEAR Intents replay fixture
```

Additional accepted upstream dependencies:

```text
UWBS-068..079 -> UWBS-103
UWBS-068..079 -> UWBS-104
```

## 3. Semantic boundary

UWBS-101 records confirmed transfer facts and evidence-backed protocol/component relationships without inferring malicious intent.

UWBS-102 may produce abnormal-flow candidates and alternative states such as treasury movement, bridge rebalance, and unknown; abnormal flow alone must not be promoted to a confirmed security incident.

UWBS-103 correlates on-chain events with market evidence while preserving the correlation/causation boundary.

UWBS-104 creates historical/replay evidence, including the 2026-10-01 NEAR Intents episode, without converting historical association into an automatic trading rule.

## 4. Deferred / excluded scope

The following remain outside REL-10A authorization:

- Stage-B mempool / pre-confirmation monitoring until confirmed-transaction replay false positives and provider/cost constraints are measured;
- live-provider activation solely for this lane;
- Worker/Cron remote mutation changes;
- D1 mutation-policy changes;
- automated trading actions;
- automatic assertion of a confirmed security incident.

## 5. v0.1.10 acceptance path

After UWBS-101..104 are individually accepted, REL-10C must verify:

1. focused UWBS-101..104 tests;
2. full Python analysis regression;
3. Worker tests/typecheck where affected;
4. compileall;
5. git diff --check;
6. reproducible NEAR Intents historical replay;
7. false-positive alternatives;
8. no unauthorized live-provider, remote-mutation, or automated-trading behavior;
9. cumulative v0.1.10 release manifest;
10. final taggable boundary SHA.

## 6. Restart point

```text
REL-07  ACCEPTED / TAG READY
REL-08  ACCEPTED / TAG READY
REL-09  ACCEPTED / TAG READY
REL-10A ACCEPTED

CURRENT: UWBS-101
NEXT:    UWBS-102
THEN:    UWBS-103 -> UWBS-104 -> REL-10C
```

REL-10A authorizes implementation planning/execution of UWBS-101 within the existing safety and provenance boundaries; it does not itself activate production infrastructure.
