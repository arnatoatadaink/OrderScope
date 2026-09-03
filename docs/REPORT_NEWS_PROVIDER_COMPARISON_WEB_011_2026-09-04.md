# OrderScope — News Provider比較更新（WEB-011）

Status: Web調査完了 / local ADR・実装 pending
Web ID: `WEB-011`
Parent: `N0-001`
Checked at: `2026-09-03T21:42Z`
Scope: AMD/NVDA Canary向けNews metadata / temporary body access候補の現在条件比較

## 1. 結論

WEB-003の共通確認票を用いて、既存第一候補のTiingo News、既存不足時候補のMassive / Benzinga News、既存Market Data providerと統合できるAlpaca Newsを現在の公式情報で比較した。

Web側の暫定ADR入力は次のとおり。

1. **Tiingo Powerをv0.1の第一候補として維持する。** 個人向けPowerは`$30/month`、News APIは3か月のqueryable history、10,000 requests/hour、100,000 requests/day、40 GB/monthを明示し、ticker・published date・crawl date・description等を取得できる。OrderScopeの初期AMD/NVDA metadata収集と1〜3か月の評価windowに最も整合する。
2. **News本文をdurable保存できるとは扱わない。** Tiingoは`Internal Use Only`を明示するが、公開ページからoriginal article bodyの取得権・durable retention・契約終了後retentionを一般化できない。N0-004/I0-006ではmetadataとtemporary contentを分離し、本文権利は契約確認完了までblockする。
3. **Massive / Benzinga Newsは高機能な昇格候補とする。** 個人向けは`$99/month`、structured real-time newsとしてheadline、full-text content、tickers、category、publication time等を提供する。個人向けは`Individual use only`で、business useは別契約である。本文を利用した抽出がTiingoで不足する場合の比較対象に適するが、個人契約で第三者配布・業務利用を許可すると解釈しない。
4. **Alpaca Newsは低追加コスト統合候補だが、News固有の権利条件を契約確認要とする。** 公式docsは2015年までのhistorical news、Benzinga提供、REST/WebSocketによるNews利用を明示する。Trading API Market DataのBasic/Algo Trader Plusには200/min・10,000/minのAPI limitがあるが、公開資料だけからNews endpointへの現行適用、本文保存、再配布、derived useの全条件を固定できないため、実装前にaccount/contract条件を確認する。

したがって、**N0-001のWeb調査は完了し、News Provider ADRへ引渡し可能**である。ただし、provider契約、credential付き疎通、本文保存権、実際のcoverage/recall/latencyはローカルまたは外部確認が必要であり、ここでは完了主張しない。

## 2. 比較表

| Provider / plan | 価格 | News履歴 | 公開rate / quota | 本文・fields | Internal / individual use | 再配布 | WEB-011判定 |
|---|---:|---|---|---|---|---|---|
| Tiingo Power (Individual) | `$30/month` | News API queryable 3 months、以後going forward | 10,000 req/hour、100,000 req/day、40 GB/month | Title、URL、News Source、Description、Tags、Ticker、Published/Crawl Date。original article body権利は公開資料で未確定 | `Internal Use Only` | internal useは第三者表示・共有不可とpricingで説明。redistributionは別条件 | **第一候補維持**。metadata優先、body/retentionは契約確認要 |
| Tiingo Commercial | `$50/month`（公開product summary） | 3 months。より長いhistoryはsales | 20,000 req/hour、150,000 req/day、100 GB/month | Individualと同系News feed | `Internal Use Only` | redistribution/historyはenterprise/sales | 法人利用時の比較候補。現在の個人v0.1には過剰 |
| Massive / Benzinga News Individual | `$99/month` | 公開partner pageで固定年数を確認できず | pricingはdeveloper-friendly unlimited accessと表示。endpoint固有のfair-use上限は公開比較内で未確認 | structured news、headline、full-text content、ticker、category、author、publication time、optional teaser/body/images | `Individual use only` | Massive Market Data Termsでは個人dataの第三者配布・business/commercial useを制限。partner datasetは追加条件の可能性あり | **昇格候補**。本文抽出能力は強いが権利と費用の確認が必要 |
| Massive Stocks `/v2/reference/news` | Stocks Basic `$0`〜Advanced `$199/month` | plan/endpointのNews履歴深度は今回の公式公開資料で未確定 | Stocks plan別。Basic 5 calls/min、上位individual plansはUnlimitedとしてpricingで案内 | publisher、article metadata、summary、sentiment、original URL | Individual plansはindividual/personal条件 | business useはBusiness plan/termsへ分離 | metadata補助候補。Benzinga Partner Newsと同一dataset/権利と仮定しない |
| Alpaca News (Trading API) | News単独の現行追加料金を公式公開資料から確定できず。Market Data Basic `$0`、Algo Trader Plus `$99/month` | 2015年まで | Market Data Trading APIはBasic 200/min、Algo Trader Plus 10,000/min。News固有の現行適用は契約確認要 | Benzinga提供。headline、summary、author、created/updated time、URL、content、symbols、source等 | TermsはServices/Contentを原則personal/non-commercial useとする | reproduction/distribution/commercial exploitationには制約。News固有の再配布条件は契約確認要 | **統合候補**。権利条件確認前にdurable body保存へ進めない |

## 3. Provider別確認票

### 3.1 Tiingo News

| 項目 | 判定 | Fact / Unknown |
|---|---|---|
| Provider / product | 公式根拠あり | Tiingo News API |
| Use case | 公式根拠あり | Individual / Commercialとも公開planあり。公開planはInternal Use Only |
| Plan / cost | 公式根拠あり | Individual Starter `$0`、Power `$30/month`。News product summaryではCommercial `$50/month` |
| Rate limit | 公式根拠あり | Power 10,000/hour、100,000/day、40 GB/month。Commercial 20,000/hour、150,000/day、100 GB/month |
| Credential | 公式根拠あり | API tokenが必要 |
| Historical depth | 公式根拠あり | Power/Commercialは3 months queryable history。commercial clientsはより長いhistoryをsalesへ問い合わせ。product pageはarchive自体を1995年から25+ years / 70M+ articlesと説明 |
| Freshness | 公式根拠あり | real-time、discovered articles are added as found |
| Article fields | 公式根拠あり | Title、URL、News Source、Description、Tags、Stock/FX/Crypto tickers、Date Published、Crawl Date |
| Original article body | 契約確認要 | 公開field summaryではDescriptionまでは明示されるが、publisher original bodyの取得・保存権を一般化できない |
| Internal use | 公式根拠あり | pricingはInternal Use Onlyを「自身のpersonal useのみ、他者/組織へdisplay/share不可」と説明 |
| Durable storage / retention | 契約確認要 | API access可能性からdurable archive権を推測しない |
| Redistribution | 契約確認要 |公開individual/commercial planはInternal Use Only。News Enterprise, History & Redistributionはsales経由 |
| Local consequence | — | N0-002ではmetadataのみをdurable保存可能な最小契約として実装し、N0-004のbody accessは別feature flag / retention classで契約確認までdisabledにする |

### 3.2 Massive / Benzinga News

| 項目 | 判定 | Fact / Unknown |
|---|---|---|
| Provider / product | 公式根拠あり | Massive Partner Data — Benzinga News |
| Plan / cost | 公式根拠あり | Individual `$99/month` per dataset。Businessはcontact sales |
| Rate limit | 記載なし | partner pricingはunlimited accessと表現するが、endpoint単位のtechnical/fair-use ceilingを今回確認した公開資料では固定できない |
| Credential | 公式根拠あり | Massive API key / Bearer認証をREST quickstartで案内 |
| Historical depth | 記載なし | Benzinga News partner page / endpoint docsでquery可能な開始年を今回確認した公開情報から固定できない |
| Freshness | 公式根拠あり | real-time structured, timestamped news |
| Article body | 公式根拠あり | endpoint docsはfull-text content、optional teaser/body/imagesを含むと明示 |
| Internal / individual use | 公式根拠あり | Individual productは`Individual use only`。business用は別plan |
| Durable storage / retention | 契約確認要 | full-textが返ることとdurable retention権を同一視しない。Third Party Provider datasetには追加agreement/use restrictionの可能性をTermsが明示 |
| Redistribution / derived use | 契約確認要 | Massive Market Data Termsは個人向けMarket Dataのredistribution、business/commercial use、一定のderived worksを制限。Benzinga partner datasetの個別契約が優先し得る |
| Local consequence | — | N0-004の本文抽出候補としてadapterを差替可能に保つ。採用時はpartner-specific termsを契約単位で記録し、body retention TTLを明示する |

### 3.3 Alpaca News

| 項目 | 判定 | Fact / Unknown |
|---|---|---|
| Provider / product | 公式根拠あり | Alpaca Historical News / Real-time News。data sourceはBenzinga |
| Plan / cost | 契約確認要 | Trading API Market Data Basic `$0` / Algo Trader Plus `$99/month`は現行公式情報。News単独の現行add-on有無・適用料金は今回の公開資料から明示できない |
| Rate limit | 契約確認要 | Market Data overviewはBasic 200/min、Algo Trader Plus 10,000/minを明示するが、News endpointへの現行適用をNews docsだけでは固定できない |
| Credential | 公式根拠あり | Market Data endpointはauthenticationを要求。Trading APIはkey/secret header |
| Historical depth | 公式根拠あり | historical newsは2015年まで |
| Freshness | 公式根拠あり | real-time WebSocket Newsを提供 |
| Article body | 公式根拠あり | realtime schema exampleに`content` fieldがある |
| Internal / personal use | 公式根拠あり | Alpaca TermsはServices/Contentを原則personal/non-commercial useとする |
| Durable storage / retention | 契約確認要 | Third Party Contentを含むNewsのdurable保存条件を公開docsだけで確定しない |
| Redistribution | 契約確認要 | Terms/Customer Agreementにreproduction/distribution/commercial exploitation制限がある。News固有・Benzinga由来contentの許諾範囲は別途確認が必要 |
| Local consequence | — | 既存Alpaca credentialを流用できる可能性はあるが、N0-002採用前にNews entitlementとcontent rightsをaccount契約で確認する |

## 4. ADR入力案

### Decision candidate

`NewsProvider`の初期実装はprovider-neutral contractを維持し、**Tiingo Newsをdefault candidate**とする。

理由:

- 初期評価windowである1〜3か月に対してPowerの3か月queryable historyが一致する。
- AMD/NVDAの2銘柄Canaryでは10,000 req/hour / 100,000 req/dayは十分大きい公開上限であり、実際の必要request量はローカル設計・実測で確定できる。
- metadata fieldsとpublished/crawl時刻がN0-002/I0-002のprovenance設計に適合する。
- 月額`$30`で既存調査方針を維持でき、Massive Benzinga Newsの`$99`より初期費用が低い。

### Escalation candidate

次の場合にMassive / Benzinga Newsを比較・昇格する。

- Tiingoのdescription/metadataだけではN1 Fact抽出のrecallが不足する。
- 契約上許されたtemporary full-text accessが必要になる。
- Benzinga native structured fieldsがcanonicalizationやlatency改善に有意な効果を示す。

### Integration candidate

Alpaca Newsは既存Market Data providerとのcredential/operational統合が可能な候補として残す。ただし、Newsのpricing entitlement、本文retention、redistribution/derived useを現契約で確認するまでdefault採用しない。

## 5. 実装へ渡す契約境界

N0-002/N0-004/I0-006へ次を渡す。

```text
NewsArticleMetadata
  provider_article_id
  provider
  publisher
  headline
  source_url
  published_at
  discovered_at / crawled_at (nullable)
  updated_at (nullable)
  symbols[]
  summary_or_description (nullable, rights_class付き)
  source_revision (nullable)

TemporaryNewsContentRef
  provider_article_id
  rights_class
  retrieval_allowed
  durable_storage_allowed
  expires_at
  delete_required
  contract_evidence_ref
```

実装規則:

- `content/body`をmetadata tableへ直接保存しない。
- `retrieval_allowed=true`と`durable_storage_allowed=true`を同義にしない。
- `Internal Use Only`を「無期限保存可」や「再配布可」と読み替えない。
- provider response bodyや記事本文をfixtureとしてGitへ置かない。fixtureは権利上保存可能な最小synthetic shapeを用いる。
- `published_at`とprovider crawl/discovery時刻を分離する。
- URL、provider article ID、content hashの三者をN0-003 canonicalizationで別々に扱う。

## 6. 未解決事項

- Tiingo Power/Commercialで`description`を超えるpublisher original bodyをAPIが返す場合の具体的権利、temporary processing、durable retention、契約終了後削除条件。
- Massive Benzinga Newsの公開technical rate ceiling、queryable historical start、partner-specific retention/derived-data terms。
- Alpaca Trading APIのNewsに対する現行plan entitlement、News固有rate、Benzinga contentのtemporary/durable retention権。
- OrderScopeを将来business/organization主体で運用する場合の各provider business契約価格と権利範囲。
- 実データでのAMD/NVDA coverage、重複率、latency、recall。これらはN0-002〜N1-006のローカル実測まで不明。

## 7. Evidence

確認日時: `2026-09-03T21:42Z`

### Tiingo

- Pricing: https://www.tiingo.com/pricing
- News product: https://www.tiingo.com/products/news-api
- News API documentation: https://www.tiingo.com/documentation/news
- General API documentation: https://www.tiingo.com/documentation/general

### Massive / Benzinga

- Benzinga partner pricing/product: https://massive.com/partners/benzinga
- Benzinga News endpoint: https://massive.com/docs/rest/partners/benzinga/news
- Partner overview: https://massive.com/docs/rest/partners/overview
- Stocks News endpoint: https://massive.com/docs/rest/stocks/news
- REST quickstart/authentication: https://massive.com/docs/rest/quickstart
- Market Data Terms: https://massive.com/legal/market-data-terms-of-service
- Terms index / Individual vs Business boundary: https://massive.com/legal/terms

### Alpaca

- Historical News: https://docs.alpaca.markets/us/docs/historical-news-data
- Real-time News: https://docs.alpaca.markets/us/docs/streaming-real-time-news
- Market Data plans/authentication: https://docs.alpaca.markets/us/docs/about-market-data-api
- Data pricing overview: https://alpaca.markets/data
- Terms and Conditions: https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf

## 8. 再確認条件

次のいずれかでWEB-011を`再確認要`へ戻す。

- News provider契約またはcredential投入直前。
- Tiingo/Massive/Alpacaのpricing、News API plan、Terms、partner dataset条件の変更通知。
- personal/internal useからbusiness/commercial useへ利用主体が変わる。
- temporary bodyをdurable保存へ変更する設計判断。
- News metadata/本文を第三者UI、API、共有reportへ出す要件追加。

## 9. Handoff

- `N0-001`: 本reportをNews Provider ADR入力として使用し、採用provider/planと未解決契約条件を明示する。
- `N0-002`: provider-neutral metadata adapterを実装し、Tiingoをdefault candidateとしてAMD/NVDA bounded retrievalをfixture/credential付き試験へ進める。
- `N0-003` / `WEB-012`: 選択providerで同一記事、syndication、訂正、更新のcase setを準備する。
- `N0-004` / `I0-006`: 本文をtemporary content lifecycleへ分離し、権利未確認時はbody retrieval/storageをdisabledにする。
- `N1-006`: SEC/IRを基準にcoverage/recall/latencyを実測し、Tiingo不足時のみMassive/Alpaca昇格を評価する。
