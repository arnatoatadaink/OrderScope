# OrderScope Windows source + WSL 実行環境 runbook

作成日: 2026-09-21（Asia/Tokyo）

この手順は、Codex Desktopで編集するWindows側sourceと、WSLで実行するOrderScopeのローカル環境を新しい担当者が再現するための運用手順である。移行検証用の完全コピーを実行対象へ戻したり、Windows nativeのPython/Nodeを混在させたりしない。

## 1. 固定された役割とpath

| 用途 | 固定値・方針 |
|---|---|
| 編集・保存するsource | `/mnt/c/Users/Y/Projects/codex_work/OrderScope` |
| Python/Node/Wranglerの実行 | WSLからsource workspaceをcwdにして実行 |
| Node.js | `.nvmrc`の`24.21.0`を`nvm use`で選択 |
| Python | `uv`管理のPython `>=3.13,<3.14`。project environmentは `${HOME}/.local/share/orderscope/venv` |
| Pythonの可変データ | `${HOME}/data/orderscope/local` |
| local Wrangler persistence | `${HOME}/data/orderscope/wrangler-state` |
| 移行検証用の退避copy | `/home/y/code/OrderScope`。保持中は編集・実行しない |

`${HOME}/data/orderscope`はWSL native filesystem上に置く。`var/`、`.wrangler/state/`、SQLiteのWAL/SHMをWindows側sourceとWSL側copyの複数箇所から同時に開かない。

## 2. WSL shellの開始と依存関係の構築

新しいshellを開くたびに、source workspaceへ移動し、`.nvmrc`を読み込ませる。

```bash
cd /mnt/c/Users/Y/Projects/codex_work/OrderScope
source "$HOME/.nvm/nvm.sh"
nvm use

node --version
test "$(node -p 'process.platform')" = linux
uv --version

uv lock --check
bash scripts/run-local-wsl.sh sync
bash scripts/run-local-wsl.sh python -c 'import sys; print(sys.version); print(sys.executable)'
npm ci
```

期待値はNode.js `v24.21.0`、Linux runtime、Python `3.13.x`である。Nodeの `node_modules` はWindows側source配下に生成されるLinux/WSL用dependencyとして維持する。Python project environmentはWindows側source配下へ生成せず、wrapperが `UV_PROJECT_ENVIRONMENT=${HOME}/.local/share/orderscope/venv` を設定する。Windows nativeのPythonまたはNodeから起動しない。

`uv lock --check`が失敗した場合や、`run-local-wsl.sh sync`後にlockfileが変更された場合は、実行を進めず差分を確認する。`npm ci`はNode.js 24を選択した後に実行する。source直下にlegacy `.venv` が残っている場合、wrapperはwarningを出すが使用しない。異なる `VIRTUAL_ENV` が既にactivateされている場合はfail-closedで停止する。

## 3. ローカルデータの初回移行

既存のWindows側`var/`と`.wrangler/state/`を初めてWSL native data rootへ移す場合だけ実行する。移行前にLocal APIとlocal Wranglerなど、可変データを書き込むprocessを停止する。

```bash
cd /mnt/c/Users/Y/Projects/codex_work/OrderScope
bash scripts/migrate-local-data-to-wsl.sh
bash scripts/run-local-wsl.sh env
```

移行scriptは、移行先が空でない場合、source checkout内を指定した場合、WSL native filesystemでない場合に停止する。manifestは`${HOME}/data/orderscope/migration-manifest-*.txt`へ作成される。secret値をmanifestへ追加しない。

通常運用では、移行後のsource側`var/`と`.wrangler/state/`を稼働中のDB正本として使用しない。data rootを変更する必要がある場合は、`ORDERSCOPE_DATA_BASE`、`ORDERSCOPE_DATA_ROOT`、`ORDERSCOPE_WRANGLER_PERSIST_TO`へsource checkout外の絶対WSL pathだけを指定する。

## 4. 日常のローカル実行

Python Local APIは、WSL shellで次のように起動する。

```bash
bash scripts/run-local-wsl.sh api --port 8000
```

別のWSL shellからhealthを確認する。

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

local Workerはlocal persistenceをWSL native data rootへ固定して起動する。

```bash
nvm use
npm run dev -- --port 8787
```

別のWSL shellからWorker healthを確認する。

```bash
curl --fail --silent --show-error http://127.0.0.1:8787/health
```

直接wrapperを使う場合は、同じ動作になる。

```bash
bash scripts/run-local-wsl.sh wrangler --port 8787
```

`npm run dev`はlocal Wrangler専用であり、remote environmentの指定は要求しない。`bash scripts/run-local-wsl.sh env`で、source root、Python data root、Wrangler persistence path、`ORDERSCOPE_PYTHON_ENV`、`UV_PROJECT_ENVIRONMENT`を実行前に確認できる。

## 5. テストと最終受入の入口

Node.js 24を選択したWSL shellで、次を実行する。

```bash
cd /mnt/c/Users/Y/Projects/codex_work/OrderScope
source "$HOME/.nvm/nvm.sh"
nvm use

uv lock --check
bash scripts/run-local-wsl.sh sync
npm ci
npm test
npm run typecheck
bash scripts/run-local-wsl.sh pytest -q
```

Wranglerのdeploy dry-runは、対象environmentを必ず明示する。

```bash
npm run deploy:check -- --env live-canary
```

`--env`の代わりにshell単位で`CLOUDFLARE_ENV=live-canary`を設定できるが、両方を指定する場合は同じ値にする。

```bash
CLOUDFLARE_ENV=live-canary npm run deploy:check
```

最終受入でLocal APIも確認する場合は、上記のAPIを起動した状態で次を実行する。

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

## 6. Wranglerのremote操作

Wranglerの認証確認は、既存のWSL Wrangler OAuth profileまたは別途承認された短期・最小権限credentialを使う。認証情報をコマンド引数、ログ、manifest、reportへ書かない。

read-only確認の例:

```bash
npx wrangler whoami
npx wrangler d1 info STATE_DB --env live-canary
npx wrangler deployments list --env live-canary
```

remote deployを行う場合も対象environmentを明示する。deployはremote状態を変更するため、承認された変更時間帯でだけ実行する。

```bash
npm run deploy -- --env live-canary
```

`npm run deploy`と`npm run deploy:check`は、environment未指定または`--env`と`CLOUDFLARE_ENV`の不一致を実行前に拒否する。直接`npx wrangler`でremote D1などを操作する場合も、同じ対象名の`--env <name>`を付ける。environmentが分からない状態でdefault environmentへフォールバックしない。

## 7. secretの境界

| 用途 | 変数名 | 保管・使用場所 |
|---|---|---|
| Worker provider secret | `ALPACA_API_KEY` / `ALPACA_API_SECRET` | Cloudflare Worker Secret binding。local Worker確認時のignored `.env`入力 |
| Python local adapter | `ORDERSCOPE_SECRET_ALPACA_API_KEY` / `ORDERSCOPE_SECRET_ALPACA_API_SECRET` | WSL process environmentのみ |
| Wrangler管理 | `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` | Wrangler管理操作のみ。Worker bindingには渡さない |

Worker用の`ALPACA_*`からPython用の`ORDERSCOPE_SECRET_*`への自動変換はない。Python adapter確認で同じcredentialを使う必要がある場合だけ、意図した一つのWSL processへ明示的に渡し、ファイルへ再保存しない。値をshellの位置引数、ログ、manifest、reportへ出さない。

`.env`と`.env.cloudflare`はGit非追跡であり、通常の移行manifestへ含めない。WSL native filesystem上にdotenvを保持する場合はmode `600`にする。`/mnt/c`はdrvfsのため、WSLから表示されるmode `777`をnative secret storeの権限確認として扱わない。

```bash
git status --short --ignored .env .env.cloudflare
```

上記確認ではsecret値を表示しない。`.env.cloudflare`を`wrangler types`の入力やWorker bindingへ渡さない。

## 8. 失敗時の停止基準

- `npm ci` またはNode dependency大量I/O中に `EIO` / `Input/output error` が再発した場合は、その場で停止してログを保存する。MIG-09Aを再オープンし、`/mnt/c` とWSL nativeの比較を再実行する。再現差が得られた場合はgenerated WSL-native runtime mirrorを第一fallbackとして評価する。
- `NODE_PATH`、source直下のWSL symlink、bind mountで一時回避しない。これらはMIG-09Bで非採用。


- `run-local-wsl.sh`がdata pathの絶対pathまたはWSL native filesystem違反で停止した場合は、source checkout内や`/mnt/c`へdataを作らず、`${HOME}/data/orderscope`を確認する。
- migration scriptが「移行先が空でない」と停止した場合は、既存dataを上書きせず、稼働中processとdata rootを調査する。
- deploy wrapperがenvironment未指定または不一致で停止した場合は、対象environmentを確認してから再実行する。
- `.nvmrc`、`uv.lock`、`package-lock.json`、移行manifestに予期しない変更が出た場合は、テストやdeployへ進まず差分を保存・確認する。

## 9. 運用開始チェックリスト

- [ ] Codex DesktopでWindows側sourceだけを開き、編集・保存する。
- [ ] WSL shellのcwdがWindows側sourceである。
- [ ] `nvm use`後のNode.jsが24.21.0、wrapper経由Pythonが3.13.xで、executableが `${HOME}/.local/share/orderscope/venv/bin/python` 配下である。
- [ ] Pythonとlocal Wranglerの可変data rootがWSL native filesystemにある。
- [ ] `/home/y/code/OrderScope`を編集・実行していない。
- [ ] remote Wrangler操作に`--env <name>`がある。
- [ ] secret値をGit、manifest、ログ、reportへ書いていない。

関連資料:

- `docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_REMAINING_TASKS_2026-09-20.md`
- `docs/REPORT_LOCAL_DB_WSL_CANONICALIZATION_2026-09-20.md`
- `docs/REPORT_LOCAL_WRANGLER_ENVIRONMENT_TASK_7_2026-09-21.md`
- `docs/REPORT_LOCAL_SECRET_BOUNDARY_TASK_8_2026-09-21.md`
