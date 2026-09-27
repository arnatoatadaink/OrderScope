# OrderScope — WEB-018 Official instrument/theme 関連付け Evidence

Status: Web research complete; local implementation/test pending
Date: 2026-09-04
Web ID: `WEB-018`
Parent: `O0-004`
Checked at: `2026-09-04T09:09:35Z`

## 1. 目的と完了境界

`O0-004`のローカル実装へ渡すため、公式sourceから得たFactをCorporate CanaryであるAMD/NVIDIAへ直接関連付ける場合と、`semiconductor` themeへ間接関連付ける場合のEvidence閾値を定義する。

本書が完了させるのはWeb側の判定規則・Canary事例・negative fixture候補までである。Relationship schema、extractor、保存、実測precision/recallはローカル実装・試験が必要であり、本書だけでは`O0-004`を完了扱いにしない。

## 2. 前提

- `WEB-001`のCorporate Canary identityを使用し、AMD/NVIDIAのcompany/instrument/product identityを本文文字列だけから新規推測しない。
- `WEB-015`のofficial source / actor分離を維持する。特にSEC EDGARにあるissuer filingは、SECがrepository/discovery sourceであってもdocument actorはissuerであり、SEC自身の政策声明として扱わない。
- `WEB-017`の`OFFICIAL_STATEMENT` / `OFFICIAL_PROPOSAL` / `OFFICIAL_DECISION` / `OFFICIAL_IMPLEMENTATION`およびpolicy relationと、本書のinstrument/theme Relationshipは別軸とする。
- 一般検索結果、第三者記事、株価反応、モデル推測をRelationship Evidenceへ昇格させない。

## 3. Relationship class

| class | target | Web判定 | 自動関連付け |
|---|---|---|---|
| `DIRECT_INSTRUMENT` | AMDまたはNVDA instrument | 公式Evidenceがissuer/company、既知subsidiary、またはregistryでissuerへ一意に解決できるproductを明示し、その対象に対する規制、許認可、契約、助成、執行、正式な企業行為、または測定可能な影響を記述 | 可。Evidence ref必須 |
| `THEME_EXPOSURE` | `semiconductor` theme | 公式Evidenceの法的scope、program scope、title/bodyがsemiconductor/chip/semiconductor manufacturing/advanced-computing IC等を明示するが、AMD/NVIDIA個別への適用を確定するEvidenceがない | themeだけ可。AMD/NVDAへ自動展開しない |
| `MENTION_ONLY` | entity/person mention | company、CEO、製品名等が出るが、出席、引用、写真caption、例示、industry comment等に留まり、当該entityへのaction/effectを確定できない | 不可 |
| `UNRESOLVED` | 未確定候補 | entity/product/theme語はあるがidentityまたはaction scopeが一意に解決できない | 不可。review queue候補 |
| `NO_LINK` | なし | broad macro/AI/national-security等の一般論のみで、semiconductor scopeまたはCanary entityへのEvidence anchorがない | 不可 |

## 4. Evidence閾値

### 4.1 `DIRECT_INSTRUMENT`

次の全条件を満たす。

1. **identity anchor**: 公式documentが`Advanced Micro Devices, Inc.` / `AMD`、`NVIDIA Corporation` / `NVIDIA`、またはregistryで当該issuerへ一意に解決できるproduct/subsidiaryを明示する。
2. **action/effect anchor**: 同じEvidence内で、そのentity/productに対する規制、license、grant、order、contract、enforcement、formal commitment、または具体的な影響を明示する。
3. **source/actor provenance**: canonical URL、publisher/source、document actor、published/filed/accepted等の利用可能な時刻を保持する。
4. **no inference bridge**: 「半導体企業だから影響する」「同業だから影響する」だけでinstrument linkを作らない。

product名からissuerへ結ぶ場合は、product→issuer対応が既存registryまたは同一official Evidenceで一意であることを要求する。

### 4.2 `THEME_EXPOSURE`

次の全条件を満たす。

1. 公式documentの規則・program・action scopeが`semiconductor`、`chip`、`semiconductor manufacturing equipment`、`advanced computing integrated circuits`等を明示する。
2. documentの主対象または適用対象が当該themeであり、単なる比喩・周辺言及ではない。
3. AMD/NVIDIA個別へのaction/effectが明示されない場合、instrumentへfan-outしない。

### 4.3 自動関連付け禁止条件

以下はcompany名が存在しても`DIRECT_INSTRUMENT`へ昇格させない。

- event attendee / fireside-chat participant / photo caption
- CEOやindustry participantのquoteだけ
- third-party media quoteをWhite House等が転載した箇所
- broad AI policyで、semiconductor scopeが明示されないもの
- 「supplier/customer/competitorであるはず」等のbusiness inference
- market price reaction、analyst interpretation、検索snippet
- product名が複数issuerへ曖昧に解決される場合

## 5. Canary Evidence set

### Case A — AMD: export-license requirement

**Expected:** `DIRECT_INSTRUMENT(AMD)` + `THEME_EXPOSURE(semiconductor)`

- Source: SEC EDGAR — AMD Form 8-K, filed 2025-04-15
- Canonical URL: https://www.sec.gov/Archives/edgar/data/2488/000000248825000039/amd-20250415.htm
- Official fact: AMD states that the U.S. government implemented a new export-license requirement applying to AMD's `MI308` products and quantified a potential inventory/purchase-commitment impact.
- Actor note: issuer-authored filing hosted by SEC; do not relabel as an SEC policy statement.
- Why direct: issuer identity、product identity、government action、issuer-specific effectが同一formal filing内で揃う。

### Case B — NVIDIA: H20 export-license requirement

**Expected:** `DIRECT_INSTRUMENT(NVDA)` + `THEME_EXPOSURE(semiconductor)`

- Source: SEC EDGAR — NVIDIA Form 8-K, filed 2025-04-09
- Canonical URL: https://www.sec.gov/Archives/edgar/data/1045810/000104581025000082/nvda-20250409.htm
- Official fact: NVIDIA states that the U.S. government informed it that a license is required for exports of its `H20` integrated circuits to specified destinations/entities.
- Actor note: issuer-authored filing hosted by SEC; the government action is reported by NVIDIA in a formal filing.
- Why direct: NVIDIAとH20が明示され、license actionがそのproductに直接適用される。

### Case C — White House semiconductor Section 232 proclamation

**Expected:** `THEME_EXPOSURE(semiconductor)` only

- Source: The White House — “Adjusting Imports of Semiconductors, Semiconductor Manufacturing Equipment, and Their Derivative Products into the United States”
- Published: 2026-01-14
- Canonical URL: https://www.whitehouse.gov/presidential-actions/2026/01/adjusting-imports-of-semiconductors-semiconductor-manufacturing-equipment-and-their-derivative-products-into-the-united-states/
- Official fact: proclamation explicitly covers semiconductors, semiconductor manufacturing equipment, derivative products and certain advanced-computing chips, including an immediate tariff action and broader semiconductor policy.
- Why theme-only: sector/product-class scopeは明確だが、本文からAMD/NVIDIA個別適用を自動確定してはいけない。HTS/product coverageと各issuer shipmentの対応は別Evidenceが必要。

### Case D — Treasury/IRS CHIPS investment-credit final rules

**Expected:** `THEME_EXPOSURE(semiconductor)` only

- Source: U.S. Department of the Treasury — “U.S. Department of the Treasury Releases Final Rules to Strengthen U.S. Semiconductor Industry”
- Published: 2024-10-22
- Canonical URL: https://home.treasury.gov/news/press-releases/jy2664
- Supporting official rule summary: https://www.irs.gov/irb/2024-51_IRB
- Official fact: Treasury/IRS final rules implement the Advanced Manufacturing Investment Credit to incentivize U.S. semiconductor and semiconductor-manufacturing-equipment production.
- Why theme-only: semiconductor manufacturing policyへのrelationは強いが、AMD/NVIDIAがそのcreditのrecipient/claimantであることはこのEvidenceだけでは確定しない。

### Case E — White House G20 event with Jensen Huang

**Expected:** `MENTION_ONLY(NVDA)`; semiconductor instrument linkなし

- Source: The White House — “G20 Innovation Ministerial Concludes with Consensus Statement”
- Published: 2026-09-02
- Canonical URL: https://www.whitehouse.gov/releases/2026/09/g20-innovation-ministerial-concludes-with-consensus-statement/
- Official fact: the release states that Secretary Lutnick hosted a fireside chat with Jensen Huang, founder and CEO of NVIDIA, among other technology leaders.
- Why not direct: participation/identity mentionであり、NVIDIAへのgrant、restriction、contract、order、formal commitment等を確定しない。

### Case F — White House AI Action Plan acclaim quoting NVIDIA CEO

**Expected:** `MENTION_ONLY(NVDA)` for instrument linkage. `semiconductor` themeは本文scopeを別に満たさない限り自動付与しない。

- Source: The White House — “Wide Acclaim for President Trump’s Visionary AI Action Plan”
- Published: 2025-07-24
- Canonical URL: https://www.whitehouse.gov/releases/2025/07/wide-acclaim-for-president-trumps-visionary-ai-action-plan/
- Official fact: release quotes NVIDIA CEO Jensen Huang while presenting industry reactions to the AI Action Plan.
- Why not direct: quoteの掲載はNVIDIAをpolicy actionの対象にするEvidenceではない。

## 6. Corroborating official source

BIS公開資料には、BISがAMDとNVIDIAへ`is informed` lettersを送付し、中国向け特定integrated circuitsへlicense requirementsを課した旨を説明する資料がある。

- Source: Bureau of Industry and Security — “Written Presentation”
- Canonical URL: https://www.bis.gov/media/1383
- Use: AMD/NVIDIAのexport-control direct relationを補強するofficial agency Evidence候補。
- Unknown: Web確認時点で当該ページからpresentation event/dateの完全な文脈を本書では確定していないため、Canaryのprimary Evidenceはstable accessionを持つSEC filingsとする。

## 7. Local contract handoff案

Relationship recordは少なくとも次を分離して保持する。

| field | rule |
|---|---|
| `relationship_type` | `DIRECT_INSTRUMENT` / `THEME_EXPOSURE` / `MENTION_ONLY` / `UNRESOLVED` / `NO_LINK` |
| `subject_fact_id` | WEB-017/I0-005で確定するsemantic Fact ID |
| `target_type` | `instrument` / `theme` / `entity_mention` |
| `target_id` | registry instrument IDまたはversioned theme ID。文字列tickerを恒久IDにしない |
| `evidence_ref` | canonical source/document ref。必須 |
| `identity_basis` | registry / same-document explicit identity / unresolved |
| `action_basis` | license / regulation / grant / contract / enforcement / formal commitment / theme scope / mention only 等 |
| `link_confidence` | 実測確率ではなくdeterministic rule結果として扱う。v0.1では数値confidenceを捏造しない |
| `review_reason` | `UNRESOLVED`時の不足Evidenceを記録 |
| `rule_version` | linkage rule変更時に再評価可能にする |

### 推奨判定順

1. source/document actorを解決する。
2. semantic FactをWEB-017規則で確定する。
3. Canary company/product identity anchorを探す。
4. action/effect anchorが同一Evidenceにあれば`DIRECT_INSTRUMENT`。
5. direct条件を満たさず、official scopeがsemiconductorを明示すれば`THEME_EXPOSURE`。
6. entity/person名だけなら`MENTION_ONLY`。
7. identity/scopeが曖昧なら`UNRESOLVED`。推測で補完しない。

## 8. Fixture expectations

| fixture | expected |
|---|---|
| AMD 2025-04-15 8-K / MI308 export control | AMD direct = true; semiconductor theme = true |
| NVIDIA 2025-04-09 8-K / H20 export control | NVDA direct = true; semiconductor theme = true |
| White House 2026-01-14 semiconductor proclamation | AMD direct = false; NVDA direct = false; semiconductor theme = true |
| Treasury 2024-10-22 CHIPS ITC final rules | AMD direct = false; NVDA direct = false; semiconductor theme = true |
| White House 2026-09-02 G20 fireside chat / Jensen Huang | NVDA direct = false; mention_only = true |
| White House 2025-07-24 AI Action Plan acclaim / Jensen quote | NVDA direct = false; mention_only = true |

## 9. Unknowns / local verification required

- Section 232/HTS coverageからAMD/NVIDIA各productへの実際の適用を確定するには、product classification/import facts等の追加Evidenceが必要であり、本書では推測しない。
- issuer filingが報告するgovernment communicationと、政府側original order/letterの全文が常に公開されるとは限らない。両sourceが得られる場合も別Evidenceとして保持する。
- `semiconductor` themeの下位taxonomy（advanced computing IC、manufacturing equipment、polysilicon等）はN1 taxonomy/I0-005との整合後にversion化する。
- Relationship precision/recall、false-positive rate等はfixture/local Canary実測前には数値を提示しない。

## 10. Handoff

- `O0-004`: 上記Relationship class、判定順、negative rulesを実装する。
- `I0-005`: FactとRelationshipを別recordとして保存し、source/actor provenanceを維持する。
- `I0-007`: direct/theme/mention/unresolved fixtureを共通contract testへ追加する。
- `O0-005` / `WEB-019`: WEB-016のupdate/delete/time fixture、WEB-017のsemantic Fact fixture、本書のlinkage fixtureを統合してOfficial Signal品質setを作る。

Web側`WEB-018`の完了境界（根拠のない関連付けを除外できるEvidence閾値とCanary事例）は満たす。親`O0-004`はlocal implementation/test待ちである。
