# OrderScope — 実装・運用進捗トラッカー

Status: active operational tracker (non-normative)
Date: 2026-09-01
Plan: `WORK_PLAN_INITIAL_VALIDATION_AND_LONG_TERM_OPERATIONS_2026-09-01.md`

## 1. 使い方

本資料は作業工程そのものではなく、工程IDごとの実施証跡、外部依存、次の安全な操作を記録する進捗管理資料である。Code of Truthと作業工程が優先し、credential値、provider response body、account情報は記録しない。

状態の意味は次のとおり。

| 状態 | 意味 |
|---|---|
| 完了 | 定義済みの成果物と検証証跡が揃っている。 |
| 進行中 | リポジトリ内で安全に進められる実装・検証が残っている。 |
| 保留（外部） | Cloudflare/Alpacaの権限、実環境の識別子、実データ、または担当者確認が必要。 |
| 未着手 | 依存ゲートが未通過で、まだ開始しない。 |

## 2. 現在地

現在は **G0完了、G1到達後のI-1残試験／I-2準備**。限定Live Smokeを実施して実bar取得を確認し、検出した株式セッション境界不具合を修正・再検証した。Live Canary Workerは検証終了後に`WORKER_MODE=shadow`へ戻し、`PREDICTION_MODE=shadow`も維持している。

このトラッカー作成時に、型生成が管理用Cloudflare token名を Worker `Env` 型へ混入させる状態を検知した。型定義には混入させず、再発防止手順を runbook に追加した。token値は確認・記録していない。

2026-09-01の追試では、`.env` に `CLOUDFLARE_API_TOKEN` の定義があることだけを確認し、Cloudflare の token verify API を読み取り専用で呼び出した。結果は認証エラー（API error code `1000`）で、active token を確認できなかった。CRLF末尾を除いた場合も結果は同じだった。値、account情報、response bodyは表示・記録していない。このため、当該tokenを用いるremote操作には進まない。

同日、セッション `01a05d0b-53b8-7bf0-a0d2-93ac851924cd` の継続として、追加の最小権限token作成を開始した。I-0の読み取り確認用として、対象Cloudflare accountだけに制限した `D1: Read` と `Workers Scripts: Read` のみを候補とする。期限は短期（推奨7日以内）とし、token値・account ID・Secret値は本資料に記録しない。作成後はtoken verify、remote migration list、Secret名のlistだけを順に行う。環境名・専用D1 ID・Live化承認が未確定のため、`Edit`/`Write`権限およびdeploy操作はこのtokenに含めない。

2026-09-02、利用者から上記の追加tokenを指定どおり作成済みとの報告を受けた。token値は受領・記録していない。Dashboardの `Workers & Pages > orderscope-market-worker` に表示される `orderscope-market-worker` は現行のdefault Worker script名であり、Live Canary用のWrangler environment名ではない。現行 `wrangler.jsonc` に `env` 定義はないため、`--env` に渡す値はまだ存在しない。専用D1を伴うsource-controlledなenvironment定義を先に決める。

同日、追加tokenはrepository-localのWorker入力とは別のterminal環境変数で保持されている旨を確認した。Wranglerが標準で解決する名前は `CLOUDFLARE_API_TOKEN` のため、保持用の独自名をWorker bindingにせず、必要な単一コマンドに限って同名へ受け渡す。保持用の変数名・token値はいずれもWorker `Env` 型、`.env`、`.dev.vars`、文書、およびコマンド出力に含めない。

Live Canary用Wrangler environmentの提案名は `live-canary` とする。source-controlled設定でのWorker名は `orderscope-market-worker-live-canary` とし、以後の限定確認では `--env live-canary` を使用する。この名称は提案段階であり、専用D1 database ID、on-call executor、および独立reviewerの確定前にdeployやLive化を行わない。

2026-09-02、`wrangler.jsonc` に `secrets.required` として `ALPACA_API_KEY`、`ALPACA_API_SECRET` の名前だけを宣言した。この設定により、Wranglerの型生成は `.env` からSecret名を推測せず、宣言済みの2名のみを型のsource of truthとして使う。`CLOUDFLARE_LOAD_DEV_VARS_FROM_DOT_ENV=false`、一時的な書込み可能XDG設定で `wrangler types`、`wrangler types --check`、`npm run typecheck`、`npm test` を実行し、全て成功した（91 tests）。生成済み `worker-configuration.d.ts` に管理token名はない。既存 `.env` に管理credentialを置かないというrunbook上の配置要件自体は未解消であり、その物理的な移動または削除は値を扱わずに別途行う。

同日、repository-local `.env` から `CLOUDFLARE_API_TOKEN` と保持用の独自名 `CLOUDFLARE_API_TOKEN2` の定義を、値を表示せず削除した。削除後の `.env` に残る定義名は `ALPACA_API_KEY` と `ALPACA_API_SECRET` のみである。dotenvをWorker開発入力から除外し一時XDG設定を用いて、`wrangler types`、`wrangler types --check`、`npm run typecheck`、`npm test`（91 tests）、既定Shadow構成の `wrangler deploy --dry-run` を再実行し、すべて成功した。dry-runはD1と宣言済み非Secret変数だけを表示し、生成 `worker-configuration.d.ts` に管理token名がないことを再確認した。terminal-only credential機構にある追加tokenのactive確認、remote操作、およびLive Canary環境の検査は行っていない。

2026-09-02（再確認）、`CLOUDFLARE_LOAD_DEV_VARS_FROM_DOT_ENV=false` と一時的な書込み可能XDG設定で `wrangler types --check`、`npm run typecheck`、`npm test`、既定Shadow構成の `wrangler deploy --dry-run` を再実行し、すべて成功した。dry-runは `STATE_DB` と既知の非Secret `vars` だけを列挙し、管理tokenおよびAlpaca Secret値を表示しなかった。`.env` の定義名も `ALPACA_API_KEY` と `ALPACA_API_SECRET` のみであることを値非表示で確認した。なお、Wrangler 4.127.1の `wrangler check` はWorker設定の検証コマンドではなくstartup profilingの入口であるため、I-0の設定検証証跡には採用しない。Cloudflare公式のenvironment仕様どおり、named environmentではbindingを明示的に再宣言する必要がある。専用D1のIDを推測・流用せず、`live-canary`環境をsource-controlledに追加する作業は保留を維持する。

2026-09-02（本セッション）、利用者の「担当者＝権限」という認識を受け、`on-call executor`／`reviewer`はCloudflareの追加権限名ではなく、実行承認と事前確認を記録する運用ロールであると整理した。単独運用では同一操作者が実行権限保有者と自己確認者を兼ねられるが、remote mutationには依然として対応するAPI token権限と明示的な昇格判断が必要である。Runbookへこの区別を追記した。

同セッションで値を表示せずに確認したところ、process environmentの`CLOUDFLARE_API_TOKEN`と保持用独自名はいずれも未設定で、Wranglerの認証済みprofileも確認できなかった。repository-local `.env` はGit対象外で、残る定義名はAlpacaの2 Secretだけである。Cloudflare管理tokenの削除状態は安全側だが、削除したtoken値は復元できず、ローカル削除だけではCloudflare側のtokenは失効しない。状態不明の旧tokenをDashboardでrevokeし、対象account・短期TTLに限定したreplacementを作成する必要がある。

専用D1作成と後続操作の権限を分離した。一度限りの作成はDashboardで行い、非Secretのdatabase IDだけを設定へ渡す経路を優先する。CLI/API作成が必要な場合だけ`D1 Edit`と確認用`Workers Scripts Read`、作成後の読み取りpreflightは`D1 Read`と`Workers Scripts Read`、migration適用・Secret登録・deployを承認した段階だけ`D1 Edit`と`Workers Scripts Write`を使用する。`Edit`は作成・読取・更新・削除・listを含むため、常用しない。専用databaseの提案名は`orderscope-state-live-canary`とし、IDは作成結果から取得する。既存`orderscope-state`のIDは流用しない。

上記文書更新後、repository-local dotenvをWorker入力から除外した一時XDG環境で `wrangler types --check`、`npm run typecheck`、`npm test`、既定Shadow構成の `wrangler deploy --dry-run` を再実行し、すべて成功した。dry-runは87.61 KiB（gzip 20.14 KiB）で、`STATE_DB=orderscope-state`、`WORKER_MODE=shadow`を含む既知bindingだけを列挙し、uploadせず終了した。管理token名およびAlpaca Secret値はbinding出力に現れなかった。Wrangler 4.127.1に4.128.0の更新通知があったが、本preflight中の依存更新は行っていない。

2026-09-02（専用D1作成後）、利用者が既存のCloudflare管理tokenをすべてrevoke済みと報告した。Cloudflare Dashboardで作成した`orderscope-state-live-canary`のdatabase IDとして`03c85865-1aa3-4b0c-b219-18987cd260a6`を受領し、UUID形式を確認した。`wrangler.jsonc`へ`env.live-canary`を追加し、Worker名`orderscope-market-worker-live-canary`、専用`STATE_DB` binding、全非継承`vars`、許可済みSecret名を明示した。昇格前なので`WORKER_MODE=shadow`、`PREDICTION_MODE=shadow`を維持している。

権限・担当者・保存先の説明を簡素化した。Workerの通常実行にCloudflare管理tokenや担当者ロールは不要である。D1 IDは非Secretとして`wrangler.jsonc`、Alpaca credentialはLive環境のCloudflare Worker Secrets、Cloudflare管理認証は管理操作時だけDashboardログイン・Wrangler OAuth profile・repository外の一時tokenのいずれかを使用する。単独運用では別担当者を設けず、具体的なremote変更に対する利用者承認とpreflight成功だけを記録する。Codex上の操作承認はCloudflare認証を代替しない。

同設定に対し、repository-local dotenvをWorker入力から除外した一時XDG環境で`wrangler types --check --env live-canary`、`npm run typecheck`、`npm test`、`wrangler deploy --dry-run --env live-canary`を実行し、すべて成功した。dry-runは87.61 KiB（gzip 20.14 KiB）で、`STATE_DB=orderscope-state-live-canary`、`WORKER_MODE=shadow`、`PREDICTION_MODE=shadow`と想定済み非Secret varsだけを列挙し、uploadせず終了した。管理token名とSecret値は出力されなかった。database IDとremote実体の一致はCloudflare認証なしでは照合できないため、remote migration確認時に検証する。

remote照合のためWrangler 4.127.1のブラウザOAuthを開始したが、認可画面がD1以外にも多数のwrite scopeを要求することを確認したため、Cloudflare側の承認前提でログイン処理をキャンセルした。OAuth credentialは取得・保存しておらず、remote操作も行っていない。次のD1照合・migrationには、ファイルへ保存せずユーザーのシェルプロセスだけで保持する、対象account限定・短期・`D1 Edit`のみのtokenを使用する方針とする。6本のmigration（`0001`〜`0006`）はWrangler経由で履歴を保って適用し、DashboardへのSQL手動貼付けは行わない。

2026-09-03、利用者からWrangler OAuth画面の権限範囲を理解した上で、本runbook作業を継続する明示承認を得た。再度ブラウザOAuthを実行し、Wranglerのユーザーprofileで認証した。これは管理操作専用であり、Worker binding、repository-local dotenv、生成型には含めていない。旧API tokenは利用者がすべてrevoke済みであり、新しいAPI tokenは作成・使用していない。

同セッションでremote D1を照合し、`orderscope-state-live-canary`と受領済みdatabase IDの一致を確認した。migration `0001`〜`0006`をWrangler経由で適用し、再確認でpending 0となった。対象WorkerのSecret一覧には`ALPACA_API_KEY`と`ALPACA_API_SECRET`の名前だけが存在した。named environmentに対する型生成・型検査・全テスト・dry-runを成功させた後、まずShadowをdeployし、CronによるDigest更新とD1永続化を確認した。

G0成立後、`UNIVERSE_PROFILE=canary-v0.1`、`ACQUISITION_MAX_JOBS_PER_TICK=1`、`PREDICTION_MODE=shadow`を維持して限定Live Smokeを実施した。初回Live版`16383165-793c-4b94-aac6-5a65675172fe`で、株式intradayの要求範囲が前営業日のcloseから翌日のRegularへ跨ぎ、`SESSION_MISMATCH`として91件のReject receiptが保存される不具合を検出した。RunbookどおりShadow版`1a57e569-b42c-4123-9485-50ff2ef18fcc`へrollbackし、D1証跡を削除せず原因を調査した。

`SchedulePolicy`を修正し、株式intradayのprovider要求を1つのauthoritative session内へ制限した。checkpointが前session closeと一致する場合は次session openから進める。2件の回帰テストを追加し、型検査と全テストに成功した。修正版をShadow版`637db4df-03bb-4290-8121-5070d050eadb`で確認後、Live版`4e17efb3-2156-47de-9be6-f7e236d3e3d4`として再Smokeした。

再SmokeではBTCUSDとNVDAの実bar／receipt／checkpoint前進、overlapによる`MATCHED`、Digest継続更新を確認した。最終read-only集計はnormalized bar 2,256件、`MATCHED` 180件、Reject 91件、Conflict 0件、Digest history 96件である。91件のRejectは全て修正前に取得された保存済み診断証跡であり、修正版Live開始後（`2026-09-02T23:05:00Z`以降）の新規Rejectは0件だった。AMDとQQQの`PARTIAL`はIEX実データのgapを表し、欠損を合成していない。SPYのcoverageが他銘柄より古い公平性課題は`CANARY-001`として継続する。

限定Smoke終了後、Shadow rollback版`2ed5be9e-c413-4961-9279-ffcaeaff1886`をdeployした。`/health`で`mode=shadow`、`status=shadow`、Alpaca credentialとD1 bindingの設定済み表示、およびSecret値非表示を確認した。Remote D1のmigration pending 0とSecret名2件も再確認済みである。

続いて`CANARY-001`の公平化を実装した。実行上限を適用する前に、eligibleなmissing、未取得、`completeThrough`が最古のforward coverage、coverage keyの順で決定的に並べる。plannerのjob hash順だけには依存しない。優先順位の単体テストとセッション境界変更後のintegration期待値を追加・更新し、TypeScript、全94テスト、named Shadow dry-runが成功した。公平化を含むShadow版`e27c6eed-62fc-4244-a1bb-f23f186b406d`をdeployし、`/health`でShadow継続と公開情報のsanitizationを確認した。5銘柄すべての実環境前進確認までは完了扱いにしない。

2026-09-03、セッション`01a06111-77aa-7563-9611-c2b871e81806`の依頼を限定Live昇格の承認として、公平化版をLive Canary version `23780cdb-3c13-4c1c-a764-3895b3bd982d`で実環境確認した。preflightはmigration pending 0、Secret名2件、型生成check、TypeScript、全94テスト、Live dry-runの全てに成功した。実attempt順はAMD `MISSING_RANGE`（`PARTIAL`）、QQQ `MISSING_RANGE`（`PARTIAL`）、SPY `FORWARD_COVERAGE`（`SUCCEEDED`）、BTCUSD `FORWARD_COVERAGE`（`PARTIAL`）、SPY `FORWARD_COVERAGE`（`SUCCEEDED`）で、missing優先と最古forward coverage優先が実環境でも成立した。SPYは`complete_through`が`2026-09-01T20:00:00.000Z`から`2026-09-02T16:49:00.000Z`へ2 chunkで前進し、従来のstarvationを解消した。限定区間ではnormalized bar +223、`MATCHED` +78、新規Reject 0、Conflict 0、Failed attempt 0だった。長い実行と次Cronが重なった2 tickは`SKIPPED_LOCKED`となり、lease解放後に後続処理が継続した。NVDAは今回の限定区間では選択されなかったため、5銘柄すべての実環境前進という`CANARY-001`最終条件は未達のままとする。

確認後はShadow version `c54f2cbc-9565-4cad-a5c8-df98afbfc6b4`へrollbackした。`/health`と`2026-09-02T23:53:44.000Z`の次Cron digestはいずれも`mode=shadow`、`status=shadow`を示した。最終read-only照合ではactive lease 0、未完了attempt 0、normalized bar 2,479件、`MATCHED` 258件、Reject 91件、Conflict 0件、Failed attempt 0件である。保存済みReject 91件は全て以前のセッション境界修正前の証跡で、今回の限定Liveでは増えていない。

同日、後続セッション`01a06480-0317-7431-b657-fd3da79065d`の継続依頼を次の限定Live承認として扱い、Wrangler OAuthをrepository外の一時XDG領域で再認証した。remote migration pending 0、許可済みSecret名2件、型生成、型check、TypeScript、全94テスト、Live dry-runを再確認し、公平化版をLive version `9e0c1e4e-ebc9-4b51-a5f6-7807a33ed8e5`へ昇格した。`/health`は`mode=live`、`status=ready`で、`UNIVERSE_PROFILE=canary-v0.1`、1 job/tick、`PREDICTION_MODE=shadow`を維持した。

`2026-09-03T07:58:16Z`からのattempt順は、AMD `MISSING_RANGE`（`PARTIAL`）、QQQ `MISSING_RANGE`（`PARTIAL`）、BTCUSD `FORWARD_COVERAGE`（`SUCCEEDED`）3回だった。BTCUSDはretention floorから100分範囲を3 chunk処理し、`complete_through`を`2026-09-02T04:36:00.000Z`から`2026-09-02T12:58:00.000Z`へ前進させた。差が300分より大きいのは、最初の要求開始が24時間retention floorの`2026-09-02T08:00:16.000Z`へ切り上がったためである。Live区間ではnormalized bar 2,479→2,776（+297）、`MATCHED` 258→263（+5）、Reject 91→91、Conflict 0→0、Failed attempt 0→0だった。

最初のBTCUSD job中、後続2 tickが`SKIPPED_LOCKED`となった。durable attemptの`started_at`と`finished_at`はどちらもscheduled timestampで実所要時間を保持しないため精密なdurationは算出できないが、2回の競合時刻からこのjobは少なくとも約100秒、次に実行できたtickまでの上限で約159秒未満と評価できる。これは`CANARY-002`でtick全体予算だけでなく実所要時間のdurable observabilityも必要であることを示す。

米国市場開始前でNVDAは前営業日Regular closeまで既に完了しており、新規Regular coverageを前進できなかった。またBTCUSDが最古coverageのため、SPY/NVDAまで待つには限定窓を超えると判断した。新規Live tickを止めるためShadow version `619c0b2b-5cb0-4351-80a8-e854c0958897`をdeployし、切替直前に開始した最後のBTCUSD jobの完了まで監視した。最終確認は`/health`と`2026-09-03T08:04:55.000Z`のdigestが`mode=shadow`、`status=shadow`、active lease 0、未完了attempt 0である。`CANARY-001`は引き続き部分合格とし、次回は米国Regular開始後かつNVDAがdueになる時間帯に実施する。

## 3. I-0 Preflight

| ID | 状態 | 証跡 / 実施内容 | 完了までの次の操作 |
|---|---|---|---|
| INIT-001 | 完了 | 専用D1`orderscope-state-live-canary`を作成済み。受領したdatabase IDで`env.live-canary`、Worker名、専用`STATE_DB`、全`vars`、Secret名をsource-controlled設定へ追加し、両modeを`shadow`に維持した。named environmentの型検査とdry-runも成功した。 | Remote照合はINIT-003で実施する。 |
| INIT-002 | 完了 | `wrangler.jsonc` のdefault／`live-canary`双方で、`secrets.required`は許可されたAlpacaの2名のみ。隔離入力で`wrangler types --check --env live-canary`と`npm run typecheck`が成功し、生成`Env`型に管理token名はない。 | 追加操作なし。設定変更時に同検査を再実行する。 |
| INIT-003 | 完了 | Remote D1の名前とIDを照合し、migration `0001`〜`0006`を適用。再確認でpending 0。 | 追加migration時に同じ手順を繰り返す。 |
| INIT-004 | 完了 | Live Canary WorkerのSecret一覧に、許可済みの`ALPACA_API_KEY`と`ALPACA_API_SECRET`の名前だけが存在。値は参照・記録していない。 | credential rotation時だけ更新し、名前のみ再確認する。 |
| INIT-005 | 完了 | named環境で型生成・`wrangler types --check`・TypeScript・全テスト・dry-runが成功。bindingは専用D1、宣言済みvars、許可済みSecret名に限定。 | 設定・型・migration変更時に再実行する。 |
| INIT-006 | 完了 | Runbookへrollback手順を追加し、利用者承認後のLive Smokeで実際に2回Shadow復帰を実行。rollback版`2ed5be9e-c413-4961-9279-ffcaeaff1886`と、後続Shadow版`e27c6eed-62fc-4244-a1bb-f23f186b406d`の`/health`でShadowを確認。 | 次回Live昇格でも承認・preflight・復旧版を記録する。 |
| INIT-007 | 完了 | 利用者が作成済みCloudflare管理tokenをすべてrevokeした。repository-local `.env` に管理tokenはなく、管理tokenをWorker runtimeへ渡す経路もない。 | 今後のremote管理は必要時だけDashboardログイン、Wrangler OAuth、または短期tokenを使用する。 |

### I-0 判定

G0の全条件を満たしたため、I-0は完了。管理認証はWranglerのユーザーOAuth profileに限定し、Worker runtimeへ管理tokenを渡す経路はない。通常のCron実行には担当者操作もCloudflare管理credentialも不要である。

## 4. 後続フェーズ

| フェーズ / 主なID | 状態 | 開始条件 / メモ |
|---|---|---|
| I-1 Bounded Live Smoke (`SMOKE-*`) | 進行中（G1到達） | `SMOKE-001`〜`005`完了。`006`の意図的provider失敗と`007`の明示的一時停止試験を残す。G1の実bar、checkpoint、重複、Reject理由、公開情報の判定条件は確認済み。 |
| I-2 Canary Operational Check (`CANARY-*`) | 進行中 | `CANARY-001`の公平な決定的優先順位を実装し、全94テスト、Shadow deploy、限定Liveでのmissing優先、SPY starvation解消、BTCUSDの連続3 chunk前進まで成功。NVDAを含む5銘柄すべての実環境前進を確認後に完了判定する。`CANARY-002`向けに、1 jobが約100秒以上継続して2 tickを`SKIPPED_LOCKED`にした証跡と、attempt timestampでは実所要時間を測れないobservability不足を記録した。 |
| I-3 Local Analysis MVP (`LOCAL-*`) | 進行中 | G1と最低限の実barを確認済み。`L0-001`でPython 3.13/uv、SQLite/DuckDB、PyArrow/Parquet、FastAPI/Uvicorn、pytest、WSL2単独writerのstackを確定した。次は`L0-002`のscaffold。fixture基盤から開始し、D1 exportを定常同期に使わない。 |
| L-1 R2 Archive (`R2-*`, `SYNC-*`) | 未着手 | G2とarchive contract承認後。private bucketと最小権限が前提。 |
| L-2 Sustained Operations (`RET-*`, `OPS-*`, `QUAL-*`) | 未着手 | G3/G4後。restore成功前にD1のmaterialなbarを削除しない。 |
| L-3 Prediction Research (`PRED-*`) | 未着手 | G5後。PredictionはAttention・自動判断へ接続しない。 |

## 5. 今回のリポジトリ内成果物

- `docs/RUNBOOK_CLOUDFLARE_WORKER_SCHEDULE_v0.1.md`
  - Worker型と管理credentialの分離ルールを追加。
  - Live CanaryからShadowへ戻す手順を追加。
  - 株式intraday要求を単一authoritative session内へ制限する運用則を追加。
- `wrangler.jsonc`
  - 必須Secret名を宣言し、型生成をrepository-local dotenvの推測から分離。
  - 専用D1を持つ`live-canary` named environmentを追加し、最終状態をShadowに設定。
- `src/schedule.ts` / `src/schedule.test.ts`
  - 株式セッション境界を跨ぐ要求を防ぎ、前session closeから次session openへ進める回帰テストを追加。
- `src/job-priority.ts` / `src/worker.ts` / `src/worker.test.ts`
  - missing、未取得、最古coverage、安定キーの順で実行候補を公平化し、tick上限適用前に使用。
- `worker-configuration.d.ts`
  - 隔離した入力で再生成し、`wrangler types --check`で最新状態を確認。
- 本トラッカー
  - I-0の検証結果、外部ブロッカー、次操作を記録。
  - 2026-09-01のtoken読み取り専用検証、clean type check失敗、typecheck/dry-run成功を追記。
  - 2026-09-02のSecret名宣言、管理credentialのrepository-local入力からの除去、隔離型生成、typecheck、91 test、Shadow dry-run成功を追記。
- `docs/ADR_LOCAL_ANALYSIS_STACK_v0.1.md`
  - `L0-001`としてローカルMVPのruntime、package/lock、storage/query、dataset、API、test、Windows/WSL境界を確定。

作業工程ファイルおよび既存の `PROGRESS_REPORT_2026-09-01.md` は進捗記録のために変更していない。

## 6. 次回の実行チェックリスト

次の順で実施する。

1. `L0-002`で`analysis/app`、`analysis/tests`、`analysis/config`をscaffoldし、`var/`をGit対象外にする。
2. `L0-004`で外部interfaceを拒否するlocalhost healthを実装する。
3. `I0-001/002`でAMD/NVDAのentity registryとprovider-neutral provenance型を実装する。
4. `S0-001`でSECの現在の公式接続・fair-access条件を確認し、SEC adapter sliceへ進む。
5. Workerの`SMOKE-006/007`、`CANARY-001`最終確認、`CANARY-002〜006`は独立バックログとして維持し、remote変更は別の承認済み窓で行う。
