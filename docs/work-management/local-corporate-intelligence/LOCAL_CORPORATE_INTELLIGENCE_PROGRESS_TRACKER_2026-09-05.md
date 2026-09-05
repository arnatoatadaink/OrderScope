# OrderScope — Local Corporate Intelligence Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-05
Parent WBS: `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Extension WBS: `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`

## 1. Purpose

この資料は Local Corporate Intelligence の実行進捗を、Parent WBS と Integrated Critical Path に対応付けて管理する。
WBSの完了条件を変更せず、各タスクの現在状態、依存、先行成果、正式受入の残作業、次の安全な操作を記録する。

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| Accepted | WBSの完了条件と依存を満たし、正式に次工程の前提として使用可能 |
| In progress | 現在の主作業または並列作業として実装・整合中 |
| Provisional result | 成果物はあるが、上流依存または正式受入が未完了 |
| Ready | 依存が満たされ、着手可能 |
| Blocked | 外部変更窓、未確定契約、上流成果などを待つ |
| Not started | 依存ゲート未通過または未着手 |

## 3. Current critical-path snapshot

| Task | Status | Evidence / interpretation | Next action |
|---|---|---|---|
| I0-001 | Accepted | Integrated CP が `I0-002` を主作業としているため前提充足済み | 変更不要。後続整合時のみ参照 |
| I0-002 | In progress | 2026-09-05 Integrated CP の現在の主作業 | provenance型とtimestamp/source revision契約を完了・受入 |
| I0-003 | Not started | `I0-002`依存 | I0-002受入後、I0-004と並列実装 |
| I0-004 | Not started | `I0-002`依存 | I0-002受入後、I0-003と並列実装 |
| I0-005 | Provisional result | Fact Store論理schemaの先行成果あり。CP上はI0-002 provenance型への適合とAccepted化が残る | I0-002受入後にschema整合・正式受入 |
| I0-006 | Not started | `I0-005`依存 | I0-005 Accepted後にtemporary content lifecycleを固定 |
| I0-007 | Provisional result | 共通contract test kitの先行成果あり。CP上はI0-003/004/006充足後の正式受入待ち | 上流3契約を接続し正式受入 |
| S0-002 | Not started | `I0-007`正式受入と`S0-001`がゲート | I0-007 Accepted後にSEC adapter開始 |
| S0-003 | Not started | `S0-002`依存 | FilingRecord永続化を実装 |
| S0-004 | Provisional result | 対象form filterの先行実装・レポートあり。CPでは完了済みとして扱うがS0-003接続前 | S0-003後に接続確認し受入状態を維持 |
| S0-005 | Not started | `S0-003` + `I0-006`依存 | document temporary-content取得を実装 |
| S0-006 | Not started | `S0-003`依存 | Company Facts/XBRL adapterを実装 |
| S0-007 | Provisional result | 先行検証成果あり得るが、WBS上はS0-004〜006接続後の受入試験 | S0-004〜006統合後に正式なCanary受入試験 |
| E0-001〜007 | Not started | S0 lane と I0-005 に依存 | S0-007通過後に順次開始 |
| N1 / O0 / X0 | Not started | Core Fact/SEC/Earnings laneに依存 | Core CP後半で開始 |

## 4. Parallel lanes

### Lane A — Core contracts

Current: `I0-002`

Planned order:

1. I0-002
2. I0-003 / I0-004 in parallel
3. I0-005 alignment and acceptance
4. I0-006
5. I0-007 formal acceptance

### Lane B — Local foundation

Current next task: `L0-002`

Planned order:

- `L0-002 → L0-003/L0-004/L0-005 → L0-006`
- `L1-001 → L1-002 → L1-004 → L1-005` via fixture path

`L1-003` remains blocked by the separately approved `SMOKE-007` change window and must not block the fixture path.

### Lane C — Cross-Market extension

| Task | Status | Next action |
|---|---|---|
| A0-001 | Provisional result | Design complete; wait for I0-002/I0-005 acceptance, then reflect fields/schema/fixtures |
| A0-002 | Not started | dataset/source definition may proceed before final schema write |

### Lane D — SEC / Earnings

Blocked until `I0-007` formal acceptance.
After the gate opens:

`S0-002 → S0-003 → (S0-005 || S0-006) → S0-007 → E0-001〜007`

## 5. Known non-blockers / deferred items

- `L1-003` remote D1 export change window is deferred and does not block local fixture implementation.
- `A0-002` is a validation lane and is not currently a serial blocker for Core Corporate Intelligence.
- Existing provisional artifacts for `I0-005`, `I0-007`, and `S0-004` must be preserved and reconciled rather than discarded.

## 6. Current restart rule

- Main local session: `I0-002`
- Second parallel local session: `L0-002`
- Cross-Market session: `A0-002` dataset/source definition only until `I0-002/I0-005` are Accepted
- SEC implementation must wait for `I0-007` formal acceptance

## 7. Unresolved items

- Analyst Consensus as-of history provider and contract conditions
- AI/Semiconductor proxy definition for A0-002
- short/borrow data provider for H4 validation
- whether A0-002 becomes mandatory for v0.1 release acceptance
- exact acceptance evidence needed to promote provisional `I0-005`, `I0-007`, and `S0-004/S0-007` artifacts after dependency integration

Do not infer unresolved values; update this tracker only from repository evidence, test results, or confirmed external contract/source information.
