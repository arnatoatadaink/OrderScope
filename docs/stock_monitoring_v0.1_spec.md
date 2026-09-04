# Stock Monitoring Project v0.1 — 統合仕様書

## 1. 目的
米国市場を対象として、価格・市場Proxy・セクター・テーマ・企業ニュース・SEC開示・政府高官発言・四半期業績・企業Regime・FFT・相関構造・アナリスト期待形成を継続監視し、「何が変化したか」をFactとして記録する。

本システムは価格予測を主目的としない。

## 2. 対象
- 米国上場株式
- 米国上場ETF
- Country Proxyは米国上場ETFのみ
- 初期Universeは約100 instrumentsで固定
- 価格取得頻度は 1m / 15m / 1d に分離
- News / SEC / Official Signal / Analyst Consensusはevent-drivenまたは定期snapshot

## 3. Universe
Universeは市場・国・セクター・テーマ・企業特性・個別企業の階層で構成する。
InstrumentとClassificationはmany-to-manyとし、企業は複数Theme / Regimeへ同時所属できる。

詳細は `stock_monitoring_v0.1_universe_spec.md` を参照。

## 4. Market Data
v0.1の第一候補はAlpaca。
CoreはProvider固有Schemaを知らず、MarketDataProvider経由でOHLCV・Market Calendarを取得する。

内部時刻はUTC、市場判定はAmerica/New_York、表示はAsia/Tokyo。

## 5. Market Analysis
主なWindow:
- 1 trading day
- 7 trading days
- 20 trading days
- 60 trading days

FFT主入力:
- log return

補助:
- close
- volatility
- volume

FFT前処理:
missing check → interval validation → log return → mean removal → optional detrend → Hann window → FFT → power spectrum

Frequency Low/Mid/Highは価格変化率ではなく周期で定義する。
3% / 5%等はAmplitude側の特徴量とする。

## 6. Session / Calendar
- Regular / Premarket / After-hoursを分離
- 休日をIntraday時系列へ人工補間しない
- Weekend / Holiday GapはDaily以上では情報として保持
- 短縮日は実取引時間のみ保存し、通常日baselineと分離

## 7. Corporate Intelligence
入力:
- News
- SEC Filing
- Official Signal
- Earnings
- Segment Revenue
- Major Contract
- CAPEX / Financing / Partnership / M&A
- Analyst Consensus / Rating / Price Target Revision

処理:
External Information → Event Extraction → Corporate Fact → Regime Engine → Classification

## 8. Source Tier
Tier 0:
- US President
- US Vice President
- US Treasury Secretary
- Federal Reserve Chair
- White House
- U.S. Treasury
- Federal Reserve
- SEC
- 関連Federal Agency
- 上記の公式Xアカウントが存在する場合は監視対象

Tier 1:
- SEC
- 企業IR
- 公式開示

Tier 2:
- Reuters等の主要報道

Tier 3:
- 業界専門媒体

Tier 4:
- 一般ニュース

Tier 5:
- 一般SNS / Reddit / X

発言と政策実施は別Factとして管理する。

## 9. SEC / Fundamental
SEC EDGARを直接監視。
主対象:
- 8-K
- 10-Q
- 10-K
- S-1
- S-3
- 424B*
- DEF 14A
- 13D
- 13G
- Form 4

四半期セグメント売上はSecEdgarFundamentalProviderで直接抽出する。
Company Facts → XBRL Dimension → Filing Fallbackの順に取得する。

## 10. Regime
企業は複数Regimeを同時に保持可能。

Provisional Strength:
- 0.25: MVP / pilot / research / feasibility / 初期評価
- 0.50: 部門立上げ / 資金調達 / CAPEX / 設備転用 / 商用準備
- 0.75: 商用契約 / 大口受注 / 顧客契約 / 売上発生

売上が個別取得できる場合はRevenue-basedへ移行。

Revenue Strength:
`MA4(segment revenue) / MAX(MA4(all segments))`

Revenue Share:
`MA4(segment revenue) / SUM(MA4(all segments))`

Revenue StrengthとRevenue Shareは別指標。

## 11. Regime Decay
- Provisionalのみ時間減衰
- Supporting Evidenceが1年間ない場合 `strength × 0.5`
- Revenue-basedは時間減衰なし
- 明確な反証・中止・撤退はinactive
- 追い風Evidenceはreactivating
- 売上回復は決算確認後にRevenue Strengthへ反映
- 契約期間不明の場合、単なるニュース欠如ではなく決算・SEC上の売上/履行状況を基準にする

将来はproposal / research / preparation / invention / contract / construction / production / sales / revenue間のExpected Realization Timeを推定し、分野別Decayへ拡張する。

`strategic_strength` は概念のみ保持し、v0.1では定量化しない。

詳細は `stock_monitoring_v0.1_regime_spec.md` を参照。

## 12. News Retention
正常にFact抽出できたRaw本文は原則即時削除。

永続保存:
- headline
- publisher
- URL
- published_at
- retrieved_at
- ticker
- event_type
- extracted facts
- source hash

例外:
- 抽出失敗
- 曖昧
- 情報矛盾
- 後続確認待ち
- 重要Regime Evidence

例外本文は最大30日保持。

## 13. Analyst Consensus Tracking
企業自身のGuidanceと、市場側の評価であるAnalyst Consensusを分離して保存する。

Consensus Snapshot:
- ticker
- observed_at
- analyst_count
- rating_counts: buy / hold / sell
- consensus_rating
- target_low
- target_median
- target_average
- target_high
- source
- source_timestamp

Revision Event:
- analyst / firm
- action: initiate / maintain / upgrade / downgrade / target_raise / target_cut
- rating_before / rating_after
- target_before / target_after
- published_at

Derived Metric:
- median_target_change
- average_target_change
- revision_breadth = upward_revisions - downward_revisions
- target_dispersion = target_high - target_low
- price_to_median_target = current_price / target_median
- price_to_low_target = current_price / target_low
- price_to_high_target = current_price / target_high

InterpretationはFactと分離する。代表的な検出条件:
- `current_price < target_low && revision_breadth >= 0`: consensus下限より市場価格のみが下方乖離
- `current_price > target_high`: 既存consensus rangeを上方突破し価格発見フェーズ候補
- `target_median`の大幅変化と高出来高・方向性の一致: expectation repricing候補

Consensusは後から過去値が上書きされる集約サイトがあるため、取得時点のsnapshotを時系列保存する。単一Providerの現在値だけから過去の中央値変化を再構築しない。

## 14. Macro / Cross-Market Context
個別株の大口フロー解釈で、金利・債券・為替・地域間資金移動は独立したMarket/Policy Factとして保持し、個別株Factへ直接原因として書き込まない。

最低限保持するContext:
- US Treasury yield / Fed policy expectation
- JGB yield / BOJ policy expectation
- USD/JPY
- major equity index / AI-semiconductor proxy
- month-end / quarter-end calendar flag

Derived Interpretation例:
- RATE_HEADWIND_EASING
- GLOBAL_BOND_RISK_OFF
- AI_RISK_APPETITE_RECOVERY
- CROSS_MARKET_CAPITAL_ROTATION_CANDIDATE

`CROSS_MARKET_CAPITAL_ROTATION_CANDIDATE` は直接観測された資金移動ではなく、複数市場の価格・出来高・為替・金利の同時変化から生成するInterpretation/Hypothesisとし、Factへ昇格させない。

Cross-Market Rotation Hypothesisでは少なくとも以下を保持する:
- source_region
- destination_region
- proposed_direction
- observed_window_start / observed_window_end
- supporting_evidence_refs
- contradicting_evidence_refs
- fx_direction_consistency
- confidence
- generated_at
- rule/model version

`fx_direction_consistency` は以下のordinal値を取る:
- SUPPORT
- NEUTRAL
- CONTRADICT
- UNKNOWN

例えばJapan → US direct rotationを仮定する場合、単純化したJPY売り/USD買い経路に対してUSD/JPY上昇はsupport候補、USD/JPYの大幅低下はcontradiction候補となる。ただしFXはcarry unwind、政策期待、hedging、介入警戒等でも動くため、FX単独で資金移動仮説をFact確定または完全棄却しない。

v0.1のconfidenceは精密確率ではなく以下のordinalとする:
- HIGH
- MEDIUM
- LOW
- UNKNOWN

重大なFX contradictionがある場合、他の独立したsupport evidenceが十分でない限りHIGHを付与しない。

詳細作業は `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md` を参照。

## 15. Provider Boundary
Coreはベンダ固有APIを知らない。

Provider:
- MarketDataProvider
- NewsProvider
- FilingProvider
- OfficialSignalProvider
- FundamentalProvider
- AnalystConsensusProvider

詳細は `stock_monitoring_v0.1_provider_research.md` を参照。

## 16. Fact Model
Fact / Derived Metric / Interpretation / Predictionを分離する。

主Event:
- MAJOR_CONTRACT
- BUSINESS_PIVOT
- NEW_SEGMENT
- CAPEX_SHIFT
- PARTNERSHIP
- M_AND_A
- GUIDANCE_CHANGE
- ANALYST_RATING_CHANGE
- ANALYST_PRICE_TARGET_CHANGE
- ANALYST_CONSENSUS_SNAPSHOT
- EARNINGS
- FINANCING
- REGULATION
- MANAGEMENT_CHANGE
- PRODUCT
- REVENUE_MIX_CHANGE
- ASSET_EXPOSURE_CHANGE
- CONTRACT_AWAITING_REVENUE
- COMPANY_REGIME_CHANGE
- CORRELATION_REGIME_CHANGE
- REACTIVATION_SIGNAL

## 17. v0.1 Definition of Done
- 約100 instrumentsを設定からロード
- 銘柄ごとのcadenceでMarket Data取得
- Provider差替え可能
- SEC新規Filing検出
- Segment Revenue抽出
- MA4 Revenue Strength計算
- Provisional Regime作成
- 1年無Evidenceで×0.5
- Negative Evidenceでinactive
- Reactivation Signal生成
- News本文をFact化後削除
- Analyst Consensus snapshotを時系列保存
- Rating / Price Target RevisionをFact化
- current priceとconsensus low/median/highの乖離をDerived Metric化
- Cross-Market Rotation仮説でsupport/contradiction EvidenceとFX方向整合性を保持
- 1D/7D/20D/60D FFT
- Market/Corporate/Policy Factを共通Storeへ保存
- Regime Historyを時系列再現
