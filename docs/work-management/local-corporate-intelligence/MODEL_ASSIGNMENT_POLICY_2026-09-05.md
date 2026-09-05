# OrderScope — Local Corporate Intelligence Model / Agent Assignment Policy

Status: active execution guidance (non-normative)
Date: 2026-09-05
Scope: Local Corporate Intelligence parent WBS and A0 extension

## 1. Purpose

この文書は、WBSの完了条件やCritical Pathを変更せず、各作業をどのモデルへ委任するのが適切かを判断するための運用ガイドである。
モデル名は作業の正当性や完了条件を構成しない。モデル構成が将来変更された場合は、この文書だけを更新し、WBSの意味を変更しない。

## 2. Model roles

| Model | Primary role | Suitable work | Avoid as sole owner |
|---|---|---|---|
| GPT-5.6 Luna | bounded executor | 変更範囲が限定された実装、fixture/test追加、定型adapter、単一契約の機械的反映、既知仕様に沿う修正 | 複数管理資料の再解釈、曖昧な設計判断、複数先行成果の統合受入、Critical Path再計算 |
| GPT-5.6 Terra | integration executor | 複数ファイル実装、schema/adapter/testの整合、既存実装との統合、中規模設計、受入前レビュー | WBS/CPそのものを再構成する高影響判断をレビューなしで確定 |
| GPT-5.6 Sol | orchestrator / acceptance reviewer | WBS・CP・Tracker横断、作業分割、Agent割当、設計境界、Provisional resultの統合、受入判定、矛盾解消 | 小さな機械的修正を常に直接実装する必要はない。Luna/Terraへ委任可能 |

## 3. Reasoning effort guidance

reasoning effortはモデル適性とは別軸として扱う。

| Work class | Sol | Terra | Luna |
|---|---|---|---|
| B1: bounded implementation | low | low〜medium | medium |
| B2: multi-file implementation | low〜medium | medium | high only when scope is tightly specified |
| B3: integration / acceptance | medium | high | 原則 sole owner にしない |
| B4: architecture / CP / conflicting evidence | high | high〜xhigh | 委任しない |
| Orchestrator cycle: task選択→Agent委任→結果レビュー→Tracker更新 | low可。初回監査・矛盾発生時はmedium | medium推奨。複数Provisional統合時はhigh | 非推奨 |

`low`を使う条件:

- WBS、CP、Trackerが既に整合している
- 1 cycleで主タスクを1つに限定する
- 子Agentの成果を親Agentがtest結果とdiffで再確認する
- 新しい設計判断を作らない
- Provisional resultの受入昇格を伴わない、または既定gateだけで判定できる

上記を満たさない場合は1段階上げる。

## 4. Assignment rules

1. WBS/CP/Trackerを読み、最初に作業IDを1つ固定する。
2. 完了条件・依存・既存成果を確認してからモデルを選ぶ。
3. Lunaへは原則として1 Agent = 1 bounded change setとする。
4. Terraへは関連するschema + implementation + test程度の複数ファイル変更をまとめてよい。
5. Solは作業分割、依存確認、Agent成果の統合レビュー、Acceptedへの昇格判断を担当する。
6. `Provisional result → Accepted`、Critical Path変更、複数laneを跨ぐschema変更はSol reviewを要求する。
7. 外部契約・provider条件・データ解釈が未確定なら、モデル能力で推測補完しない。
8. モデル選択理由をProgress Trackerへ1行で記録する。

## 5. Parent WBS task suitability

Legend:

- **L** = Luna primary
- **T** = Terra primary
- **S** = Sol primary/review owner
- `L/T` = Lunaで実装可能、複数ファイル化したらTerra
- `T+S` = Terra実装、Sol受入レビュー
- `L/T+S` = bounded実装はLuna/Terra、受入はSol

### W0 — Boundary / Canary / provider governance

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| W0-001 | S | low | backlog境界とLocal開始条件の整合確認。管理資料横断だが判断は既定 |
| W0-002 | T+S | medium | registry表現は実装可能だがinstrument/ticker/CIK/IR identityの整合レビューが必要 |
| W0-003 | S | medium | v0.1 scope境界の設計判断 |
| W0-004 | T+S | medium | checklist作成はTerra、契約条件の採否・例外はSolレビュー |

### L0 — Local foundation

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| L0-001 | S | medium | stack ADR。複数技術選択とWindows/WSL境界を確定 |
| L0-002 | L | medium | scaffold/.gitignore中心のbounded change |
| L0-003 | T | medium | config/schema/secret/logging testの複数ファイル整合 |
| L0-004 | L/T | medium | localhost bind + test。小規模ならLuna |
| L0-005 | T | medium | migration設計と再生成性の整合 |
| L0-006 | T | medium | CLI command groupと既存config/migration/health統合 |

### L1 — Market import / quality

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| L1-001 | T | medium | manifest schema/provenance/checksum契約 |
| L1-002 | L/T | medium | importer + idempotency fixture。境界明確ならLuna |
| L1-003 | S | high | remote変更窓、停止/再開/catch-upを伴う運用判断 |
| L1-004 | T | medium | bar/receipt provenance保持とParquet決定順生成 |
| L1-005 | T+S | medium | 品質規則が複数dimensionを跨ぐ。閾値・gap解釈はSol review |
| L1-006 | T | medium | read-only API統合 |

### I0 — Common External Information / Fact contracts

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| I0-001 | T+S | medium | source/entity履歴registry。identity境界レビューが重要 |
| I0-002 | T+S | high | provenanceと複数timestampの意味境界。後続多数に波及 |
| I0-003 | T+S | medium | cursor/checkpoint/pagination/partial/error契約 |
| I0-004 | T+S | high | stable ID、update、duplicate、conflictの意味境界 |
| I0-005 | T+S | high | Fact/Evidence/Relationship/Derived/Interpretation分離。Provisional統合受入を含む |
| I0-006 | T+S | medium | retention/expiry/delete proof/exception lifecycle |
| I0-007 | L/T+S | high | test kit実装自体は委任可。正式受入は複数上流契約を横断するためSol |

### S0 — SEC Filing

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| S0-001 | T+S | medium | 公式条件調査はTerra、採用条件はSol review |
| S0-002 | T | medium | provider adapterのbounded incremental実装 |
| S0-003 | T | medium | FilingRecord永続化とidempotency |
| S0-004 | L/T+S | medium | form filterはbounded。既存Provisional接続時のみSol review |
| S0-005 | T | medium | temporary content lifecycleとの統合 |
| S0-006 | T+S | high | XBRL unit/period/dimension/provider-neutral正規化は意味整合が難しい |
| S0-007 | T+S | high | new/duplicate/amendment/partialを含むCanary受入判定 |

### E0 — Earnings / Fundamental

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| E0-001 | T+S | high | schedule/result、GAAP/non-GAAP、source時刻境界の契約 |
| E0-002 | T | medium | SEC filingからcandidate生成 |
| E0-003 | T+S | high | SEC/IR dedupとsource priorityの統合 |
| E0-004 | T | medium | 明示Fact抽出。欠損推測禁止で境界明確 |
| E0-005 | T+S | high | Company Facts→Dimension→Filing fallbackの意味・失敗理由統合 |
| E0-006 | T+S | high | rename/merge/split/recast identity historyは意味判断が多い |
| E0-007 | S | high | 複数四半期・複数sourceの品質受入と未解決差異判定 |

### N0/N1 — News acquisition / Fact extraction

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| N0-001 | S | high | 価格・権利・internal-use条件を比較して採否ADR化 |
| N0-002 | T | medium | metadata adapter実装 |
| N0-003 | T+S | high | canonical URL、syndication、update分類の意味境界 |
| N0-004 | T | medium | temporary body accessを既定lifecycleへ接続 |
| N1-001 | S | high | event taxonomyという意味論設計 |
| N1-002 | L/T | medium | deterministic baseline。パターン境界が固定されれば委任しやすい |
| N1-003 | T+S | high | evidence span/confidence/versionとLLM境界の設計 |
| N1-004 | S | high | SEC/IR contradiction、ambiguity、pending reviewの判断 |
| N1-005 | T+S | medium | retention controller実装 + compliance確認 |
| N1-006 | S | high | recall/lag/misattributionの評価設計と結果解釈 |

### O0 — Official / policy context

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| O0-001 | T+S | medium | actor/source identity registry |
| O0-002 | T | medium | feed adapter実装 |
| O0-003 | T+S | high | statement/proposalとsigned/implementedのFact type境界 |
| O0-004 | S | high | direct instrument relationとtheme indirect relationのEvidence判断 |
| O0-005 | T+S | high | update/delete/identity/relevanceを含む品質受入 |

### X0 — Integration / local observability

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| X0-001 | T+S | high | market/filing/earnings/news/officialのas-of統合timeline |
| X0-002 | T | medium | coverage/health summaryの集約 |
| X0-003 | T | medium | localhost read-only API統合 |
| X0-004 | T+S | high | scheduler、lock、resume、dry-run、adapter横断 |
| X0-005 | T+S | high | E2E deterministic regenerationの統合受入 |
| X0-006 | S | high | credential/rate/recovery/delete/backupを跨ぐ運用runbook |

## 6. A0 extension task suitability

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| A0-001 | S | high | Cross-Market RotationをFact化しない境界、FX contradiction、confidence ruleの意味論設計 |
| A0-002 | T+S | high | dataset整列・計算はTerra、5仮説のsupport/contradiction統合判断はSol |

## 7. Current restart assignment

2026-09-05のProgress Tracker/Integrated CPに対しては次を推奨する。

- Orchestrator: **Sol low** で開始可
- Main task `I0-002`: **Terra high** で実装・既存コード調査、**Sol medium/high** で受入レビュー
- Parallel `L0-002`: **Luna medium**
- A0-002 dataset/source definition only: **Terra medium**。仮説評価開始時はSol reviewを追加

Sol low orchestratorは、主タスク選択・bounded delegation・diff/test review・Tracker更新に限定する。
I0-002の設計内容そのものをSolが直接確定するcycleではmedium以上へ上げる。

## 8. Escalation triggers

以下のいずれかが発生したら、現在のAgentを停止せず成果を保存し、親Agentのreasoning/modelを1段階上げて再レビューする。

- 3つ以上のdomain（例: provenance + Fact Store + A0）へschema影響が波及
- 既存Provisional resultと新実装が矛盾
- WBS完了条件の解釈が2通り以上成立
- testは通るがsemantic invariantが確認できない
- remote mutation / credential / retention / provider contractを伴う
- `Accepted`昇格またはCritical Path変更を提案する

