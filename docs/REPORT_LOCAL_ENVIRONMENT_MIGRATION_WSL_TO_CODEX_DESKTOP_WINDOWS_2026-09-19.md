# OrderScope ローカル実装環境移行 Gap レポート

作成日: 2026-09-19（Asia/Tokyo）
対象: 現PCの WSL2 環境から、別PCの Codex Desktop を利用する Windows 環境への手動ファイル移行

## 1. 結論

推奨構成は、**別PCでも WSL2 を OrderScope の実行・可変データ保管環境として維持し、Codex Desktop はそのリポジトリを操作する開発クライアントとして利用する構成**である。

現行の受入済み ADR は WSL2 を唯一の Python 実行／writer と定義しており、Windows ネイティブ実行は未サポートである。ソースコード自体は概ねクロスプラットフォームだが、次の要素はそのまま Windows へ移せない。

- `.venv/`: 現PCの `/home/y/...` を指す絶対シンボリックリンクと Linux 用ネイティブパッケージを含む。
- `node_modules/`: Linux 用 `workerd`、`esbuild` 等を含む。
- Bash 運用スクリプト: `bash`、process substitution、`/tmp`、`curl` 等に依存する。
- 可変データ: ADR 上、SQLite／DuckDB／Parquet／ロック等は WSL ネイティブ filesystem に置く必要がある。
- 認証状態: Cloudflare の Wrangler ログイン／API token と各種 secret はリポジトリのコピーでは移行しない。

したがって、**リポジトリと必要なローカル成果物はコピーするが、仮想環境・依存ディレクトリ・認証セッションは移行先で再作成する**のが安全である。

## 2. 調査時点の現環境ベースライン

| 項目 | 現環境 |
|---|---|
| OS/runtime | WSL2、Linux `6.6.87.2-microsoft-standard-WSL2`、x86_64 |
| Node.js | `v24.15.0` |
| npm | `11.14.1` |
| Wrangler | `4.127.1`（project-local） |
| Python | `.python-version` は `3.13`、`pyproject.toml` は `>=3.13,<3.14` |
| uv | `0.11.21`、Linux x86_64 build |
| Node lock | `package-lock.json` あり |
| Python lock | `uv.lock` あり |
| Worker state | Cloudflare Worker + D1、`live-canary` 環境あり |
| Local API | FastAPI/Uvicorn、literal `127.0.0.1` のみ |
| 時刻 | 内部 UTC、market classification は `America/New_York`、表示は `Asia/Tokyo` |

移行前の回帰基準:

- `npm test`: 199 passed、0 failed
- `npm run typecheck`: 成功
- `UV_CACHE_DIR=/tmp/orderscope-uv-cache uv run pytest -q`: 696 passed
- `UV_CACHE_DIR=/tmp/orderscope-uv-cache uv lock --check`: **失敗**（`pyproject.toml` の `httpx2` が現行 `uv.lock` に未反映）

試験は成功しているが、Python lockの不整合は移行前の未解決事項である。`uv.lock` をレビュー付きで更新し、`uv sync --locked` と全試験を再実行した結果を、移行後の同一性判定に使用する。

## 3. Gap 一覧

| 領域 | 現状 | 移行先 Gap | 重要度 | 対応 |
|---|---|---|---|---|
| 実行境界 | WSL2 が唯一の Python runtime/writer | Windows native は ADR で明示的に非採用 | Critical | 新PCにも WSL2 を用意する。Windows native 化するなら別変更として ADR 改訂と全回帰を行う |
| Python | 3.13、uv、Linux用 `.venv` | `.venv` は絶対 symlink／native wheel を含み移植不能 | Critical | `.venv` をコピーせず、新環境で `uv sync --locked` |
| Python lock整合性 | `pyproject.toml` に `httpx2>=2.12,<3`、現行lockには未反映 | `uv sync --locked` が新環境で失敗する | Critical | 移行前に `uv lock` の差分をレビューし、lock更新後に全Python試験を再実行 |
| Node | Node 24、npm lock、Linux用 modules | `node_modules` のnative binaryはOS依存 | Critical | `node_modules` をコピーせず、新環境で `npm ci` |
| Shell | `scripts/*.sh` は Bash 前提 | PowerShell／cmd から直接は実行不能 | High | WSL Bash から実行。native Windows を選ぶ場合は PowerShell 化と二重保守が必要 |
| 可変データ | `ORDERSCOPE_DATA_ROOT`、既定 `var/` | Git除外のためリポジトリだけでは移らない | Critical | 停止後に選択したデータrootを別途コピーし、hash／manifestを検証 |
| Local D1 | `.wrangler/state/v3` に SQLite/WAL/SHM | Git除外。コピー時の同時更新やWAL分離は危険 | High | 通常は再生成。状態継続が必要なら Wrangler 停止後に `.wrangler/state` 全体を一括コピー |
| Remote D1 | ID は `wrangler.jsonc` にある | データ本体は Cloudflare 側でありPCコピー不要 | Low | 同じaccountへ再認証し read-only 確認。databaseを新規作成しない |
| Alpaca secrets | local `.env` と Cloudflare Worker Secrets | `.env` はGit除外、Worker Secret値はexport不能 | Critical | 安全な別経路で再設定。コピー先でファイル権限と非追跡を確認 |
| Cloudflare管理認証 | `.env.cloudflare` に管理用変数名、またはWrangler profile | token/OAuth sessionはPC依存 | Critical | 新PCで再ログイン、または最小権限tokenを安全に設定。リポジトリへ入れない |
| Local config | `ORDERSCOPE_DATA_ROOT` 等のprocess env | shell profile／ユーザーenvは自動移行しない | High | 新PCで明示的に再設定し、絶対パスを確認 |
| Filesystem | WSL native storageを運用用に要求 | NTFS、OneDrive、同期folderでlocking/atomic rename差 | Critical | 可変データはWSL ext4側に置く。同期folderをDB/data rootにしない |
| Path | `pathlib` 中心、一部文書／テストにPOSIX例 | drive letter、separator、case sensitivity差 | Medium | WSL構成なら影響を限定。native Windowsなら path/case/長いpathを追加検証 |
| localhost | `127.0.0.1` 固定 | Codex DesktopとWSL間の到達性はPC設定次第 | Medium | WSL内でhealth確認後、必要ならWindows側からも `127.0.0.1:8000` を確認。外部bindへ変更しない |
| 改行／実行bit | `.gitattributes` なし、shell scriptはGit上 `100644` | Windows Git のCRLF変換でBash scriptが壊れ得る | High | Git設定でLF維持を確認。`.sh` は `bash scripts/...` で実行する |
| Architecture | 現在 x86_64 | 新PCがARM64ならnative package差 | High | lockから対象artifactを再解決し全試験。バイナリdirectoryはコピーしない |
| Firewall/proxy/CA | 現PC設定に依存 | npm/uv/SEC/Alpaca/Cloudflare通信が遮断され得る | High | `npm ci`、`uv sync`、read-only API接続を個別確認。企業proxy/CAはsecretと分離 |
| Codex Desktop | 開発操作クライアント | Python/Node/uv/WSL/data/secretを自動移行する前提はない | High | ランタイム再構築を独立作業として実施し、Codex側のworkspace/sandbox許可を設定 |

## 4. 手動コピー対象

### 4.1 コピーするもの

1. リポジトリの追跡ファイル一式（`.git` を含めるか、別途cloneして同一commitをcheckoutする）。
2. 必要な場合のみ、Git除外の `var/` または実際の `ORDERSCOPE_DATA_ROOT`。
3. 継続が必要なローカル Miniflare/D1 状態がある場合のみ、停止後の `.wrangler/state/` 全体。
4. Git除外のローカル設定・secretは、通常のファイルコピーとは分けた安全な経路で移す。

現checkoutの `var/` には少なくとも以下の非追跡成果物がある。

- `benchmarks/n1-006/`: news candidates、labels、final benchmark
- `cross-market/a0-002/`: macro／Alpaca daily observations
- `d1-custody/`: custody/export manifest と NDJSON

これらはサイズが小さくても再現不能な手作業・受入証跡を含み得るため、依存directoryより優先して保全する。

### 4.2 コピーしないもの

- `.venv/`（約226 MB、現PCの絶対symlinkを含む）
- `node_modules/`（約416 MB、Linux native binaryを含む）
- uv/npm cache
- Codex Desktop の一時状態やsandbox cache
- Wranglerのログ／一時ファイル
- 使用を継続しない古いtoken

`.wrangler/state/` は「必ずコピー」ではない。local dev databaseの継続が必要な場合だけコピーし、それ以外はmigrationから再生成する。

## 5. Secret と認証の移行境界

現環境で確認できた**変数名のみ**は次のとおりであり、値は本調査で表示していない。

| 用途 | 変数名 |
|---|---|
| Worker/local Alpaca | `ALPACA_API_KEY`, `ALPACA_API_SECRET` |
| Local Python Alpaca | `ORDERSCOPE_SECRET_ALPACA_API_KEY`, `ORDERSCOPE_SECRET_ALPACA_API_SECRET` |
| Cloudflare管理 | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` |
| Local non-secret | `ORDERSCOPE_DATA_ROOT`, `ORDERSCOPE_LOG_LEVEL`, `ORDERSCOPE_SEC_USER_AGENT` |

注意事項:

- Worker Secrets はCloudflare側に残るため、同じWorkerを扱うだけなら再投入不要。ただし新PCの管理認証は別途必要である。
- Cloudflare管理tokenを `.dev.vars` や Worker binding にしない。
- tokenの状態が不明、または安全でない経路でコピーした場合は旧tokenをrevokeして作り直す。
- local Python adapterの変数名と Worker用の変数名は異なる。片方を設定しただけではもう片方の実行要件を満たさない。
- secretファイルをコピーする場合は、通常のUSB／共有folderに平文で長期残置しない。

## 6. 推奨移行手順

### Phase A — 現PCで凍結

1. Uvicorn、Wrangler dev、import、dataset publicationを停止する。
2. `git status --short --branch` と現在のcommitを記録する。
3. `uv lock --check` の現行失敗を解消する。lock差分をレビューし、`uv sync --locked` と696件のPython試験を再実行する。
4. `ORDERSCOPE_DATA_ROOT` の実値を確認する。未設定ならrepository-relative `var/` が既定である。
5. `var/`／外部data rootの対象ファイル一覧、サイズ、SHA-256 manifestを作る。
6. `.wrangler/state` を移す場合は、SQLiteの `.sqlite`、`-wal`、`-shm` を分離せずdirectory単位で扱う。
7. secretはデータmanifestに含めず、安全な別経路を選ぶ。

### Phase B — 新PCの基盤

1. WSL2 と対象Linux distributionを準備する。
2. WSL内に Git、Node.js 24系、npm、uv、CPython 3.13を用意する。
3. repositoryはWindows同期folderではなく、可能ならWSL native filesystemに配置する。
4. Codex Desktopから対象workspaceを開き、workspace書込みと必要なnetwork accessが許可されていることを確認する。
5. Gitの改行設定を確認し、`.sh` をLFで維持する。

### Phase C — ソースとデータ

1. repositoryを手動コピーするかcloneし、同一commit／branchであることを確認する。
2. `.venv` と `node_modules` がコピーされていた場合は使用せず、再作成対象として除外する。
3. data rootをWSL native pathへコピーし、移行前manifestとSHA-256を照合する。
4. `ORDERSCOPE_DATA_ROOT` を新しい絶対pathに設定する。
5. `.wrangler/state` を引き継ぐ場合は、全ファイルのコピー完了後に初めてWranglerを起動する。

### Phase D — 依存関係と設定の再作成

WSL内のrepository rootで実行する。

```bash
npm ci
uv sync --locked
./node_modules/.bin/wrangler --version
uv run python --version
```

ここでの `uv sync --locked` は、Phase Aでlock不整合を解消した後の `uv.lock` を前提とする。その後、non-secret環境変数とsecretを用途別に再設定する。Cloudflare操作が必要な場合は新PCで認証し、最初は `wrangler whoami` やsecret/databaseのlist等、read-only確認に限定する。

### Phase E — 受入検証

```bash
npm test
npm run typecheck
npm run deploy:check
uv run pytest -q
uv run orderscope serve
```

別terminalから以下を確認する。

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

合格条件:

- Worker testが199件以上、失敗0（件数変更時は差分をレビュー）。
- Python testが696件以上、失敗0（同上）。
- `uv lock --check` が成功し、`uv sync --locked` がlockfileを変更しない。
- typecheckとdeploy dry-runが成功。
- local APIが `127.0.0.1` だけで応答し、LAN向けbindを行わない。
- data manifest/hashが一致し、SQLite／DuckDBを複数OS/processから同時に開かない。
- remote D1のIDが既存resourceを指し、誤って新規databaseや別environmentへ接続していない。

## 7. Windows ネイティブ実行を選ぶ場合の追加作業

これは単なるPC移行ではなく、現行設計の変更である。少なくとも以下が必要になる。

1. `ADR_LOCAL_ANALYSIS_STACK_v0.1.md` の改訂。
2. Bash scriptsのPowerShell版またはクロスプラットフォームCLI化。
3. Windows上のPython 3.13用 DuckDB／PyArrow wheel、SQLite locking、atomic renameの検証。
4. NTFS上のcase sensitivity、long path、file permission、antivirusによるlockの検証。
5. `ORDERSCOPE_DATA_ROOT` のWindows path正規化とroot escape guardの全試験。
6. `.gitattributes` でLF方針を明文化。
7. localhost、Windows Firewall、proxy、certificate storeの検証。
8. WSL版とWindows版を併存させるなら、同じDB／DuckDB／Parquet rootを同時に開かない強制策。

この追加作業を実施しない限り、Windows nativeは「動く可能性がある構成」であり、受入済み・運用可能な構成ではない。

## 8. 未確定事項と移行前の判断点

| 判断点 | 推奨既定 |
|---|---|
| 新PCでWSL2を使うか | 使う |
| repository配置 | WSL native filesystem。Windows側配置は開発用途に限定 |
| `var/` を移すか | 移す。受入証跡・benchmarkを保全 |
| `.wrangler/state` を移すか | local D1継続が必要な場合のみ移す |
| remote D1をコピーするか | コピーしない。同じCloudflare resourceへ再認証 |
| secretをrepositoryと一緒にコピーするか | コピーしない。別経路で再設定 |
| Windows native対応を今回行うか | 行わない。別work itemとして扱う |

## 9. 主要な根拠ファイル

- `docs/ADR_LOCAL_ANALYSIS_STACK_v0.1.md`
- `analysis/config/README.md`
- `pyproject.toml`, `.python-version`, `uv.lock`
- `package.json`, `package-lock.json`
- `wrangler.jsonc`
- `.gitignore`
- `scripts/*.sh`
- `analysis/app/orderscope_local/config.py`
- `analysis/app/orderscope_local/cli.py`

## 10. 最終判定

**条件付き Go**。

移行前にPython lock不整合を解消したうえで、別PCにWSL2を再構築し、依存directoryを再生成し、data rootとsecretを明示的に移し、上記回帰試験を通すなら、アプリケーションコード変更なしで移行できる見込みが高い。Windows nativeへ直接移す場合は現行ADRとのGapがCriticalであり、今回の単純移行としては No-Go と判定する。
