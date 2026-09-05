# OrderScope — Analyst / Cross-Market 進捗トラッカー

Status: active operational tracker (non-normative)
Date: 2026-09-05
Scope: `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Parent: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`

## 1. 目的

Analyst Consensus / Cross-Market Context拡張の進捗を、会話履歴ではなくrepository上で再開可能にする。

## 2. 状態定義

| 状態 | 意味 |
|---|---|
| 未着手 | 依存条件未充足または作業開始前 |
| 設計完了 | schema/contract/判定境界が文書化済み。実装・受入は残る |
| 進行中 | 実装、データ収集、検証のいずれかを実施中 |
| 検証完了 | Acceptance CriteriaをEvidence付きで満たした |
| 保留（依存） | 先行contract/provider/data待ち |

## 3. 現在地

2026-09-05時点で、Analyst Consensus / Cross-Market Context拡張用に新規パッケージ`A0`を追加し、既存Local Corporate Intelligenceクリティカルパスへの統合も完了した。

- `A0-001`: Cross-Market RotationのFX反証条件は設計完了。
- `A0-001`: v0.1全体のCross-Market acceptance laneとしてCPへ統合済み。実装受入は`I0-002/005`のAccepted化後に行う。
- `A0-002`: CBRS 2026-09-01〜09-04 Multi-Layer Flow Validationは未着手。
- `A0-002`: Core SEC/Earnings実装の直列ブロッカーにはせず、validation laneとして並列管理する。
- `A0-002`の実測検証にはmarket/macro/consensusのas-ofデータが必要。

## 4. タスク台帳

| ID | 状態 | 成果物 | 依存・blocker | 次の操作 | 最終更新 |
|---|---|---|---|---|---|
| A0-001 | 設計完了 / CP統合済み | `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`; `stock_monitoring_v0.1_spec.md` §14; `WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md` | 実装受入はI0-002/005 Accepted待ち | provenance/Fact schemaとfield整合確認後、`fx_direction_consistency`・hypothesis evidence refs・confidence ordinalをInterpretation/Hypothesis型/schemaへ実装 | 2026-09-05 |
| A0-002 | 未着手 / CP validation lane統合済み | 予定: `REPORT_CBRS_MULTI_LAYER_FLOW_VALIDATION_2026-09-05.md`; CP定義は`WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md` | A0-001、CBRS/NVDA/QQQ or Nasdaq/AI proxy/UST10Y/JGB10Y/USDJPY/BTC、Consensus as-of data | schema確定前でもdataset/source定義は先行し、A0-001実装contract確定後に2026-08-26〜09-04の時系列データを収集して5仮説を評価 | 2026-09-05 |

## 5. A0-001 設計決定

### Factとの分離

`CROSS_MARKET_CAPITAL_ROTATION_CANDIDATE`はFactではなくInterpretation/Hypothesisとする。

### FX整合性

`fx_direction_consistency`:

- SUPPORT
- NEUTRAL
- CONTRADICT
- UNKNOWN

Japan → US direct rotationを仮定しながらUSD/JPYが大幅低下する場合、単純な円売り・ドル買い経路とは逆なので`CONTRADICT`候補とする。

ただし、carry unwind、金利差期待、hedging、介入警戒等でFXは独立して動き得るため、FX単独ではHypothesisをFactへ昇格も完全棄却もしない。

### Confidence

v0.1は精密確率を採用せず、以下のordinalのみとする。

- HIGH
- MEDIUM
- LOW
- UNKNOWN

重大なFX contradictionがある場合、他の独立support evidenceが十分でない限りHIGHを禁止する。

## 6. A0-002 初期仮説

- H1 Global Macro Relief
- H2 AI Theme Flow
- H3 CBRS-specific Repricing
- H4 Short Covering
- H5 Japan → US Capital Rotation

既知Evidence:

- H5 contradiction candidate: USD/JPY 約160 → 155 → 156
- H3 support candidate: CBRS positive corporate news + consensus gap
- H1/H2: 同期間のmarket/theme proxyとの比較が未実施
- H4: short/borrow data未取得

## 7. CP統合判断

`A0-001`は統合仕様のDefinition of Doneに含まれるCross-Market RotationのEvidence/FX整合性保持を実現するため、v0.1 acceptance laneに含める。

一方、`A0-002`のCBRSケース自体は現行Definition of Doneに固有ケースとして記載されていない。このためCore実装の直列ブロッカーにはせず、実測validation laneとして扱う。Validation結果を受けてrelease acceptance必須gateへ昇格するかを判断する。

## 8. 次回再開地点

主CPは`I0-002`を継続する。

A0側で独立して進められる最短作業は`A0-002`のデータソース確認とas-of dataset定義である。schemaへの実装は`I0-002/005` Accepted化後にA0-001 fieldをFact Store/Interpretation schemaへ反映する。
