# OrderScope — Codex Local Harness Setup Guide

Status: implementation preparation guide (non-normative)
Date: 2026-09-05
Scope: Local Corporate Intelligence work management

## 1. Purpose

ローカルCodex環境に専用ハーネス実装が存在しない状態から、OrderScopeのWBS / Critical Path / Progress Tracker / Model Assignment Policyを使って安全に作業を委任・レビュー・記録できる最小構成を整備するための準備資料。

この文書は、特定のAgent frameworkや外部orchestratorへ固定しない。最初は手動運用可能な境界を作り、その後必要に応じて自動化する。

## 2. Design principles

1. WBS / CP / Trackerを正本とし、ハーネス内部に独自の作業状態を持たない。
2. 1 Agent = 1 bounded change setを基本とする。
3. 親Agentと実装Agentの責任を分離する。
4. Model Assignment Policyを作業選択とは別のポリシー層として扱う。
5. Agent成果はdiff/testを親が再確認する。
6. Progress Tracker更新を作業完了条件の一部にする。
7. Secret、provider response body、raw dumpをAgent間handoffへ含めない。
8. 並列化は依存関係が明確なtaskだけに限定する。
9. ハーネス障害時は手動再開可能であること。
10. Codex固有機能へ依存しすぎず、将来CLI/IDE/別Agent harnessへ移行可能にする。

## 3. Minimal operating architecture

```text
Management documents
  ├─ WBS
  ├─ Critical Path
  ├─ Progress Tracker
  └─ Model Assignment Policy
          ↓
Parent Orchestrator
  ├─ select one task
  ├─ resolve dependencies
  ├─ choose model / effort
  ├─ create bounded work packet
  └─ review result
          ↓
Execution Agent
  ├─ inspect bounded files
  ├─ implement
  ├─ run tests
  └─ return structured result
          ↓
Parent Orchestrator
  ├─ inspect diff
  ├─ verify tests
  ├─ decide acceptance state
  └─ update Progress Tracker
```

ハーネス未実装の初期段階では、この構造を複数Codexセッションまたは同一セッション内の明示的なrole切替で模倣できる。

## 4. Required artifacts

### 4.1 Management input

必須:

- `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/MODEL_ASSIGNMENT_POLICY_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/CODEX_LOCAL_ORCHESTRATION_PROMPT_2026-09-05.md`

### 4.2 Work packet

親Agentは子Agentへ最低限次を渡す。

```yaml
task_id: I0-002
objective: <WBS task text>
completion_conditions:
  - <condition>
dependencies:
  - I0-001
allowed_paths:
  - analysis/...
  - docs/... only when required
forbidden_changes:
  - WBS completion conditions
  - Critical Path ordering
known_provisional_results:
  - I0-005
required_tests:
  - <commands>
model: GPT-5.6 Terra
reasoning_effort: high
return_contract:
  - changed_files
  - tests_run
  - test_results
  - unresolved_items
  - suggested_tracker_update
```

初期実装ではYAMLファイルを自動生成する必要はない。上記項目をprompt templateとして使えばよい。

## 5. Parent orchestrator responsibilities

親Agentだけが次を行う。

- 現在の主タスク選択
- dependency gate判定
- model / reasoning effort選択
- allowed/forbidden scope確定
- Provisional resultとの統合判断
- 子Agent成果の受入レビュー
- Progress Trackerの状態変更
- Critical Path変更提案

通常の親Agent推奨:

- Sol low: 通常cycle
- Sol medium: 初回監査、矛盾、Accepted昇格
- Sol high: CP変更、architecture境界、複数lane衝突

Terraを親にする場合:

- medium: 通常cycle
- high: integration review
- Sol review: Provisional→Accepted、CP変更、高影響schema変更

## 6. Execution agent responsibilities

子Agentは割り当てられたtask内だけを担当する。

行うこと:

- 指定pathと関連依存を読む
- bounded implementation
- fixture/test追加
- test実行
- structured result返却

行わないこと:

- 次タスクへ進む
- WBS/CPを書き換える
- dependencyを推測で解除する
- Provisional resultを独断でAcceptedにする
- 別laneのrefactorを便乗して行う

## 7. Result contract

各実行Agentは最低限次を返す。

```text
Task: I0-002
Status: completed / partial / blocked
Changed files:
- ...
Tests:
- command -> pass/fail
Completion condition check:
- condition A: pass
- condition B: pass/partial
Unresolved:
- ...
Potential cross-task impacts:
- I0-005: ...
Recommended next state:
- In progress / Provisional result / Accepted candidate
```

親Agentがこの結果と実diff/testを照合する。

## 8. Progress Tracker update contract

Trackerには最低限以下を記録する。

- timestamp/date
- task ID
- previous status → new status
- model / reasoning effort
- model selection rationale
- changed files
- test evidence
- acceptance evidence
- unresolved items
- next safe action

子AgentがTrackerを直接更新する運用も可能だが、初期段階では親Agentだけが更新する方が安全。

## 9. Failure and recovery rules

### Agent failure

- partial変更を勝手に次Agentへ継承しない
- `git diff`とtest状態を確認
- rollback可能ならtask boundary内で戻す
- partial成果を残す場合はTrackerへProvisionalとして記録

### Parent session interruption

再開時は必ず:

1. Progress Tracker
2. git status / diff
3. last test result
4. current task ID
5. allowed scope

を再確認する。

### Conflicting edits

同一ファイルを複数Agentへ並列割当しない。
同一schemaを触るtaskは原則直列化する。

## 10. Concurrency policy

初期段階の推奨最大並列数は2。

安全な例:

- I0-002 と L0-002

避ける例:

- I0-002 と I0-005
- I0-003 と I0-007 formal acceptance
- S0-003 と S0-004 integration review when same schema is changing

並列化判断はCritical Pathとfile overlapの両方で行う。

## 11. Suggested repository structure for future harness implementation

実装する場合の候補:

```text
tools/
└─ codex-harness/
   ├─ README.md
   ├─ task_packet.schema.json
   ├─ result.schema.json
   ├─ prompts/
   │  ├─ orchestrator.md
   │  └─ executor.md
   ├─ scripts/
   │  ├─ build_task_packet.py
   │  ├─ validate_result.py
   │  └─ append_progress.py
   └─ examples/
      └─ I0-002.yaml
```

現時点では未実装。必要性が確認されるまではdocsのみで運用する。

## 12. Harness implementation phases

### H0 — Manual structured operation

- prompt template使用
- work packetを手動作成
- 子Agent結果をstructured formatで返す
- Trackerは親Agentが手動更新

追加コード不要。

### H1 — Validation helpers

- task packet schema
- result schema
- path scope checker
- test command recorder
- Tracker追記helper

この段階でもAgent起動自体は手動。

### H2 — Local orchestration wrapper

- task選択補助
- model/effort mapping
- 子Agent起動
- result collection
- diff/test validation

Codex CLI/Desktopで実際に利用可能なsub-agent invocation interfaceを確認してから設計する。

### H3 — Parallel orchestration

- dependency-aware scheduling
- file overlap lock
- retry / timeout
- interrupted session recovery

H0/H1で運用上の必要性が確認されるまで実装しない。

## 13. Current recommendation

現在はH0から開始する。

理由:

- Local Corporate IntelligenceのWBS/CP/Trackerは既に存在する
- model assignment policyも定義済み
- task境界はWBS上で十分細かい
- 自動orchestrationを先に作ると、本体I0/L0作業よりハーネス開発が先行する

まずI0-002/L0-002をH0運用で1〜2 cycle実施し、繰り返し手作業になった部分だけH1へ昇格する。

## 14. Open questions before H1/H2

- ローカルCodexが子Agentごとにmodelを明示指定できるか
- 子Agentごとにreasoning effortを指定できるか
- sub-agent invocationの標準interfaceが存在するか
- session間でstructured resultを安全に受け渡す標準方法
- Codex Desktop / CLIのどちらを主運用面とするか
- allowed path enforcementをCodex側に任せられるか、外部validatorが必要か

これらは実環境を確認してから確定する。
