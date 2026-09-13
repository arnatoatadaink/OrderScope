# OrderScope — Earnings event/result契約事例調査（WEB-007）

Status: Web調査完了 / local handoff ready (non-normative)
Date: 2026-09-04
Web ID: `WEB-007`
Parent: `E0-001`
Branch: `docs/mermaid-conventions-v0.1`
Evidence checked at: `2026-09-03T18:16Z`

## 1. 目的

`E0-001`のEarnings event/result契約で、予定日時、実発表時刻、fiscal period、通貨、GAAP/non-GAAP、sourceを混同しないためのCanary事例をAMD/NVIDIAの公式一次情報から収集する。

本書はWeb調査による設計入力であり、schema実装、adapter、fixture実行、受入試験を完了したとは扱わない。

## 2. 結論

Earningsを1個の`timestamp`や1個の`eps`へ潰すと、公式情報だけでも意味が衝突する。少なくとも次を分離する必要がある。

1. **予定された決算発表日 / release window** — 例: AMDは2026-08-04の`after the market close`。
2. **予定されたearnings call時刻** — AMDは17:00 ET、NVIDIAは2026-08-26 14:00 PT。
3. **実際のrelease公開時刻** — sourceが時刻を明示した場合だけ保存する。今回確認したAMD/NVIDIA IR本文ではrelease日付は確認できるが、秒単位の公開時刻は確認できない。
4. **SEC filing accepted時刻** — AMD 8-Kは2026-08-04 16:16:24、NVIDIA 8-Kは2026-08-26 16:21:19。これはEDGAR受理時刻であり、IR release公開時刻の代用にしない。
5. **fiscal period** — AMD Q2 2026は2026-06-27終了、NVIDIA Q2 FY2027は2026-07-26終了。
6. **accounting basis** — GAAPとnon-GAAPを同一metric recordへ上書きしない。
7. **source role** — IR announcement、IR result release、SEC 8-K、SEC Exhibitを別Evidenceとして保持する。

## 3. Canary事例

### 3.1 AMD — Q2 2026

#### 予定情報

AMDの2026-07-08公式IR発表は、Q2 2026決算を**2026-08-04のmarket close後**に発表し、conference callを**17:00 ET / 14:00 PT**に行うと告知している。

このため、`scheduled_release_date=2026-08-04`と`scheduled_release_window=after_market_close`、`scheduled_call_at=2026-08-04T17:00:00-04:00`は別概念として保持する。

#### 結果・会計期間

AMD公式IR releaseはQ2 2026 resultsを2026-08-04付で公表している。SEC 8-Kは対象四半期が**2026-06-27終了**であることを明示する。

#### GAAP / non-GAAP

同じrelease内で、たとえばdiluted EPSはGAAP **$1.38**、non-GAAP **$1.66**である。gross margin、operating income、net income等もGAAP/non-GAAPの双方が並ぶ。

したがってmetric keyだけを`diluted_eps`とし値を1個にすると情報損失が起きる。`accounting_basis`または同等のdimensionが必須である。

#### source / timestamp境界

SECの8-K accession `0000002488-26-000121`は2026-08-04 **16:16:24** acceptedである。これは`filed_at`/`accepted_at` Evidenceとして使えるが、IR releaseの`released_at`とは別物である。

今回確認できたIR release本文は日付を示すが、公式本文上で秒単位release時刻は確認できなかった。したがって`actual_release_at`をSEC accepted時刻から補完してはならない。

### 3.2 NVIDIA — Q2 FY2027

#### 予定情報

NVIDIA公式IR event pageは`NVIDIA 2nd Quarter FY27 Financial Results`を**2026-08-26 14:00 PT**として掲載している。これはWebcast / earnings callの予定時刻として扱い、結果release時刻そのものとは分離する。

#### 結果・会計期間

NVIDIA公式IR releaseは2026-08-26付でQ2 FY2027 resultsを公表し、対象四半期が**2026-07-26終了**であることを明示する。

ここではissuerの表示上の`Q2 FY2027`をそのまま保持し、calendar yearだけから`Q2 2026`へ変換しない。

#### GAAP / non-GAAP

同じ公式releaseで、GAAP/non-GAAP diluted EPSはそれぞれ**$2.46 / $2.22**と区別される。gross marginは当該四半期では両方75.0%だが、値が同じでもbasisは統合しない。

#### source / timestamp境界

SECの8-K accession `0001045810-26-000073`は2026-08-26 **16:21:19** acceptedで、Item 2.02とExhibit 99.1/99.2を持つ。IR release日付、IR event時刻、SEC accepted時刻はそれぞれ別Evidenceである。

今回確認した公式IR release本文では秒単位release時刻を確認できなかったため、`actual_release_at`はunknownとして保持する。

## 4. 契約へ必要な区別

### 4.1 Event側

| Field候補 | 意味 | nullable | Canary根拠 |
|---|---|---:|---|
| `instrument_id` | internal instrument identity | no | WEB-001 handoff |
| `event_kind` | earnings release / earnings call等 | no | releaseとcallを分離 |
| `scheduled_release_date` | 予定発表日 | yes | AMD 2026-08-04 |
| `scheduled_release_window` | before/open/after-market-close等の予定window | yes | AMD `after the market close` |
| `scheduled_call_at` | earnings call/webcast予定時刻 | yes | AMD 17:00 ET、NVIDIA 14:00 PT |
| `actual_release_at` | sourceが明示した実release時刻 | yes | 今回のIR本文ではexact time未確認 |
| `fiscal_year_label` | issuer表示のFY label | no | NVIDIA FY2027 |
| `fiscal_quarter` | issuerのquarter label | no | Q2 |
| `period_end` | 会計期間終了日 | no | AMD 2026-06-27、NVDA 2026-07-26 |
| `source_evidence_id` | announcement/result/SEC等のEvidence参照 | no | source role分離 |

`actual_release_at`が不明でもevent recordを作れるようnullableとし、`scheduled_call_at`やSEC `accepted_at`から補完しない。

### 4.2 Result / Metric側

| Field候補 | 意味 | 例 |
|---|---|---|
| `metric_type` | revenue / net_income / diluted_eps / gross_margin等 | `diluted_eps` |
| `value` | sourceに記載された値 | AMD `1.38` |
| `unit` | currency/share/percent等 | `currency_per_share` |
| `currency` | currency normalization | `USD`（`$`表示をsource evidenceとともに正規化） |
| `accounting_basis` | GAAP / non-GAAP | `gaap`, `non_gaap` |
| `period_end` | 値が属するperiod | `2026-06-27` |
| `source_evidence_id` | 数値を裏付けるsource | AMD IR / SEC Exhibit |

`currency`はsourceの表示記号もEvidence側へ残す。ISO currencyへの正規化規則はlocal contractで明示し、記号だけを一般化して推測しない。

### 4.3 Provenance側

`I0-002`の共通provenance契約と整合させ、最低限次を別々に扱う。

- `event_time`: economic/event semantics上の時刻
- `published_at` / `released_at`: sourceが公表時刻を明示した場合
- `filed_at` / `accepted_at`: SEC受理時刻
- `retrieved_at`: adapter取得時刻
- `available_at`: システムで利用可能になった時刻
- `accepted_at`（internal）: OrderScope Coreが受理した時刻

SECのEDGAR `Accepted`とOrderScope内部の`accepted_at`は名称衝突しやすいため、実装では`source_accepted_at`等へ明示的に名前分けすることを推奨する。

## 5. Source role案

| Source role | 使う情報 | 優先・注意 |
|---|---|---|
| `issuer_schedule_announcement` | 発表予定日、release window、call予定 | scheduleの一次根拠 |
| `issuer_result_release` | actual result values、issuer fiscal label、GAAP/non-GAAP | resultの一次根拠 |
| `sec_8k` | period、filing metadata、Item 2.02、Exhibit参照 | filing/provenanceの一次根拠 |
| `sec_exhibit_99_1` | issuer releaseのSEC添付版 | IRとのcross-check |
| `issuer_event_page` | webcast/call時刻 | release時刻と同一視しない |

IRとSEC Exhibitの同一内容を別resultとして二重計上せず、Evidenceは複数紐づけ可能にする。

## 6. Unknowns / 推測禁止

- AMD Q2 2026 IR releaseの**秒単位の実公開時刻**: 今回確認した公式IR本文では未確認。
- NVIDIA Q2 FY2027 IR releaseの**秒単位の実公開時刻**: 今回確認した公式IR本文では未確認。
- SEC accepted時刻がpress release公開より前/後のどちらか: 個別sourceで明示されない限り推測しない。
- `$`から`USD`へのISO正規化: local contractのissuer/source context ruleとして明文化してから適用する。
- `after market close`の固定時刻化: 16:00 ETなどへ自動変換しない。windowとして保持する。

## 7. Local handoff

`E0-001`では次を実装・contract testする。

1. schedule、call、actual release、SEC filing時刻を別fieldで表現する。
2. `actual_release_at`をnullableにし、他のtimestampから補完しない。
3. issuer fiscal labelと`period_end`を両方保持する。
4. metricへ`accounting_basis`、unit、currency、period、sourceを持たせる。
5. IR releaseとSEC ExhibitをEvidenceとしてdedupeしつつ、provenanceは複数保持する。
6. AMD/NVIDIAの本書Canaryをfixture化し、GAAP/non-GAAPの上書き、FY label誤変換、SEC accepted時刻のrelease時刻誤用をnegative testにする。

`E0-002`以降の決算検出実装、adapter実行、抽出成功率は本Web調査では完了扱いにしない。

## 8. Evidence

### AMD

- AMD IR — `AMD to Report Fiscal Second Quarter 2026 Financial Results`
  - https://ir.amd.com/news-events/press-releases/detail/1289/amd-to-report-fiscal-second-quarter-2026-financial-results
  - Extracted fact: 2026-08-04 after market close、conference call 17:00 ET / 14:00 PT
  - Evidence class: official data
- AMD IR — `AMD Reports Second Quarter 2026 Financial Results`
  - https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results
  - Extracted fact: Q2 2026 result、GAAP/non-GAAP values
  - Evidence class: official data
- SEC — AMD Form 8-K accession `0000002488-26-000121`
  - https://www.sec.gov/Archives/edgar/data/2488/000000248826000121/0000002488-26-000121-index.htm
  - Extracted fact: accepted 2026-08-04 16:16:24、Item 2.02、Exhibits
  - Evidence class: official data
- SEC — AMD 8-K primary document
  - https://www.sec.gov/Archives/edgar/data/2488/000000248826000121/amd-20260804.htm
  - Extracted fact: quarter ended 2026-06-27、GAAP/non-GAAP separation
  - Evidence class: official data

### NVIDIA

- NVIDIA IR — `NVIDIA 2nd Quarter FY27 Financial Results`
  - https://investor.nvidia.com/events-and-presentations/events-and-presentations/event-details/2026/NVIDIA-2nd-Quarter-FY27-Financial-Results/default.aspx
  - Extracted fact: 2026-08-26 14:00 PT event/webcast
  - Evidence class: official data
- NVIDIA IR — `NVIDIA Announces Financial Results for Second Quarter Fiscal 2027`
  - https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/default.aspx
  - Extracted fact: quarter ended 2026-07-26、GAAP/non-GAAP values
  - Evidence class: official data
- SEC — NVIDIA Form 8-K accession `0001045810-26-000073`
  - https://www.sec.gov/Archives/edgar/data/1045810/000104581026000073/0001045810-26-000073-index.html
  - Extracted fact: accepted 2026-08-26 16:21:19、Item 2.02、Exhibit 99.1/99.2
  - Evidence class: official data

## 9. Web完了判定

WEB-007の完了境界である「予定時刻、実発表時刻、期間、通貨、GAAP/non-GAAP、sourceの必要な区別を例示できる」を満たす。

ただし`actual_release_at`のexact timestampは公式IR本文から確認できなかったため、unknownを明示し、SEC accepted時刻で補完しない設計入力とした。これ自体がnullable timestamp契約の必要性を示すCanaryとなる。

状態は`引渡し済み`とし、`E0-001`のlocal contract実装へ渡す。
