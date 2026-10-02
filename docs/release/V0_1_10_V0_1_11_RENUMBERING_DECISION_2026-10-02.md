# OrderScope v0.1.10 / v0.1.11 Renumbering Decision — 2026-10-02

Status: **ACCEPTED VERSION-ALLOCATION DECISION**

## 1. Decision

The next two semantic-version boundaries are allocated as follows:

```text
v0.1.9   VIX / Cross-Asset Volatility          UWBS-094..100
v0.1.10  PB / active-market validation close   PB-00..PB-10 closeout lane
v0.1.11  Crypto On-chain Event Intelligence    UWBS-101..104
```

This resolves the prior naming collision where both the PB closeout history and the planned UWBS-101..104 implementation lane had been referred to as `v0.1.10`.

## 2. v0.1.9 scope confirmation

`v0.1.9` remains unchanged and includes the complete volatility lane:

- UWBS-094 — source-neutral volatility instrument contract;
- UWBS-095 — VIX spot / futures term structure;
- UWBS-096 — volatility interpretation;
- UWBS-097 — BTC IV30;
- UWBS-098 — MSTR IV30;
- UWBS-099 — MSTR/BTC IV differential;
- UWBS-100 — historical volatility calibration / threshold / false-positive / capacity acceptance.

Therefore UWBS-100 is part of `v0.1.9` and must not be moved to `v0.1.10`.

## 3. v0.1.10 scope

`v0.1.10` is reserved for the PB / active-market validation closeout lane.

Its release purpose is historical and operational validation rather than a new UWBS feature family. The release manifest should preserve the PB closeout evidence and explicitly separate it from later feature work.

No UWBS-101..104 implementation is included in `v0.1.10`.

## 4. v0.1.11 scope

`v0.1.11` becomes the planned implementation release for `UWBS-101..104`, titled **Crypto On-chain Event Intelligence**.

Planned scope:

- UWBS-101 — confirmed transfer facts plus project / chain / wallet / contract registry;
- UWBS-102 — abnormal flow candidates preserving treasury / bridge / unknown alternatives;
- UWBS-103 — join on-chain anomaly with price / OI / funding / liquidation context while preserving correlation vs causation;
- UWBS-104 — historical replay, including the 2026-10-01 NEAR Intents reference episode.

Stage-B mempool work remains deferred unless separately approved.

The planned v0.1.11 lane does not itself authorize:

- live provider activation;
- new Worker/Cron/D1 mutation behavior;
- automated trading;
- inference of malicious intent from transfer facts alone.

## 5. Critical-path renumbering

Existing planning references that used `REL-10*` for UWBS-101..104 should be interpreted as the new `v0.1.11` lane. Future documents should prefer `REL-11*` identifiers to avoid ambiguity.

Recommended sequence:

```text
REL-10A  PB boundary / release-manifest reconciliation
REL-10B  PB exact-boundary acceptance as required
REL-10C  v0.1.10 release closeout / tag-ready decision

REL-11A  UWBS-101 scope and contract acceptance
REL-11B  UWBS-102 abnormal-flow candidate implementation
REL-11C  UWBS-103 market-context join
REL-11D  UWBS-104 historical replay
REL-11X  cumulative v0.1.11 acceptance / tag-ready decision
```

## 6. Historical-document handling

Do not rewrite older documents solely because they used `v0.1.10` for the then-current future plan. Treat those documents as historical planning evidence.

This decision document is the authoritative renumbering rule for subsequent release planning.
