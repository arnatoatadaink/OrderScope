# OrderScope — Local Corporate Intelligence 統合クリティカルパス

Status: non-normative execution plan
Date: 2026-09-05
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Extension WBS: `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Normative spec: `stock_monitoring_v0.1_spec.md`

## 1. 目的

2026-09-04に確定したLocal Corporate Intelligenceクリティカルパスへ、その後追加されたAnalyst Consensus / Cross-Market Contextの`A0`作業を統合する。

この文書は完了条件を変更しない。親WBS、拡張WBS、統合仕様の依存関係と2026-09-05時点の実装状態を重ね、次にどの作業を進めるべきかを一枚で示す。

## 2. 2026-09-04 CP確定後の追加差分

基準commit `b60f562d027fb4226baf82162ec5e21a447ca7a1` 以降、2026-09-05統合時点までの追加は4 commitsで、変更対象は次の3ファイルに限定される。

- `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md` — 新規
- `docs/ANALYST_CROSS_MARKET_PROGRESS_TRACKER_2026-09-05.md` — 新規
- `docs/stock_monitoring_v0.1_spec.md` — Analyst Consensus / Macro・Cross-Market Contextを追加

したがって、CP確定後にrepository上で新しくWBS化された作業パッケージは`A0`である。現時点で他の新規WBSパッケージは確認されない。

## 3. 統合依存グラフ

```text
I0-001
  ↓
I0-002  ← 現在の主作業
  ├─→ I0-003 ─┐
  ├─→ I0-004 ─┼─→ I0-007 正式受入
  └─→ I0-005 ─┤
        │       │
        │       └─→ I0-006 ───────┘
        │
        └─→ A0-001 設計済み / 実装受入待ち
                  ↓
               A0-002 Validation

I0-007
  ↓
S0-002
  ↓
S0-003
  ├─→ S0-004 完了済み
  ├─→ S0-005
  └─→ S0-006
        ↓
      S0-007
        ↓
   E0-001〜007
        ↓
   N1 / O0 / X0
```

`A0-001`は`I0-002`と`I0-005`のAccepted化を実装受入ゲートとする。`A0-002`は`A0-001`およびmarket/macro/consensusのas-of datasetに依存する。

## 4. クリティカルパス判定

### 4.1 Core Corporate Intelligence delivery CP

Coreの取得・Fact保存・SEC・Earnings・News/Official統合を完成させる主経路は従来どおりである。

1. `I0-002`
2. `I0-003` / `I0-004`
3. `I0-005` Accepted化
4. `I0-006`
5. `I0-007` 正式受入
6. `S0-002 → S0-003 → S0-005/S0-006 → S0-007`
7. `E0-001〜007`
8. `N1 / O0 / X0`

`A0`追加によって、この主経路を直列に延長しない。

### 4.2 v0.1 Cross-Market acceptance lane

統合仕様のDefinition of DoneにはCross-Market Rotation仮説でsupport/contradiction EvidenceとFX方向整合性を保持することが含まれる。そのため`A0-001`のschema/contract実装受入はv0.1全体のacceptance laneに含める。

`A0-001`は`I0-002/I0-005`が整った時点でCore SEC実装と並列化する。これによりA0を追加しても、SEC/Earningsの主経路を不要に停止させない。

### 4.3 A0-002の扱い

`A0-002`はCBRSを用いた具体的Validation Caseである。現行の統合仕様Definition of Doneには、CBRS 2026-09-01〜09-04のケースそのものを完了条件とする記述はない。

したがって現時点では、`A0-002`をCore実装の直列ブロッカーにはしない。ただしCross-Market ruleの実測妥当性を確認するvalidation gateとして扱い、v0.1 release acceptanceへ必須化するかはValidation結果を見て判断する。

## 5. 並列実行計画

### Lane A — 共通契約 / 主CP

- `I0-002`
- `I0-003` / `I0-004`
- `I0-005` Accepted化
- `I0-006`
- `I0-007` 正式受入

### Lane B — Local foundation

- `L0-002 → L0-003/L0-004/L0-005 → L0-006`
- `L1-001 → L1-002 → L1-004 → L1-005` fixture経路

`L1-003`は`SMOKE-007`変更窓待ちであり、他laneのブロッカーにしない。

### Lane C — Cross-Market extension

- `A0-001`: 設計完了状態を維持
- `I0-002/I0-005` Accepted後にfield/schema/fixtureへ反映
- `A0-002`: as-of dataset定義・データソース確認を先行可能。ただしHypothesis recordの最終形状はA0-001実装contractに合わせる

### Lane D — SEC / Earnings

`I0-007`受入後に開始する。

- `S0-002 → S0-003`
- `S0-005` / `S0-006`を並列化
- 完了済み`S0-004`を接続
- `S0-007`
- `E0-001〜007`

## 6. 追加タスク反映監査

| 追加内容 | 仕様反映 | WBS収載 | CP統合 | 実装/検証状態 |
|---|---|---|---|---|
| Analyst Consensus tracking | 済み (`stock_monitoring_v0.1_spec.md` §13) | A0のValidation入力として収載 | 統合済み。A0 laneとして扱う | Provider/as-of datasetは未確定 |
| Macro / Cross-Market Context | 済み (§14) | `A0-001/002` | 統合済み | A0-001設計完了、実装受入待ち |
| FX contradiction rule | 済み (§14) | `A0-001` | `I0-002/I0-005`から分岐 | 設計完了 |
| CBRS Multi-Layer Flow Validation | 仕様の一般要件とは分離 | `A0-002` | validation laneへ統合 | 未着手 |

区分結果:

- 仕様反映済み / WBS済み / CP統合済み: `A0-001`
- WBS済み / CP統合済み / 検証未着手: `A0-002`
- WBS未収載の追加パッケージ: 2026-09-04 CP基準commit以降のrepository差分では確認されない

## 7. 現在の実行優先順位

1. `I0-002`を主作業として完了させる。
2. `I0-003`と`I0-004`を並列化する。
3. `I0-005`をI0-002 provenance型へ適合させAccepted化する。
4. 同時点で`A0-001`の`fx_direction_consistency`、evidence refs、confidence ordinalをInterpretation/Hypothesis schemaへ反映する。
5. `I0-006`と`I0-007`正式受入を完了する。
6. SEC laneと並列して`A0-002`用as-of dataset定義・取得可能性を確定する。

## 8. 次回再開規則

- 主セッション: `I0-002`
- 第2並列セッション: `L0-002`
- A0側セッション: まず`A0-002` dataset/source定義まで進めてよい。schema書込みは`I0-002/I0-005` Accepted後
- `I0-005`、`I0-007`、`S0-004`は先行成果を破棄せず、依存充足後の整合・正式受入として扱う

## 9. 未確定事項

- Analyst Consensusのas-of履歴を取得できるProviderと契約条件
- A0-002で採用するAI/Semiconductor proxyの確定値
- short/borrow dataをH4検証へ含めるProvider
- A0-002をv0.1 release acceptanceの必須gateへ昇格させるか

これらは推測で補完せず、source/contractまたはValidation evidence取得後に確定する。
