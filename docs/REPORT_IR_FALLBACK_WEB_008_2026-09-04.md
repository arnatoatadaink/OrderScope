# OrderScope — WEB-008 AMD/NVIDIA IR fallback 調査

Status: Web research complete; local implementation handoff
Date: 2026-09-04
Web ID: `WEB-008`
Parent: `E0-003`
Session: `web-2026-09-04-WEB-008`
Evidence checked at: `2026-09-03T21:15Z`

## 1. 目的と完了境界

`E0-003` の企業IR fallback実装へ渡すため、Corporate CanaryであるAMD/NVIDIAについて、決算releaseへ到達する公式のstable listing/archive経路と個別release URLを確認し、SECとの重複統合時に保持すべきsource優先順位を整理する。

本調査のWeb完了境界は、両社について公式release/archive経路を示すか、経路が確認できない場合にその欠落を明示することまでとする。adapter実装、HTTP挙動、hash/idempotency、更新・削除検知、SECとの自動重複統合はローカル試験を要するため、本書では完了扱いにしない。

## 2. 結論

- AMD、NVIDIAともに、公式IR/Newsroomから決算releaseへ到達する継続的な一覧経路と個別HTML URLを確認できた。
- AMDは `Financial Results` が決算専用の最も強いlistingであり、同じEarnings Releaseを `Press Releases` archiveからも辿れる。
- NVIDIAは `Investor Relations / Quarterly Results` が決算専用入口であり、個別release本文はNVIDIA公式Newsroomに置かれる。Newsroomには年別・press release別に辿れる `News Archive` がある。
- fallback adapterでは「入口/listing URL」と「最終個別release URL」を分離して保存し、取得時に個別URLをcanonical source refとして固定する。
- SECとIRが同一決算イベントを表す場合、SECを捨ててIRへ置換したり、その逆を行わず、同一eventへ複数Evidenceを関連付ける。数値Factはperiod/unit/accounting basis/sourceを保持する。

## 3. AMD stable経路

| 用途 | 公式経路 | 確認結果 | adapter上の扱い |
|---|---|---|---|
| 決算専用listing | `https://ir.amd.com/financial-information/financial-results` | 2026、2025、2024…と複数年を連続掲載し、各四半期に `Earnings Release`、webcast、資料、10-Q/10-K、XBRL等を対応付ける | 第一IR fallback listing。quarter/fiscal periodとrelease URLの対応取得に使う |
| Press release archive | `https://ir.amd.com/news-events/press-releases` | ページネーション、年、カテゴリを持つ公式archive。`financial`カテゴリで決算releaseを絞り込み可能 | 決算専用listingが欠ける場合の第二探索経路。通常ニュースとの混在を前提に分類する |
| 個別決算release例 | `https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results` | AMD Q2 2026の公式HTML release。発表日、GAAP/non-GAAP、segment summary等を含む | 最終canonical IR source ref候補。取得時のcontent hashを別途保持する |

### AMDで確認できた構造

`Financial Results` はQ2 2026について `Earnings Release` と同時に10-Q/XBRL等を同じquarter blockへ関連付けており、過去年も同構造で掲載されている。したがって、単なる最新ニュース画面よりもquarter単位のfallback discoveryに適している。

個別release URLは `/news-events/press-releases/detail/<numeric-id>/<slug>` の形を確認した。ただし、このURL形式が将来不変であるという公式保証は確認していない。実装ではURL規則を生成せず、listingから取得したhrefを保存する。

## 4. NVIDIA stable経路

| 用途 | 公式経路 | 確認結果 | adapter上の扱い |
|---|---|---|---|
| 決算専用入口 | `https://investor.nvidia.com/financial-info/quarterly-results/default.aspx` | Investor Relationsの `Financial Info > Quarterly Results` として公式ナビゲーションに固定。IR homeから `All Results` へ到達可能 | 第一IR fallback listing。IRが指すrelease/source群をquarter単位で取得する |
| 公式Newsroom archive | `https://nvidianews.nvidia.com/news` | `News Archive` でpress release/blog、年を選択でき、複数年のfinancial-results releaseを辿れる | 第二探索経路。IR listingから個別releaseが解決できない場合や履歴探索に使う |
| 個別決算release例 | `https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2027` | NVIDIA Q2 FY2027の公式Press Release。release日、GAAP/non-GAAP、period、決算値を含む | 最終canonical IR/issuer source ref候補。IRドメインからNewsroomへ遷移してもpublisherはNVIDIAとして保持 |

### NVIDIAで確認できた構造

NVIDIA Investor Relationsは公式ナビゲーション上で `News` を `nvidianews.nvidia.com` へリンクし、`Quarterly Results` を独立したFinancial Infoとして持つ。またIRページは、重要なfinancial informationをIR website、press releases、SEC filings、public conference calls/webcastsで発表する旨を明記している。

Newsroomの `News Archive` は年を選択でき、financial resultsの個別releaseを複数年にわたって辿れる。個別URLは `/news/<slug>` の形を確認したが、AMD同様、slug規則を生成せずlisting hrefを保存する。

## 5. source優先順位案

ここでいう優先順位は「真実のsourceを一つに決めて他を破棄する順位」ではなく、取得・照合・fallback discoveryの順序である。

### 5.1 discovery優先順位

1. SEC側で既に対象決算候補が検出できている場合は、そのevent/periodを基準にする。
2. issuerの決算専用IR listingを確認する。
   - AMD: `Financial Results`
   - NVIDIA: `Quarterly Results`
3. issuerの公式release archiveを確認する。
   - AMD: `Press Releases`
   - NVIDIA: `News Archive`
4. listing/archiveから得た個別release URLを取得し、content hash、retrieved_at、published date等を保存する。
5. 個別releaseが取得不能でも、SEC Evidenceが存在するならevent自体を欠損扱いにせず、IR Evidenceだけをpartial/errorとして記録する。

### 5.2 Evidence保持順位

- SEC Filing / accepted record: filing/acceptanceのTier 1 Evidenceとして保持。
- Issuer IR earnings release: 企業が公表した決算releaseのTier 1 Evidenceとして保持。
- IR listing/archive: discovery provenanceとして保持し、個別release本文の代替sourceとはみなさない。
- webcast/transcript/slides等: 補助Evidence。E0-003の最小fallbackでは必須にしない。

SECとIRで同じ値が確認できても、sourceを一つへ潰さない。`event identity` と `evidence identity` を分け、同じeventへ複数Evidenceを関連付ける。

## 6. adapter contractへのhandoff

ローカル `E0-003` では最低限、次を保持する。

| Field / concept | 要求 |
|---|---|
| `issuer/instrument identity` | WEB-001/004のregistryを参照し、hostnameだけで企業を推定しない |
| `discovery_url` | Financial Results / Quarterly Results / archive等、個別releaseへ到達した入口 |
| `canonical_release_url` | listingから取得した個別release href。URLパターンから生成しない |
| `source_role` | `issuer_ir_release`、`issuer_ir_listing`、`sec_filing`等を分離 |
| `published_at/date` | sourceが明示した値のみ。時刻が不明なら補完しない |
| `retrieved_at` | 実取得時刻 |
| `content_hash` | 個別release本文または正規化対象contentのhash。hash方式はI0契約へ合わせる |
| `fiscal_period` | issuer labelを保持し、calendar quarterへ無断変換しない |
| `accounting_basis` | GAAP/non-GAAPを混同しない |
| `dedupe/event link` | SEC/IRを同一eventへ関連付けてもEvidence recordは残す |
| `fetch_status/error` | listing発見、個別取得失敗、partial等を区別する |

## 7. fixture候補

### AMD

- Q2 2026 Financial Results listing block
- Q2 2026 individual earnings release
- 同quarterの10-Q linkとの対応
- Press Releases `financial` categoryから同releaseへ到達する重複discovery

### NVIDIA

- Q2 FY2027 Quarterly Results / IR入口
- Q2 FY2027 individual Newsroom release
- News Archive検索から同releaseへ到達する重複discovery
- issuer fiscal label `Q2 Fiscal 2027` とcalendar dateを別属性として扱うcase

これらは公開URLをfixture metadataとして使えるが、実本文の長期保存可否・取得頻度・HTTP挙動はローカル実装時に再確認する。

## 8. 不明点・未検証

- AMD/NVIDIAいずれも、確認した個別URL形式が将来不変であるという公式保証は未発見。
- listing/archiveのHTML構造、pagination query、DOM selectorの安定性は未検証。
- ETag、Last-Modified、conditional GET、redirect、429/5xx、bot対策等の実HTTP挙動は未検証。
- release差し替え・訂正・削除時に同URLの本文が更新されるか、新URLになるかは未検証。
- `content_hash` の正規化方式はI0-002/I0-004側contractへ従う必要がある。
- SECとIR間で数値・時刻・period表記が食い違うcaseの自動優先規則は、E0-007の照合Evidenceとlocal testを待つ。

推測で埋めず、これらはlocal adapter/fixture/quality testの未完了項目として残す。

## 9. ローカルhandoff

`E0-003` は次の順で実装可能。

1. WEB-001/004のissuer/source registryを使ってAMD/NVIDIAを固定する。
2. issuer別の決算専用listing adapterを実装する。
3. archiveを第二discovery pathとして実装する。
4. listingから個別hrefを取得し、URL・hash・retrieval provenanceを保存する。
5. `E0-002` SEC決算候補とevent identityで照合し、SEC/IR Evidenceを両方残す。
6. 重複discovery、個別取得失敗、content変更をfixture/contract test化する。

Web側のWEB-008はこのhandoffをもって `引渡し済み` とできる。ただし `E0-003` 親タスク自体はlocal実装・試験が残る。

## 10. 公式Evidence

- AMD Investor Relations — Press Releases: https://ir.amd.com/news-events/press-releases
- AMD Investor Relations — Financial Results: https://ir.amd.com/financial-information/financial-results
- AMD — Q2 2026 earnings release: https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results
- NVIDIA Investor Relations — Home: https://investor.nvidia.com/
- NVIDIA Investor Relations — Quarterly Results: https://investor.nvidia.com/financial-info/quarterly-results/default.aspx
- NVIDIA Newsroom — News Archive: https://nvidianews.nvidia.com/news
- NVIDIA — Q2 FY2027 earnings release: https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2027

Evidence class: `official data` / `official issuer disclosure`.
