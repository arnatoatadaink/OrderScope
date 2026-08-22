# Stock Monitoring Project v0.1 — Provider Research / API STUB

調査基準日: 2026-08-22

## 1. 方針
APIベンダ選定はCore仕様から分離する。
Coreは以下のProvider契約のみ知る。

- MarketDataProvider
- NewsProvider
- FilingProvider
- FundamentalProvider
- OfficialSignalProvider

料金・プランは契約時点で必ず再確認する。

## 2. v0.1候補一覧

| 用途 | 候補 | 公開価格 | v0.1位置づけ |
|---|---|---:|---|
| Market Data | Alpaca Basic | $0/月 | 初期候補 |
| Market Data | Alpaca Algo Trader Plus | $99/月 | 昇格候補 |
| News | Tiingo Power | $30/月 | 第一候補 |
| SEC Filing | SEC EDGAR | $0 | 採用 |
| Segment Fundamental | SEC EDGAR / XBRL | $0 | 採用 |
| Official X | X API | 未確定 | 契約前再調査 |
| 統合Market Data | Massive Basic | $0/月 | 比較候補 |
| 統合Market Data | Massive Starter | $29/月 | 将来候補 |
| 統合Market Data | Massive Developer | $79/月 | 将来候補 |
| 統合Market Data | Massive Advanced | $199/月 | 本格運用候補 |
| Premium News | Benzinga via Massive | $99/月/データセット | Tiingo不足時 |

## 3. Alpaca
公開情報:
- Basic: Free
- Algo Trader Plus: $99/month
- Basic equities realtime: IEXのみ
- Plus: 全米株式取引所
- Basic WebSocket: 30 symbols
- Plus WebSocket: Unlimited
- Historical: since 2016
- Basic Historical API: 200/min
- Plus Historical API: 10,000/min

v0.1調査事項:
- Tier A約25銘柄ならBasic WebSocket範囲に収まるか
- IEXのみでFFT / anomaly検出品質が十分か
- 15m / Daily銘柄をRESTで補完できるか
- 欠損率 / 遅延 / market-calendar整合性
- SIP全市場へ昇格する条件

公式参考:
https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api

## 4. Tiingo News
Power:
- $30/month
- News API利用可
- 3 months queryable news history
- 10,000 requests/hour
- 100,000 requests/day
- 40GB/month
- Internal use only

評価方法:
SEC / IRを基準側として1〜3か月比較し、以下のRecallを測定する。
- Major Contract
- Business Pivot
- CAPEX
- Financing
- M&A
- Regulation
- Earnings
- Partnership
- Major Customer

調査事項:
- Ticker tagging精度
- 記事発見遅延
- Major event取りこぼし
- 本文アクセスと保存条件
- ライセンス / Internal Use制約

公式参考:
https://www.tiingo.com/pricing
https://www.tiingo.com/products/news-api

## 5. Massive
公開Stocks価格:
- Basic: $0/month
- Starter: $29/month
- Developer: $79/month
- Advanced: $199/month

主な差:
- Basic: EOD、2年履歴、5 API calls/min、Minute Aggregates
- Starter: 15分遅延、5年履歴、Unlimited API Calls、WebSocket
- Developer: 15分遅延、10年履歴、Trades
- Advanced: Realtime、20+年履歴、Trades、Quotes、Financials & Ratios

Premium Partner Data:
- Benzinga realtime financial news / analyst ratings: $99/month per dataset

調査事項:
- Alpacaとの差
- Realtime latency
- Historical depth
- News coverage
- 統合運用による簡素化
- Alpaca + Tiingoより費用対効果が高くなる境界

公式参考:
https://massive.com/pricing?product=stocks

## 6. SEC EDGAR
v0.1で直接採用。

用途:
- Filing incremental detection
- 8-K / 10-Q / 10-K等
- Company Facts
- XBRL
- Segment Revenue
- Source accession保存

実装:
SecEdgarProvider
SecEdgarFundamentalProvider
  - CompanyFactsExtractor
  - XbrlDimensionExtractor
  - FilingFallbackExtractor

調査事項:
- Segment dimension抽出成功率
- custom taxonomy
- segment rename / merge / split
- recast / restatement
- segment revenue未開示企業

## 7. X API / Official Signal
v0.1対象:
- US President
- US Vice President
- Treasury Secretary
- Federal Reserve Chair
- White House
- U.S. Treasury
- Federal Reserve
- SEC
- 関連Federal Agency
- 上記の公式Xアカウント

現在の料金はこの文書では固定しない。
契約直前に公式Developer Platformで再確認する。

調査事項:
- Post read cost
- User/account lookup cost
- polling / streaming method
- rate limits
- edited/deleted post
- official account verification
- archive access
-利用規約

## 8. 暫定コスト方針
最小:
- SEC EDGAR: $0
- Alpaca Basic: $0
- Tiingo Power: $30/月
- X: 未確定従量/契約費

必要時:
- Alpaca Plus: +$99/月

本格統合候補:
- Massive Advanced: $199/月

## 9. Provider STUB要件
### MarketDataProvider
- historical bars
- latest bars
- market calendar
- US stocks / ETFs
- 1m / 15m / 1d
- UTC normalization

### NewsProvider
- ticker-filtered news
- published_at
- headline
- publisher
- source URL
- stable article ID
- incremental retrieval
- temporary body access

### FilingProvider
- CIK-based detection
- accession number
- form type
- filing document
- XBRL facts

### FundamentalProvider
- quarterly segment revenue
- fiscal period
- source filing
- segment identity/history

### OfficialSignalProvider
- source/account incremental retrieval
- original timestamp
- permanent source reference
- update/delete information where available
