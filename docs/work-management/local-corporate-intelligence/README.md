# Local Corporate Intelligence — Work Management Index

Status: active management index (non-normative)
Date: 2026-09-05

このディレクトリは、Local Corporate Intelligence 周辺の作業管理資料への入口を一元化する。
既存文書は他資料から参照されているため、2026-09-05時点では破壊的な移動を行わず、正本の場所を明示して管理する。

## Core management documents

| Role | Canonical document | Purpose |
|---|---|---|
| Parent WBS | `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md` | Local Corporate Intelligence 全体の作業分解、完了条件、依存関係を定義する実行バックログ |
| Integrated Critical Path | `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md` | Parent WBS と A0 拡張を重ね、現在の主CP、並列lane、再開優先順位を示す |
| Local Progress Tracker | `LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` | WBS/CPのタスク状態、依存充足、先行成果、次の安全な作業を記録する |

## Extension / parallel management documents

| Role | Canonical document | Purpose |
|---|---|---|
| A0 extension WBS | `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md` | Analyst Consensus / Macro / Cross-Market Context の追加WBS |
| A0 progress tracker | `../../ANALYST_CROSS_MARKET_PROGRESS_TRACKER_2026-09-05.md` | A0-001/A0-002 の進捗・検証状態を管理 |
| Web workstream plan | `../../REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md` | Web側で実施する調査タスクの作業ストリーム定義 |
| Web progress tracker | `../../WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md` | Web-xxx 調査タスクの実施状況・成果物を管理 |
| Worker implementation plan | `../../WORK_PLAN_INITIAL_VALIDATION_AND_LONG_TERM_OPERATIONS_2026-09-01.md` | Market Workerの初期検証と長期運用の工程定義 |
| Worker implementation tracker | `../../IMPLEMENTATION_PROGRESS_TRACKER_2026-09-01.md` | Market Workerの実装・運用証跡、外部依存、次操作を管理 |
| Worker progress report | `../../PROGRESS_REPORT_2026-09-01.md` | 2026-09-01時点のWorker進捗を圧縮したスナップショット |

## Role boundaries

- WBS は「何を完了させるか」を定義する。
- Critical Path は「どの依存順で進めると全体完了へ最短で到達するか」を示す。
- Progress Tracker は「今どこまで終わったか、何がブロックされているか、次に何を安全に進めるか」を記録する。
- Report / Workstream は調査結果や特定laneの実行計画であり、Parent WBSの代替ではない。

## Current restart point

2026-09-05 integrated CP に従い、Local Corporate Intelligence の主作業は `I0-002`。
並列laneは `L0-002`、A0側は `A0-002` のdataset/source定義まで先行可能。
`I0-005`、`I0-007`、`S0-004` は先行成果を破棄せず、依存充足後に正式受入・整合を行う。
