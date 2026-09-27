# OrderScope — v0.1公式source範囲（WEB-002）

Status: Web research complete; local registry/feed implementation pending  
Web task: `WEB-002`  
Parent task: `W0-003`  
Scope proposal version: `official-source-scope-v0.1`  
Checked at: `2026-09-03T12:18:39Z`

## 1. 結論

v0.1の公式sourceを、発行主体とコンテンツ種別の組で固定する。対象はSECのEDGAR/公開データと当局発表、AMD/NVIDIAのInvestor Relations、White House、U.S. Department of the Treasury、Federal Reserve Boardの公式公開物である。

一般SNS、検索結果、ニュース集約、転載、企業の一般ブログ/マーケティングページは初期取得対象外とする。公式ページから外部サイトへlinkされているだけではTier 1 Evidenceへ昇格させない。

親計画の「SEC」と「SEC公式」という重複表現は、v0.1では次の2 laneとして明確化する。

1. `SEC_EDGAR`: filer提出物、submission metadata、XBRL/Company Facts等の公式公開データ
2. `SEC_AGENCY`: SEC自身のpress release、statement、rule・行政上の公式発表

EDGAR提出物はSECが公開する公式データだが、記載内容のactorは原則として提出者であり、SEC自身の見解または承認とは扱わない。

## 2. 受入判定

sourceをv0.1 Tier 1として受け入れるには、次をすべて満たす必要がある。

- 登録済みofficial ownerまたはissuerが管理する公式入口から到達できる。
- canonical URLと実際の発行主体を記録できる。
- 下表の対象コンテンツ種別に該当する。
- published/filed/event/effectiveの各時刻を、存在するものだけ区別して保持できる。
- 外部link、転載、検索snippetだけを根拠にしていない。

hostname allowlistは必要条件であり十分条件ではない。個別ページのactor、source type、canonical URLをregistry recordへ保持する。

## 3. 対象source表

| Source lane | Official owner / actor | 公式入口 | v0.1で含める公開物 | Evidence上の注意 | 主なhandoff |
|---|---|---|---|---|---|
| `SEC_EDGAR` | U.S. Securities and Exchange Commission（配布主体）/ 各filer（提出内容のactor） | https://www.sec.gov/search-filings / https://data.sec.gov/ | EDGAR filing detail・document、submissions、Company Facts/XBRL、filing metadata | filing内容をSECの見解と扱わない。accession、form、filed_at、amendmentを保持する | I0-001/002、S0-002〜006 |
| `SEC_AGENCY` | U.S. Securities and Exchange Commission | https://www.sec.gov/newsroom/press-releases | SEC press release、statement、正式に公開されたrule・行政上の発表への公式ページ | press releaseと施行・発効を同一Factにしない | O0-001/002、O0-003 |
| `CORPORATE_IR_AMD` | Advanced Micro Devices, Inc. | https://ir.amd.com/ | Financial Results、SEC Filings、IR news release、IR event/presentation、公式IR文書 | 一般AMD blog・product marketingは、同一資料がIR/SECに掲載されない限り対象外 | I0-001、E0-003 |
| `CORPORATE_IR_NVDA` | NVIDIA Corporation | https://investor.nvidia.com/home/default.aspx | Quarterly Results、Financial Reports、SEC Filings、IR news、IR event/presentation、公式IR文書 | NVIDIA newsroom・technical/company blogは、同一資料がIR/SECに掲載されない限り対象外 | I0-001、E0-003 |
| `WHITE_HOUSE` | Executive Office of the President / pageに明記されたofficial actor | https://www.whitehouse.gov/news/ | Briefings & Statements、Fact Sheets、Presidential Actions、Executive Orders、Presidential Memoranda、Proclamations、公式Remarks/transcript | 発言・方針・署名済みaction・effective dateを分離する | O0-001〜003 |
| `US_TREASURY` | U.S. Department of the Treasury / pageに明記されたofficial | https://home.treasury.gov/news/press-releases | press release、statement、remarks、readout、公式policy/data release | Treasury外部へのlinkは自動受入しない。bureau別sourceはregistryで別identityにする | O0-001〜003 |
| `FED_BOARD` | Board of Governors of the Federal Reserve System、FOMC、pageに明記されたBoard official | https://www.federalreserve.gov/newsevents.htm | press release、FOMC statement/minutes、speech/testimony、calendar、Board公式data publication | 個人発言、Board action、FOMC decision、統計releaseを別source typeにする | O0-001〜003 |

### Corporate Canaryとの対応

- v0.1の企業IR対象issuerは`WEB-001`で固定したAMDとNVIDIAだけとする。
- ticker文字列だけでsourceを関連付けず、CIK/company identityとIR ownerの履歴付き対応を使う。
- IRのstable release/archive URL、pagination、更新・削除挙動は`WEB-008`で確認する。

### Federal Reserveの境界

v0.1の`Fed`は`federalreserve.gov`上のBoard of Governors/FOMC公開物に限定する。12のFederal Reserve Bank、New York Fed等の各地区連銀sourceは初期allowlistへ含めず、必要時にactor/sourceを別registry entryとして追加する。

## 4. 初期対象外

| 対象外 | 例 | 扱い |
|---|---|---|
| 一般SNS | X、Truth Social、Facebook、Instagram、LinkedIn、Threads、Bluesky | 取得・Evidence基準とも初期対象外。公式Webの探索leadにも自動利用しない |
| 動画・配信platform | YouTube等の第三者platform上の動画、live配信 | 初期取得対象外。公式サイトにtranscriptがあればtranscript側だけを候補にする |
| 検索結果・生成要約 | 検索snippet、検索ランキング、AI要約 | source発見用leadに限り、Evidenceとして保存しない |
| 一般News・集約・転載 | wire転載、金融portal、news aggregator、syndication先 | Tier 1基準外。News Provider workstreamで別管理する |
| 企業の非IR公開物 | product page、support、developer/technical blog、一般company blog、marketing campaign | IR/SECに同一の公式資料が存在しない限り初期対象外 |
| 第三者への外部link | 公式ページからlinkされた報道、partner page、研究、業界団体文書 | link元が公式でも第三者文書をTier 1へ昇格させない |
| 未登録の政府source | Federal Register、Congress、裁判所、他省庁、州政府、地区連銀 | v0.1の自動取得対象外。必要性を別ADRで評価する |
| 私的・認証済み情報 | email、会員page、credential必須page、非公開document | GitHubへ保存せず、v0.1公式公開sourceから除外する |
| archive mirror/cache | Internet Archive、検索cache、非公式mirror | canonical sourceの代替にしない。欠落調査時も別Evidence classが必要 |

一般SNSを除外するため、official actor本人のaccountであってもSNS投稿を`Official Signal`として受け入れない。X API等の採否は後続ADRまで保留する。

## 5. 境界事例

| 事例 | 判定 | 理由 |
|---|---|---|
| SEC EDGAR上のAMD 10-Q | 対象 | `SEC_EDGAR`。actorはAMD、配布主体はSECとして分離できる |
| SEC press release内の執行発表 | 対象 | `SEC_AGENCY`。SEC自身の公式発表 |
| AMD IR releaseと同内容の一般news転載 | IR版のみTier 1 | canonical issuer sourceを優先し、転載を基準にしない |
| White House executive order page | 対象 | Presidential Actionとしてsource typeを識別できる |
| White House公式SNSのみの発言 | 対象外 | 一般SNSを初期範囲から除外 |
| Treasury pageから外部団体reportへのlink | 外部reportは対象外 | linkだけではofficial ownerがTreasuryにならない |
| Federal Reserve Bank of New Yorkのpage | 初期対象外 | v0.1のFedをBoard/FOMCに限定 |
| 公式ページから配布されるPDF | 条件付き対象 | official owner、landing page、document URLを共に記録できる場合 |
| 複数当局のjoint statement | 条件付き対象 | 登録済みsource上の公式版を使い、共同actorを省略しない |

## 6. Evidence

| Source title | Publisher / actor | Canonical URL | Checked at | Effective/version date | Evidence class | Extracted fact | Unknowns | Local consequence |
|---|---|---|---|---|---|---|---|---|
| Search Filings | U.S. Securities and Exchange Commission | https://www.sec.gov/search-filings | 2026-09-03T12:18:39Z | 記載なし | official data | Latest Filings、full-text search等のEDGAR公式入口 | 自動取得条件はWEB-005で確認 | `SEC_EDGAR`入口をregistry化 |
| EDGAR Application Programming Interfaces | U.S. Securities and Exchange Commission | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | 2026-09-03T12:18:39Z | page updated dateは本調査で確定せず | official rule/data documentation | submissionsとXBRL data APIの公式案内 | rate、User-Agent、保存条件はWEB-005 | S0 adapter候補 |
| SEC Press Releases | U.S. Securities and Exchange Commission | https://www.sec.gov/newsroom/press-releases | 2026-09-03T12:18:39Z | 記載なし | official data | SEC自身の公式announcement入口 | rule/statement各archiveの増分取得形状は未確認 | `SEC_AGENCY`入口候補 |
| AMD Investor Relations | Advanced Micro Devices, Inc. | https://ir.amd.com/ | 2026-09-03T12:18:39Z | 記載なし | official data | Financial Results、SEC Filings、News & Eventsへの公式導線 | stable URL等はWEB-008 | issuer source registry |
| NVIDIA Investor Relations | NVIDIA Corporation | https://investor.nvidia.com/home/default.aspx | 2026-09-03T12:18:39Z | 記載なし | official data | Financial Reports、SEC Filings、Quarterly Results、Newsへの公式導線 | stable URL等はWEB-008 | issuer source registry |
| White House News | The White House | https://www.whitehouse.gov/news/ | 2026-09-03T12:18:39Z | 記載なし | official data | statements、fact sheets、presidential actions、remarks等の公式入口 | pagination/update/delete挙動はWEB-016 | official source registry |
| Presidential Actions | The White House | https://www.whitehouse.gov/presidential-actions/ | 2026-09-03T12:18:39Z | 記載なし | official data | executive orders、memoranda、proclamations等の公式分類入口 | published/effectiveの抽出規則はWEB-017 | source type候補 |
| Treasury Press Releases | U.S. Department of the Treasury | https://home.treasury.gov/news/press-releases | 2026-09-03T12:18:39Z | 記載なし | official data | releases、statements/remarks、readouts等の公式入口 | feed/pagination/update/delete挙動はWEB-016 | official source registry |
| Federal Reserve News & Events | Board of Governors of the Federal Reserve System | https://www.federalreserve.gov/newsevents.htm | 2026-09-03T12:18:39Z | 記載なし | official data | press releases、speeches/testimony、calendar等の公式入口 | feed/archive挙動はWEB-016 | `FED_BOARD`入口候補 |
| Federal Reserve Press Releases | Board of Governors of the Federal Reserve System | https://www.federalreserve.gov/newsevents/pressreleases.htm | 2026-09-03T12:18:39Z | page上のLast Updateは個別publication更新を意味しない | official data | FOMCを含む年別press release archiveへの導線 | incremental取得設計は未確認 | source type候補 |

## 7. Handoff

### I0-001 source/entity registry

最低限、次を別fieldまたは関連recordで表現する。

- `source_scope_version`
- `source_lane`
- official owner identity
- page/document actor identity
- canonical entry URLとcanonical item URL
- source type
- valid_from / valid_to
- checked_at
- inclusion statusと理由
- parent/linked source（外部linkを自動継承しない）

`WEB-001`のAMD/NVIDIA identityと本書のsource laneを組み合わせれば、`WEB-004`の履歴付き対応案へ進める。

### O0-001 / O0-002

本書はsource範囲の境界であり、恒久URLの完全なregistry、RSS/API、pagination、timestamp、update/delete挙動を確定していない。これらは`WEB-015`と`WEB-016`で公式Evidenceを追加する。

### 共通contract

- source item取得時にownerとactorを分離する。
- `published_at`、`filed_at`、`event_time`、`effective_at`は存在する値だけ保存し、相互に補完しない。
- 外部link先へofficial statusを継承しない。
- allowlist外sourceは黙って受け入れず、`out_of_scope`またはreview対象として記録する。
- source範囲変更は`official-source-scope-v0.1`を書き換えず、新versionとして扱う。

## 8. 未解決事項

- rate limit、User-Agent、保存、本文利用、再配布、費用、credentialは`WEB-003`と`WEB-005`で未確認。
- feed、RSS/API、pagination、時刻、更新・削除挙動は`WEB-016`で未確認。
- AMD/NVIDIA IR archive URLの長期安定性は`WEB-008`で未確認。
- statement、proposal、署名、施行、effective timeの分類fixtureは`WEB-017`で未作成。
- 地区連銀、Federal Register、他省庁を追加する必要性は未決定。
- Web確認のみであり、adapter、parser、redirect、cursor、idempotency、retryのローカル試験は行っていない。
