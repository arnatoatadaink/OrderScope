# OrderScope — WEB-009 segment revenue fallback 可用性調査

Status: Web research complete; local implementation handoff
Date: 2026-09-04
Web ID: `WEB-009`
Parent: `E0-005`
Session: `web-2026-09-04-WEB-009`
Evidence checked at: `2026-09-03T21:36Z`

## 1. 目的と完了境界

`E0-005` の segment revenue fallback chain 実装へ渡すため、Corporate CanaryであるAMD/NVIDIAについて、複数四半期・複数年の公式SEC開示を使い、`Company Facts → XBRL Dimension → Filing Fallback` の各段階でsegment revenueを取得できる範囲と失敗理由を整理する。

Web完了境界は、各段階について取得可否または制約を公式Evidenceで記録し、欠損値を推測しないことまでとする。SEC APIへの実リクエスト、XBRL instance/contextのprogrammatic parse、dimension/member正規化、segment rename/merge/split/recast履歴の実装、抽出成功率の測定はローカル証跡が必要なため、本書では完了扱いにしない。

## 2. 結論

- `Company Facts` はsegment revenueの万能入口にはできない。SEC公式仕様ではXBRL APIの集約対象が「非custom taxonomy」かつ「filing entity全体に適用されるfact」に限定されるため、segment member等のdimensionを持つfactやissuer custom extensionは構造的に第一段階から外れ得る。
- NVIDIAではSECのInteractive Data reportが `Compute & Networking | Operating Segments`、`Graphics | Operating Segments` のようにmember別Revenueを明示しており、dimension-aware XBRLを第二段階として扱う根拠を確認できた。
- AMDでも10-Q/10-KのSegment Reportingに四半期・累計・比較期間のsegment net revenue表が継続して存在する。2025年度からClientとGamingを一つのreportable segmentへ統合し、過年度segment dataをretrospectiveに調整しているため、segment nameだけで履歴同一性を固定してはならない。
- Filing fallbackは両社で利用可能である。SEC HTML/Interactive Dataのsegment tableから公式値を取得でき、Company Factsやdimension parserが失敗しても欠損値を推測せず、filing accession・period・table role・source location付きでfallbackできる。
- `E0-005` は各試行結果に `method` と `failure_reason` を保存する必要がある。`Company Facts` が空であっても「segment revenueが存在しない」と解釈せず、`dimension_or_custom_fact_not_in_companyfacts_scope` 等として次段へ進む。

## 3. SEC XBRL APIの境界

SECのEDGAR API公式文書は、XBRL APIsが複数submissionから集約するfactについて次の条件を明記している。

1. non-custom taxonomy（例: `us-gaap`、`ifrs-full`、`dei`、`srt`）を使うこと。
2. filing entity全体に適用されること。

`companyfacts` は、その条件を満たすcompany conceptsを一社分まとめて返すAPIである。したがって、同一の標準Revenue conceptであってもsegment memberをcontext dimensionとして持つfactは「entity全体」のfactではなく、第一段のCompany Factsだけでsegment値を網羅できるとは扱わない。

### 実装上の判定

| Company Facts結果 | 解釈 | 次の操作 |
|---|---|---|
| 対象period/unitのsegment値が明示的に得られる | `company_facts_success`。source accession/contextを保持し、filingと照合候補にする | dimension/fallbackを必須にせず、quality/reconciliationで検証 |
| consolidated Revenueのみ得られる | segment欠損ではなく `entity_wide_only` | XBRL Dimensionへ進む |
| issuer custom conceptが必要 | `custom_extension_excluded_or_not_normalized` | filing XBRL instance / taxonomy extensionを読む |
| conceptは存在するがperiod/unitが一致しない | `period_or_unit_mismatch` | 対象filingのcontextを確認する |
| API/取得失敗 | `transport_or_partial_error` | retry policy後、source availabilityを失わず次段へ進む |

Company Factsの未取得をゼロやunknown revenueへ数値補完してはならない。

## 4. NVIDIA — dimension-aware XBRL可用性

### 4.1 年次: FY2026 Form 10-K

SEC Interactive Dataの `Segment Information - Reportable Segments (Details)` は、2026/2025/2024の3年を同じ表で保持している。

| Fiscal year end | Compute & Networking revenue | Graphics revenue | Total revenue |
|---|---:|---:|---:|
| 2026-01-25 | 193,479 | 22,459 | 215,938 |
| 2025-01-26 | 116,193 | 14,304 | 130,497 |
| 2024-01-28 | 47,405 | 13,517 | 60,922 |

単位はUSD millions。Interactive Data表示では `Compute & Networking | Operating Segments`、`Graphics | Operating Segments` のmember contextが明示されるため、第二段のdimension-aware parserで扱うべきcaseとして確認できる。

### 4.2 Q1 FY2027 Form 10-Q

2026-04-26終了四半期のSegment Informationでは次を確認した。

| Period | Compute & Networking | Graphics | Total |
|---|---:|---:|---:|
| 3M ended 2026-04-26 | 74,550 | 7,065 | 81,615 |
| 3M ended 2025-04-27 | 39,589 | 4,473 | 44,062 |

同filingはRevenue by Market Platformの表示方法をQ1 FY2027に変更し、比較期間をrecastしている。これはreportable segmentとは別の分類軸であるため、`Compute & Networking` / `Graphics` と `Data Center` / `Hyperscale` / `AI Clouds, Industrial, & Enterprise` 等を同じSegmentIdentityとして統合しない。

### 4.3 Q2 FY2027 Form 10-Q

2026-07-26終了四半期では次を確認した。

| Period | Compute & Networking | Graphics | Total |
|---|---:|---:|---:|
| 3M ended 2026-07-26 | 88,299 | 7,922 | 96,221 |
| 6M ended 2026-07-26 | 162,850 | 14,987 | 177,837 |
| 3M ended 2025-07-27 | 41,331 | 5,412 | 46,743 |
| 6M ended 2025-07-27 | 80,920 | 9,885 | 90,805 |

このため、単一quarter値とYTD値を `period_start/end` またはdurationで区別せずに同じ値として扱ってはならない。

### NVIDIA判定

- Company Facts: `要fallback前提`。SEC API scope上、dimension付きsegment factsの網羅を保証しない。
- XBRL Dimension: `Web Evidenceで可用性確認`。Interactive DataでOperating Segments member別Revenueを確認。
- Filing fallback: `可用`。10-K/10-QのSegment Information表に公式値が存在。

## 5. AMD — segment tableとrecast境界

### 5.1 FY2025 Form 10-K

AMDの2025 Form 10-Kは、2025年度からsegment structureを変更してClientとGamingを一つのreportable segmentに統合した構造を採用している。年次表では2025/2024/2023の値を同じ現在表示へ並べている。

| Fiscal year | Data Center | Client | Gaming | Total Client & Gaming | Embedded | Total revenue |
|---|---:|---:|---:|---:|---:|---:|
| 2025 | 16,635 | 10,640 | 3,910 | 14,550 | 3,454 | 34,639 |
| 2024 | 12,579 | 7,054 | 2,595 | 9,649 | 3,557 | 25,785 |
| 2023 | 6,496 | 4,651 | 6,212 | 10,863 | 5,321 | 22,680 |

Client/Gamingは現在のreportable segment内で個別business revenueを継続開示しているが、各business自体は別reportable segmentではない。`segment_identity` と `disaggregated_business_line` を別属性にする必要がある。

### 5.2 Q1 2026 Form 10-Q

2026-03-28終了四半期では次を確認した。

| Period | Data Center | Client | Gaming | Total Client & Gaming | Embedded | Total revenue |
|---|---:|---:|---:|---:|---:|---:|
| 3M ended 2026-03-28 | 5,775 | 2,885 | 720 | 3,605 | 873 | 10,253 |
| 3M ended 2025-03-29 | 3,674 | 2,294 | 647 | 2,941 | 823 | 7,438 |

### 5.3 Q2 2026 Form 10-Q

2026-06-27終了四半期では次を確認した。

| Period | Data Center | Client | Gaming | Total Client & Gaming | Embedded | Total revenue |
|---|---:|---:|---:|---:|---:|---:|
| 3M ended 2026-06-27 | 6,718 | 3,062 | 779 | 3,841 | 977 | 11,536 |
| 3M ended 2025-06-28 | 3,240 | 2,499 | 1,122 | 3,621 | 824 | 7,685 |
| 6M ended 2026-06-27 | 12,493 | 5,947 | 1,499 | 7,446 | 1,850 | 21,789 |
| 6M ended 2025-06-28 | 6,914 | 4,793 | 1,769 | 6,562 | 1,647 | 15,123 |

### AMD判定

- Company Facts: `要fallback前提`。API scopeからdimension/custom factsを第一段だけで網羅できない。
- XBRL Dimension: `filingはInline XBRLだが、Web調査だけではAMDの各Revenue cellのcontext/member mappingを完全確定していない`。ローカルでEXTRACTED XBRL INSTANCEとdefinition/presentation linkbaseをparseし、member・concept・duration・unitを保存する。
- Filing fallback: `可用`。複数四半期・年次のSegment Reporting表から公式segment/disaggregated revenueを取得可能。

AMDの第二段をWeb上で「抽出成功」とは扱わず、`dimension_context_mapping_requires_local_instance_parse` を既知の未検証理由として残す。

## 6. Fallback chain contract案

`E0-005` の最小contractは次の順序とする。

1. `Company Facts`
   - issuer、concept候補、period、unitを照合する。
   - segment値が取得できなければ失敗理由を保存して次段へ進む。
2. `XBRL Dimension`
   - filing accessionを固定する。
   - standard/custom concept、context、axis、member、period、unitを読む。
   - text labelだけでsegmentを同定しない。
3. `Filing Fallback`
   - Segment Reporting/Segment Informationの公式tableを対象とする。
   - accession、form、period、table/section role、row label、column period、unitをEvidenceとして保持する。
   - parserで確定できないcellはnull+failure reasonとし、人間向け表示から値を推測しない。

### 保存すべきmethod/failure reason例

| Field | 候補 |
|---|---|
| `extraction_method` | `company_facts`, `xbrl_dimension`, `filing_table` |
| `status` | `success`, `not_applicable`, `partial`, `failed` |
| `failure_reason` | `entity_wide_only`, `dimension_fact_not_in_companyfacts_scope`, `custom_extension_not_normalized`, `concept_not_found`, `period_mismatch`, `unit_mismatch`, `context_member_unresolved`, `table_layout_unresolved`, `transport_error` |
| `source_accession` | SEC accession。fallback間で必ず追跡可能にする |
| `concept_qname` | 標準/customを含む実際のQName。filing tableだけの場合はnullable |
| `axis_member` | dimension取得時のaxis/member。table fallbackだけの場合はnullable |
| `period_start/end` | quarter/YTD/annualを区別 |
| `unit` | USD、USD millions等の表示単位とXBRL unitを正規化前後で保持 |
| `raw_label` | issuerが表示したsegment/business label |
| `normalized_segment_id` | E0-006の履歴contractで解決。WEB-009だけでは固定しない |

## 7. SegmentIdentityHistoryへの影響

WEB-009の調査だけでも、E0-006でname-only同一視を禁止すべきcaseが確認できた。

- AMD: 2025年度からClientとGamingを一つのreportable segmentへ統合し、prior-period segment dataをretrospectiveに調整。現在表に現れる2024/2023値が当時のoriginal presentationと同じ分類であるとは限らない。
- AMD: `Client` と `Gaming` は統合後も個別revenueを開示するが、別reportable segmentではない。
- NVIDIA: reportable segmentsはCompute & Networking / Graphicsを維持しつつ、market-platform revenue presentationをQ1 FY2027に変更し比較期間をrecast。分類軸が異なる。

よって `as_reported_at`, `filing_accession`, `classification_role`（reportable segment / disaggregated business / market platform）、`recast_flag` を履歴設計で検討する。

## 8. Fixture候補

### AMD

- FY2025 10-K: 2025/2024/2023のrecast済みsegment table。
- Q1 2026 10-Q: quarter比較のData Center / Client and Gaming / Embedded。
- Q2 2026 10-Q: 3Mと6Mが同時に存在するduration disambiguation case。
- Client/Gaming individual revenueは存在するがreportable segmentではないnegative identity case。

### NVIDIA

- FY2026 10-K Interactive Data `Reportable Segments (Details)`: dimension/member別Revenue。
- Q1 FY2027 10-Q: reportable segmentとrecast済みMarket Platformが同一filingに並ぶclassification-axis case。
- Q2 FY2027 10-Q: 3M/6M durationが同時に存在するcase。

fixtureには公開metadataと最小必要なfact/table構造を使い、SEC取得条件はWEB-005のlimiter/User-Agent方針に従う。

## 9. 不明点・ローカル未検証

- AMD/NVIDIAのCompany Facts APIを実際に取得して、どのsegment関連conceptが欠落/残存するかを網羅比較していない。
- AMD Q1/Q2 2026の各segment revenue cellについて、axis/member/QNameの完全なcontext mappingはローカルinstance parse未実施。
- NVIDIAについてInteractive Data上のmember構造は確認したが、adapterが取得するraw instance表現とSEC viewer表示の同値性はcontract test未実施。
- custom taxonomy extensionのrename、namespace revision、標準taxonomyへのmigrationを跨ぐ正規化規則は未確定。
- Filing fallbackのHTML DOM selector、table header span、footnote/recast annotationのparser安定性は未試験。
- `Client`/`Gaming`等のbusiness lineをsegmentとして保存するか、別Fact dimensionとして保存する最終schemaはE0-006/I0-005の設計判断が必要。
- 抽出成功率、coverage、latencyは実測していない。

これらを推測で補完せず、local adapter/fixture/quality testへ引き渡す。

## 10. ローカルhandoff

`E0-005` は次の順で着手可能。

1. S0-006でCompany Factsとfiling XBRL instanceをprovider-neutral factへ正規化する。
2. Company Facts lookupは成功/失敗理由を必ずrecordし、segment欠損を0に変換しない。
3. accession固定後、dimension-aware parserでconcept/context/axis/member/duration/unitを抽出する。
4. dimension解決不能時のみSegment Reporting table parserへfallbackする。
5. AMD/NVIDIAの上記fixtureで3M/6M/annual、recast、business-line vs reportable-segmentをnegative/positive test化する。
6. E0-006でSegmentIdentityHistoryを実装してから、E0-007の複数四半期reconciliationへ進む。

Web側のWEB-009はこのhandoffをもって `引渡し済み` とできる。ただし親`E0-005`はS0-006/E0-004依存のlocal実装・試験が残る。

## 11. 公式Evidence

- SEC — EDGAR Application Programming Interfaces (APIs): https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- AMD Q1 2026 Form 10-Q: https://www.sec.gov/Archives/edgar/data/2488/000000248826000076/amd-20260328.htm
- AMD Q2 2026 Form 10-Q: https://www.sec.gov/Archives/edgar/data/2488/000000248826000123/amd-20260627.htm
- AMD FY2025 Form 10-K: https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm
- AMD H1 2025 SEC Interactive Data — Segment Reporting: https://www.sec.gov/Archives/edgar/data/2488/000000248825000108/R11.htm
- NVIDIA FY2026 Form 10-K — Segment Information: https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/R25.htm
- NVIDIA FY2026 Interactive Data — Reportable Segments (Details): https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/R82.htm
- NVIDIA Q1 FY2027 Form 10-Q: https://www.sec.gov/Archives/edgar/data/1045810/000104581026000052/nvda-20260426.htm
- NVIDIA Q1 FY2027 Interactive Data — Segment Information: https://www.sec.gov/Archives/edgar/data/1045810/000104581026000052/R20.htm
- NVIDIA Q2 FY2027 Form 10-Q: https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm
- NVIDIA Q2 FY2027 Interactive Data — Segment tables: https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/R33.htm

Evidence class: `official rule` / `official data`.
