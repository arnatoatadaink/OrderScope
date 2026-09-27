# OrderScope — Official Source Registry（WEB-015）

Status: Web research complete; local feed adapter implementation pending  
Web task: `WEB-015`  
Parent task: `O0-001`  
Registry proposal version: `official-source-registry-v0.1`  
Checked at: `2026-09-04T07:44Z`

## 1. 結論

`WEB-002`で固定したv0.1公式source範囲と、`WEB-004`のActor / OfficialSource境界を前提に、White House、U.S. Department of the Treasury、Board of Governors of the Federal Reserve System、U.S. Securities and Exchange Commissionについて、恒久的なdiscovery入口、公式owner、source type、item actor解決規則をregistry seedとして整理した。

- sourceの公式性はhostnameだけで決めず、登録済みowner、公式入口、個別itemのactor/source typeで判定する。
- canonical item URLはlisting/indexから得た公式hrefを保存し、URL patternを推測生成しない。
- owner/publisherとcontent actorを分離する。個人発言、FOMC decision、Board action、agency press releaseを同一actorへ潰さない。
- White Houseは既存`WEB-004`と同様、v0.1では`The White House`を公式Web owner identityとして扱い、Executive Office of the Presidentとの法的・組織的階層を推測追加しない。
- Federal Reserveは`federalreserve.gov`上のBoard/FOMC公開物だけを対象とし、12地区連銀やNew York Fed等はv0.1初期allowlistへ追加しない。
- SECのEDGAR filer提出物は本タスクのagency signal laneとは別の`SEC_EDGAR`として既に管理される。本書のSEC registryは`SEC_AGENCY`のNewsroom、press release、speeches/statementsを対象にする。

本成果で`O0-001`のWeb入力は揃い、`WEB-016 / O0-002`のofficial feed調査を開始できる。RSS/API、pagination、timestamp、update/delete挙動は本タスクでは確定せず、`WEB-016`へ引き渡す。

## 2. Registry contract

### 2.1 最低限保持するfield

| Field | 規則 |
|---|---|
| `source_id` | OrderScope内部ID。外部URLやhostnameをIDそのものにしない |
| `source_lane` | `WHITE_HOUSE` / `US_TREASURY` / `FED_BOARD` / `SEC_AGENCY` |
| `canonical_entry_url` | discoveryに使う公式index/archive入口 |
| `owner_actor_id` | 公式サイト/sourceを管理するActor |
| `publisher_actor_id` | 通常はownerと同一。個別item actorとは分離 |
| `source_type` | entryの意味を固定する分類 |
| `content_actor_mode` | fixed owner、item declared、FOMC等の解決規則 |
| `policy_status` | v0.1対象なら`INCLUDED_V0_1` |
| `policy_valid_from` | OrderScopeでの採用日。外部URLの開設日と混同しない |
| `observed_at` | Webで入口を確認した日時 |
| `evidence_refs` | 公式一次情報Evidenceへの参照 |

`policy_valid_from = 2026-09-04`、`policy_valid_to = open`を本追加registry entryのOrderScope採用期間とする。外部source自体の開始日は本調査で確認していないため`external_valid_from = unknown`とする。

### 2.2 item actor解決

| Mode | 意味 |
|---|---|
| `ITEM_DECLARED` | itemに明示されたPresident、official、agency officer等をactorとして解決。解決できなければownerへ黙って代入しない |
| `ITEM_DECLARED_OR_FIXED_OWNER` | itemに明示actorがあれば保持し、ない場合だけagency ownerを使いresolution methodを残す |
| `FED_BOARD_OR_FOMC_FROM_ITEM` | Board action、FOMC statement/minutes、individual speech/testimonyをitem metadata/title/pageから区別する |
| `SEC_AGENCY_OR_PERSON_FROM_ITEM` | SEC agency announcementとChair/Commissioner/staffによるspeech/statementを区別する |

共同発表では共同actorを複数関係として保存する。公式pageから第三者siteへlinkされるだけではofficial statusまたはactorを継承しない。

## 3. Official owner / actor seed

| actor_id（内部提案） | actor_kind | display name | v0.1上の役割 | Evidence |
|---|---|---|---|---|
| `actor-gov-us-white-house` | `GOVERNMENT_OFFICIAL_SOURCE` | The White House | White House公式Web source owner/publisher | `E-WH-NEWS`, `E-WH-BRIEFINGS`, `E-WH-ACTIONS`, `E-WH-FACT-SHEETS` |
| `actor-gov-us-treasury` | `GOVERNMENT_AGENCY` | U.S. Department of the Treasury | Treasury公式News source owner/publisher | `E-TREASURY-PRESS`, `E-TREASURY-STATEMENTS` |
| `actor-gov-us-fed-board` | `GOVERNMENT_AGENCY` | Board of Governors of the Federal Reserve System | federalreserve.gov News & Events owner/publisher | `E-FED-NEWS`, `E-FED-PRESS`, `E-FED-SPEECHES` |
| `actor-gov-us-fomc` | `GOVERNMENT_COMMITTEE` | Federal Open Market Committee | FOMC statement/minutes等でitemに明示されるcontent actor | `E-FED-NEWS`, `E-FED-PRESS` |
| `actor-gov-us-sec` | `GOVERNMENT_AGENCY` | U.S. Securities and Exchange Commission | SEC Newsroom source owner/publisher | `E-SEC-NEWSROOM`, `E-SEC-PRESS`, `E-SEC-SPEECHES` |

個人officialのActorは氏名がitemに明記された時点で既存/新規Actorへ解決する。office holderの現職期間を本Web調査の確認日だけから推測生成しない。

## 4. Official source registry seed

### 4.1 White House

| source_id | canonical entry URL | source_type | owner / publisher | content_actor_mode | 採用理由 |
|---|---|---|---|---|---|
| `official-white-house-news` | https://www.whitehouse.gov/news/ | `GOVERNMENT_NEWS_ENTRY` | `actor-gov-us-white-house` / same | `ITEM_DECLARED` | White House公開物を横断するNews入口 |
| `official-white-house-briefings` | https://www.whitehouse.gov/briefings-statements/ | `BRIEFINGS_STATEMENTS_INDEX` | `actor-gov-us-white-house` / same | `ITEM_DECLARED` | Briefings & Statementsの専用分類入口 |
| `official-white-house-presidential-actions` | https://www.whitehouse.gov/presidential-actions/ | `PRESIDENTIAL_ACTIONS_INDEX` | `actor-gov-us-white-house` / same | `ITEM_DECLARED` | Executive Orders、Presidential Memoranda、Proclamations等を分類表示する公式入口 |
| `official-white-house-fact-sheets` | https://www.whitehouse.gov/fact-sheets/ | `FACT_SHEETS_INDEX` | `actor-gov-us-white-house` / same | `ITEM_DECLARED` | Fact Sheet専用の公式分類入口 |

`News`はumbrella entry、下位3 sourceは意味分類用entryとする。同一itemが複数entryからdiscoverされてもcanonical item URLを同一identity候補とし、entryの違いだけで別Factへ分裂させない。重複・revision規則の実装は後続adapter/fixtureで検証する。

### 4.2 U.S. Department of the Treasury

| source_id | canonical entry URL | source_type | owner / publisher | content_actor_mode | 採用理由 |
|---|---|---|---|---|---|
| `official-us-treasury-press` | https://home.treasury.gov/news/press-releases | `AGENCY_PRESS_RELEASE_INDEX` | `actor-gov-us-treasury` / same | `ITEM_DECLARED_OR_FIXED_OWNER` | TreasuryのPress Releases公式一覧。ReadoutsやStatements & Remarks等の分類表示も確認できる |
| `official-us-treasury-statements` | https://home.treasury.gov/news/press-releases/statements-remarks/ | `AGENCY_STATEMENTS_REMARKS_INDEX` | `actor-gov-us-treasury` / same | `ITEM_DECLARED_OR_FIXED_OWNER` | Secretary等のStatements & Remarks専用入口 |

Treasury本体とbureau/officeをhostnameだけで同一Actorへ統合しない。個別itemに共同省庁・個人official・bureauが明示される場合はitem actor関係として保持する。

### 4.3 Board of Governors of the Federal Reserve System / FOMC

| source_id | canonical entry URL | source_type | owner / publisher | content_actor_mode | 採用理由 |
|---|---|---|---|---|---|
| `official-fed-board-news` | https://www.federalreserve.gov/newsevents.htm | `CENTRAL_BANK_NEWS_ENTRY` | `actor-gov-us-fed-board` / same | `FED_BOARD_OR_FOMC_FROM_ITEM` | Press Releases、Speeches、Testimony、Calendarへの公式News & Events入口 |
| `official-fed-board-press` | https://www.federalreserve.gov/newsevents/pressreleases.htm | `CENTRAL_BANK_PRESS_RELEASE_INDEX` | `actor-gov-us-fed-board` / same | `FED_BOARD_OR_FOMC_FROM_ITEM` | Board actionとFOMC関連publicationを含む公式press release系入口 |
| `official-fed-board-speeches-testimony` | https://www.federalreserve.gov/newsevents/speeches-testimony.htm | `CENTRAL_BANK_SPEECH_TESTIMONY_INDEX` | `actor-gov-us-fed-board` / same | `ITEM_DECLARED` | Board officialsのSpeeches / Testimony専用入口 |

FOMCをBoardと同一content actorに潰さない。個人のspeech/testimonyは発言者Actor、Board actionはBoard、FOMC statement/minutesはFOMCとして解決する。`federalreserve.gov`外の地区連銀sourceは本seedへ含めない。

### 4.4 U.S. Securities and Exchange Commission

| source_id | canonical entry URL | source_type | owner / publisher | content_actor_mode | 採用理由 |
|---|---|---|---|---|---|
| `official-sec-agency-newsroom` | https://www.sec.gov/newsroom | `SEC_AGENCY_NEWSROOM_ENTRY` | `actor-gov-us-sec` / same | `SEC_AGENCY_OR_PERSON_FROM_ITEM` | Press Releases、What's New、Speeches & Statements等の公式Newsroom入口 |
| `official-sec-agency-press` | https://www.sec.gov/newsroom/press-releases | `AGENCY_PRESS_RELEASE_INDEX` | `actor-gov-us-sec` / same | `ITEM_DECLARED_OR_FIXED_OWNER` | SEC自身の公式announcement一覧 |
| `official-sec-agency-speeches-statements` | https://www.sec.gov/newsroom/speeches-statements | `AGENCY_SPEECH_STATEMENT_INDEX` | `actor-gov-us-sec` / same | `SEC_AGENCY_OR_PERSON_FROM_ITEM` | Chair、Commissioners、SEC staffのspeeches/statements/testimony/transcript系入口 |

`SEC_AGENCY`と`SEC_EDGAR`を混同しない。Newsroom itemがrule、order、litigation等の正式文書へlinkする場合も、announcement itemと正式文書のeffective/legal stateを別Evidenceとして扱う。

## 5. Canonical URL policy

1. `canonical_entry_url`は上表の固定公式入口をregistryへ保存する。
2. 個別itemはentryから取得した公式hrefを`canonical_item_url`として保存する。
3. query parameter付きlisting URLはfilter/pagination状態であり、source identityのcanonical entryには原則使わない。
4. 個別item URLのslug/date/path patternを自動生成しない。
5. redirectが発生する場合はHTTP実測が必要なため、redirect先固定・permanent判定は`WEB-016`またはlocal adapter試験で行う。
6. archive/year pageはbounded incremental取得に有用でも、primary source identityとpagination/feed endpointは別fieldに分離する。

## 6. Evidence registry

| Evidence ID | Source title | Publisher / actor | Canonical URL | Checked at | Evidence class | Extracted fact | Unknowns / next verification |
|---|---|---|---|---|---|---|---|
| `E-WH-NEWS` | News | The White House | https://www.whitehouse.gov/news/ | `2026-09-04T07:44Z` | `official data` | Releases、Briefings & Statements、Presidential Actions、Fact Sheets、Remarks等を分類する公式News入口 | pagination/update/delete/feedはWEB-016 |
| `E-WH-BRIEFINGS` | Briefings & Statements | The White House | https://www.whitehouse.gov/briefings-statements/ | `2026-09-04T07:44Z` | `official data` | Briefings & Statements専用一覧 | incremental取得形状はWEB-016 |
| `E-WH-ACTIONS` | Presidential Actions | The White House | https://www.whitehouse.gov/presidential-actions/ | `2026-09-04T07:44Z` | `official data` | Executive Orders、Nominations & Appointments、Presidential Memoranda、Proclamationsを分類する公式入口 | published/effective分離はWEB-017 |
| `E-WH-FACT-SHEETS` | Fact Sheets | The White House | https://www.whitehouse.gov/fact-sheets/ | `2026-09-04T07:44Z` | `official data` | Fact Sheets専用一覧 | pagination/update/deleteはWEB-016 |
| `E-TREASURY-PRESS` | Press Releases | U.S. Department of the Treasury | https://home.treasury.gov/news/press-releases | `2026-09-04T07:44Z` | `official data` | Press Releasesの公式一覧。Readouts、Statements & Remarks等の分類表示を含む | feed/pagination/update/deleteはWEB-016 |
| `E-TREASURY-STATEMENTS` | Statements & Remarks | U.S. Department of the Treasury | https://home.treasury.gov/news/press-releases/statements-remarks/ | `2026-09-04T07:44Z` | `official data` | Secretary等のStatements & Remarks専用一覧 | actor identityのoffice-historyはitemごとに解決 |
| `E-FED-NEWS` | News & Events | Board of Governors of the Federal Reserve System | https://www.federalreserve.gov/newsevents.htm | `2026-09-04T07:44Z` | `official data` | Press Releases、Speeches、Testimony、Calendarへの公式入口 | feed/archive/paginationはWEB-016 |
| `E-FED-PRESS` | Press Releases | Board of Governors of the Federal Reserve System | https://www.federalreserve.gov/newsevents/pressreleases.htm | `2026-09-04T07:44Z` | `official data` | 年別press release系archiveへの公式入口 | FOMC/Boardのcategory別feed挙動はWEB-016 |
| `E-FED-SPEECHES` | Speeches and Testimony of Federal Reserve Officials | Board of Governors of the Federal Reserve System | https://www.federalreserve.gov/newsevents/speeches-testimony.htm | `2026-09-04T07:44Z` | `official data` | SpeechesとTestimonyを年別に提供する公式入口 | RSSのURL・更新挙動はWEB-016 |
| `E-SEC-NEWSROOM` | Newsroom | U.S. Securities and Exchange Commission | https://www.sec.gov/newsroom | `2026-09-04T07:44Z` | `official data` | Press Releases、What's New、Speeches & Statements等の公式Newsroom入口 | category別incremental取得はWEB-016 |
| `E-SEC-PRESS` | Press Releases | U.S. Securities and Exchange Commission | https://www.sec.gov/newsroom/press-releases | `2026-09-04T07:44Z` | `official data` | SEC official announcementsの一覧。RSS導線が表示される | RSS endpoint自体と更新挙動はWEB-016 |
| `E-SEC-SPEECHES` | Speeches and Statements | U.S. Securities and Exchange Commission | https://www.sec.gov/newsroom/speeches-statements | `2026-09-04T07:44Z` | `official data` | Chair、Commissioners、staffのspeech/statement/testimony/transcript系一覧。Speaker/Typeを表示 | RSS endpoint、pagination、revision挙動はWEB-016 |

## 7. Fact / Interpretation / Unknown

### Fact

- White Houseの`News`、`Briefings & Statements`、`Presidential Actions`、`Fact Sheets`は現行公式サイト上で独立した分類入口として確認できる。
- TreasuryのPress Releases一覧とStatements & Remarks専用一覧を公式サイトで確認できる。
- Federal Reserve BoardのNews & EventsはPress Releases、Speeches、Testimony等への入口を持ち、個別掲載ではBoard action、FOMC publication、個人official speechを区別できる。
- SEC NewsroomはPress ReleasesとSpeeches & Statementsを公式categoryとして持ち、Speeches & Statementsはspeaker/typeを明示する。

### Interpretation / registry decision

- umbrella entryとcategory entryを両方registry化し、同一itemの重複discoveryをcanonical URLで統合できるようにする。
- FOMCはBoard owner配下で配信されてもcontent actorとして別Actorを持つ。
- White Houseの法的組織階層は本調査では追加せず、既存のWeb owner identityを維持する。

### Unknown / deferred

- RSS/APIの完全なendpoint一覧、pagination cursor/page規則、timestamp timezone、ETag/Last-Modified、HTTP redirect、削除・訂正・再公開挙動。
- source別のbounded incremental取得上限とarchive completeness。
- 個人officialのoffice-term履歴を自動解決するためのauthoritative directory source。
- 同一itemが複数categoryに現れる場合のID/URL revision挙動の実測。

これらは`WEB-016`以降で確認し、未確認のままadapter contractへ固定値として埋め込まない。

## 8. Handoff

### O0-001

Web完了条件である「公式owner、source type、入口URL、確認日」は4機関について揃った。local registry schema/migrationは未実装のため、親`O0-001`の実装完了は主張しない。

### WEB-016 / O0-002

次の作業では本registryの各entryについて、次を公式一次情報とHTTP実測可能範囲で確認する。

- RSS / Atom / API / HTML update list
- pagination / year archive / bounded backfill
- publication timestamp、timezone、date-onlyの扱い
- ETag / Last-Modified / redirect（公開される場合）
- item update、correction、delete、URL replacement
- sourceごとのincremental cursor候補と停止条件

### I0-001

`WEB-004`の`OfficialSource` / `SourceActorRule`へ、本書のcategory-level source entryと`actor-gov-us-fomc`をseed追加する。外部validity開始日は推測せず、`observed_at`とOrderScope policy validityを分離する。

## 9. 完了判定

`WEB-015`のWeb完了条件を満たす。

- [x] White Houseの公式owner/source type/入口URLを確認
- [x] Treasuryの公式owner/source type/入口URLを確認
- [x] Federal Reserve Board/FOMCのowner/content actor境界と入口URLを確認
- [x] SEC agency laneのowner/content actor境界と入口URLを確認
- [x] 全EvidenceにWeb確認日時を記録
- [x] 個別item actorをownerから推測しない規則を明示
- [x] RSS/API/pagination/update/delete等の未確認事項をWEB-016へ分離
- [x] local schema/adapter実装・実測を完了扱いしていない
