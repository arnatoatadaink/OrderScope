# OrderScope — Provider・利用条件 共通確認票（WEB-003）

Status: Web調査完了 / local implementation pending
Web ID: `WEB-003`
Parent: `W0-004`
Checked at: `2026-09-03T16:23:58Z`
Scope: SEC / Market Data / News / Official Source 等の外部source・providerを採用または再確認するときの共通利用条件確認票

## 1. 目的

`W0-004`の完了条件である、rate limit、User-Agent、保存、本文利用、再配布、費用、credentialを公式情報で再確認するための共通票を定義する。

本票はprovider採否そのものを決めるADRではない。後続の`S0-001`、`N0-001`、provider adapter ADR等が同じEvidence規則で現在条件を確認できるよう、確認項目・判定状態・根拠記録・再確認条件を固定する。

既存の`stock_monitoring_v0.1_provider_research.md`に記載された価格・制限は調査時点のsnapshotとして扱い、契約・実装・本番利用前に本票で再確認する。

## 2. 判定状態

各確認項目は必ず次のいずれかで記録する。空欄や推測値を許可しない。

| 判定 | 意味 | 実装・採否への扱い |
|---|---|---|
| `公式根拠あり` | provider自身、規制当局、契約文書、公式pricing/docs等に対象条件が明示されている | 根拠URL、確認時刻、適用plan/use caseを記録して利用可能 |
| `記載なし` | 調査した公式公開資料で対象条件を確認できない | 「許可」と解釈しない。必要なら契約確認へ昇格 |
| `契約確認要` | plan、法人/個人区分、再配布、本文保存等で公開情報だけでは適用条件を確定できない | credential投入・本番保存・再配布等を開始しない |

補助値として`対象外`を記録してよいが、判定自体は上記3状態のいずれかとし、なぜ対象外かを公式根拠または設計scopeで説明する。

## 3. Evidence優先順位

1. provider / authority の契約・Terms・Market Data Agreement・利用規約
2. provider / authority の公式API documentation・Fair Access・developer policy
3. provider公式pricing / plan comparison / product page
4. provider公式support / FAQ
5. sales回答・account-specific contract（GitHubには秘密や契約本文を保存せず、確認済みという事実と参照IDだけを保持）

検索結果、ブログ、レビュー、過去のOrderScope調査文書は公式source探索のleadには使えるが、利用条件確定のEvidenceにはしない。

## 4. 共通確認票

provider/sourceごとに以下を1行ずつ記録する。

| 項目 | 必須記録 | 判定基準 |
|---|---|---|
| Provider / source | 法人・公的機関名、service/product名 | 公式根拠あり |
| Use case | personal / internal business / commercial / redistribution / research 等 | 適用条件の取り違え防止 |
| Plan / tier | Free / Individual / Business / Enterprise 等 | plan不明なら契約確認要 |
| Endpoint / product scope | market data / news / filing / official feed 等 | scopeを越えた条件流用を禁止 |
| Rate limit | request/sec、request/min、hour/day、bandwidth、stream connection等 | 明記値＋単位。複数制限は全て記録 |
| User-Agent / request identity | 必須header、連絡先、client identification規則 | 明記がなければ記載なし |
| Credential | API key、secret、OAuth、不要等 | secret値は保存しない |
| Credential handling | header/query、token期限、共有禁止等 | 値ではなく方式だけ記録 |
| Historical depth | 履歴開始日、queryable history、plan差 | 時点依存の場合は確認日必須 |
| Data freshness | realtime / delayed / EOD / dissemination timing | plan・feed差を分離 |
| 保存 | raw response、metadata、derived data、cache、archiveの保存可否 | 明記がなければ許可と推測しない |
| 本文利用 | article body / description / filing text等の取得・処理・一時保持可否 | Newsはmetadataとbodyを分離して判断 |
| 再配布 | display、API提供、第三者共有、公開dataset、report添付等 | internal useとredistributionを別欄で判断 |
| Derived data | aggregate、feature、model output等への制約 | underlying dataを再構成可能か等も確認 |
| 費用 | 月額・年額・従量、個人/法人、add-on | 税・exchange fee・sales quoteは分離 |
| 契約主体 | individual / business / organization / non-professional等 | OrderScopeの実利用主体と一致確認 |
| Attribution | 表示義務、source link等 | 再配布不可でも内部report要件を確認 |
| Deletion / retention | expiration、削除義務、契約終了後の扱い | temporary content lifecycleへhandoff |
| Change mechanism | Terms更新通知、pricing変更、version date | 再確認triggerへ利用 |
| Canonical URL | 公式Terms/docs/pricingへの直接URL | 検索結果URLを使わない |
| Checked at | UTC | 時点情報として必須 |
| Effective / updated date | 公式に記載されていれば記録 | 無ければ`記載なし` |
| Unknowns | 未解決事項 | 推測で補完しない |
| Local consequence | adapter/config/schema/test/ADRへの影響 | 次工程を明示 |

## 5. 最低限の採用ゲート

外部providerを実装・credential付き接続へ進める前に、最低でも次を満たす。

- `rate limit`が`公式根拠あり`、または公式上「個別契約」と確認できており`契約確認要`としてblockされている。
- User-Agent等のrequest identity規則を確認している。SEC等で要求される場合はadapter contractへ反映する。
- credential方式が判明し、credential値をGit、DB dump、API response、ログへ保存しない設計になっている。
- 保存・本文利用・再配布を別々に確認している。
- `internal use`を「保存自由」「公開可能」と読み替えていない。
- News本文または第三者copyright contentを扱う場合、公開資料で明示されない保存権限を推測しない。
- 費用・plan・個人/法人区分が現在の利用主体に適合している。
- 条件が時点依存であるため、実装前または契約前に再確認日を設定する。

## 6. Seed適用例（採否決定ではない）

以下は本票が実際に3状態へ落とせることを確認するための限定例である。詳細なSEC条件は`WEB-005`、News Provider比較は`WEB-011`で再確認・拡張する。

### 6.1 SEC EDGAR

| 項目 | 判定 | 現時点の限定Fact / Unknown |
|---|---|---|
| rate limit | 公式根拠あり | SEC Accessing EDGAR Dataはcurrent max request rateを10 requests/secondと記載 |
| User-Agent | 公式根拠あり | declared User-Agentを要求し、company/contactを含むsample headerを提示 |
| credential | 公式根拠あり | 公開EDGAR取得はfree public accessとして案内。credential方式は当該公開取得説明に無し |
| 保存 | 記載なし | 当該Fair AccessページだけではOrderScopeの保存・retention条件を確定しない |
| 本文利用 | 記載なし | filing取得可能性と二次利用条件は別論点として扱う |
| 再配布 | 記載なし | 当該Fair Accessページだけから再配布権を推測しない |
| 費用 | 公式根拠あり | EDGAR情報はfree download/queryと案内 |

Canonical evidence:
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

### 6.2 Tiingo News（WEB-011用seed）

| 項目 | 判定 | 現時点の限定Fact / Unknown |
|---|---|---|
| rate limit | 公式根拠あり | pricing/product pageにplan別hour/day/bandwidth上限あり |
| User-Agent | 記載なし | 今回確認した公式pricing/news/general docsでは専用User-Agent必須規則を確認していない |
| credential | 公式根拠あり | News API docsはAPI tokenが必要と記載 |
| 保存 | 契約確認要 | internal use条件は明記されるが、News本文・description等のdurable retention範囲を公開情報だけで一般化しない |
| 本文利用 | 契約確認要 | product pageのfieldsはTitle/URL/Source/Description等。original article bodyの権利や一時保存範囲は別途確認が必要 |
| 再配布 | 公式根拠あり | General docs / Termsはinternal useとredistributionを区別し、redistributionは別途permission/licenseが必要とする |
| 費用 | 公式根拠あり | Individual Power $30/month、commercial/internal business pricing等を公式pricingで確認可能 |

Canonical evidence:
- https://www.tiingo.com/about/pricing
- https://www.tiingo.com/products/news-api
- https://www.tiingo.com/documentation/general
- https://api.tiingo.com/tos/

### 6.3 Alpaca Market Data（市場データ側のseed）

| 項目 | 判定 | 現時点の限定Fact / Unknown |
|---|---|---|
| rate limit | 公式根拠あり | Market Data docsにTrading API Basic 200/min、Algo Trader Plus 10,000/min等を記載 |
| User-Agent | 記載なし | 今回確認したMarket Data overviewでは専用User-Agent要件を確認していない |
| credential | 公式根拠あり | Trading APIはkey/secret header、Broker APIはclient credentials flowを記載 |
| 保存 | 契約確認要 | API docsだけでは保存・exchange data retention条件を一般化しない |
| 本文利用 | 公式根拠あり | Market Data product scopeではNews本文は対象外として扱う |
| 再配布 | 契約確認要 | Customer Agreement等でmarket dataのreproduction/distribution制限が存在するため、利用主体・feed・planに応じた契約確認が必要 |
| 費用 | 公式根拠あり | Trading API Basic Free、Algo Trader Plus $99/month等を公式docsで確認可能 |

Canonical evidence:
- https://docs.alpaca.markets/us/docs/about-market-data-api

### 6.4 Massive Stocks（比較候補seed）

| 項目 | 判定 | 現時点の限定Fact / Unknown |
|---|---|---|
| rate limit | 公式根拠あり | individual Stocks Basicは5 API calls/min、上位individual planはUnlimited等をpricingで明記 |
| User-Agent | 記載なし | 今回確認したpricing / Market Data Termsでは専用User-Agent要件を確認していない |
| credential | 契約確認要 | API認証方式はadapter実装前にAPI docsで再確認する |
| 保存 | 契約確認要 | individual/business、exchange data、partner datasetで条件が変わり得るためplan単位で確認 |
| 本文利用 | 契約確認要 | Stocks APIのNews endpointとBenzinga partner dataはmarket data planと権利条件を同一視しない |
| 再配布 | 契約確認要 | Market Data Termsはpersonal/non-business licenseを示す一方、business pricingも別に存在するため実利用契約で確定する |
| 費用 | 公式根拠あり | individual Stocks Basic $0、Starter $29、Developer $79、Advanced $199。Business planは別価格 |

Canonical evidence:
- https://massive.com/pricing?product=stocks
- https://massive.com/legal/market-data-terms-of-service
- https://massive.com/business-stocks

## 7. 実装用record案

本票自体はschema実装を要求しないが、後続で機械的に扱う場合は次のようなprovider-neutral recordへ落とせる。

```text
provider_terms_check:
  provider_id
  product_id
  plan_id
  use_case
  checked_at
  effective_date
  field
  status: official_evidence | not_stated | contract_confirmation_required
  value_summary
  canonical_url
  evidence_class
  unknowns
  local_consequence
```

`value_summary`へcredential値、契約本文、provider response bodyを入れない。

## 8. 再確認trigger

次のいずれかで既存確認を`再確認要`にする。

- 契約または有料planへ移行する直前
- individual → business / organizationへ利用主体が変わる
- internal use → display / redistribution / external API提供へ用途が変わる
- News本文のdurable保存を開始する
- endpoint/feed/providerを切替える
- pricing、Terms、developer docsに更新日変更を検出する
- rate-limit error、licence warning、account restriction等を観測する
- 90日以上前の時点情報を採用判断に使う場合（運用上の再確認目安。provider公式規則ではない）

最後の90日はOrderScope側の運用目安であり、providerの公式期限ではない。

## 9. Handoff

### S0-001 / WEB-005

SECのUser-Agent、Fair Access、endpoint、保存条件を本票の各欄で再確認する。WEB-003のseed値は完了証跡として流用せず、WEB-005の確認日時で更新する。

### N0-001 / WEB-011

Tiingo、Massive/Benzinga等のNews候補について、価格・履歴・rate・本文権利・internal-use・redistributionをplan/use case単位で本票へ適用し、採否をADR化する。

### adapter ADR / contract test

- rate limit値とbackoff/pacing設定を分離する。
- request identity / credential方式をadapter boundaryに閉じ込める。
- temporary content lifecycleは`保存`と`本文利用`が明示的に許容または契約確認済みの場合のみ有効化する。
- `記載なし`をdefault allowにしない。

## 10. 未解決事項

- SEC公開情報の再利用・保存・再配布の法的整理はWEB-005で追加確認する。
- Tiingo NewsのArticle body相当データの提供範囲とdurable retention可否はWEB-011で確認する。
- Alpacaのmarket data retention / redistributionは利用主体・exchange agreementを含めadapter採用前に確認する。
- Massiveのindividual/business/partner dataにまたがる保存・再配布条件は候補採用時にproduct/plan単位で確認する。

これらはWEB-003の共通票作成を妨げないが、各provider採用判断を完了したことを意味しない。
