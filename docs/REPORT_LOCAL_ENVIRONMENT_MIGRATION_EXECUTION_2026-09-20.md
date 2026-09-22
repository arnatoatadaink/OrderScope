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

複数environmentが定義されているため、deploy入口に `scripts/run-wrangler-with-env.sh` を追加した。`npm run deploy`と`npm run deploy:check`は `--env` または `CLOUDFLARE_ENV` がない場合に停止し、両方の値が異なる場合も停止する。`npm run deploy:check -- --env live-canary`はenvironment警告なしで成功した。

`live-canary`のWorker、D1 name、D1 resource IDをread-onlyで再確認した。詳細は `docs/REPORT_LOCAL_WRANGLER_ENVIRONMENT_TASK_7_2026-09-21.md` に記録した。

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

## 10. 2026-09-21 区切り時点の進捗更新

### 10.1 完了した移行タスク

2026-09-21までに、残作業12項目のうち次を完了または最終受入へ集約した。

- タスク1: Node.js 24固定。`.nvmrc=24.21.0`を配置し、最終確認はタスク9へ集約。
- タスク2: `uv.lock`整合。最終の`uv lock --check` / `uv sync --locked`をタスク9へ集約。
- タスク3: 移行資料・lockfileのGit確定を継続。最終文書更新を含むcommit状態確認はタスク9完了時に行う。
- タスク4: Windows側source / WSL runtimeの役割分担をREADMEへ明文化。
- タスク5: 可変データとlocal Wrangler stateをWSL native filesystemへ正本化。SQLite integrity、manifest/hash、Local API / local Worker healthを確認。
- タスク6: npm warningを調査し、advisory、依存経路、production bundle非包含、`allowScripts`、更新方針を記録。
- タスク7: Wrangler remote environmentを必須化し、`live-canary` resourceをread-only照合。deploy/dry-run入口をfail-closed化。
- タスク8: Worker / Python local adapter / Wrangler管理credentialのsecret境界を確認。dotenvのGit非追跡とWSL native側mode 600を記録。
- タスク12: `docs/RUNBOOK_LOCAL_ENVIRONMENT_WSL_WINDOWS_2026-09-21.md`を追加し、Windows source + WSL runtimeの再現手順を文書化。
- タスク10: `/home/y/code/OrderScope` は退避・比較用copyとして保持継続。
- タスク11: 退避copyの整理・削除判断は移行完了後の後工程とし、移行完了ゲートから除外。

### 10.2 タスク9最終受入で検出したブロッカー

タスク9の最終受入を現行構成で開始した結果、データhashとPython lock/syncは先行部分で成功した一方、`npm ci`中にWindows側source `/mnt/c/Users/Y/Projects/codex_work/OrderScope` への大量の `EIO: i/o error` が発生した。

確認された代表例:

- `node_modules` 配下で多数の `TAR_ENTRY_ERROR EIO`
- `node_modules/esbuild/bin/esbuild` の `lstat` がEIO
- 後続ではrepository直下の `package.json` そのもののopenがEIO
- `uv.toml` のopenも `Input/output error (os error 5)`
- Local APIは起動に至らず、`127.0.0.1:8000` healthも未成立

このため、今回の失敗をNode test、Python test、typecheck、Worker dry-run、Local APIのアプリケーション回帰失敗とは判定しない。filesystem/runtime配置の受入ブロッカーとして扱う。

### 10.3 現時点の総合判定

PC移行は **実装・文書化フェーズ完了、最終受入ブロック中** とする。

source正本、可変データ正本、secret境界、Cloudflare environment安全策、runbookまでは確定している。一方、WSLから`/mnt/c`上のLinux用`node_modules`を再生成・使用する現在の依存配置は、最終受入で安定性を証明できなかった。

したがって、移行完了とはまだ判定しない。

### 10.4 次回の再開地点

次回はタスク9を直接再試行せず、先に以下を行う。

1. `/mnt/c` EIOの再現条件と一時障害か構成依存かを切り分ける。
2. source正本をWindows側に維持したまま、`node_modules`と必要に応じて`.venv`をWSL native filesystemへ分離する構成を再評価する。
3. 採用構成をrunbookと移行資料へ反映する。
4. その構成でタスク9を最初から再実行する。
5. タスク9が成功した後、移行を完了判定し、通常開発のクリティカルパスである`I0-002`へ戻る。

残作業は `docs/REPORT_REMAINING_WORK_AFTER_WSL_MIGRATION_CHECKPOINT_2026-09-21.md` を正として管理する。


## 11. 2026-09-22 MIG-09A〜MIG-09D 更新

### 11.1 MIG-09A: /mnt/c EIO切り分け

正式証跡:

- `docs/evidence/mig09a/20260921T092425Z/diagnostic.log`
- `docs/evidence/mig09a/20260921T092425Z/summary.tsv`

WSL restart後の修正版診断では以下が全てPASSした。

- source通常read
- repeated source read
- `/mnt/c` small I/O
- WSL native small I/O
- `/mnt/c` isolated `npm ci`
- WSL native isolated `npm ci`
- heavy I/O後のsource read

初回最終受入で観測したEIOは事実として保持するが、再現条件は得られなかったためMIG-09Aは完了とした。

### 11.2 MIG-09B: runtime dependency配置決定

Accepted構成:

- source正本: `/mnt/c/Users/Y/Projects/codex_work/OrderScope`
- Node dependency: source-local `node_modules` を維持
- Python project environment: `${HOME}/.local/share/orderscope/venv`
- local mutable data: `${HOME}/data/orderscope/local`
- local Wrangler persistence: `${HOME}/data/orderscope/wrangler-state`

Node側は、MIG-09AでEIOが再現せず、ESM module resolutionへ新しい複雑性を追加しないため現配置を維持した。Python側は `UV_PROJECT_ENVIRONMENT` でWSL nativeへ分離した。

`NODE_PATH`、source symlink、bind mountは非採用。EIOが再現した場合はgenerated WSL-native runtime mirrorを第一fallbackとして評価する。

### 11.3 MIG-09C: wrapper / path実装

`scripts/run-local-wsl.sh` を更新し、以下を実装した。

- `ORDERSCOPE_PYTHON_ENV`
- `UV_PROJECT_ENVIRONMENT`
- default Python env: `${HOME}/.local/share/orderscope/venv`
- WSL native filesystem validation
- source checkout内Python envの拒否
- unexpected active `VIRTUAL_ENV` の拒否
- legacy source-local `.venv` のwarning
- `sync` subcommand
- `env` subcommandへのPython environment表示

ローカル最終検証:

- Python 3.13.15
- Python tests: **696 passed**
- `npm ci`: 成功、EIO再発なし
- `import("miniflare")`: PASS
- Node tests: **199 passed / 0 failed**
- TypeScript typecheck: PASS
- Git working tree: clean

従ってMIG-09Cは完了。

### 11.4 MIG-09D: 文書整合

以下を最終runtime layoutへ更新した。

- `README.md`
- `docs/RUNBOOK_LOCAL_ENVIRONMENT_WSL_WINDOWS_2026-09-21.md`
- 本移行実施レポート

文書上のPython dependency構築入口は `bash scripts/run-local-wsl.sh sync` に統一した。Python testは `bash scripts/run-local-wsl.sh pytest -q`、Python runtime確認はwrapper経由で行う。

source-local legacy `.venv` は移行期間中のrollback用残置を許可するが、runtimeとしては使用しない。MIG-09Eの最終受入完了後に削除可否を判断する。

### 11.5 現時点の総合判定

PC移行は **MIG-09Dまで完了、MIG-09E最終受入待ち**。

MIG-09Eでは、最新runbookの入口から次を再検証する。

1. source / data hash・path境界
2. `uv lock --check`
3. wrapper経由 `sync`
4. `npm ci`
5. Node tests
6. typecheck
7. Python tests
8. Wrangler deploy dry-run
9. Local API health
10. Git working tree / secret / runtime dependency非追跡

MIG-09E成功後にMIG-09F Git最終確認へ進む。
