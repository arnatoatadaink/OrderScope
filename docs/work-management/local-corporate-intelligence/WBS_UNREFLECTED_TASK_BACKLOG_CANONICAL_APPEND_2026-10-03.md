# OrderScope — WBS-Unreflected Task Backlog Canonical Append — 2026-10-03

Status: **CURRENT CANONICAL APPEND / INCORPORATION DISPOSITION**
Parent backlog: `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
Registry: `WBS_PROVISIONAL_ID_REGISTRY.md`
Namespace authority: `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`

## 1. Purpose

Record the canonical disposition of the post-100 backlog without rewriting historical append-only evidence.

Historical dated reports and append files retain the identifier text they originally used. This append controls current interpretation, formal WBS incorporation and future references.

## 2. Frozen conflict range

`UWBS-101..104` are permanently frozen as **CONFLICT / LEGACY-ONLY**.

They must not be assigned to any new task, implementation branch, CP node, handoff or acceptance record.

| Frozen ID | Historical meaning | Canonical replacement |
|---|---|---|
| UWBS-101 | Macro Release / Yen Carry context | UWBS-105 |
| UWBS-101 | Crypto wallet/chain/confirmed-transfer context | UWBS-106 |
| UWBS-102 | Crypto abnormal-flow context | UWBS-107 |
| UWBS-103 | Crypto price/OI/funding/liquidation context | UWBS-108 |
| UWBS-104 | Crypto exploit/replay/NEAR Intents context | UWBS-109 |

If context is insufficient, retain the reference as `AMBIGUOUS`; never guess a mapping.

## 3. Canonical post-100 backlog disposition

| Canonical UWBS | Task | Historical planning state | Final WBS ID | Disposition | Release |
|---|---|---|---|---|---|
| UWBS-105 | Macro Release Surprise / Yen Carry Flow Observability | Ready for WBS design | A0-018 | **Incorporated / implementation pending** | **v0.1.12** |
| UWBS-106 | Cross-chain project/wallet/contract registry + confirmed-transfer Fact | Ready for WBS design | C0-001 | **Incorporated / implementation pending** | **v0.1.11 REL-11A** |
| UWBS-107 | Abnormal on-chain flow Derived Metrics + candidate-state machine | Ready for WBS design | C0-002 | **Incorporated / implementation pending** | **v0.1.11 REL-11B** |
| UWBS-108 | On-chain anomaly × price/OI/funding/liquidation context join | Ready for WBS design | C0-003 | **Incorporated / implementation pending** | **v0.1.11 REL-11C** |
| UWBS-109 | Historical exploit price-impact dataset + NEAR Intents replay | Ready for WBS design | C0-004 | **Incorporated / implementation pending** | **v0.1.11 REL-11D** |

Formal WBS authorities:

- `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_POST100_2026-10-03.md`
- `docs/WORK_BREAKDOWN_CRYPTO_ONCHAIN_EVENT_INTELLIGENCE_2026-10-03.md`

Release authority:

- `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`

## 4. Canonical dependency chains

Macro / v0.1.12:

```text
A0-003 + A0-004 + A0-013..016
   |
   v
A0-018 / UWBS-105
   |
   v
A0-005 existing carry-unwind / deleveraging path
```

Crypto / v0.1.11:

```text
C0-001 / UWBS-106
   -> C0-002 / UWBS-107
   -> C0-003 / UWBS-108
   -> C0-004 / UWBS-109
   -> REL-11X

UWBS-068..079
   -> C0-003
   -> C0-004
```

## 5. Backlog governance effect

For current planning:

1. UWBS-105..109 are no longer merely WBS-unreflected proposals; they have formal WBS destinations.
2. Their implementation status remains pending until task-specific acceptance evidence exists.
3. Incorporation does not imply implementation acceptance.
4. Historical source reports remain planning provenance and may retain their original filenames.
5. New documents use final WBS IDs for formal execution and may include canonical UWBS source IDs for traceability.
6. New documents never use UWBS-101..104 as active IDs.

## 6. Release effect

```text
v0.1.11 = C0-001..004 / UWBS-106..109
v0.1.12 = A0-018 / UWBS-105
```

Planned order:

```text
v0.1.11 REL-11A -> REL-11B -> REL-11C -> REL-11D -> REL-11X
   then
v0.1.12 REL-12A -> REL-12B -> REL-12C -> A0-005 path -> REL-12D -> REL-12X
```

A0-018 is not technically dependent on C0-001..004; the ordering is release governance.

## 7. Authorization boundary

This append performs planning/WBS incorporation only. It does not authorize provider activation, Worker/Cron changes, remote D1 mutation, automated trading, paid procurement, tag creation, history rewrite or force push.
