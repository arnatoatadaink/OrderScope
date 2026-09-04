# OrderScope — Official Statement / Implementation Separation Research（WEB-017）

Status: Web research complete; local Fact type implementation pending  
Web task: `WEB-017`  
Parent task: `O0-003`  
Depends on: `WEB-015`, `WEB-016`  
Checked at: `2026-09-04T08:48Z`

## 1. 結論

`O0-003`のWeb入力として、公式情報から得られる「発言・提案」と「署名・施行・正式決定」を同一Factへ潰さず、少なくとも **statement / proposal / decision / implementation** を分離して保存できる事例を収集した。

今回の公式Evidenceから、次をv0.1のFact契約入力として固定できる。

- `STATEMENT`: actorの見解、方針、将来意向。法的・運用上の発効を意味しない。
- `PROPOSAL`: NPRM等の提案段階。comment受付や将来のfinal actionを予定していても、operative ruleとして扱わない。
- `DECISION`: 投票、署名、採択、Final Rule発行等の正式決定。決定時点と発効時点が同日とは限らない。
- `IMPLEMENTATION`: 関税・金利運用・規則等が実際に効力を持つ時点。sourceが明示したeffective date/timeを保存する。

同一政策系列には複数Factを許可し、`policy_thread_id`等の関係で束ねる。`published_at`、`decision_at`、`effective_at`、`retrieved_at`を別fieldにし、sourceが日付しか示さない場合は時刻を補完しない。

## 2. 代表事例

### 2.1 Treasury — Outbound Investment: NPRM → Final Rule → effective

TreasuryのOutbound Investment Security Programは、proposalとimplementationを最も明瞭に分離できる。

- 2024-06-21: TreasuryがNPRMをissued。proposalであり、public commentを募集し、後続のfinal implementing regulationsがeffective dateを設定すると明示した。
- 2024-07-05: NPRMがFederal Registerでpublished。
- 2024-10-28: TreasuryがFinal Ruleをissued。proposalではなくoperative regulationsを確定した正式決定。
- 2024-11-15: Final RuleがFederal Registerでpublished。
- 2025-01-02: Final Ruleがeffective。対象transactionへの義務がこの日から適用される。

したがって、2024-06-21のNPRMを`IMPLEMENTATION`として扱うことも、2024-10-28のFinal Rule発行をそのまま`effective_at`へ代入することも誤りである。

### 2.2 Federal Reserve — FOMC decision → implementation effective

Federal Reserveの2025-07-30 FOMC系列では、statementとimplementation noteが公式に分離されている。

- 2025-07-30 2:00 p.m. EDT: FOMC statementで政策スタンスを決定・公表。
- 2025-07-30: Implementation Noteが発行され、その政策スタンスを実装するためのBoard/FOMCの具体的決定を列挙。
- 2025-07-31: reserve balance rateやDeskへのdirectiveがeffective。

FOMC statementに含まれる「将来追加調整を検討する」等の文言は`STATEMENT`/forward guidanceであり、将来の政策変更Factを先取り生成してはならない。一方、投票済みtarget range決定は`DECISION`、翌日effectiveと明示された実装項目は`IMPLEMENTATION`として扱える。

### 2.3 White House — signed proclamation → tariff effective

2026-01-14の半導体Section 232 Proclamationは、署名日と関税の発効時刻を分離できる。

- 2026-01-14: PresidentがProclamationに署名。White House Fact Sheetも同日にsignedと明示。
- Proclamationは一定のCovered Productsへ25% tariffを課すことを正式決定。
- 2026-01-15 12:01 a.m. EST: 対象goodsについてtariffがeffective。
- 同Proclamation中の、交渉後により広範な半導体関税を検討する将来方針は、同日の25% tariff実装Factとは別の将来意向であり、`STATEMENT`として扱う。

同一文書内でも、署名済み措置、発効時刻、将来意向が混在する。document typeだけからFact typeを一意決定してはいけない。

### 2.4 SEC — Proposed Rule → Final Rule → effective expression

SECのInternet Investment Advisers rule pageは、同一rulemaking系列のPrior Actionsを公式に関連付けている。

- 2023-07-26: Proposed Rule issued。
- 2024-03-27: Final Rule issued。
- 2024-04-09: Final RuleがFederal Registerでpublished。
- Effective DateはSEC page上で「Federal Register publicationから90日後」と明示。

Web成果物ではsource記載のeffective expressionを保持し、絶対日付への正規化はlocal deterministic parser/testで行う。Web調査側で暗黙計算した日付をEvidence原値として保存しない。

## 3. Fact type contract案

| fact_type | 必須意味 | 典型source | 禁止する昇格 |
|---|---|---|---|
| `OFFICIAL_STATEMENT` | 見解、意向、forward guidance、将来検討 | remarks, statement, fact sheet内の意向文 | `effective_at`が無いのに施行済みと扱わない |
| `OFFICIAL_PROPOSAL` | NPRM/ANPRM等の正式提案 | proposed rule, NPRM | final/operative ruleとして扱わない |
| `OFFICIAL_DECISION` | vote、署名、adoption、Final Rule issuance等の正式決定 | proclamation, FOMC decision, final rule | decision timestampをeffective timestampへコピーしない |
| `OFFICIAL_IMPLEMENTATION` | 効力発生・運用開始 | effective clause, implementation note, operative date | sourceにeffective根拠が無い場合は生成しない |

将来必要なら`OFFICIAL_REVOCATION`/`OFFICIAL_SUSPENSION`を別Fact typeへ拡張できるが、WEB-017では未定義とする。

## 4. Timestamp contract案

| field | 規則 |
|---|---|
| `published_at` | sourceが公開日時を明示した場合だけ設定。日付のみならprecisionを保持 |
| `decision_at` | vote、署名、adoption、Final Rule issuance等の正式決定日時。source根拠がある場合のみ |
| `effective_at` | 法的・運用上の効力開始日時。明示されたeffective clause等がある場合のみ |
| `effective_expression` | `90 days after publication in the Federal Register`等、sourceが相対表現しか示さない場合の原文意味を正規化せず保持 |
| `event_at` | speech/meeting等の現実イベント日時。policy effectiveと別概念 |
| `retrieved_at` | adapter取得実時刻 |

同一値を複数fieldへ機械的コピーしない。sourceがdate-onlyなら`DATE_ONLY`等のprecisionを保持し、00:00 UTCへ補完しない。

## 5. Policy thread / relation contract案

同一政策系列を1 Factへ上書きせず、次のrelationを許可する。

- `PROPOSAL -> SUPERSEDED_BY -> DECISION`
- `DECISION -> IMPLEMENTED_BY -> IMPLEMENTATION`
- `STATEMENT -> RELATED_TO -> DECISION`
- `DECISION -> AMENDS / REVOKES / EXTENDS -> prior DECISION/IMPLEMENTATION`（将来fixture）

最低限のlocal field候補:

- `fact_id`
- `fact_type`
- `policy_thread_id`
- `actor_id`
- `source_id`
- `canonical_url`
- `published_at` + precision
- `decision_at` + precision
- `effective_at` + precision
- `effective_expression`
- `relation_type`
- `related_fact_id`
- `evidence_ref`

## 6. Fixture候補

| Fixture | Input | Expected classification | 主要assertion |
|---|---|---|---|
| `treasury_outbound_nprm` | Treasury 2024-06-21 NPRM | `OFFICIAL_PROPOSAL` | effective未設定、Final Ruleとは別Fact |
| `treasury_outbound_final` | Treasury 2024-10-28 Final Rule | `OFFICIAL_DECISION` | `decision_at=2024-10-28`相当、`effective_at=2025-01-02`は別semantic field |
| `fed_fomc_2025_07_30` | FOMC statement | `OFFICIAL_DECISION` + statement component | target decisionとfuture guidanceを区別 |
| `fed_impl_2025_07_30` | Implementation Note | `OFFICIAL_IMPLEMENTATION` | effective 2025-07-31を保持 |
| `wh_semiconductor_2026_01_14` | Section 232 Proclamation | `OFFICIAL_DECISION` + `OFFICIAL_IMPLEMENTATION` + statement component | signed 2026-01-14、tariff effective 2026-01-15 00:01 EST、future tariff intentを分離 |
| `sec_internet_adviser_rule` | SEC proposed/final rule chain | proposal + decision + effective expression | proposed/finalを別Fact、relative effective expressionを保持 |

1 source documentから複数Fact候補が生成されるfixtureを最低1件（White House Proclamation）含める。document単位分類のみで実装するとこのfixtureで失敗する設計にする。

## 7. Source-specific Evidence

| Evidence ID | Source title | Canonical URL | Checked at | Evidence class | Extracted fact | Unknowns / local verification |
|---|---|---|---|---|---|---|
| `E-WEB017-TREASURY-PROGRAM` | Program Regulations | https://home.treasury.gov/policy-issues/international/outbound-investment-program/program-regulations | `2026-09-04T08:48Z` | `official rule` | NPRM issued 2024-06-21 / FR published 2024-07-05、Final Rule issued 2024-10-28 / FR published 2024-11-15、effective 2025-01-02を同一系列で明示 | item-level exact clock timeは未確認 |
| `E-WEB017-TREASURY-NPRM` | Treasury Issues Proposed Rule to Implement Executive Order... | https://home.treasury.gov/news/press-releases/jy2421 | `2026-09-04T08:48Z` | `official rule` | NPRMはproposalでありcomment募集、後続final regulationsがeffective dateを設定すると明示 | proposal内の個別条項taxonomyはlocal extractor fixtureで限定 |
| `E-WEB017-TREASURY-FINAL` | Additional Information on Final Regulations Implementing Outbound Investment Executive Order | https://home.treasury.gov/news/press-releases/jy2690 | `2026-09-04T08:48Z` | `official rule` | Final Rule issued 2024-10-28、effective 2025-01-02 | exact issuance clock timeは未確認 |
| `E-WEB017-FED-STATEMENT` | Federal Reserve issues FOMC statement | https://www.federalreserve.gov/monetarypolicy/monetary20250730a.htm | `2026-09-04T08:48Z` | `official data` | 2025-07-30 2:00 p.m. EDT release、target-range decision、future-adjustment guidanceを同一pageで確認 | sentence-level extractionはlocal deterministic rule/fixtureで確認 |
| `E-WEB017-FED-IMPLEMENT` | Implementation Note issued July 30, 2025 | https://www.federalreserve.gov/newsevents/pressreleases/monetary20250730a1.htm | `2026-09-04T08:48Z` | `official data` | implementation decisionsは2025-07-30発行、reserve rate/Desk directiveは2025-07-31 effective | source itemのexact publication clock timeは未確認 |
| `E-WEB017-WH-SEMI` | Adjusting Imports of Semiconductors, Semiconductor Manufacturing Equipment, and Their Derivative Products into the United States | https://www.whitehouse.gov/presidential-actions/2026/01/adjusting-imports-of-semiconductors-semiconductor-manufacturing-equipment-and-their-derivative-products-into-the-united-states/ | `2026-09-04T08:48Z` | `official rule` | Proclamation dated 2026-01-14、25% tariff effective 2026-01-15 12:01 a.m. EST、将来のbroader tariff方針を含む | page-level published exact timeは未確認 |
| `E-WEB017-WH-FACTSHEET` | Fact Sheet: President Donald J. Trump Takes Action on Certain Advanced Computing Chips... | https://www.whitehouse.gov/fact-sheets/2026/01/fact-sheet-president-donald-j-trump-takes-action-on-certain-advanced-computing-chips-to-protect-americas-economic-and-national-security/ | `2026-09-04T08:48Z` | `official data` | President signed the Proclamation on 2026-01-14と確認でき、NVIDIA H200 / AMD MI325Xも例示 | Proclamation本文を法的根拠のprimaryとする |
| `E-WEB017-SEC-INTERNET` | Exemption for Certain Investment Advisers Operating Through the Internet | https://www.sec.gov/rules-regulations/2024/03/s7-13-23 | `2026-09-04T08:48Z` | `official rule` | Proposed Rule issue date、Final Rule issue date、FR publication date、effective expressionを同一rule pageで確認 | relative effective dateの絶対日付化はlocal deterministic parser/testへ渡す |

## 8. Local handoff

### `O0-003` Fact type

- document分類ではなくstatement/proposal/decision/implementationのsemantic Factを保存する。
- 1 documentから複数Factを生成できる形にする。
- `published_at` / `decision_at` / `effective_at` / `event_at`を分離する。
- relative effective expressionは原値を保持し、deterministic normalizerの入力とする。
- proposalをoperative、future intentをimplementedへ昇格させないnegative fixtureを入れる。

### `I0-005` Fact contract

- `fact_type`をversion化し、今回の4区分を初期enum候補とする。
- relationで政策系列を束ね、後続actionが来ても過去Factを上書きしない。
- source/evidence provenanceを各Factへ付与する。

### `O0-004` / WEB-018

WEB-018では、このsemantic分離を前提にAMD/NVIDIAへの直接関連とsemiconductor themeへの間接関連をEvidence付きで定義する。White House semiconductor Proclamationは、Fact SheetがNVIDIA H200 / AMD MI325Xを明示するため、direct instrument Evidence fixture候補として利用できるが、個別企業への業績影響を自動推測しない。

## 9. 未解決・local verification

- White House/Treasury/SECの多くのitemはexact publish clock timeを公開HTMLだけでは確認できない。date-only precisionを許容する。
- SECのrelative effective expressionを絶対日付へ変換するnormalizer仕様とcalendar testはlocalで決める。
- statement sentenceとoperative clauseのsentence-level抽出精度はWeb調査では実測しない。
- amendment / revocation / suspension / court stay等のFact type拡張はWEB-019 fixtureまたは後続設計で扱う。
- local `O0-003`が実装・fixture passするまでは親タスク完了扱いにしない。

## 10. WEB-017完了判定

Web完了条件である「発言・提案と署名・施行・正式決定の分離例」および「公式に得られるevent/publish/effective時刻の記録」は満たした。

したがって`WEB-017`は **引渡し済み** とする。親`O0-003`はlocal Fact type実装・fixture試験が残るため未完了である。
