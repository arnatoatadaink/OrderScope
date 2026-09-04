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

2026-09-04時点のWeb作業カタログは20件である。

| 状態 | 件数 |
|---|---:|
| 未着手 | 1 |
| 進行中 | 0 |
| 調査完了 | 0 |
| 引渡し済み | 13 |
| 保留（依存） | 6 |
| 保留（外部） | 0 |
| 再確認要 | 0 |

`WEB-003`は共通のProvider・利用条件確認票を`W0-004`、`S0-001`、`N0-001`、adapter ADRへ引渡し済みである。`WEB-005`はSECのUser-Agent、Fair Access、endpoint、公開content再利用条件を現行公式資料で再確認し、`S0-001`および`S0-002〜007`へ引渡し済みである。`WEB-006`は対象SEC formについてbase/amendment/近縁form境界を公式情報で整理し、strict allowlistとfixture条件を`S0-004`/`S0-007`へ引き渡した。これによりSEC form filterのWeb入力は揃った。

`WEB-009`はAMD/NVIDIAの複数四半期・年次segment revenueを調査し、Company Factsのentity-wide/non-custom境界、NVIDIAのdimension member Evidence、AMD/NVIDIAのfiling table fallback、AMDのsegment統合・recast境界を整理して`E0-005`/`S0-006`/`E0-006`へ引渡し済みである。`WEB-011`はTiingo、Massive/Benzinga、Alpaca Newsを現行公式情報で再比較し、Tiingo Powerをv0.1第一候補として維持しつつ、本文保存・再配布等の未確定権利を契約確認要として分離した。`WEB-012`はReuters wireのregional mirror / syndication、明示的訂正、同一canonical URLのmaterial updateを公開Evidenceでcase set化し、story identityとdistribution instance、revisionを分離するcanonicalization fixture案を`N0-003`へ引渡した。`WEB-015`はWhite House、Treasury、Federal Reserve Board/FOMC、SEC Agencyについて公式owner、source type、恒久discovery入口、item actor解決規則をregistry seedとして整理し、`O0-002`/`I0-001`へ引渡し済みである。`WEB-016`は各sourceのRSS/HTML取得候補、pagination/backfill、timestamp精度、update/delete観測境界を整理し、Fed/SECをRSS-first、White House/TreasuryをHTML-index-firstとするbounded incremental contract案を`O0-002`/`I0-003/004/007`へ引渡した。これにより即時着手可能な未着手タスクは`WEB-017`となった。`WEB-010`はWeb側のWEB-007〜009が揃ったが、公式照合setのfieldを固定するためのlocal E0-004〜006 contract/adapter形状を待つ。

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
| WEB-003 | W0-004 | A | 引渡し済み | なし | [`REPORT_PROVIDER_TERMS_CHECKLIST_WEB_003_2026-09-04.md`](REPORT_PROVIDER_TERMS_CHECKLIST_WEB_003_2026-09-04.md); Evidence確認 `2026-09-03T16:23:58Z` | W0-004、S0-001、N0-001、adapter ADR / contract test | WEB-005はSEC詳細を再確認、WEB-011はNews候補へ共通票を適用。`記載なし`をdefault allowにしない | 2026-09-04 | web-2026-09-04-WEB-003 |
| WEB-004 | I0-001 | B | 引渡し済み | WEB-001/002引渡し済み | [`REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`](REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md); Evidence再確認 `2026-09-03T15:53:08Z` | I0-001 registry schema・migration・contract test | 共通Actor、nullable外部validity、listing/source endpoint履歴、Evidence制約を実装。AMD venue履歴のunknown gapをfixtureで検証 | 2026-09-03 | web-2026-09-03-WEB-004 |
| WEB-005 | S0-001 | A | 引渡し済み | WEB-003引渡し済み | [`REPORT_SEC_ACCESS_CONDITIONS_WEB_005_2026-09-04.md`](REPORT_SEC_ACCESS_CONDITIONS_WEB_005_2026-09-04.md); Evidence確認 `2026-09-03T16:28Z`〜`2026-09-03T16:31Z` | S0-001、S0-002〜007、WEB-006/007/009 | local SEC adapterでdeclared User-Agent、source-wide limiter、bounded retry/cooldown、Submissions/bulk経路を実装・試験。Web側はWEB-006/007/009へ進める | 2026-09-04 | web-2026-09-04-WEB-005 |
| WEB-006 | S0-004 | B | 引渡し済み | WEB-005引渡し済み | [`REPORT_SEC_FORM_FILTER_WEB_006_2026-09-04.md`](REPORT_SEC_FORM_FILTER_WEB_006_2026-09-04.md); Evidence確認 `2026-09-03T16:39Z` | S0-004 filter実装、S0-007 fixture/受入試験 | strict allowlist、`raw_form`/family/amendment正規化、near-miss fixtureを実装。AMD/NVDA限定取得でamendment/partialを検証 | 2026-09-04 | web-2026-09-04-WEB-006 |
| WEB-007 | E0-001 | C | 引渡し済み | WEB-001/005引渡し済み | [`REPORT_EARNINGS_EVENT_RESULT_CONTRACT_WEB_007_2026-09-04.md`](REPORT_EARNINGS_EVENT_RESULT_CONTRACT_WEB_007_2026-09-04.md); Evidence確認 `2026-09-03T18:16Z` | E0-001 Earnings contract実装、I0-002 provenance整合、E0-002 fixture | schedule/release/call/SEC accepted時刻を分離し、nullable actual release、issuer fiscal label、GAAP/non-GAAP dimensionをcontract testへ反映 | 2026-09-04 | web-2026-09-04-WEB-007 |
| WEB-008 | E0-003 | B | 引渡し済み | WEB-001引渡し済み | [`REPORT_IR_FALLBACK_WEB_008_2026-09-04.md`](REPORT_IR_FALLBACK_WEB_008_2026-09-04.md); Evidence確認 `2026-09-03T21:15Z` | E0-003 IR fallback adapter、I0-002/004 provenance・idempotency contract | AMD Financial Results / Press Releases、NVIDIA Quarterly Results / News Archiveをdiscovery経路にし、listing hrefをcanonical release URLとして保存。SEC/IR Evidenceを同一eventへ関連付けつつ両方保持し、HTTP更新挙動をfixtureで検証 | 2026-09-04 | web-2026-09-04-WEB-008 |
| WEB-009 | E0-005 | C | 引渡し済み | WEB-001/005引渡し済み | [`REPORT_SEGMENT_REVENUE_FALLBACK_WEB_009_2026-09-04.md`](REPORT_SEGMENT_REVENUE_FALLBACK_WEB_009_2026-09-04.md); Evidence確認 `2026-09-03T21:36Z` | E0-005 segment fallback実装、S0-006 XBRL adapter、E0-006 SegmentIdentityHistory | Company Facts失敗理由を保存し、dimension-aware XBRL→filing tableへfallback。AMDのcontext/member mappingはlocal instance parseで確定し、recast/business-line区別をE0-006 contract testへ反映 | 2026-09-04 | web-2026-09-04-WEB-009 |
| WEB-010 | E0-007 | D | 保留（依存） | WEB-007〜009引渡し済み、残りlocal E0-004〜006 contract/adapter形状 | WEB-009でsegment fallback/recast入力を準備済み | local reconciliation・品質report | E0-004〜006のfield/identity形状確定後に複数四半期の公式照合setを準備 | 2026-09-04 | — |
| WEB-011 | N0-001 | A | 引渡し済み | WEB-003引渡し済み | [`REPORT_NEWS_PROVIDER_COMPARISON_WEB_011_2026-09-04.md`](REPORT_NEWS_PROVIDER_COMPARISON_WEB_011_2026-09-04.md); Evidence確認 `2026-09-03T21:42Z` | N0-001 News Provider ADR、N0-002/004、I0-006、N1-006 | Tiingo Powerをdefault candidateとしてADR化。本文権利・durable retentionは契約確認までdisabled。Massive/Benzingaをfull-text昇格候補、Alpaca Newsを統合候補として保持 | 2026-09-04 | web-2026-09-04-WEB-011 |
| WEB-012 | N0-003 | C | 引渡し済み | WEB-011引渡し済み | [`REPORT_NEWS_CANONICALIZATION_CASES_WEB_012_2026-09-04.md`](REPORT_NEWS_CANONICALIZATION_CASES_WEB_012_2026-09-04.md); Evidence確認 `2026-09-04T07:24Z` | N0-003 canonicalization fixture/test、N0-002/004、I0-006 | story / distribution / revisionを分離し、same-story mirror、syndication、correction、material update、ambiguous relation fixtureを実装。Tiingo revision semanticsはcredential付きlocal観測で確定 | 2026-09-04 | web-2026-09-04-WEB-012 |
| WEB-013 | N1-001 | C | 保留（依存） | WEB-007とI0-005のcontract方針 | 親計画に初期分類あり | taxonomy schema・extractor fixture | 定義とEvidence付き事例を作成 | 2026-09-03 | — |
| WEB-014 | N1-006 | D | 保留（依存） | WEB-008、WEB-010とlocal評価形状 | WEB-008でIR基準source経路は準備済み | recall/latency評価 | WEB-010とlocal評価形状が揃った後、1〜3か月のSEC/IR基準イベントsetを準備 | 2026-09-04 | — |
| WEB-015 | O0-001 | A | 引渡し済み | なし | [`REPORT_OFFICIAL_SOURCE_REGISTRY_WEB_015_2026-09-04.md`](REPORT_OFFICIAL_SOURCE_REGISTRY_WEB_015_2026-09-04.md); Evidence確認 `2026-09-04T07:44Z` | O0-002 official feed adapter、I0-001 OfficialSource/SourceActorRule | registry seedをlocal schemaへ反映。Web側はWEB-016で各entryのRSS/API/更新一覧、pagination、timestamp、update/delete挙動を調査 | 2026-09-04 | web-2026-09-04-WEB-015 |
| WEB-016 | O0-002 | B | 引渡し済み | WEB-002/015引渡し済み | [`REPORT_OFFICIAL_FEED_BEHAVIOR_WEB_016_2026-09-04.md`](REPORT_OFFICIAL_FEED_BEHAVIOR_WEB_016_2026-09-04.md); Evidence確認 `2026-09-04T07:50Z` | O0-002 official feed adapter、I0-003/004/007 | Fed/SECはRSS-first + HTML/archive fallback、White House/TreasuryはHTML-index-first。date-only精度、overlap checkpoint、hash update、404/410/redirectをcontract/fixtureへ反映 | 2026-09-04 | web-2026-09-04-WEB-016 |
| WEB-017 | O0-003 | C | 未着手 | WEB-015/016引渡し済み | WEB-015でactor/source type、WEB-016で取得・timestamp境界を準備済み | official Fact type fixture | 発言・提案と署名・施行・正式決定の事例を収集し、event/publish/effective時刻を分離 | 2026-09-04 | — |
| WEB-018 | O0-004 | C | 保留（依存） | WEB-001/015済、残りWEB-017 | WEB-015でofficial actor/source identityを準備済み | instrument/theme関連付け実装 | WEB-017後にEvidence閾値とCanary事例を定義 | 2026-09-04 | — |
| WEB-019 | O0-005 | D | 保留（依存） | WEB-017/018とlocal adapter形状 | WEB-016でupdate/delete/重複/時刻fixture候補を準備済み | Official Signal品質test | WEB-017/018後にsemantic fixtureを追加し、local adapter形状確定後に品質setを完成 | 2026-09-04 | — |
| WEB-020 | X0-006 | D | 保留（依存） | WEB-003/005/011/016済、残りlocal実装証跡 | WEB-005でSEC公開制約、WEB-011でNews利用条件、WEB-016でofficial feed取得制約をhandoff | Canary運用runbook | local official feed実装・試験証跡が揃った後に公開制約部分を統合 | 2026-09-04 | — |

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
| 2026-09-03 | web-2026-09-03-WEB-004 | WEB-004 | AMD/NVDAのcompany・instrument・CIK・ticker/listingと、7つの公式source laneのowner/publisher/content actor規則を履歴付きregistry seedへ変換して引渡し | `REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`; Evidence再確認 `2026-09-03T15:48:29Z` | I0-001でactor統合、履歴schema、Evidence制約、as-of/identity contract testを実装。Web側はWEB-003/005/008/015へ進む |
| 2026-09-03 | web-2026-09-03-WEB-004-followup | WEB-004 | 並行セッションの完了成果を維持して競合を解消し、AMDの2017年NASDAQ Capital Market／2020年Global Select Market Evidenceと、正確な切替日を推測しない履歴規則を追記 | `REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`; 追加Evidence確認 `2026-09-03T15:53:08Z` | I0-001 contract testでvenue切替のunknown gapを保持。次のWeb候補はWEB-003/005/008/015 |
| 2026-09-03 | web-2026-09-03-WEB-004-verification | WEB-004 | 対象remote branchへの反映、成果物link、状態別件数を照合し、AMD 2017/2020 Form 10-K、NVIDIA 2026 Form 10-K、SEC association file注意事項を公式一次情報で再確認。追加修正なし | `REPORT_ENTITY_SOURCE_REGISTRY_VALUES_WEB_004_2026-09-03.md`; 限定再確認 `2026-09-03T16:00:29Z` | WEB-004は引渡し済みを維持。次セッションは優先度と依存を確認してWEB-003/005/008/011/015のいずれかに着手 |
| 2026-09-03 | web-2026-09-04-WEB-003 | WEB-003 | rate、User-Agent、credential、履歴/freshness、保存、本文利用、再配布、費用等を`公式根拠あり` / `記載なし` / `契約確認要`へ必ず分類する共通確認票を作成し、SEC/Tiingo/Alpaca/Massiveの限定seedで適用可能性を確認 | `REPORT_PROVIDER_TERMS_CHECKLIST_WEB_003_2026-09-04.md`; Evidence確認 `2026-09-03T16:23:58Z` | W0-004のWeb入力として引渡し。次はWEB-005でSEC接続条件を詳細化、またはWEB-011でNews Provider比較へ適用 |
| 2026-09-03 | web-2026-09-04-WEB-005 | WEB-005 | SEC Developer Resources、Webmaster FAQ、EDGAR APIs、Accessing EDGAR Data、Privacy/Security policyを再確認。10 req/s以下のFair Access、declared User-Agent、API key不要、Submissions/XBRL/bulk経路、公開EDGAR content reuse、保存期間の明示なしをFact/Unknownへ分離して引渡し | `REPORT_SEC_ACCESS_CONDITIONS_WEB_005_2026-09-04.md`; Evidence確認 `2026-09-03T16:28Z`〜`2026-09-03T16:31Z` | S0-002〜007でadapter/limiter/retry/storageを実装・試験。Web側は解放されたWEB-006/007/009、またはWEB-008/011/015へ進む |
| 2026-09-03 | web-2026-09-04-WEB-006 | WEB-006 | 8-K、10-Q、10-K、S-1、S-3、424B群、DEF 14A、Schedule 13D/G、Form 4の目的・amendment・近縁form境界をSEC公式情報で整理。strict allowlist、raw form保持、family/amendment正規化、near-miss fixture条件を引渡し | `REPORT_SEC_FORM_FILTER_WEB_006_2026-09-04.md`; Evidence確認 `2026-09-03T16:39Z` | S0-004でfilterを実装し、S0-007でbase/amendment/near-miss/unknownとAMD/NVDA限定取得を試験。Web側はWEB-007/008/009/011/015へ進む |
| 2026-09-03 | web-2026-09-04-WEB-007 | WEB-007 | AMD Q2 2026とNVIDIA Q2 FY2027を公式IR/SECで照合し、予定release window、call時刻、IR release日、SEC accepted時刻、period end、GAAP/non-GAAP、source roleを分離するCanary契約案を作成。IR本文でexact release時刻が未確認なケースはunknownのまま保持 | `REPORT_EARNINGS_EVENT_RESULT_CONTRACT_WEB_007_2026-09-04.md`; Evidence確認 `2026-09-03T18:16Z` | E0-001でnullable actual release、issuer fiscal label、accounting basis、source roleを実装し、SEC accepted時刻のrelease時刻誤用をnegative test化。Web側はWEB-008/009/011/015へ進む |
| 2026-09-03 | web-2026-09-04-WEB-008 | WEB-008 | AMD/NVIDIAの決算専用IR listing、公式release archive、個別release URLを公式一次情報で確認。listing/archive URLとcanonical individual release URLを分離し、SEC/IRを同一eventへ関連付けてもEvidenceは両方残すfallback contract案を引渡し | `REPORT_IR_FALLBACK_WEB_008_2026-09-04.md`; Evidence確認 `2026-09-03T21:15Z` | E0-003でissuer別listing/archive adapter、canonical URL/hash/provenance、partial/error、重複discoveryを実装・試験。Web側はWEB-009/011/015へ進む |
| 2026-09-03 | web-2026-09-04-WEB-009 | WEB-009 | 着手。AMD/NVIDIA複数四半期のsegment revenueについてCompany Facts、XBRL Dimension、filing/table fallbackの可用性と失敗理由を調査開始 | 調査中。成果物は完了時に追加 | `Company Facts → XBRL Dimension → Filing Fallback`を一次情報で照合し、欠損を推測しない |
| 2026-09-03 | web-2026-09-04-WEB-009 | WEB-009 | Company Factsのentity-wide/non-custom境界、NVIDIAのdimension member、AMD/NVIDIA複数四半期・年次segment table、AMDのrecast/business-line境界を整理し、fallback method/failure reason contractを引渡し | `REPORT_SEGMENT_REVENUE_FALLBACK_WEB_009_2026-09-04.md`; Evidence確認 `2026-09-03T21:36Z` | E0-005/S0-006でCompany Facts→dimension→filing tableを実装し、E0-006でrecast/segment identityを履歴化。Web側はWEB-011またはWEB-015へ進む |
| 2026-09-03 | web-2026-09-04-WEB-011 | WEB-011 | Tiingo、Massive/Benzinga、Alpaca Newsの現行価格・履歴・rate・本文fields・internal/individual use・再配布/retention境界を公式情報で比較。Tiingo Powerをdefault candidateとして維持し、本文権利未確定箇所を契約確認要へ分離して引渡し | `REPORT_NEWS_PROVIDER_COMPARISON_WEB_011_2026-09-04.md`; Evidence確認 `2026-09-03T21:42Z` | N0-001でADR化し、N0-002/004ではmetadataとtemporary bodyを分離。Web側は解放されたWEB-012またはWEB-015へ進む |
| 2026-09-04 | web-2026-09-04-WEB-012 | WEB-012 | Reuters wireのregional mirror / syndication、明示的訂正、同一canonical URLのmaterial updateをcase set化し、story identity・distribution instance・revision chainを分離するcanonicalization contract案を引渡し | `REPORT_NEWS_CANONICALIZATION_CASES_WEB_012_2026-09-04.md`; Evidence確認 `2026-09-04T07:24Z` | N0-003でfixture/testを実装し、Tiingo同一URL更新時のID/re-crawl挙動とfalse merge/false splitをcredential付きlocal観測で測定。Web側の即時候補はWEB-015 |
| 2026-09-04 | web-2026-09-04-WEB-015 | WEB-015 | White House、Treasury、Federal Reserve Board/FOMC、SEC Agencyの公式owner、source type、恒久discovery入口、item actor解決規則を公式一次情報で整理しofficial source registryを引渡し | `REPORT_OFFICIAL_SOURCE_REGISTRY_WEB_015_2026-09-04.md`; Evidence確認 `2026-09-04T07:44Z` | O0-002でRSS/API/HTML更新一覧、pagination、timestamp、update/delete挙動を調査・adapter設計。I0-001でcategory-level sourceとFOMC actorをseed化 |
| 2026-09-04 | web-2026-09-04-WEB-016 | WEB-016 | White House/Treasury/Fed/SECの公式取得経路、bounded pagination/backfill、timestamp精度、update/delete観測境界を調査し、RSS-first/HTML-index-firstのsource別adapter contract案を引渡し | `REPORT_OFFICIAL_FEED_BEHAVIOR_WEB_016_2026-09-04.md`; Evidence確認 `2026-09-04T07:50Z` | O0-002でadapterを実装し、I0-003/004/007でoverlap、partial checkpoint、hash revision、redirect/404/410 fixtureを試験。Web側は解放されたWEB-017へ進む |

## 8. 更新時チェックリスト

- [x] 編集前に対象ブランチの最新版を読んだ。
- [x] 変更したタスクの`WEB-*` IDと親IDを維持した。
- [x] Fact、Interpretation、ローカル完了主張を分離した。
- [x] 公式sourceへの直接linkと確認日を記録した。
- [x] 不明値を明示した。
- [x] credential、account identifier、provider response body、制限対象本文を含めていない。
- [x] 時点依存の料金・条件に再確認条件を付けた。
- [x] 状態別件数と台帳が一致する。
- [x] Session logと次の操作を更新した。

## 9. 関連文書

- `REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md`
- `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `IMPLEMENTATION_PROGRESS_TRACKER_2026-09-01.md`
- `ADR_LOCAL_ANALYSIS_STACK_v0.1.md`
- `MERMAID_CONVENTIONS.md`