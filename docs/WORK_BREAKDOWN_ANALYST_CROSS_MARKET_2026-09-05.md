# OrderScope — Analyst Expectations / Cross-Market Context 作業分解

Status: non-normative execution backlog extension
Date: 2026-09-05
Parent: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Normative spec: `stock_monitoring_v0.1_spec.md`

## 1. 目的

既存のCorporate Intelligence作業分解に未収載だった、Analyst ConsensusとCross-Market Contextの検証作業を追加する。

この拡張では、Fact / Derived Metric / Interpretation / Predictionの分離原則を維持し、直接観測できない資金移動をFactへ昇格させない。

## 2. A0 — Analyst Expectations / Allocation Context

| ID | タスク | 完了条件 | 依存 |
|---|---|---|---|
| A0-001 | Cross-Market RotationのFX反証条件を定義 | source/destination、想定FX方向、support/contradiction evidence、`fx_direction_consistency`、confidence低下規則を仕様化し、FX単独で資金移動Factを確定しないことを固定 | `I0-005`論理schema。設計作業は先行可、実装受入は`I0-002/005`Accepted後 |
| A0-002 | CBRS 2026-09-01〜09-04 Multi-Layer Flow Validation | CBRS/NVDA/市場・AI proxy/UST/JGB/USDJPY/BTCを同一時系列で比較し、Macro / Theme / Company-specific / Short-cover / Japan→US rotation仮説をSUPPORT/PARTIAL/CONTRADICT/UNKNOWNで評価 | A0-001、利用可能なmarket/macro/consensusデータ |

## 3. A0-001 設計境界

### 入力Context

最低限:

- source market index / proxy
- destination market index / proxy
- source/destination volumeまたはflow proxy
- source/destination sovereign yield
- relevant FX pair
- policy expectation
- observation window

### Hypothesis Record

資金移動はFactではなくInterpretation/Hypothesisとして保持する。

必須候補field:

- hypothesis_type
- source_region
- destination_region
- proposed_direction
- observed_window_start
- observed_window_end
- supporting_evidence_refs
- contradicting_evidence_refs
- fx_direction_consistency
- confidence
- generated_at
- model_or_rule_version

### `fx_direction_consistency`

値:

- `SUPPORT`
- `NEUTRAL`
- `CONTRADICT`
- `UNKNOWN`

日本→米国の直接的な新規資金移動を仮定する場合、単純化した期待方向はJPY売り/USD買いであり、USD/JPY上昇がsupport候補になる。

USD/JPYが大幅低下している場合は`CONTRADICT`候補とする。ただし為替はcarry unwind、政策期待、hedging、介入警戒等でも動くため、FX単独で仮説を棄却またはFact確定してはならない。

### Confidence rule

v0.1では固定スコアをまだ定めない。まずordinal判定を採用する。

- `HIGH`: 複数独立Evidenceが方向一致し、重大なcontradictionなし
- `MEDIUM`: support優勢だがcontradictionまたは欠測あり
- `LOW`: 主要な方向整合性が崩れる、またはsupportが弱い
- `UNKNOWN`: 必須Context不足

FXが`CONTRADICT`の場合、他の独立Evidenceで強く支持されない限り`HIGH`にしない。

## 4. A0-002 Validation Case

対象期間:

- baseline: 2026-08-26〜2026-08-31
- primary: 2026-09-01〜2026-09-04

最低比較系列:

- CBRS
- NVDA
- Nasdaq CompositeまたはQQQ
- AI/Semiconductor proxy
- U.S. 10Y Treasury yield
- Japan 10Y JGB yield
- USD/JPY
- BTC

仮説:

- H1 Global Macro Relief
- H2 AI Theme Flow
- H3 CBRS-specific Repricing
- H4 Short Covering
- H5 Japan → US Capital Rotation

現在の既知反証材料として、USD/JPYが約160→155→156と推移した点をH5へ登録する。この為替方向は、単純な日本資産売却→円売り→ドル買い→米国資産購入の説明とは逆であるため、H5の初期confidenceを低く置く。

## 5. 完了の定義

### A0-001

- FXを資金移動仮説のsupport/contradiction Evidenceとして扱える
- `fx_direction_consistency`を定義
- confidenceのordinal ruleを定義
- FX単独で資金移動をFact化しない
- as-of時点のEvidence参照を保持できる

### A0-002

- 対象系列を同一時間軸で比較
- CBRS relative return / relative volumeを計算
- Consensus gapを評価
- UST/JGB/USDJPYの方向を評価
- 5仮説にSUPPORT/PARTIAL/CONTRADICT/UNKNOWNを付与
- FactとInterpretationを分離したValidation Reportを保存

## 6. 着手順

1. `A0-001` 設計仕様確定
2. `I0-002/005`とfield整合確認
3. `A0-002` データ取得・Validation
4. Validation結果を受けてconfidence ruleの数値化要否を判断

## 7. 非目標

- 為替だけから国際資金フロー総額を推定しない
- 単一ニュースから買い主体を機関投資家と断定しない
- 無料集約サイトの現在値からConsensus過去履歴を再構築しない
- v0.1で資金移動confidenceを精密確率として出力しない
