# OrderScope — Web企業情報調査・進捗トラッカー

Status: active operational tracker (non-normative)
Date: 2026-09-03
Scope: `REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md`
Parent plan: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`

## 1. 目的

`WEB-001`〜`WEB-020`を管理する単一の進捗台帳である。会話履歴を正本にせず、別のChatGPT Webセッションから参照・更新できるようにする。

Web作業の意味は可視化レポート、本日時点のWeb進捗・Evidence・handoff・次の操作は本書を正とする。W0/L0/L1/I0/S0/E0/N0/N1/O0/X0の完了条件は、引き続き親作業分解文書を正とする。

## 2. 状態定義

| 状態 | 意味 |
|---|---|
| `未着手` | repositoryに調査成果がまだ存在しない。依存条件を満たしているものは着手可能 |
| `進行中` | 記録されたsessionが調査または文書化を実行中 |
| `調査完了` | Web成果物と公式Evidenceが完成。ローカルhandoffまたは親タスク実装は残り得る |
| `引渡し済み` | 成果物のローカル利用先が明確で、その作業を開始できる状態 |
| `保留（依存）` | 先行Web成果、ローカルcontract/adapter形状、またはユーザー判断が必要 |
| `保留（外部）` | access、licence、契約確認、公式開示など外部条件が必要 |
| `再確認要` | 完了済みの時点情報が古いか、source・料金・条件の変更可能性がある |

`調査完了`または`引渡し済み`は、対応する親タスクの完了を意味しない。品質に関する数値はローカル実測証跡が必要である。

## 3. 現在地

2026-09-03時点のWeb作業カタログは20件である。

| 状態 | 件数 |
|---|---:|
| 未着手 | 5 |
| 進行中 | 0 |
| 調査完了 | 0 |
| 引渡し済み | 3 |
| 保留（依存） | 12 |
| 保留（外部） | 0 |
| 再確認要 | 0 |

即時着手可能なのは`WEB-003`、`WEB-005`、`WEB-008`、`WEB-011`、`WEB-015`である。`WEB-004`は履歴付きregistry seedを`I0-001`へ引渡し済みである。`WEB-008`は`WEB-001`のidentity handoffを利用できる。`WEB-011`は候補調査を開始できるが、採否提案には`WEB-003`の利用条件確認方式を適用する。

隣接作業の既知状態は次のとおり。

- `W0-001`はローカルMVP開始条件として満たされている。Workerの残り`SMOKE-*`、`CANARY-*`は別バックログである。
- `L0-001`は`ADR_LOCAL_ANALYSIS_STACK_v0.1.md`により完了している。
- 次のローカル実装は`L0-002`である。
- 親作業分解と既存実装トラッカー上、WorkerとPredictionはShadowを維持する。

## 4. タスク台帳

| Web ID | 親 | Wave | 状態 | 依存・blocker | 成果物・Evidence | ローカルhandoff | 次の操作 | 最終更新 | Session |
|---|---|---|---|---|---|---|---|---|---|
| WEB-001 | W0-002 | A | 引渡し済み | なし | [`REPORT_CORPORATE_CANARY_IDENTITY_WEB_001_2026-09-03.md`](REPORT_CORPORATE_CANARY_IDENTITY_WEB_001_2026-09-03.md); Evidence確認 2026-09-03T11:43:05Z | I0-001、S0-002、E0-003 | I0-001で内部ID、履歴、share classのschemaをreview・実装 | 2026-09-03 | web-2026-09-03-WEB-001 |
| WEB-002 | W0-003 | A | 引渡し済み | なし | [`REPORT_OFFICIAL_SOURCE_SCOPE_WEB_002_2026-09-03.md`](REPORT_OFFICIAL_SOURCE_SCOPE_WEB_002_2026-09-03.md); Evidence確認 2026-09-03T12:18:39Z | I0-001、WEB-004、O0-001/002 | source laneとowner/actor境界をWEB-004の履歴付きregistry案へ変換。恒久入口・feed詳細はWEB-015/016で継続 | 2026-09-03 | web-2026-09-03-WEB-002 |
| WEB-003 | W0-004 | A | 未着手 | なし | 既存Provider調査は時点情報 | S0-001、N0-001、adapter ADR | 共通の公式利用条件確認票を作成 | 2026-09-03 | — |
| WEB-004 | I0-001 | B | 引渡し済み | WEB-001/002引渡し済み | [`REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`](REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md); Evidence再確認 `2026-09-03T15:53:08Z` | I0-001 registry schema・migration・contract test | 共通Actor、nullable外部validity、listing/source endpoint履歴、Evidence制約を実装。AMD venue履歴のunknown gapをfixtureで検証 | 2026-09-03 | web-2026-09-03-WEB-004 |
| WEB-005 | S0-001 | A | 未着手 | なし | SEC EDGAR/XBRLはv0.1 baseline | S0-002〜007 | SEC公式接続・Fair Access条件を再確認 | 2026-09-03 | — |
| WEB-006 | S0-004 | B | 保留（依存） | WEB-005 | form一覧は親計画で固定済み | S0-004 test/fixture | 公式のform目的・例外対応表を作成 | 2026-09-03 | — |
| WEB-007 | E0-001 | C | 保留（依存） | WEB-001済、残りWEB-005 | — | Earnings contract実装 | 必須の時刻・会計区分を示すCanary事例を収集 | 2026-09-03 | — |
| WEB-008 | E0-003 | B | 未着手 | WEB-001引渡し済み | WEB-001でIR入口確認済み | IR fallback adapter | AMD/NVDAのstable release/archive経路を調査 | 2026-09-03 | — |
| WEB-009 | E0-005 | C | 保留（依存） | WEB-001済、残りWEB-005 | — | segment fallback実装 | 複数四半期のsegment source可用性を整理 | 2026-09-03 | — |
| WEB-010 | E0-007 | D | 保留（依存） | WEB-007〜009とlocal contract形状 | — | local reconciliation・品質report | field確定後に公式照合setを準備 | 2026-09-03 | — |
| WEB-011 | N0-001 | A | 未着手 | 候補調査はなし。採否にはWEB-003 | 既存Provider調査の更新が必要 | News Provider ADR | 現行価格、履歴、rate、本文権利を更新 | 2026-09-03 | — |
| WEB-012 | N0-003 | C | 保留（依存） | WEB-011 | — | canonicalization fixture/test | 対象Providerに対応する重複・転載・訂正例を収集 | 2026-09-03 | — |
| WEB-013 | N1-001 | C | 保留（依存） | WEB-007とI0-005のcontract方針 | 親計画に初期分類あり | taxonomy schema・extractor fixture | 定義とEvidence付き事例を作成 | 2026-09-03 | — |
| WEB-014 | N1-006 | D | 保留（依存） | WEB-008、WEB-010とlocal評価形状 | — | recall/latency評価 | 1〜3か月のSEC/IR基準イベントsetを準備 | 2026-09-03 | — |
| WEB-015 | O0-001 | A | 未着手 | なし | official actor種別は親計画で固定済み | O0-002 adapter設計 | 恒久入口を含むofficial source registryを作成 | 2026-09-03 | — |
| WEB-016 | O0-002 | B | 保留（依存） | WEB-002、WEB-015 | — | official feed adapter | source別のRSS/API/更新一覧を調査 | 2026-09-03 | — |
| WEB-017 | O0-003 | C | 保留（依存） | WEB-015、WEB-016 | — | official Fact type fixture | 発言・提案と施行・正式決定の事例を収集 | 2026-09-03 | — |
| WEB-018 | O0-004 | C | 保留（依存） | WEB-001済、残りWEB-015、WEB-017 | — | instrument/theme関連付け実装 | Evidence閾値とCanary事例を定義 | 2026-09-03 | — |
| WEB-019 | O0-005 | D | 保留（依存） | WEB-016〜018とlocal adapter形状 | — | Official Signal品質test | update/delete/重複/時刻fixture候補を準備 | 2026-09-03 | — |
| WEB-020 | X0-006 | D | 保留（依存） | WEB-003、005、011、016とlocal実装証跡 | — | Canary運用runbook | 公開制約部分を作成し、未試験操作を明示 | 2026-09-03 | — |

## 5. 親タスクへのhandoff

| 親領域 | Web入力 | 親タスク完了に必要なローカル証跡 |
|---|---|---|
| W0 境界 | WEB-001〜003 | 必要に応じたregistry/config review |
| I0 契約 | WEB-004 | schema、履歴意味論、contract test |
| S0 SEC | WEB-005/006 | adapter、永続化、filter、文書/XBRL、受入試験 |
| E0 決算 | WEB-007〜010 | 検出、抽出、fallback、segment履歴、品質実測 |
| N0/N1 News | WEB-011〜014 | adapter、canonicalization、本文lifecycle、抽出、retention、recall実測 |
| O0 公式情報 | WEB-015〜019 | feed adapter、Fact type、関連付け、fixture試験 |
| X0 統合 | WEB-020 | timeline/API/scheduler/E2E証跡と試験済みrunbook |

## 6. 更新手順

### 着手時

1. trackerの最新版を取得する。
2. 台帳の依存条件を確認する。
3. 対象を`進行中`へ変更する。
4. `Session`へChatGPT session識別子または安定したsession名を記録する。
5. `次の操作`を今回実行する限定的な調査内容へ更新する。

### Web調査完了時

1. 対象範囲を限定した成果物を`docs/`へ保存する。
2. `成果物・Evidence`へ相対linkと確認日を記録する。
3. `ローカルhandoff`へ利用する親・ローカルタスクを記録する。
4. 成果物はあるがhandoff充足を未確認なら`調査完了`とする。
5. 利用先が明確で着手可能なら`引渡し済み`とする。
6. 状態別件数を再計算する。
7. Session logへ1行追加する。

### 不明・変更への対応

- 先行成果が不足する場合は`保留（依存）`とする。
- access、licence、非公開条件が必要なら`保留（外部）`とする。
- 料金、規約、URL、API、公式ルールが古くなった場合は`再確認要`とする。
- `記載なし`、`未発見`、未解決質問を明示し、推測で補完しない。
- ローカル実行証跡が必要な親タスクをWeb調査だけで完了にしない。

## 7. Session log

| UTC日付 | Session | Web ID | 変更 | Evidence・成果物 | 次の操作 |
|---|---|---|---|---|---|
| 2026-09-03 | initial tracker creation | WEB-001〜020 | カタログ、依存Wave、状態、handoffを作成 | `REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md` | Wave Aを開始。最初の限定タスクはWEB-001またはWEB-005 |
| 2026-09-03 | web-2026-09-03-WEB-001 | WEB-001 | AMD/NVDAのCIK、ticker、security class、exchange、公式IR入口を公式一次情報で確認し、version付きregistry案を引渡し | `REPORT_CORPORATE_CANARY_IDENTITY_WEB_001_2026-09-03.md`; Evidence確認 2026-09-03T11:43:05Z | I0-001でregistry schemaを実装。Web側はWEB-002/003/005/015または解放済みWEB-008へ進む |
| 2026-09-03 | web-2026-09-03-WEB-002 | WEB-002 | SECをEDGAR/当局発表に分離し、AMD/NVIDIA IR、White House、Treasury、Federal Reserve Boardの対象範囲と一般SNS等の除外範囲を固定して引渡し | `REPORT_OFFICIAL_SOURCE_SCOPE_WEB_002_2026-09-03.md`; Evidence確認 2026-09-03T12:18:39Z | WEB-004で履歴付きsource/entity対応案を作成。WEB-015/016で恒久入口とfeed挙動を詳査 |
| 2026-09-03 | web-2026-09-03-WEB-004 | WEB-004 | AMD/NVIDIAのcompany・instrument・CIK・ticker/listingと、7つの公式source laneのowner/publisher/content actor規則を履歴付きregistry seedへ変換して引渡し | `REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`; Evidence再確認 `2026-09-03T15:48:29Z` | I0-001でactor統合、履歴schema、Evidence制約、as-of/identity contract testを実装。Web側はWEB-003/005/008/015へ進む |
| 2026-09-03 | web-2026-09-03-WEB-004-followup | WEB-004 | 並行セッションの完了成果を維持して競合を解消し、AMDの2017年NASDAQ Capital Market／2020年Global Select Market Evidenceと、正確な切替日を推測しない履歴規則を追記 | `REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`; 追加Evidence確認 `2026-09-03T15:53:08Z` | I0-001 contract testでvenue切替のunknown gapを保持。次のWeb候補はWEB-003/005/008/015 |
| 2026-09-03 | web-2026-09-03-WEB-004-verification | WEB-004 | 対象remote branchへの反映、成果物link、状態別件数を照合し、AMD 2017/2020 Form 10-K、NVIDIA 2026 Form 10-K、SEC association file注意事項を公式一次情報で再確認。追加修正なし | `REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`; 限定再確認 `2026-09-03T16:00:29Z` | WEB-004は引渡し済みを維持。次セッションは優先度と依存を確認してWEB-003/005/008/011/015のいずれかに着手 |

## 8. 更新時チェックリスト

- [ ] 編集前に対象ブランチの最新版を読んだ。
- [ ] 変更したタスクの`WEB-*` IDと親IDを維持した。
- [ ] Fact、Interpretation、ローカル完了主張を分離した。
- [ ] 公式sourceへの直接linkと確認日を記録した。
- [ ] 不明値を明示した。
- [ ] credential、account identifier、provider response body、制限対象本文を含めていない。
- [ ] 時点依存の料金・条件に再確認条件を付けた。
- [ ] 状態別件数と台帳が一致する。
- [ ] Session logと次の操作を更新した。

## 9. 関連文書

- `REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md`
- `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `IMPLEMENTATION_PROGRESS_TRACKER_2026-09-01.md`
- `ADR_LOCAL_ANALYSIS_STACK_v0.1.md`
- `MERMAID_CONVENTIONS.md`
