# OrderScope v0.1.11 UWBS Namespace Correction — 2026-10-03

Status: **CURRENT RELEASE-PLANNING CORRECTION**
Supersedes for current planning: the `UWBS-101..104` allocation in `V0_1_10_V0_1_11_RENUMBERING_DECISION_2026-10-02.md`.

## Decision

The semantic-version allocation remains:

```text
v0.1.10  PB / active-market validation closeout
v0.1.11  Crypto On-chain Event Intelligence
```

The UWBS namespace for v0.1.11 changes because `UWBS-101` was independently used by a Macro Release / Yen Carry planning lane before canonical incorporation, creating a namespace collision.

`UWBS-101..104` are therefore frozen as legacy/conflict identifiers. The canonical v0.1.11 scope is:

```text
v0.1.11  Crypto On-chain Event Intelligence  UWBS-106..109
```

Canonical work sequence:

```text
REL-11A  UWBS-106 scope and on-chain registry/transfer Fact contract
REL-11B  UWBS-107 abnormal-flow candidate implementation
REL-11C  UWBS-108 market-context join
REL-11D  UWBS-109 historical exploit / NEAR Intents replay
REL-11X  cumulative v0.1.11 acceptance / tag-ready decision
```

`UWBS-105` is separately allocated to Macro Release Surprise / Yen Carry Flow Observability and is not included in v0.1.11 by this decision.

## Historical interpretation

Prior release-planning documents that state `v0.1.11 = UWBS-101..104` remain historical evidence. For current planning, those references are interpreted as:

```text
legacy UWBS-101 (Crypto context) -> UWBS-106
legacy UWBS-102                  -> UWBS-107
legacy UWBS-103                  -> UWBS-108
legacy UWBS-104                  -> UWBS-109
```

A legacy `UWBS-101` reference in PCE / Durable Goods / rate-spread / USDJPY / yen-carry context maps instead to `UWBS-105`.

If context is insufficient, the old reference remains ambiguous and must not be guessed.

## Authority

Canonical namespace details are governed by:

- `docs/work-management/local-corporate-intelligence/UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`
- `docs/work-management/local-corporate-intelligence/WBS_PROVISIONAL_ID_REGISTRY.md`

No Git tag creation/push, provider activation, deployment, D1 mutation, secret change, automated trading action, history rewrite, or force push is authorized by this correction.
