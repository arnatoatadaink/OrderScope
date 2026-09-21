# OrderScope ローカル移行 タスク7実施レポート

作成日: 2026-09-21（Asia/Tokyo）
対象: Wrangler environmentの明示とremote resource誤操作防止
判定: **完了**

## 1. 実施内容

複数environmentが定義された`wrangler.jsonc`に対して、deploy入口で対象environmentを必須化した。

- `scripts/run-wrangler-with-env.sh`を追加した。
- `npm run deploy`と`npm run deploy:check`を同ラッパー経由へ変更した。
- `--env <name>`または`CLOUDFLARE_ENV`がない場合は終了コード2で停止する。
- 両方が指定されている場合、値が異なれば停止する。
- `CLOUDFLARE_ENV`だけが指定された場合は、Wranglerへ明示的な`--env`として渡す。
- Local Wrangler (`npm run dev`)はlocal persistence専用の既存ラッパーを使うため、このremote deploy制約とは分離している。

READMEに、deploy dry-run、remote D1、deployment一覧のenvironment明示手順を追加した。既存のremote preflight scriptも確認し、D1操作とdeployment一覧は`--env`を指定していることを再確認した。

## 2. `live-canary` resourceのread-only照合

`wrangler.jsonc`のsource-controlled定義とCloudflare read-only APIの応答を照合した。

| 項目 | 確認値 |
|---|---|
| environment | `live-canary` |
| Worker | `orderscope-market-worker-live-canary` |
| D1 binding | `STATE_DB` |
| D1 name | `orderscope-state-live-canary` |
| D1 resource ID | `03c85865-1aa3-4b0c-b219-18987cd260a6` |

実行したread-only確認:

```bash
npx wrangler whoami
npx wrangler d1 info STATE_DB --env live-canary
npx wrangler deployments list --env live-canary
```

`d1 info`は上記D1 ID/nameを返し、`deployments list`も`live-canary`の既存deployment一覧を返した。Secret値、認証token、D1データ内容は記録していない。

## 3. dry-run結果

```bash
npm run deploy:check -- --env live-canary
```

結果:

- 成功（exit status 0）
- environment未指定警告なし
- upload表示: `164.64 KiB / gzip 36.11 KiB`
- `env.STATE_DB`は`orderscope-state-live-canary`へ解決
- `WORKER_MODE=shadow`
- `PREDICTION_MODE=shadow`
- `NEWS_ACQUISITION_ENABLED=false`
- `UNIVERSE_PROFILE=canary-v0.1`
- `--dry-run: exiting now.`

安全ラッパーの負系も確認した。

| ケース | 結果 |
|---|---|
| environment未指定 | exit status 2、実行停止 |
| `--env other` と `CLOUDFLARE_ENV=live-canary`の不一致 | exit status 2、実行停止 |

今回、Worker deploy、D1 migration、D1 write、Secret変更、Cron変更は実施していない。

## 4. 次の作業

次はタスク8「secret設定を用途別に確認」である。`.env` / `.env.cloudflare`の存在・mode・Git非追跡を値非表示で確認し、Python local adapter用の`ORDERSCOPE_SECRET_*`とWorker用のCloudflare managed secret名を混同しない手順を確定する。Secret値そのものはレポート、manifest、Git diffへ出さない。
