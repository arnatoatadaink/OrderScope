# OrderScope ローカル実装環境 PC 移行実施レポート

作成日: 2026-09-20（Asia/Tokyo）
対象: 別PCの WSL2 環境から現PCの WSL2 環境への OrderScope 移行
関連文書: `REPORT_LOCAL_ENVIRONMENT_MIGRATION_WSL_TO_CODEX_DESKTOP_WINDOWS_2026-09-19.md`

## 1. 結論

OrderScope のソース、ローカルデータ、ローカル D1 状態を現PCへ移し、WSL2からWindows側sourceを参照する実行環境を再構築した。データ完全性検証、依存関係の再作成、全自動試験、型検査、Cloudflare Worker の dry-run、ローカル API health check、および Cloudflare 認証の read-only 確認は成功している。

Codex Desktopで編集するsourceの正本は `/mnt/c/users/y/projects/codex_work/orderscope` とする。WSL側の `/home/y/code/OrderScope` は、移行検証済みの退避コピーおよび比較用環境として保持する。`.venv`と`node_modules`はWSLのNode/Pythonで生成するが、今回の運用ではCodexの保存エラーを避けるためWindows側source直下に配置する。また、並行して移行している別プロジェクトの影響により nvm の default が Node.js 22.20.0 へ変更されている。OrderScope の受入検証は Node.js 24.21.0 で実施したため、プロジェクト単位のバージョン固定が残課題である。

総合判定は **条件付き完了** とする。Windows側sourceをCodexの正式workspaceとして維持し、WSL実行環境のNode.js 24固定、lockfileおよび移行資料のコミット、npm警告の評価が完了すれば移行完了と判定できる。

## 2. 移行元と移行先

| 区分 | パス | 状態 |
|---|---|---|
| Windows側source正本 | `/mnt/c/users/y/projects/codex_work/orderscope` | Codex Desktopで編集・保存するworkspace |
| WSL側検証コピー | `/home/y/code/OrderScope` | 完全コピー。退避・比較用として保持 |
| WSL生成Python環境 | `/mnt/c/users/y/projects/codex_work/orderscope/.venv` | WSLのuvで生成したLinux環境 |
| WSL生成Node環境 | `/mnt/c/users/y/projects/codex_work/orderscope/node_modules` | WSLのNode 24/npmで生成したLinux依存 |
| 可変データ正本 | `/home/y/data/orderscope/local` | `ORDERSCOPE_DATA_ROOT`でWSL native filesystemへ固定 |
| local D1状態正本 | `/home/y/data/orderscope/wrangler-state` | `--persist-to`でWSL native filesystemへ固定。SQLite、WAL、SHMを一組として扱う |

WSL側の完全コピーは、Windows側sourceでの継続運用確認とGit変更確定が終わるまで削除しない。

## 3. 実施内容

### 3.1 移行元由来の依存物・キャッシュ削除

次の移植不能または再生成可能な成果物を削除した。

- `.venv/`
- `node_modules/`
- `.pytest_cache/`
- `analysis/` 配下の全 `__pycache__/`
- `*.pyc`、`*.pyo`
- 存在していたPythonツールキャッシュ

`var/`、`.wrangler/state/`、`.env`、`.env.cloudflare` は削除対象から除外した。

### 3.2 データコピーと完全性検証

検証用移行先 `/home/y/code/OrderScope` を作成し、Windows側コピーからWSL2 native filesystemへファイルを転送した。最初のコピーが途中終了したため、`rsync -a` で差分転送を再開し、Git repositoryとして完全に読み取れることを確認した。その後、Codex DesktopからWSL側ファイルを保存できない制約を確認したため、source正本はWindows側へ戻し、依存関係だけをWSLコマンドでWindows側source直下に再生成した。

`MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256` を使用し、以下を含む全対象ファイルが移行元と一致することを確認した。

- Miniflare cache SQLite本体、WAL、SHM
- local D1 SQLite本体、WAL、SHM
- news benchmark、candidate、label
- cross-market観測結果
- D1 custody/export manifest、NDJSON、検証結果

検証コマンド:

```bash
sha256sum --check MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256
```

結果: 全項目 `OK`。

### 3.3 WSL2ランタイム構築

現PCのWSL2ユーザー環境へ次を導入した。

| コンポーネント | 導入・検証時バージョン |
|---|---|
| uv | 0.12.17 |
| Python | CPython 3.13.15 |
| nvm | 0.40.7 |
| Node.js | 24.21.0 |
| npm | 11.19.0 |
| Wrangler | project-local 4.127.1 |

Python 3.13はuv管理、Node.js 24はnvm管理とした。実行ツールはWSL側に置き、プロジェクトsourceと生成先の`.venv`・`node_modules`はWindows側workspace直下とした。

### 3.4 lockfile整合性修正

移行前から判明していた `pyproject.toml` と `uv.lock` の不整合を解消した。`uv lock` により `uv.lock` に49行が追加された。

追加された主なpackage:

- `httpx2 2.13.0`
- `httpcore2 2.13.0`
- `httpx2-jsfetch 1.0`
- `truststore 0.10.4`

既存packageの削除やversion変更はなかった。更新後の `uv lock --check` は成功した。

### 3.5 依存関係再生成

移行元のバイナリdirectoryは使用せず、WSL2上でlockfileから再生成した。

```bash
npm ci
uv sync --locked
```

生成物（WSLコマンドでWindows側source直下に生成）:

- `/mnt/c/users/y/projects/codex_work/orderscope/node_modules`
- `/mnt/c/users/y/projects/codex_work/orderscope/.venv`

この構成ではLinux ELFバイナリを含む依存directoryがNTFS上に置かれる。実行はWSLに限定し、Windows native Node/Pythonからこれらを使用しない。

### 3.6 可変データ・local Wrangler stateのWSL正本化

全書き込みprocessが停止していることを確認し、Windows側sourceの`var/`と`.wrangler/state/`を次へコピーした。

- `/home/y/data/orderscope/local`
- `/home/y/data/orderscope/wrangler-state`

移行manifestは `/home/y/data/orderscope/migration-manifest-20260920T225347Z.txt` に保存した。`var/` 14ファイルとWrangler state 9ファイルのsource/target SHA-256が一致し、移行後の全SQLiteで`PRAGMA integrity_check`が`ok`となった。`scripts/run-local-wsl.sh`を追加し、Windows側sourceをcwdにしてもPythonは`ORDERSCOPE_DATA_ROOT`、local Wranglerは`--persist-to`を外部WSL rootへ使用する。収集・検証スクリプトのrepository-relative `var/`参照もdata root参照へ修正した。

## 4. 受入検証結果

| 検証 | 結果 |
|---|---|
| `uv lock --check` | 成功 |
| `npm test` | 199 passed、0 failed |
| `uv run pytest -q` | 696 passed、0 failed |
| `npm run typecheck` | 成功 |
| `npm run deploy:check` | 成功 |
| Local API bind | `127.0.0.1:8000` のみ |
| `GET /health` | HTTP 200、`status=ok` |
| `wrangler whoami` | Account API Tokenで成功 |

ローカルAPIは次のラッパー経由で検証した。

```bash
bash scripts/run-local-wsl.sh api --port 8000
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

結果はHTTP 200、`status=ok`、`bind_host=127.0.0.1`。Wranglerも `bash scripts/run-local-wsl.sh wrangler --port 8787` で起動し、`/health` がHTTP 200となり、追加stateは`/home/y/data/orderscope/wrangler-state`配下に生成された。両processとも確認後に正常停止した。

## 5. Secretと認証

次のファイルが移行先に存在することを確認した。値は調査・レポートに表示していない。

- `.env`
- `.env.cloudflare`

NTFSからのコピー直後は両ファイルのmodeが`777`になっていたため、WSL側で`600`へ修正した。

```text
600 .env
600 .env.cloudflare
```

Cloudflareは `CLOUDFLARE_API_TOKEN` を使用した `wrangler whoami` に成功した。remote D1データはCloudflare側に存続しており、PC間ファイルコピーの対象としていない。

Pythonローカルadapterが必要とするsecret名はWorker側と異なるため、利用前に次を確認する必要がある。

- `ORDERSCOPE_SECRET_ALPACA_API_KEY`
- `ORDERSCOPE_SECRET_ALPACA_API_SECRET`

## 6. 検出した警告と残課題

### 6.1 Codex保存制約に伴う配置方針変更

Codex DesktopからWSL側 `/home/y/code/OrderScope` のsourceを編集・保存すると設定保存エラーで作業が停止したため、source正本はWindows側 `/mnt/c/...` に戻した。依存関係と実行はWSLから行い、CodexはWindows側sourceを編集する。この方針を採用した同一配置でNode/Python試験、deploy dry-run、Local API healthが成功している。

### 6.2 Node.js defaultの競合

移行検証時はNode.js 24.21.0を明示して実行した。その後、共有nvm環境のdefaultが別プロジェクトの影響とみられるNode.js 22.20.0へ変化した。

```text
default -> 22.20.0
installed -> 22.20.0, 24.21.0
```

OrderScopeには`.nvmrc`および`package.json`の`engines`指定がない。プロジェクト単位でNode.js 24を固定し、Node.js 24で受入試験を再実行する必要がある。

### 6.3 npm警告

`npm ci` は成功したが、次が報告された。

- `sharp@0.35.2`（`miniflare`経由）にHigh advisory 1系統
- `undici@7.28.0`（rootの`miniflare@4`経由）にHigh advisory 1系統とModerate advisory 4件
- `esbuild@0.28.1`および`workerd@1.20260730.1` / `1.20260828.1`のinstall-script未承認警告

調査結果は `docs/REPORT_LOCAL_NPM_AUDIT_TASK_6_2026-09-21.md` に記録した。対象packageはdevDependenciesで、`wrangler deploy --dry-run --env live-canary`のproduction Worker bundleには含まれない。`npm audit fix`や強制更新は未実施であり、依存経路とlocal runtimeへの影響をレビューしてから別変更として扱う。install-scriptは確認済みの3 package/versionだけを`package.json`の`allowScripts`で許可した。

### 6.4 Wrangler環境指定

deploy dry-runは成功したが、複数environmentが定義されているにもかかわらず対象environmentが未指定という警告が出た。remote操作では `--env` または `CLOUDFLARE_ENV` を明示し、誤環境への操作を防止する。

### 6.5 未コミット差分

WSL側には次の差分がある。

```text
M  uv.lock
?? MIGRATION_WSL2_LOCAL_STATE_2026-09-19.md
?? MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256
?? docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_WSL_TO_CODEX_DESKTOP_WINDOWS_2026-09-19.md
```

本レポートも追加対象となる。内容をレビューし、移行に関する一つの変更としてcommitするか、資料とlockfileを分割してcommitするかを決定する。

## 7. 完了までの推奨手順

1. Codex Desktopでは `/mnt/c/users/y/projects/codex_work/orderscope` を正式workspaceとして使用する。
2. WSL shellでNode.js 24を選択し、Windows側sourceに対して`npm ci`と`uv sync --locked`を実行する。
3. Node.js 24を選択して全試験、型検査、deploy dry-runを再実行する。
4. `uv.lock`差分と移行資料をレビューしてcommitする。
5. npmの4件のhigh severity警告とinstall-script警告を調査する。
6. Cloudflare操作時のenvironment指定方針を確認する。
7. WSL側の検証コピーとWindows側sourceのcommit・hashを照合する。
8. 保留期間経過後、WSL側検証コピーの削除可否を判断する。

## 8. 完了条件

次をすべて満たした時点でPC移行を完了とする。

- CodexはWindows側source、terminal/runtimeはWSLという役割分担が明文化されている。
- WSLコマンドでWindows側sourceの`.venv`・`node_modules`を再生成できる。
- Node.js 24がプロジェクト単位で再現可能に選択される。
- `uv lock --check`、Python 696件、Node 199件、typecheck、deploy dry-runが再度成功する。
- 移行資料と`uv.lock`がGitで確定されている。
- secretファイルが追跡されず、mode`600`を維持している。
- `var/`および`.wrangler/state/`を複数process・複数コピーから同時に開かない。
- remote操作でCloudflare environmentを明示する。

## 9. 最終評価

アプリケーションコード変更なしで、Windows側sourceをCodex Desktopから編集し、WSL上で依存関係・テスト・実行を行う構成が成立することを確認した。データ完全性と主要な回帰基準は満たしている。残作業はNode.js versionの固定、Git差分の確定、および依存警告の運用判断である。
