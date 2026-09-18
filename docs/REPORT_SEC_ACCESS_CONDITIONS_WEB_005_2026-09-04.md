# OrderScope — SEC接続条件再確認（WEB-005）

Status: Web research complete; local implementation pending
Date: 2026-09-04
Web ID: `WEB-005`
Parent: `S0-001`
Dependency: `WEB-003` handed off
Evidence checked at: `2026-09-03T16:28Z`〜`2026-09-03T16:31Z` UTC

## 1. 目的

`S0-001`のWeb入力として、SEC EDGAR / `data.sec.gov` を自動取得する際の現行公式条件を、`WEB-003`の共通確認票に沿って再確認する。

本書は公開情報の調査結果であり、adapter実装、credential付き取得、実測rate試験、retry試験、保存実装の完了を意味しない。

## 2. 結論

v0.1のSEC取得baselineは維持できる。

- SECはprogrammatic accessを許容しているが、Fair Accessを守る必要がある。
- 現行公式上限は、利用者単位で**合計10 requests/second以下**。複数machineへ分散しても合算される。
- 自動取得requestでは、組織名と連絡可能なemailを含む識別可能な`User-Agent`を宣言する。
- `data.sec.gov`のSubmissions / XBRL Data APIsは公開REST APIで、**authentication / API key不要**。
- `data.sec.gov`はCORSをサポートしないため、browser direct access前提ではなくserver/adapter側から取得する。
- 大量取得ではnightly bulk ZIPが公式に「most efficient」とされており、逐次APIだけに固定しない。
- SEC作成コンテンツおよび公開EDGAR filing contentは、SEC FAQ上free to access and reuse。ただしFair Access制約は別途守る。
- retention期間やローカル保存量の上限は、今回確認したSEC公式公開資料では明示的な制限を発見していない。これは`無制限保存を許可`という意味ではなく、`記載なし`として扱う。

## 3. WEB-003共通確認票への適用

| 項目 | 判定 | 現行公式情報 | ローカル設計への帰結 |
|---|---|---|---|
| Provider / source | 公式根拠あり | U.S. Securities and Exchange Commission / EDGAR / `data.sec.gov` | SEC adapterを独立source laneとして維持 |
| Credential | 公式根拠あり | Public Data APIsはauthentication / API key不要 | secret schemaへSEC API keyを要求しない |
| User-Agent | 公式根拠あり | SEC FAQはdeclared bot header例として会社名と管理連絡先emailを示す | `User-Agent`をconfig必須にし、空・generic botを拒否するcontract test候補 |
| Rate / Fair Access | 公式根拠あり | user totalで10 req/s以下。machine数によらない。過剰アクセスはIP制限対象 | process単位でなくSEC lane全体のshared limiterを設計。10 req/sを目標値ではなくhard public ceilingとして扱う |
| Block解除 | 公式根拠あり | Privacy/Security policyは、rateがthreshold未満へ下がった後10分でresume可能と記載 | 429/403相当を即時tight loopで再試行せず、cooldownを持つ。実際のresponse code挙動はlocal testで確認 |
| API endpoint | 公式根拠あり | `https://data.sec.gov/submissions/CIK##########.json` | CIK/submissions adapterのprimary endpoint |
| Company Concept | 公式根拠あり | `/api/xbrl/companyconcept/CIK.../{taxonomy}/{tag}.json` | concept単位取得が必要なfallback候補 |
| Company Facts | 公式根拠あり | `/api/xbrl/companyfacts/CIK##########.json` | Company Facts adapterのprimary endpoint候補 |
| Frames | 公式根拠あり | `/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json` | entity横断比較用。個社segmentの完全代替とみなさない |
| Filing documents / index | 公式根拠あり | EDGAR Archives、daily/full indexes、filing directoryを公開 | Filing document取得・historical catch-upのsource候補 |
| Bulk data | 公式根拠あり | `companyfacts.zip`、`submissions.zip`をnightly再構築 | bootstrap / catch-upではbulkを優先できるcontractを残す |
| API freshness | 公式根拠あり | Submissionsは通常1秒未満、XBRL APIは通常1分未満のprocessing delay。ただしpeak時は長くなり得る | `available_at`を推測せずretrieval時刻とSEC timestampを分離。latency保証値として扱わない |
| Bulk freshness | 公式根拠あり | nightly、約3:00 a.m. ET更新 | intraday検出には使わずbootstrap/catch-up向け |
| CORS | 公式根拠あり | `data.sec.gov`はCORS非対応 | browser direct fetchをv0.1 contractにしない |
| Public content reuse | 公式根拠あり | SEC FAQ: Government-created contentとpublic EDGAR filing contentはfree to access and reuse | filing本文をsource evidenceとして利用可能。ただし一部非政府素材等の例外は個別確認 |
| Retention / local storage duration | 記載なし | 今回確認した公式developer/API/Fair Access/FAQ資料では、公開EDGAR filingのローカル保存期間上限を発見せず | `記載なし`をdefault allowへ変換しない。OrderScope側retention policyを別途適用 |
| Redistribution | 公式根拠あり / 例外注意 | public EDGAR filing contentはreuse可。SEC FAQは一部stock art等に例外があるとする | EDGAR filingとsec.govページ上の第三者素材を同一扱いしない |
| Cost | 公式根拠あり | Public EDGAR/Data API accessはAPI key不要で公開。FAQはpublic contentをfree to accessとする | SEC source自体のAPI subscription costはv0.1で不要。network/storage/compute costは別 |
| Technical support | 公式根拠あり | SECはscripted downloadの開発・debug supportを提供しない | adapter障害時にprovider supportを前提としない |

## 4. Endpointと取得経路

### 4.1 Incremental / near-real-time

1. `data.sec.gov/submissions/CIK##########.json`
   - entity current filing history。
   - metadataとしてname、former names、exchange、ticker等を含む。
   - recent filingsはcompact columnar array、古い履歴は追加JSON fileへの参照を持つ。

2. EDGAR Latest Filings / RSS
   - SEC FAQはfilingを可能な限り早く取得する用途でLatest Filingsと関連RSSを案内している。
   - heavily accessed resourceなのでFair Accessを厳守する。
   - v0.1のAMD/NVDA bounded pollingで必須とは限らず、S0 adapter形状確定時に採否を決める。

### 4.2 Filing document / historical

- `/Archives/edgar/daily-index`
- `/Archives/edgar/full-index`
- `/Archives/edgar/data/{CIK}/...`

index directoryには`index.html` / `index.xml` / `index.json`が用意されている。大量historical crawlをHTML画面検索へ依存させない。

### 4.3 XBRL

- Company Facts: 個社のstandard taxonomy factsを一括取得。
- Company Concept: 個社×concept。
- Frames: calendar periodへ近似整列したentity横断facts。

重要な制約として、SEC API documentationはXBRL aggregation対象を、non-custom taxonomyかつfiling entity全体に適用されるfactsとして説明している。したがって、segment revenue等でdimension/custom extensionが必要な場合にCompany Factsだけで完全取得できるとは仮定しない。これは`WEB-009` / `E0-005`で別途検証する。

## 5. Fair Access実装へのhandoff

### Fact

- 公開上限は10 req/s以下。
- SECはefficient scriptingと必要な分だけのdownloadを求めている。
- unclassified bots / automated tools outside acceptable policyは制御対象になり得る。

### Interpretation / design input

以下はSEC公式文言そのものではなく、OrderScope側の実装提案である。

- limiterはworker/thread/machineごとではなく`SEC` source lane共通で持つ。
- 10 req/sぎりぎりを通常運用値にせず、headroomを設ける。
- `User-Agent`は`<product-or-org> <contact-email>`をconfigで固定し、credentialとは扱わないがGitへ個人emailを直接埋め込まない。
- 429/403/Access Denied時はbounded backoff + cooldownへ移し、tight retryを禁止する。
- historical bootstrapはbulk ZIPを優先し、AMD/NVDAの日次incrementalにSubmissions APIを使う二経路をcontractで許容する。
- response cache / ETag / conditional requestの具体挙動は今回の公式資料で完了条件にできるだけの根拠を確認していないため、実装時に別途検証する。

## 6. 保存・再利用条件

SEC FAQは、Government-created content on sec.govおよびEDGAR public filing contentについてfree to access and reuseと明記している。

ただし、次を分ける。

- **Fact:** public EDGAR filing contentのreuseは許可される。
- **Fact:** sec.gov上でもstock art等、free reuseでない例外が少数存在する。
- **Unknown:** SEC公開資料に、OrderScopeのローカルDBへ保存するpublic filing本文の具体的な最大retention日数は今回確認できなかった。
- **Local policy:** OrderScope側のtemporary-content lifecycle、hash/provenance、削除規則を独立に適用する。

したがって`SEC公開データだから何でも無期限保存`とは結論しない。

## 7. 曖昧点・未解決

1. `User-Agent`の厳密な文法はsampleが示されているが、正式なABNF等は確認できない。
2. 10 req/s以下であっても、アクセスpatternや負荷によって追加制御されない保証はない。
3. block時のHTTP status、Retry-After header等の実際の挙動はlocal adapter testが必要。
4. retention期間の明示的上限は今回の公式資料では`記載なし`。
5. conditional GET / ETag / Last-Modifiedのendpoint別保証は今回未確認。
6. Company Factsでsegment dimension/custom taxonomyを十分に扱えるとは確認できず、`WEB-009`へ引き継ぐ。

## 8. ローカルhandoff

### S0-002 CIK/submissions adapter

- declared `User-Agent`必須。
- source-wide rate limiter。
- Submissions API primary + historical referenced JSON / bulk fallback。
- vendor JSONをCoreへ漏らさずprovider-neutral `FilingRecord`へ変換。

### S0-003〜005 Filing persistence/document

- accessionをstable identity候補として扱い、document ref/hashとretrieved timeを保持。
- EDGAR Archive pathをsource provenanceとして保持。
- reuse可否とOrderScope retention policyを分離。

### S0-006 XBRL adapter

- Company Facts / Company Concept / Framesの役割を分離。
- taxonomy、tag、unit、period、source filingを保持。
- dimension/custom extensionを欠損値で推測しない。

### S0-007 acceptance test

最低限、以下をlocal fixture / controlled live testで確認する。

- declared User-Agentなし/ありの扱い
- shared limiterの上限遵守
- duplicate accessionの冪等性
- amendment / partial / transient failure
- cooldown/backoff
- submissions recent/history境界
- XBRL missing/dimension case

## 9. WEB-005完了判定

Web完了条件「現行公式文書、確認日、曖昧点が記録される」を満たす。

`WEB-005`は`S0-001`へ**引渡し済み**とする。一方、`S0-001`以降のlocal implementation / testは未完了である。

この完了によりWeb依存上は次を解放できる。

- `WEB-006` — form目的・例外の公式対応表
- `WEB-007` — Earnings契約事例
- `WEB-009` — segment revenue取得可能性

`WEB-020`はSEC条件依存の一部だけが解消され、`WEB-011`、`WEB-016`およびlocal implementation evidenceが引き続き必要。

## 10. 公式Evidence

1. SEC, **Developer Resources**  
   https://www.sec.gov/about/developer-resources  
   - Fair Access、10 req/s、efficient scripting、EDGAR/data APIへの入口。

2. SEC, **Webmaster Frequently Asked Questions**  
   https://www.sec.gov/about/webmaster-frequently-asked-questions  
   - declared User-Agent sample、10 req/s、public EDGAR content reuse、Latest Filings/RSS、ticker/CIK files。

3. SEC, **EDGAR Application Programming Interfaces (APIs)**  
   https://www.sec.gov/search-filings/edgar-application-programming-interfaces  
   - no authentication/API key、Submissions、Company Concept、Company Facts、Frames、bulk ZIP、update schedule、CORS非対応。

4. SEC, **Accessing EDGAR Data**  
   https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data  
   - daily/full indexes、EDGAR archive access。

5. SEC, **Privacy Information / Internet Security Policy**  
   https://www.sec.gov/about/privacy-information  
   - 10 req/s threshold、excessive access制御、threshold未満へ低下後10分のresume条件、policy変更可能性。

## 11. Evidence分類

| Source | Publisher | Evidence class | Effective/version date | Checked at |
|---|---|---|---|---|
| Developer Resources | SEC | official rule / official data | Last reviewed 2025-03-10 | 2026-09-03 UTC |
| Webmaster FAQ | SEC | official rule / official data | page current at check; individual sections version not separately stated | 2026-09-03 UTC |
| EDGAR APIs | SEC | official data / official rule | Last reviewed 2025-04-08 | 2026-09-03 UTC |
| Accessing EDGAR Data | SEC | official data | page current at check | 2026-09-03 UTC |
| Privacy Information | SEC | official rule | page current at check; policy explicitly changeable | 2026-09-03 UTC |

料金、rate、Fair Access、endpoint挙動は時点依存情報として、実装前および運用時に再確認する。
