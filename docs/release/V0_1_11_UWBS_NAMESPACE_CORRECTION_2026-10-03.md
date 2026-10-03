# OrderScope v0.1.11 UWBS Namespace Correction — 2026-10-03

Status: **CURRENT RELEASE-PLANNING CORRECTION**
Supersedes for current planning: the `UWBS-101..104` allocation in `V0_1_10_V0_1_11_RENUMBERING_DECISION_2026-10-02.md`.
Companion forward release plan: `V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`.

## Decision

The semantic-version allocation is now:

```text
v0.1.10  PB / active-market validation closeout
v0.1.11  Crypto On-chain Event Intelligence
v0.1.12  Macro Release / Yen Carry Observability
```

The UWBS namespace for v0.1.11 changed because `UWBS-101` was independently used by a Macro Release / Yen Carry planning lane before canonical incorporation, creating a namespace collision.

`UWBS-101..104` are therefore frozen as legacy/conflict identifiers.

Canonical allocation:

```text
v0.1.11  Crypto On-chain Event Intelligence
         C0-001..004
         UWBS-106..109

v0.1.12  Macro Release / Yen Carry Observability
         A0-018
         UWBS-105
```

## v0.1.11 work sequence

```text
REL-11A  C0-001 / UWBS-106 scope and on-chain registry/transfer Fact contract
REL-11B  C0-002 / UWBS-107 abnormal-flow candidate implementation
REL-11C  C0-003 / UWBS-108 market-context join
REL-11D  C0-004 / UWBS-109 historical exploit / NEAR Intents replay
REL-11X  cumulative v0.1.11 acceptance / tag-ready decision
```

## v0.1.12 relation

`UWBS-105` is separately allocated to `A0-018` and `v0.1.12`.
It extends the existing Macro/Carry implementation rather than the new C0 lane.

```text
REL-12A  Macro release Fact / consensus / revision
REL-12B  Surprise + event-window transmission
REL-12C  Carry BUILD / STABLE / COOLING integration
REL-12D  Historical / revision / false-positive validation
REL-12X  cumulative v0.1.12 acceptance / tag-ready decision
```

v0.1.12 does not technically depend on v0.1.11; the sequence is the current release-management order.

## Historical interpretation

Prior release-planning documents that state `v0.1.11 = UWBS-101..104` remain historical evidence. For current planning, those references are interpreted as:

```text
legacy UWBS-101 (Crypto context) -> UWBS-106
legacy UWBS-102                  -> UWBS-107
legacy UWBS-103                  -> UWBS-108
legacy UWBS-104                  -> UWBS-109
```

A legacy `UWBS-101` reference in PCE / Durable Goods / rate-spread / USDJPY / yen-carry context maps instead to `UWBS-105 / A0-018 / v0.1.12`.

If context is insufficient, the old reference remains ambiguous and must not be guessed.

## Authority

Canonical namespace and release details are governed by:

- `docs/work-management/local-corporate-intelligence/UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`
- `docs/work-management/local-corporate-intelligence/WBS_PROVISIONAL_ID_REGISTRY.md`
- `docs/WORK_BREAKDOWN_CRYPTO_ONCHAIN_EVENT_INTELLIGENCE_2026-10-03.md`
- `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_POST100_2026-10-03.md`
- `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`

No Git tag creation/push, provider activation, deployment, D1 mutation, secret change, automated trading action, history rewrite, or force push is authorized by this correction.
