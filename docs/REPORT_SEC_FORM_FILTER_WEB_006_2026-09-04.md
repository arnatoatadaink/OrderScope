# OrderScope — SEC対象Form filter調査（WEB-006）

Status: Web調査完了 / local handoff ready
Date: 2026-09-04
Web ID: `WEB-006`
Parent: `S0-004`
Depends on: `WEB-005` / `S0-001`
Checked at: `2026-09-03T16:39Z`
Evidence class: `official rule` / `official data`

## 1. 目的

`S0-004`の対象form filterを実装するため、親計画で固定された次の対象についてSEC公式情報から目的、amendment、近縁form、例外を整理する。

- `8-K`
- `10-Q`
- `10-K`
- `S-1`
- `S-3`
- `424B*`
- `DEF 14A`
- `Schedule 13D / 13G`
- `Form 4`

本書はWeb側の調査成果であり、filter実装、fixture再生、AMD/NVDA限定取得、amendment/partialの受入試験はローカル`S0-004`〜`S0-007`へ引き渡す。

## 2. 結論

### 2.1 v0.1の推奨分類

| family | v0.1 accepted EDGAR form type | amendment扱い | purpose / 注意点 |
|---|---|---|---|
| Current report | `8-K`, `8-K/A` | 同一familyの更新として保持。ただし元accessionを上書きしない | EDGARは`8-K`をCurrent reportとして表示する。`8-K/A`を別accessionとして受け入れる |
| Quarterly report | `10-Q`, `10-Q/A` | 同上 | 四半期報告。amendmentを除外すると後訂正を落とすため対象に含める |
| Annual report | `10-K`, `10-K/A` | 同上 | 年次報告。EDGARは`10-K/A`をannual report amendmentとして表示する |
| Securities registration | `S-1`, `S-1/A` | 同上 | Securities Act of 1933に基づく一般登録届出。SEC filing detailは`S-1/A`を`[Amend]`として区別する |
| Securities registration | `S-3`, `S-3/A` | 同上 | Securities Act of 1933に基づくregistration statement。`S-3ASR`等は親計画の明示対象外なのでv0.1で自動包含しない |
| Prospectus Rule 424(b) | `424B1`, `424B2`, `424B3`, `424B4`, `424B5`, `424B7`, `424B8` | `/A` wildcardではなくSEC定義のform type集合を扱う | SECの現行EDGAR XBRL Guideが`424B*`をこの7種として明示。`424B6`はこの集合にない |
| Definitive proxy | `DEF 14A` | `DEF 14A/A`を存在前提で生成しない | EDGARは`DEF 14A`をOther definitive proxy statementsとして表示。追加soliciting materialの`DEFA14A`やpreliminaryの`PRE 14A`は別formでありv0.1自動包含しない |
| Beneficial ownership | `SCHEDULE 13D`, `SCHEDULE 13D/A` | amendmentを同一familyで保持 | EDGARは5%超のbeneficial ownership acquisition報告とamendmentを区別して表示する |
| Beneficial ownership | `SCHEDULE 13G`, `SCHEDULE 13G/A` | amendmentを同一familyで保持 | EDGARはcertain investorsによる5%超beneficial ownership報告とamendmentを区別して表示する |
| Insider ownership change | `4`, `4/A` | amendmentを同一familyで保持 | Form 4はbeneficial ownershipのchangesを報告。公式Form 4 instructionsはForm 4と「any amendment」を明示する |

### 2.2 filter方針

`form`文字列を単純なprefix一致だけで通さない。

推奨は、入力のraw EDGAR form typeを保存したうえで、正規化familyを別fieldへ写像する方式である。

例:

```text
raw_form = "10-K/A"
form_family = "10-K"
is_amendment = true
```

これにより、

- amendmentを元filingへ破壊的に上書きしない
- accession単位のidempotencyを維持する
- `S-3ASR`を`S-3`と誤認しない
- `DEFA14A`を`DEF 14A`と誤認しない
- `424B*`の意味をSEC公式定義の有限集合として固定できる

という境界を保てる。

## 3. Form別の公式根拠と例外

### 3.1 8-K

**Fact**

- SEC EDGARのentity landing pageは`8-K`を`Current report`と説明する。
- 同じEDGAR form type体系では`8-K/A`がamendmentとして現れる。

**Local consequence**

- `8-K`と`8-K/A`を同一familyへ正規化し、accessionは別recordとして保存する。
- event extractionではamendmentを「同一イベント」と即断せず、content/evidence比較後にrelationshipを付ける。

### 3.2 10-Q

**Fact**

- SECはForm 10-Qの公式formを公開している。
- EDGARでは`10-Q`をquarterly reportとして扱う。

**Local consequence**

- `10-Q/A`もfilter対象に含める。
- fiscal periodやfiled_atはform名から推測せずFilingRecordのfieldから保持する。

### 3.3 10-K

**Fact**

- EDGARは`10-K`をannual reportとして扱い、`10-K/A`をannual report amendmentとして明示表示する。

**Local consequence**

- `10-K/A`を除外しない。
- amendmentを年度の最新値へ即置換せず、元accessionとの関係を後段で扱う。

### 3.4 S-1

**Fact**

- SEC filing detailは`S-1`を`General form for registration of securities under the Securities Act of 1933`と説明する。
- SEC filing detailは`S-1/A`を同formの`[Amend]`として区別する。

**Local consequence**

- `S-1`と`S-1/A`のみをこのfamilyのv0.1対象とする。
- `S-1MEF`等は親計画に含まれていないため、自動的に同一familyとしてacceptしない。

### 3.5 S-3

**Fact**

- SEC filing detailは`S-3`を`Registration statement under Securities Act of 1933`と説明する。
- SECのEDGAR validation資料では`S-3`と`S-3/A`が別submission typeとして列挙される。

**Local consequence**

- `S-3`, `S-3/A`をacceptする。
- `S-3ASR`, `S-3D`, `S-3MEF`等は文字列prefixだけで取り込まず、v0.1では対象外として明示する。

### 3.6 424B*

**Fact**

SECの2026年5月EDGAR XBRL Guideは、`424B*`を次の有限集合として明示する。

- `424B1`
- `424B2`
- `424B3`
- `424B4`
- `424B5`
- `424B7`
- `424B8`

同じ現行ガイドとEDGAR Full Text Searchのform listには`424B6`が含まれていない。

**Local consequence**

`startsWith("424B")`ではなく上記7種のallowlistを採用する。SECのform type体系が将来変更された場合はallowlist更新をreview対象にする。

### 3.7 DEF 14A

**Fact**

- SEC filing detailは`DEF 14A`を`Other definitive proxy statements`と説明する。
- EDGARには`DEFA14A`（additional definitive proxy soliciting materials）や`PRE 14A`（preliminary proxy statement）など別form typeが存在する。

**Interpretation**

親計画が明示しているのは`DEF 14A`であり、proxy関連form全般ではない。

**Local consequence**

- v0.1のstrict filterは`DEF 14A`を対象とする。
- `DEFA14A`, `PRE 14A`, merger系proxy等は自動包含せず、将来scope拡張時に別途reviewする。
- `/A`を機械生成したform typeとして仮定しない。実在form typeのみ受け入れる。

### 3.8 Schedule 13D / 13G

**Fact**

- EDGARは`SCHEDULE 13D`を5%超のclass of equity securitiesのbeneficial ownership acquisitionを報告するscheduleとして表示する。
- EDGARは`SCHEDULE 13D/A`をそのamendmentとして明示する。
- EDGARは`SCHEDULE 13G`をcertain investorsによる5%超beneficial ownership報告として表示し、`SCHEDULE 13G/A`をamendmentとして明示する。

**Local consequence**

EDGAR raw typeの表記をそのまま保存し、正規化時のみ`13D` / `13G` familyへ写像する。`13D`と`13G`を一つのgeneric ownership formへ潰さない。

### 3.9 Form 4

**Fact**

- SEC公式Form 4は`STATEMENT OF CHANGES IN BENEFICIAL OWNERSHIP OF SECURITIES`である。
- General InstructionsはForm 4と`any amendment`のfilingについて明示する。
- EDGARのform type表示は`4`を`Statement of changes in beneficial ownership of securities`とする。

**Local consequence**

`4`と`4/A`をacceptし、reporting person、issuer、transaction date等はdocument側から抽出する。issuer filingだけを前提としない。

## 4. 推奨実装contract

### 4.1 allowlist

```text
8-K
8-K/A
10-Q
10-Q/A
10-K
10-K/A
S-1
S-1/A
S-3
S-3/A
424B1
424B2
424B3
424B4
424B5
424B7
424B8
DEF 14A
SCHEDULE 13D
SCHEDULE 13D/A
SCHEDULE 13G
SCHEDULE 13G/A
4
4/A
```

### 4.2 明示的に「自動包含しない」近縁form

少なくとも次をprefix一致で誤ってacceptしない。

```text
S-3ASR
S-3D
S-3MEF
S-1MEF
DEFA14A
PRE 14A
424H
424H/A
425
3
5
```

これは「重要でない」という意味ではなく、`S0-004`の親計画で固定されたv0.1範囲外という意味である。

### 4.3 推奨field

```text
raw_form
form_family
is_amendment
accession_number
filed_at
period_end
primary_document_ref
retrieved_at
```

`is_amendment`は既知のraw form type mappingから決め、末尾`/A`だけを唯一の意味論にしない。

## 5. fixture / contract test handoff

ローカル`S0-004` / `S0-007`では最低限次をfixture化する。

1. base formをacceptする。
2. 対応するamendmentを別accessionとしてacceptする。
3. amendment再取得がidempotentである。
4. `S-3ASR`を`S-3`として誤acceptしない。
5. `DEFA14A`を`DEF 14A`として誤acceptしない。
6. `424B1/2/3/4/5/7/8`をacceptし、`424B6`を存在前提で生成しない。
7. `SCHEDULE 13D`と`SCHEDULE 13G`を別familyとして保持する。
8. `4`と`4/A`をissuer-only filingと仮定しない。
9. unknown formは破棄理由を記録でき、silent coercionしない。

実データでのAMD/NVDA限定取得、amendment検出率、partial/retryの実測は本Web成果物では未実施であり、`S0-007`の完了条件として残る。

## 6. Unknowns / scope外

- `DEF 14A`近縁の追加proxy materialsを将来どこまでFact対象に含めるかは未決定。
- `S-3ASR`等のregistration派生formを将来Corporate Intelligence対象へ広げるかは未決定。
- form amendment間のevent-level同一性はform typeだけでは決められない。content hash / evidence relationship側で扱う必要がある。
- 本調査はform type filterの意味論を確定するものであり、document parsing精度や検出成功率を実測していない。

## 7. 公式Evidence

Checked at: `2026-09-03T16:39Z`

| Source | Publisher | Evidence | Canonical URL |
|---|---|---|---|
| Form 4 | U.S. Securities and Exchange Commission | Form 4の目的、filing timing、amendmentの存在 | https://www.sec.gov/files/form4.pdf |
| Form 10-Q | U.S. Securities and Exchange Commission | 10-Q公式form | https://www.sec.gov/file/form10-qpdf |
| EDGAR XBRL Guide, May 2026 | U.S. Securities and Exchange Commission | `424B*` = `424B1/2/3/4/5/7/8`; `S-1/A`, `S-3/A`等submission type | https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2026-05-15.pdf |
| Understand Automated Conformance Rules for EDGAR Data Fields | U.S. Securities and Exchange Commission | `S-1`, `S-1/A`, `S-3`, `S-3/A`, 424B群などのsubmission type | https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/understand-automated-conformance-rules-edgar-data-fields |
| EDGAR Full Text Search | U.S. Securities and Exchange Commission | 現行form type選択肢に`424B1/2/3/4/5/7/8`が存在 | https://www.sec.gov/edgar/search/ |
| EDGAR filing detail — S-1 / S-1/A | U.S. Securities and Exchange Commission | S-1の公式descriptionとamendment表記 | https://www.sec.gov/Archives/edgar/data/1900851/000149315226023581/0001493152-26-023581-index.htm ; https://www.sec.gov/Archives/edgar/data/2127043/000119312526308260/0001193125-26-308260-index.htm |
| EDGAR filing detail — S-3 | U.S. Securities and Exchange Commission | S-3の公式description | https://www.sec.gov/Archives/edgar/data/1853070/000149315226029385/0001493152-26-029385-index.htm |
| EDGAR filing detail — DEF 14A | U.S. Securities and Exchange Commission | `DEF 14A` = Other definitive proxy statements | https://www.sec.gov/Archives/edgar/data/56679/000130817926000388/0001308179-26-000388-index.htm |
| EDGAR entity landing pages | U.S. Securities and Exchange Commission | `8-K`, `10-K/A`, `DEFA14A`, `PRE 14A`, `SCHEDULE 13D/A`, `SCHEDULE 13G/A`, `4`の実在form type / description | https://www.sec.gov/edgar/browse/?CIK=70487 ; https://www.sec.gov/edgar/browse/?CIK=1794515 |

## 8. Handoff

### S0-004

- 上記allowlistをraw EDGAR form typeに対するstrict mappingとして実装する。
- `raw_form`を失わず`form_family`と`is_amendment`を派生させる。
- prefix coercionを禁止する。

### S0-007

- base/amendment、near-miss、unknown formのfixtureを追加する。
- AMD/NVDA限定の実取得で新規、重複、amendment、partialを検証する。
- 実測前に成功率やcoverageを主張しない。

## 9. Web完了判定

`WEB-006`のWeb完了境界である「8-K、10-Q、10-K、S-1、S-3、424B*、DEF 14A、13D/G、Form 4についてamendment等を含む公式根拠が揃う」は満たした。

したがってWeb状態は`引渡し済み`とする。ただし親`S0-004`および`S0-007`はローカル実装・試験未実施のため完了扱いにしない。
