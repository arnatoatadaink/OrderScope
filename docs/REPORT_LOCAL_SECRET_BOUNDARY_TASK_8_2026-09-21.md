# OrderScope ローカル移行 タスク8実施レポート

作成日: 2026-09-21（Asia/Tokyo）
対象: secret設定の用途別確認
判定: **完了**

## 1. 用途別のsecret境界

| 用途 | 変数名 | 読み込み先・扱い |
|---|---|---|
| Cloudflare Worker runtime | `ALPACA_API_KEY` / `ALPACA_API_SECRET` | Cloudflare Worker Secret binding。local Worker確認時だけrepository-localのignored dotenvから読み込まれる |
| Python local adapter | `ORDERSCOPE_SECRET_ALPACA_API_KEY` / `ORDERSCOPE_SECRET_ALPACA_API_SECRET` | WSLのprocess environmentだけ。`analysis/app/orderscope_local/config.py`の登録名からのみ読む |
| Wrangler管理認証 | `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` | Wranglerのread-only管理操作だけ。Worker `Env` bindingや生成型へ渡さない |

Worker用の`ALPACA_*`とPython用の`ORDERSCOPE_SECRET_*`は同じ名前として自動解決しない。Python adapterを起動する場合は、利用者が意図したときだけ、WSL process内で`ORDERSCOPE_SECRET_*`へ明示的に設定する。値をファイルへ複製したり、CLI引数・ログ・manifestへ書き出したりしない。

## 2. 値を表示しない状態確認

Windows側sourceのdotenvについて、定義名だけを確認した。

| ファイル | 定義名 | Git状態 |
|---|---|---|
| `.env` | `ALPACA_API_KEY`, `ALPACA_API_SECRET` | untracked、`.gitignore`の`.env`に一致 |
| `.env.cloudflare` | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` | untracked、`.gitignore`の`.env.*`に一致 |

WSL native filesystem上の退避コピーでは、次の2ファイルがともにmode `600`であることを確認した。

```text
/home/y/code/OrderScope/.env
/home/y/code/OrderScope/.env.cloudflare
```

一方、Windows側sourceの`/mnt/c`上では、WSLから`chmod 600`を実行してもmode表示が`777`のままになった。これはdrvfs側のmode表示によるものであり、これらをWSL native secret storeとは扱わない。WSL native側のmode `600`を維持し、Windows側sourceのdotenvはGit非追跡の一時入力としてのみ扱う。

## 3. 値を出さない実行確認

以下はsecret値、account情報、API response bodyを記録せずに実施した。

| 確認 | 結果 |
|---|---|
| Python News/Daily adapterのcredential境界 | 合成値で両adapterの初期化に成功 |
| 実dotenvからPython用変数名への明示的なprocess内受け渡し | adapter初期化に成功。ファイルへの再保存なし、外部API呼び出しなし |
| Python config/news関連試験 | 138 passed |
| Local API | `127.0.0.1` のhealthがHTTP成功。確認後にprocessを終了 |
| Wrangler read-only確認 | 既存WSL Wrangler OAuth profileで`whoami`成功 |
| `.env.cloudflare`経由の`whoami` | ネットワーク到達性エラーで完了せず。認証失敗とは判定していない |

`.env.cloudflare`経由の確認で到達性エラーが出たため、同経路をremote操作の成功根拠にはしない。remote操作前は、既存のWrangler認証profileまたは別途承認済みの最小権限tokenを使い、`--env <name>`を必ず指定する。

## 4. 漏えい確認

- dotenvはtracked fileではない。
- dotenvの値は本レポート、移行manifest、Git diffへ記録していない。
- `worker-configuration.d.ts`の管理token名と、Workerの非Secret binding出力に管理認証情報を含めていない。
- Pythonの`LocalConfig`はcredential値を保持せず、adapterが必要な時点だけprocess environmentから読む。

## 5. 次の作業

次はタスク12「移行手順を運用文書化」である。今回確定したsecret境界、WSL native側mode `600`、Wrangler認証profile、remote environment明示をREADMEとrunbookの再現手順へ統合する。その後、タスク9の最終受入で全試験とhealthをまとめて再記録する。
