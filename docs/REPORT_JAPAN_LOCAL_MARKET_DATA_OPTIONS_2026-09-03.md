# OrderScope — 日本株ローカル市場データ取得候補調査

Status: non-normative research report
Date: 2026-09-03
Scope: 個人によるローカル利用、情報取得のみ

## 1. 結論

日本株のローカル取得経路は、目的ごとに次のように分ける。

| 目的 | 第一候補 | 理由 |
|---|---|---|
| 場中のリアルタイム監視 | kabuステーション API | Excel不要で、公式REST APIとWebSocket PUSHを利用できる。 |
| 日足・財務・信用・空売り等の分析 | J-Quants API | JPX系の整形済みデータをWSLから直接HTTPSで取得できる。 |
| 過去2年の株式分足・Tickによる検証 | J-Quants Light以上＋分足/Tickアドオン | 履歴取得用として有効。ただし日次配信でありリアルタイムではない。 |
| 既存の対応Excelライセンスを活用する場合 | MARKET SPEED II RSS | リアルタイム情報を取得できるが、Windows版Microsoft Excelとデスクトッププロセスに依存する。 |

Excel費用を新たに負担して楽天RSSを採用するより、リアルタイム取得はkabuステーション API、履歴・分析データは必要に応じてJ-Quantsとする構成がOrderScopeには適する。最終採用は口座・利用プラン条件、対象銘柄数、必要な履歴、月額上限を確認して別途決定する。

## 2. MARKET SPEED II RSSとExcel

### 2.1 公式対応環境

2026-09-03確認時点の公式必要・推奨環境は次のとおりである。

- OS: Windows 11
- Office 2021 Excel
- Office 2024 Excel
- Microsoft 365 Excel

MARKET SPEED II RSSは、Windows版MARKET SPEED IIにログインし、Microsoft ExcelへRSSアドインを登録して、`RssMarket`、`RssChart`等のワークシート関数から情報を取得する方式である。

Microsoft 365の場合も、Windowsデスクトップ版Excelを使用する。ブラウザ版Excel、LibreOffice、Google Sheets、Mac版Excelは公式経路にならない。

公式資料:

- [MARKET SPEED II RSS 推奨環境](https://marketspeed.jp/ms2_rss/system_requirements/)
- [MARKET SPEED II RSSとは](https://marketspeed.jp/ms2_rss/onlinehelp/ohm_001/ohm_001_01.html)
- [起動・終了](https://marketspeed.jp/ms2_rss/onlinehelp/ohm_001/ohm_001_08.html)
- [投資情報関数](https://marketspeed.jp/ms2_rss/onlinehelp/ohm_002/ohm_002_03.html)

### 2.2 古いExcelと無料Web版

2011年前後のライセンスとして想定される製品は、Windows版Office/Excel 2010またはMac版Excel 2011である。いずれも現在の公式対応範囲外である。

- Mac版Excel 2011は、MARKET SPEED II自体がWindows専用であるため利用できない。
- Windows版Excel 2010は現在の必要環境に含まれず、アドインを登録できたとしても運用上の動作保証はない。
- 無料のExcel for the webは一般的なセル編集、数式、表、グラフ、OneDrive保存、共同編集には利用できる。
- Excel for the webではVBAマクロを作成・実行・編集できず、WindowsのCOM/VBA/DLL/XLLアドインやローカルExcel自動操作を楽天RSSの代替として利用できない。
- `.xlsm`をブラウザで開くことはできるが、マクロは実行されない。RTD/COM由来の新しいリアルタイム値もブラウザ側では取得できない。

公式資料:

- [ブラウザとデスクトップExcelの差](https://support.microsoft.com/en-US/Excel/differences-between-using-a-workbook-in-the-browser-and-in-excel)
- [Excel for the webのVBA制限](https://support.microsoft.com/en-gb/office/work-with-vba-macros-in-excel-for-the-web-98784ad0-898c-43aa-a1da-4f0fb5014343)
- [Excelアドインの種類](https://support.microsoft.com/en-us/office/add-or-remove-add-ins-in-excel-0af570c4-5cf3-4fa9-9b88-403625a0b460)

### 2.3 Python連携とアドイン解析

公式に近い実装経路は、Windows上のExcelを`pywin32`または`xlwings`から自動操作し、RSS関数の計算済みセル値を読み出す方式である。PythonプロセスもExcel/COMと同じWindows側で動かし、取得結果だけをimmutableなNDJSON/CSVとmanifestへ出力する。

```text
MARKET SPEED II
    -> Excel + RSS add-in
    -> Windows Python/VBA collector
    -> temporary file + manifest + SHA-256
    -> publish by atomic rename
    -> WSL importer
    -> SQLite / DuckDB / Parquet
```

アドインのファイル形式、署名、PE情報、依存DLL、公開関数等の静的確認は技術的に可能である。一方、Excelを除外するために非公開IPC、認証、セッション、購読、更新通知等を再実装する方法は、公式契約ではなく、仕様変更に弱く、利用条件の個別確認も必要になる。初期MVPでは採用しない。

参考実装:

- [xlwings/xlwings](https://github.com/xlwings/xlwings): PythonからExcelを操作する汎用ライブラリ。楽天専用ではない。
- [maakunh/N225OP](https://github.com/maakunh/N225OP): MARKET SPEED II RSS、Excel、VBAで取得した値を外部ファイルへ出力するMITライセンスの実例。Python実装ではないが、handoff構成の参考になる。
- [tsubokazu/rakuten-ms2rss-collector](https://github.com/tsubokazu/rakuten-ms2rss-collector): リポジトリ説明はRSS/VBA収集だが、2026-09-03確認時のmainブランチは説明されたVBA本体を直接再利用できる状態ではないため、採用根拠にはしない。

成熟して継続保守されている、Excelを不要にして楽天RSSの内部通信をPythonだけで再実装した公開リポジトリは、今回の調査では確認できなかった。

## 3. kabuステーション API

### 3.1 特徴

kabuステーション APIは、三菱UFJ eスマート証券が提供する個人向けの公式APIである。Windows上でkabuステーションを起動・ログインし、ローカルREST APIとWebSocketを利用する。Excelは不要である。

WebSocketの本番endpointは`ws://localhost:18080/kabusapi/websocket`で、登録銘柄の値が更新されたときにPUSH配信される。REST/PUSHを含む登録上限は最大50銘柄である。

取得可能な代表項目:

- 銘柄コード・市場
- 現在値と現在値時刻
- 前日終値・前日比・騰落率
- 始値・高値・安値
- 出来高・売買代金・VWAP
- 最良売買気配
- 最大10本の板情報

公式資料:

- [kabuステーション APIサービス](https://kabu.com/item/kabustation_api/default.html)
- [時価PUSH配信](https://kabucom.github.io/kabusapi/ptal/push.html)
- [APIリファレンス](https://kabucom.github.io/kabusapi/reference/index.html)
- [APIサービス利用規定](https://kabu.com/pdf/Gmkpdf/service/kabustationapiuserpolicy.pdf)

### 3.2 費用・利用条件

kabuステーション APIは、kabuステーション Professionalプラン以上の適用中に無料で利用できる。Professionalプランは口座・取引状況による適用条件があるため、口座準備時に最新条件を再確認する。

通常のkabuステーションが無料であっても、APIはProfessional以上という別条件である。APIの設定、APIパスワード管理、kabuステーションの起動・ログインも必要になる。

公式資料:

- [kabuステーション APIの料金・条件](https://kabu.com/item/kabustation_api/default.html)
- [kabuステーションの利用プラン](https://kabu.com/pdf/Eikpdf/kabustation/ks_motto_kt.pdf)

### 3.3 OrderScopeとの接続

APIはWindows側の`localhost`に公開される。WSLのネットワークモードによってはWSLからWindows endpointへ到達できる場合があるが、それを公式・安定経路とはみなさない。

初期構成ではWindows上の小さなcollectorだけがkabuステーション APIを呼び、OrderScopeのprovider-neutral snapshotへ変換して、WSLへimmutable handoffする。OrderScopeのSQLite/DuckDB/ParquetをWindows側から直接開かない。

リアルタイム監視だけが目的の場合、取得したPUSHをローカルで継続保存し、event timeとreceived timeを分けて記録する。1分足が必要な場合は、公式フィールドと欠損規則を保った決定的な集約処理を別途実装する。

APIは注文機能も持つが、初期OrderScope adapterは情報取得endpointだけをallowlistし、注文endpointを型・CLI・設定へ追加しない。

## 4. J-Quants API個人向けプラン

### 4.1 通常プラン

2026-09-03確認時点の月額と主要差分は次のとおりである。金額は税込。

| プラン | 月額 | API上限 | CSV | 履歴 | 主な範囲 |
|---|---:|---:|---|---:|---|
| Free | 0円 | 5件/分 | なし | 直近12週間を除く2年 | 上場銘柄、日足、財務サマリー等の試用範囲 |
| Light | 1,650円 | 60件/分 | あり | 5年 | 日足、財務サマリー、決算予定、TOPIX、投資部門別等 |
| Standard | 3,300円 | 120件/分 | あり | 10年 | Lightに加え、各種指数、信用・空売り、日経225オプション日足、EDINET関連等 |
| Premium | 16,500円 | 500件/分 | あり | 最長20年 | Standardに加え、前場四本値、配当、BS/PL/CF、売買内訳、先物・オプション四本値等 |

有料通常プランはFreeの12週間遅延を解消し、各datasetの公式更新時刻に従った当日・最新の日次データを取得できる。ただし、日足APIを場中リアルタイムquoteとして扱わない。

公式資料:

- [J-Quants API料金・プラン比較](https://jpx-jquants.com/)
- [JPXのJ-Quants API概要](https://www.jpx.co.jp/markets/other-data-services/j-quants-api/index.html)

### 4.2 分足・Tickアドオン

Light以上へ月額5,500円（税込）で追加できる。

- 対象は株式の分足とTick（歩み値）
- 取得可能期間は2年間
- デリバティブは含まれない
- 分足はAPI経由、Tickはbulk downloadで扱える
- 日次配信であり、リアルタイム配信ではない

合計月額:

| 組合せ | 月額（税込） |
|---|---:|
| Light＋分足/Tick | 7,150円 |
| Standard＋分足/Tick | 8,800円 |
| Premium＋分足/Tick | 22,000円 |

公式資料:

- [J-Quants API CSV・分足・Tick追加のお知らせ](https://www.jpx.co.jp/corporate/news/news-releases/6020/20260119.html)
- [J-Quants API提供データ例](https://www.jpx.co.jp/markets/other-data-services/j-quants-api/index.html)
- [公式J-Quants CLI](https://github.com/J-Quants/jquants-cli)

### 4.3 TDnetアドオン

Light以上へ月額11,000円（税込）で追加できる。

- TDnet/適時開示情報
- 過去5年間
- 日中のタイムリーな適時開示取得

株価だけを取得する構成には不要である。企業情報・決算・ニュース領域で採用を検討する場合は、公開TDnet/企業IR/EDINETとの機能差、保存条件、本文利用条件を`W0-004`およびprovider ADRで比較する。

### 4.4 技術・利用境界

J-Quants API V2はAPI key認証を使用する。HTTPS APIなのでWSL Pythonから直接取得でき、ExcelやWindowsデスクトップアプリを必要としない。

公式実装:

- [J-Quants公式Python client](https://github.com/J-Quants/jquants-api-client-python)
- [J-Quants公式CLI](https://github.com/J-Quants/jquants-cli)
- [J-Quants公式QuickStart](https://github.com/J-Quants/jquants-api-quick-start)

個人向けJ-Quantsは個人の私的利用に限定される。取得データそのものを閲覧可能な形で第三者へ配布・共有することや、同データによる分析結果を継続反復して第三者へ提供することは許可されない。法人・外部提供用途はJ-Quants Pro等の別契約領域である。

OrderScopeの現時点のlocal-only個人分析には適合し得るが、API response、raw dataset、再配布可能な出力をGit、HTTP response、共有storageへ置かない。

## 5. 比較

| 観点 | MARKET SPEED II RSS | kabuステーション API | J-Quants API |
|---|---|---|---|
| 主用途 | 場中情報・Excel利用 | 場中リアルタイム・ローカルプログラム | 日次・履歴・財務・市場分析 |
| Excel | 対応デスクトップ版が必須 | 不要 | 不要 |
| Windowsアプリ | 必須 | 必須 | 不要 |
| WSLから直接利用 | 不可。Windows handoffが必要 | `localhost`境界のためWindows collectorを推奨 | HTTPSで直接利用可能 |
| リアルタイム | 対応 | WebSocket PUSH | 非対応。分足/Tickアドオンも日次 |
| 過去分足/Tick | RSS関数・取得可能範囲に依存 | 自前蓄積が基本 | 2年分を有料アドオンで取得 |
| 代表的な費用条件 | 対応Excelライセンス | Professional以上の適用中はAPI無料 | Light 1,650円/月から |
| 実装契約 | Excel RSS関数 | 公式REST/WebSocket | 公式HTTPS API/CSV |

## 6. 推奨導入順

1. 場中リアルタイムが必要なら、kabuステーション APIの口座・Professional適用条件を確認する。
2. 取得専用のWindows collectorをprovider adapterとして設計し、注文endpointを含めない。
3. fixtureでPUSH、再接続、重複、欠損、時刻、50銘柄上限を検証する。
4. 日足・財務の不足を評価し、必要ならJ-Quants LightまたはStandardを追加する。
5. 過去分足/Tickを使う具体的な検証が始まる月だけ、J-Quants分足/Tickアドオンを検討する。
6. 対応Excelを既に保有し、kabuステーション APIで不足する項目がある場合に限り、MARKET SPEED II RSSをfallbackとして検証する。

この順序では、J-Quantsの履歴データとkabuステーションのリアルタイムデータを同一Factとみなさない。provider、dataset、source event time、retrieved/received time、集約methodを保持し、同時刻の差異はconflictまたはquality evidenceとして扱う。

## 7. ADRとの関係

本調査は`ADR_LOCAL_ANALYSIS_STACK_v0.1.md`を変更しない。同ADRの境界で次の両経路を扱える。

- J-Quants: WSL内のHTTPS provider adapterから直接取得
- 楽天RSS/kabuステーション: Windows-native adapterからimmutable handoffを経由

特定providerの採用、credential名、取得頻度、保存期間、利用条件確認票は本レポートでは確定しない。これらは該当するprovider作業単位でversion付きに決定する。
