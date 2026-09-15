# OrderScope — Official Feed / Incremental Acquisition Research（WEB-016）

Status: Web research complete; local official feed adapter implementation pending  
Web task: `WEB-016`  
Parent task: `O0-002`  
Depends on: `WEB-002`, `WEB-015`  
Checked at: `2026-09-04T07:50Z`

## 1. 結論

`WEB-015`で固定したWhite House、U.S. Department of the Treasury、Federal Reserve Board/FOMC、SEC Agencyの公式source registryを前提に、RSS/API/公開更新一覧、pagination/backfill、時刻、update/delete観測境界を調査した。

Web側で確定できるadapter入力は次のとおりである。

- **White House**: 公式News一覧とcategory一覧はHTMLで安定して公開され、`/news/page/2/`のようなpage-number navigationを公式ページから確認できる。公開ページ上で公式RSS/APIの案内は確認できなかったため、v0.1ではHTML indexを一次取得経路とし、推測したWordPress系feed URLをTier 1 sourceとして登録しない。
- **Treasury**: Press Releases / Statements & Remarksの公式HTML一覧を利用でき、Press Releases一覧にはkeyword、start date、end dateの絞り込みUIとGovDelivery購読入口がある。公式RSS/APIの案内は確認できなかったため、v0.1ではHTML indexを一次取得経路とする。filter query parameterはWeb調査で推測せず、local adapter実装時にform action/parameterを実取得して固定する。
- **Federal Reserve Board/FOMC**: Federal Reserve自身がRSS Feedsページを公開し、All Press Releases、All Speeches、All Testimony、All Speeches & Testimony等のfeedを提供する。Press Releases / Speeches & Testimonyにはyear archiveもあり、RSSをincremental、year pageをbounded backfill/fallbackに使える。
- **SEC Agency**: SEC自身がRSS Feedsページを公開し、Press Releases、Speeches and Statements等のRSSを提供する。HTML一覧は25件単位のpaginationとyear/month等のfilterを持つため、RSSをincremental、HTML listingをbounded backfill/fallbackに使える。

共通して、公開仕様だけから「削除通知」「revision ID」「更新履歴保持」が保証されるとは確認できなかった。したがって、canonical item URL + content hash + retrieved_atを保存し、overlap再取得で`new / unchanged / changed / missing-from-window`を判定する。`missing-from-window`だけで削除確定にせず、個別item再取得のHTTP結果をlocal fixture/testで確認する。

## 2. Source別取得候補

| source lane | WEB-015 entry | primary incremental candidate | bounded backfill / fallback | pagination / bound | 公開時刻の扱い | update / delete境界 |
|---|---|---|---|---|---|---|
| `WHITE_HOUSE` | `official-white-house-news` | official HTML News index | category index / numbered page | `/news/page/{n}/`を公式navigationから確認。item dateがcheckpoint-overlapより古くなったpageで停止可能 | listingは日付表示。exact clock timeは必須扱いしない | revision/delete feed仕様は未確認。URL+hash再取得で観測 |
| `WHITE_HOUSE` | `official-white-house-briefings` / `presidential-actions` / `fact-sheets` | official category HTML index | category page navigation | categoryごとに同一のbounded page walkを実装候補。URL pattern生成ではなくpage上のnext/number linkを追う | item page/listingで得られるpublished dateを保持。時刻不明はnullable | 同上。category間重複はcanonical item URLで統合候補 |
| `US_TREASURY` | `official-us-treasury-press` | official Press Releases HTML index | keyword/date filtered listing | page上にStart date / End date UIあり。query parameterはlocalでform実測して固定 | listingは日付表示。exact clock timeは確認できない場合nullable | revision/delete feed仕様は未確認。canonical URL+hash、再取得HTTPで観測 |
| `US_TREASURY` | `official-us-treasury-statements` | official Statements & Remarks HTML index | Press Releases taxonomy/filter | category/dateでbounded scan | listing/itemに明示された日付をpublished dateとして保持し、発言時刻とは分離 | 同上 |
| `FED_BOARD` / `FOMC` | `official-fed-board-press` | official RSS `https://www.federalreserve.gov/feeds/press_all.xml` | year/FOMC archive pages | RSSはrecent window、year archiveをbackfill。FOMC専用year indexも存在 | listingは日付。個別press releaseでは`For release at 2:00 p.m. EDT`等のrelease timeが明示される例あり | FedはRSS readerがupdated/changed contentを取り込むと説明するがrevision ID/delete notification仕様は未確認。hash比較を維持 |
| `FED_BOARD` | `official-fed-board-speeches-testimony` | official RSS `https://www.federalreserve.gov/feeds/speeches_and_testimony.xml`（必要ならspeech/testimony個別feedも選択可能） | year archive pages | year単位backfill | speech pageは日付を明示。event timeとpublish/retrieve timeを混同しない | hash比較 + item再取得で更新観測。削除保証なし |
| `SEC_AGENCY` | `official-sec-agency-press` | official RSS `https://www.sec.gov/news/pressreleases.rss` | HTML Press Releases listing | 25件単位、`page=1`等のpaginationを確認。year/month filterあり | listingは日付。exact clock timeがない場合nullable | RSSはmost recent materials用途。revision/delete通知仕様は未確認。hash/HTTP再取得で観測 |
| `SEC_AGENCY` | `official-sec-agency-speeches-statements` | official RSS `https://www.sec.gov/news/speeches-statements.rss` | HTML Speeches and Statements listing | 25件単位、year/month/speaker/type filterあり | listingは日付。speaker/typeをitem metadataとして保持可能 | 同上 |
| `SEC_AGENCY` | `official-sec-agency-newsroom` | Newsroom HTMLはumbrella discovery | Press Releases / Speeches RSSと各listing | umbrellaは重複discoverを許容し、canonical item URLで同一候補へ寄せる | sectionごとの日付を保持 | umbrellaとの差分だけで削除判定しない |

## 3. Bounded incremental contract案

### 3.1 共通checkpoint

local `I0-003` / `O0-002` adapterでは、最低限次をsource単位で保持する。

- `source_id`
- `checkpoint_observed_at`
- `latest_published_date_or_time`
- `latest_item_identity`（source内stable IDが無い場合はcanonical item URL）
- `overlap_start`
- `last_successful_page_or_archive_ref`（HTML fallback時のみ）
- `partial/error`状態

RSS/HTMLの順序が完全なcursor semanticsを持つとは仮定しない。checkpointは「前回末尾を再開するopaque cursor」ではなく、**published date/time + overlap window + canonical identity/hash**を組み合わせる。

### 3.2 Incremental flow

1. registryの`canonical_entry_url`または明示されたofficial feed URLから開始する。
2. `checkpoint - overlap`以降のrecent itemsを再取得する。
3. canonical item URLをlisting/feedから取得し、slug/pathを推測生成しない。
4. `published_at`が日付のみなら精度を`DATE_ONLY`として保持し、00:00 UTC等へ勝手に補完しない。
5. 同一URLのcontent hashが変化した場合はrevision candidateとする。
6. recent listingから消えただけではdeleteとしない。canonical item URLを再取得してHTTP/redirect結果を記録する。
7. pagination/archiveの途中でerrorが出た場合はpartial checkpointを残し、成功した範囲より先へcheckpointを進めない。

### 3.3 推奨overlap

具体的な時間幅はlocal実測前なので固定しない。v0.1 contractでは`overlap_window`を設定値とし、最低でも前回取得境界を跨いで再取得できることだけを必須とする。更新遅延・同日複数item・日付のみtimestampを考えると、overlapを0にする設計は避ける。

## 4. Timestamp semantics

| field | 規則 |
|---|---|
| `published_at` | sourceが公開日時を明示した場合だけ設定。日付のみならprecisionを保持 |
| `event_time` | speech、meeting、effective action等の実イベント時刻。`published_at`と別field |
| `retrieved_at` | adapterがitem/feed/listingを取得した実時刻 |
| `available_at` | local pipelineで利用可能になった時刻。公開時刻の代用にしない |
| `source_last_update` | pageが`Last Update`を表示する場合のpage-level metadata。個別item revision timeと同一視しない |

Federal ReserveのFOMC press releaseでは、個別itemに`For release at 2:00 p.m. EDT`のような明示時刻が存在する。この場合のみtimezone付きpublished/release timestamp候補として正規化できる。White House、Treasury、SECのlistingで日付しか得られない場合は時刻を推測しない。

## 5. Update / delete / redirect policy

### 5.1 確定Fact

- Federal ReserveのRSS説明は、readerがfeed内容のupdated/changed contentを取り込む用途であることを明記している。
- SECはRSSをmost recent materialsを追う公式手段として案内している。
- White House / Treasuryの今回確認した公式indexには、revision ID、delete tombstone、削除通知feedの仕様説明は確認できなかった。
- SEC / Fedについても、今回確認した公式RSS案内ではitem-level revision IDやdelete tombstoneの保証は確認できなかった。

### 5.2 Localで必ず試験する項目

- same canonical URLの本文変更時にRSS item metadataが変わるか
- HTTP `ETag` / `Last-Modified`の有無と信頼性
- 301/302時のcanonical URL扱い
- 404/410時にdelete candidateとする条件
- listing/feedから消えたitemがcanonical URLでは残るケース
- 同一itemがumbrella/category/feedで重複discoverされるケース
- date-only itemが同日に複数ある場合のstable ordering

削除は`listing_missing`と`canonical_unavailable`を分離する。`404/410`を即時hard deleteへ結び付けず、Evidence/historyは保持し、source availability stateを更新する。

## 6. Source-specific Evidence

| Evidence ID | Source title | Canonical URL | Checked at | Evidence class | Extracted fact | Unknowns / local verification |
|---|---|---|---|---|---|---|
| `E-WEB016-WH-NEWS-PAGING` | News | https://www.whitehouse.gov/news/ | `2026-09-04T07:50Z` | `official data` | News indexにcategoryとpage navigationがあり、page 2は`/news/page/2/`として公式linkから到達可能 | official RSS/API、revision/delete semanticsは未確認 |
| `E-WEB016-TREASURY-PRESS` | Press Releases | https://home.treasury.gov/news/press-releases | `2026-09-04T07:50Z` | `official data` | press listing、日付、category、keyword/start/end date filter UI、GovDelivery購読入口を確認 | form query parameter、revision/delete semanticsはlocalで実測 |
| `E-WEB016-FED-RSS` | RSS Feeds | https://www.federalreserve.gov/feeds/feeds.htm | `2026-09-04T07:50Z` | `official data` | Press Releases、Speeches、Testimony等の公式RSSを列挙。updated/changed contentをreaderが取り込む説明あり | feed item field、revision/delete IDの保証はlocal parseで確認 |
| `E-WEB016-FED-PRESS` | Press Releases | https://www.federalreserve.gov/newsevents/pressreleases.htm | `2026-09-04T07:50Z` | `official data` | RSS link、year/FOMC year archiveを公式提供 | archive ordering・HTTP metadataをlocal検証 |
| `E-WEB016-FED-FOMC-TIME` | Federal Reserve issues FOMC statement | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260729a.htm | `2026-09-04T07:50Z` | `official data` | itemにJuly 29, 2026と`For release at 2:00 p.m. EDT`が明示 | 全itemがexact timeを持つとは仮定しない |
| `E-WEB016-SEC-RSS` | RSS Feeds | https://www.sec.gov/about/rss-feeds | `2026-09-04T07:50Z` | `official data` | Press Releases、Speeches and Statements等をmost recent SEC materialsのRSSとして公式案内 | revision/delete semanticsは未確認 |
| `E-WEB016-SEC-PRESS` | Press Releases | https://www.sec.gov/newsroom/press-releases | `2026-09-04T07:50Z` | `official data` | RSS link、25件単位listing、year/month filter、`page=1` paginationを確認 | exact publish time、HTTP metadataをlocal検証 |
| `E-WEB016-SEC-SPEECHES` | Speeches and Statements | https://www.sec.gov/newsroom/speeches-statements | `2026-09-04T07:50Z` | `official data` | RSS link、25件単位listing、speaker/year/month/type filterを確認 | exact publish time、revision/delete semanticsをlocal検証 |

## 7. Local handoff

### `O0-002` official feed adapter

- adapter routeを`RSS`と`HTML_INDEX`に分け、provider/site固有parserをCoreへ漏らさない。
- Fed/SECはRSS-first、HTML/year archive fallback。
- White House/TreasuryはHTML-index-first。非公式または推測feed URLを初期allowlistへ入れない。
- date-only precision、canonical URL、content hash、retrieved_at、source entryを必須保存する。
- bounded overlap、partial checkpoint、page/archive stop conditionを`I0-003` contract testへ含める。

### `I0-004` idempotency / update boundary

- canonical URL + source laneをidentity seedにし、content hash変化をrevision candidateとして分離する。
- umbrella/categoryの複数discoveryはsource refsを複数保持し、同一canonical URLだけで別Factへ分裂させない。
- redirect、404/410、listing disappearanceは別statusとして履歴化する。

### `I0-007` common contract test kit

fixture最低セット:

1. RSS new item
2. RSS same item unchanged
3. same URL content changed
4. HTML page overlap duplicate
5. date-only same-day multiple items
6. pagination途中error / partial checkpoint
7. listing missing but canonical URL alive
8. canonical 301/302
9. canonical 404/410
10. umbrella/category duplicate discovery

### `WEB-017 / O0-003`

WEB-016でsource取得境界が揃ったため、次のWeb作業はstatement / proposal / signed / implemented / effectiveを分離するofficial case setを作成できる。

## 8. 完了境界

WEB-016のWeb完了条件「sourceごとにbounded incremental取得候補または制約が明示される」は満たした。

ただし、次は未完了である。

- RSS XMLの実adapter parse / field mapping
- Treasury filter form parameterの実取得固定
- HTTP header、redirect、404/410挙動の実測
- update/delete fixtureの再生試験
- retry、checkpoint persistence、idempotencyのローカル実装
- latency / recall / coverage等の品質実測

したがって親`O0-002`はWeb調査完了ではなく、local implementation pendingのままとする。
