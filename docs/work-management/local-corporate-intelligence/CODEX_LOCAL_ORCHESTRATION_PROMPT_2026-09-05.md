# OrderScope — Codex Local Orchestration Resume Prompt

Status: active execution prompt template (non-normative)
Date: 2026-09-05

## Purpose

ローカルCodex環境で Local Corporate Intelligence の作業を安全に再開するための親Agent向けプロンプト。
ハーネス実装が存在しない環境でも、管理資料・モデル適正・作業境界・Progress Tracker更新を手順化して運用する。

## Prompt

次の4ファイルを作業管理上の正本として参照してください。

- `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/MODEL_ASSIGNMENT_POLICY_2026-09-05.md`

まず4ファイルと現在のrepository状態を確認し、以下を特定してください。

1. Progress Tracker上の現在の主作業
2. WBS上の完了条件と依存関係
3. Critical Path上の後続・並列タスク
4. 既存実装、fixture、test、先行成果、Provisional resultとの整合
5. Model Assignment Policy上の推奨モデルとreasoning effort

今回の作業対象は、Progress Trackerで主作業として指定されているタスクを原則1つに限定してください。
後続タスクへ自動的に進まないでください。
並列laneを同時に変更しないでください。
既存のProvisional resultは削除・再実装せず、整合対象として扱ってください。

対象タスクを、単独でreview・test・rollback可能な作業単位へ分割してください。
Agent委任が可能な場合は、1 Agent = 1 bounded change setを基本としてください。

モデル選択は `MODEL_ASSIGNMENT_POLICY_2026-09-05.md` に従ってください。
管理資料にモデル適正が明示されていない新規作業では、推測で割り当てず、作業クラスをB1〜B4に分類して選定理由を記録してください。

親Agentは以下を担当してください。

- タスク選択
- 依存確認
- Agentへの作業境界提示
- Agent成果のdiff/testレビュー
- WBS完了条件との照合
- Provisional resultと既存schema/test/fixtureの整合確認
- Acceptedへ昇格可能かの判定
- Progress Tracker更新

子Agentの成果をそのまま採用しないでください。
以下を確認してから統合してください。

- WBSの完了条件を満たすこと
- 上流契約を破壊していないこと
- 後続タスクの前提を壊していないこと
- 既存testと新規testが通ること
- Secret/credential/provider raw bodyをGitへ追加していないこと
- 変更範囲が対象タスクの境界を越えていないこと

`Provisional result → Accepted`、Critical Path変更、複数laneに跨るschema変更、既存設計との矛盾が発生した場合は、通常実装を停止して高位レビューへ切り替えてください。

作業完了後は、
`docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
へ以下を追記してください。

- 実施タスクID
- 使用モデル / reasoning effort
- モデル選定理由
- 変更ファイル
- test結果
- 完了条件への適合状況
- 状態変更
- 残作業
- 次の安全な作業
- 未解決事項

WBSやCritical Pathの完了条件・依存関係そのものは、実装都合だけで変更しないでください。
不明な設計判断や未確定事項を推測で補完せず、Progress Trackerへ未解決事項として記録してください。

## Recommended current execution profile

2026-09-05時点の現在地:

- Parent orchestrator: Sol low
- Main task `I0-002`: Terra high + Sol acceptance review
- Parallel `L0-002`: Luna medium
- A0 dataset/source definition: Terra medium

ハーネス未実装環境では、実際に複数Agentを同時起動できない場合でも、この分担を「作業境界とレビュー責任」のルールとして使用する。
