# OrderScope — WEB-012 News canonicalization case set

Status: Web調査完了 / local implementation handoff ready
Date: 2026-09-04
Web ID: `WEB-012`
Parent: `N0-003`
Depends on: `WEB-011`
Session: `web-2026-09-04-WEB-012`
Evidence checked: `2026-09-04T07:24Z`

## 1. 目的

News Providerから取得した記事について、`同一記事`、`syndication / 転載`、`訂正`、`重要更新`を区別するための公開Evidence付きcase setを作る。

本書はcanonicalization / dedup fixtureの設計入力であり、Provider本文の恒久保存権、adapter実装、実データでの重複除去精度を完了扱いにしない。本文は保存せず、公開URL、時刻、headline、publisher/source、訂正・更新表示などのmetadataだけを記録する。

## 2. Provider field境界

### 2.1 Tiingo News

Tiingo公式News API documentationでは、記事に次のfieldがある。

- `id`: Tiingo内の記事固有ID
- `title`
- `url`
- `description`
- `publishedDate`: sourceが報告した公開時刻。sourceに時刻がなければcrawler discovery時刻を使用
- `crawlDate`
- `source`: news source domain
- `tickers`, `tags`

公式documentation上、記事revisionを直接表す`updated_at`やrevision numberは確認できなかった。したがってTiingoだけで「同一URLの内容更新」と「別記事」を確定できるとは限らない。

Source: https://www.tiingo.com/documentation/news

### 2.2 Alpaca News — 補助比較

Alpacaのreal-time News schemaには`id`, `headline`, `created_at`, `updated_at`, `content`, `url`がある。Tiingoにない明示的な`updated_at`を持つため、同一provider article ID内のrevision確認には利用しやすい。

Source: https://docs.alpaca.markets/us/docs/streaming-real-time-news

### 2.3 WEB-011から継承する権利境界

`WEB-011`の結論を継承し、Tiingo Powerをv0.1 default candidateとする。ただし本文のdurable retention / redistributionは契約確認までdisabledとし、WEB-012 fixtureはmetadataと公開URLで再現できる形に限定する。

## 3. Case set

### CASE-DUP-01 — 同一wire記事のmirror / regional duplicate

**分類:** `same_story_duplicate`

Reuters配信の「Wall St futures subdued as investors weigh earnings, oil prices」が、Investing.comの複数地域domainで同一headline、Reuters attribution、同一publish時刻帯で掲載されている。

観測URL:

- https://www.investing.com/news/economy-news/wall-st-futures-subdued-as-investors-weigh-earnings-oil-prices-4887340
  - Published: 2026-09-03 06:02 AM
  - Updated: 2026-09-03 06:08 AM
- https://ca.investing.com/news/economy-news/wall-st-futures-subdued-as-investors-weigh-earnings-oil-prices-4827091
  - Published: 2026-09-03 06:02 AM
  - Updated: 2026-09-03 06:10 AM
- https://au.investing.com/news/economy-news/wall-st-futures-subdued-as-investors-weigh-earnings-oil-prices-4627932
  - 同一Reuters headline / attribution

**判定理由:** host / regional wrapperが異なっても、wire source、headline、publish時刻、story内容が一致するため、独立eventとして数えない。

**fixture期待値:** URL完全一致だけをdedup keyにしない。`wire_source + normalized_headline + published_time_window + story fingerprint`で同一story groupへ寄せる。

### CASE-SYN-01 — Reuters originalから第三者媒体へのsyndication

**分類:** `syndicated_copy`

同じReuters記事がReuters originalとYahoo Financeに別URLで存在する。

Original:

- Reuters current canonical URL:
  https://www.reuters.com/business/wall-st-futures-subdued-investors-weigh-earnings-oil-prices-2026-09-03/

Syndicated copy:

- Yahoo Finance:
  https://finance.yahoo.com/markets/stocks/articles/wall-st-futures-subdued-investors-100210089.html
  - Reuters attribution
  - Published: 2026-09-03 06:02 AM EDT
  - headline: `Wall St futures subdued as investors weigh earnings, oil prices`

補助mirror:

- MarketScreener:
  https://www.marketscreener.com/news/wall-st-futures-subdued-as-investors-weigh-earnings-oil-prices-ce7858d3de8ef42c
  - Reuters attribution
  - Published: 2026-09-03 06:04 AM EDT

**判定理由:** publisher wrapper URLは異なるが、原著者sourceはReutersであり、headlineと公開時刻が一致する。publisher URL単位では別recordでも、event / story identityでは同一clusterに置く。

**fixture期待値:** `canonical_story_id`は共通、`distribution_instance_id`はURLごとに保持する。転載先を捨てずprovenanceとして保持する。

### CASE-CORR-01 — 明示的訂正

**分類:** `correction_revision`

Reuters記事「Tech pilgrims flock to China as global innovation race heats up」は、記事上で明示的に訂正が示されている。

URL:

- https://www.reuters.com/world/china/tech-pilgrims-flock-china-global-innovation-race-heats-up-2026-09-03/

Observed correction note:

- 2026-09-03 story
- paragraph 9の企業名表記を`GloPen`から`Glopen`へ訂正したことが明示されている

**判定理由:** event自体が新規発生したのではなく、既存storyの事実表記が訂正されたrevisionである。

**fixture期待値:** 旧版を完全削除して新規storyとしてinsertしない。`revision_kind=correction`、`supersedes=<previous revision>`を持ち、訂正後をcurrent表示に使う。旧revisionのmetadata/provenanceは監査用に保持する。

### CASE-UPDATE-01 — 同一canonical URLの重要更新

**分類:** `material_update_revision`

Reutersの同一URLが、朝のpre-market記事から引け後のmarket wrapへ大きく更新されている。

Canonical URL:

- https://www.reuters.com/business/wall-st-futures-subdued-investors-weigh-earnings-oil-prices-2026-09-03/

Early syndicated observation:

- headline: `Wall St futures subdued as investors weigh earnings, oil prices`
- Yahoo / Investing.com mirrorで2026-09-03 06:02 AM EDT前後の公開を確認
- 内容状態: futures / pre-market

Later Reuters observation:

- headline: `Wall Street ends sharply higher as Waller remarks ease rate hike fears`
- 同じReuters URL
- 内容状態: regular session close後のmarket wrap

**判定理由:** URL identityは同じだが、市場状態、headline、主要Factがmaterially変化している。単純なURL dedupで後続版をdropすると重要更新を失う。

**fixture期待値:** `canonical_story_id`は維持しつつ、新しい`revision_id`を生成する。headline / timestamp / material fact fingerprintが閾値を超えて変化した場合は`material_update`として保存し、downstream event extractorを再実行する。

## 4. canonicalization判定順序案

1. Provider article IDが同一なら同一provider object候補とする。ただしrevisionを否定しない。
2. canonical URL完全一致なら同一story候補とするが、headline / updated timestamp / content fingerprint差分を確認する。
3. URLが異なってもwire attribution、normalized headline、publish time window、author/sourceが強く一致する場合はsyndication cluster候補とする。
4. 明示的な`corrected`, `correction`, `updated`表示、またはProviderの`updated_at`進行がある場合はrevisionとして扱う。
5. 同一story cluster内でもmaterial factが変わる更新はdedup dropせず、revisionとして保持する。
6. source / URL /時刻だけでは確定できない場合は`uncertain_relation`とし、推測でmergeしない。

## 5. 最小contract案

```text
NewsStory
- canonical_story_id
- source_family
- first_published_at
- current_revision_id

NewsDistributionInstance
- distribution_instance_id
- canonical_story_id
- provider
- provider_article_id nullable
- source_domain
- url
- published_at nullable
- crawled_at nullable

NewsRevision
- revision_id
- canonical_story_id
- observed_at
- provider_updated_at nullable
- normalized_headline
- revision_kind: initial | correction | material_update | minor_update | unknown
- supersedes_revision_id nullable
- metadata_fingerprint
- body_fingerprint nullable / temporary-only
- evidence_url
```

`body_fingerprint`は本文そのものをdurable storageへ保存せず、一時処理で算出可能な場合だけ利用する。権利未確定時はmetadata fingerprintだけで動作できる必要がある。

## 6. negative fixtures

- URLが同じ → 常にduplicateとしてdrop: **禁止**。CASE-UPDATE-01を失う。
- headlineが同じ → 常に同一story: **禁止**。定型headlineや継続記事でfalse mergeし得る。
- URLが違う → 常に別story: **禁止**。CASE-SYN-01を重複計上する。
- provider IDが違う → 常に別story: **禁止**。providerを跨ぐsyndicationを見逃す。
- correctionを新規eventとしてcount: **禁止**。既存story revisionとして扱う。
- 訂正前revisionを無証跡で上書き: **禁止**。provenance / auditを失う。

## 7. Fact / Interpretation / Unknown

### Fact

- Tiingo documented News schemaには`id`, `url`, `publishedDate`, `crawlDate`, `source`等がある。
- Tiingo documentationでは`publishedDate`がsource時刻を優先し、欠落時はcrawler discovery時刻になる。
- Alpaca News schemaには`created_at`と`updated_at`がある。
- Reuters記事は複数の第三者媒体へ同一wire storyとしてsyndicationされる実例がある。
- Reutersには明示的な訂正noteを持つ記事がある。
- 同一Reuters URLが同日中にpre-market版からclosing wrapへmaterial updateされた実例がある。

### Interpretation / design proposal

- story identityとdistribution instanceを分離する。
- correction / material updateをduplicate dropと分離し、revision chainを持つ。
- Tiingoでは明示的revision timestampがdocumentedされていないため、URL / headline / crawl observation / fingerprintを組み合わせる。
- Alpacaの`updated_at`は補助signalとして使える。

### Unknown / local verification required

- Tiingoが同一source URL更新時に同じ`id`を更新するのか、新しい`id`を発行するのかは公開documentationから未確定。
- Tiingoの`description`がsource訂正後にどのタイミングで再crawl / 更新されるかは未確定。
- Massive/Benzingaでのrevision identity / correction semanticsは今回の公開Evidenceだけでは十分に固定できない。
- metadata-only fingerprintの閾値、time window、false merge / false split率はローカル実測が必要。

## 8. Local handoff

対象: `N0-003 canonicalization fixture/test`、`N0-002/004 News ingest/lifecycle`、`I0-006 provenance/idempotency`

実装時に最低限試験すること:

- CASE-DUP-01: regional mirrorsを1 story / 複数distributionへまとめる
- CASE-SYN-01: Reuters originalとYahoo等の転載を1 storyへまとめ、URL provenanceは保持する
- CASE-CORR-01: correction revisionが旧版をsupersedeし、story countを増やさない
- CASE-UPDATE-01: same URLのmaterial updateをdropせずrevisionとして保持し、extractor再実行対象にする
- ambiguous caseはmergeせず`uncertain_relation`へ送る

## 9. Evidence URLs

- Tiingo News API documentation: https://www.tiingo.com/documentation/news
- Tiingo News product: https://www.tiingo.com/products/news-api
- Alpaca real-time News schema: https://docs.alpaca.markets/us/docs/streaming-real-time-news
- Reuters material-update canonical URL: https://www.reuters.com/business/wall-st-futures-subdued-investors-weigh-earnings-oil-prices-2026-09-03/
- Yahoo syndicated early copy: https://finance.yahoo.com/markets/stocks/articles/wall-st-futures-subdued-investors-100210089.html
- Investing.com early Reuters copy: https://www.investing.com/news/economy-news/wall-st-futures-subdued-as-investors-weigh-earnings-oil-prices-4887340
- MarketScreener early Reuters copy: https://www.marketscreener.com/news/wall-st-futures-subdued-as-investors-weigh-earnings-oil-prices-ce7858d3de8ef42c
- Reuters correction example: https://www.reuters.com/world/china/tech-pilgrims-flock-china-global-innovation-race-heats-up-2026-09-03/

## 10. 完了境界

WEB-012のWeb完了条件「URL、時刻、分類理由が揃った同一記事、転載、訂正、重要更新case set」は満たした。

ただし`N0-003`親タスクは未完了である。canonicalization implementation、provider credential付き観測、本文lifecycle、false merge / false splitの実測、idempotency / retry試験はローカル側に残る。
