# OrderScope PC移行 残作業レポート

作成日: 2026-09-20（Asia/Tokyo）
対象: Windows側source + WSL実行環境構成への移行完了作業
関連文書: `REPORT_LOCAL_ENVIRONMENT_MIGRATION_EXECUTION_2026-09-20.md`

## 1. 現在の判定

依存関係の再構築と受入試験は完了している。現在の運用構成は、Codex DesktopがWindows側sourceを編集し、WSLからPython、Node.js、npm、uv、Wranglerを実行する方式である。

残作業は、実行環境の構築ではなく、バージョン固定、変更の確定、警告の評価、運用ルールの明文化、および退避コピーの整理である。

## 2. 配置方針

### 2.1 正式なsource workspace

```text
/mnt/c/users/y/projects/codex_work/orderscope
```

Codex Desktopから編集・保存するsource正本である。`src/`、`analysis/`、`scripts/`、`migrations/`、設定ファイル、lockfileを含む。可変データの正本はcheckout外のWSL native filesystemに分離した。

### 2.2 WSL実行環境

WSLからWindows側sourceをカレントディレクトリとして、依存関係のインストール、テスト、API起動、Wrangler操作を行う。

```text
/mnt/c/users/y/projects/codex_work/orderscope/.venv
/mnt/c/users/y/projects/codex_work/orderscope/node_modules
```

これらはLinux x86_64向けに生成された依存directoryであり、Windows native Python/Nodeから使用しない。

### 2.3 退避・比較用コピー

```text
/home/y/code/OrderScope
```

WSL側の完全コピーである。sourceの正式workspaceではなく、移行検証結果を保持する退避・比較用コピーとして、最終判断まで削除しない。

## 3. 残作業一覧

### 1. Node.js 24をプロジェクト単位で固定

現状、nvmにはNode.js 22.20.0と24.21.0が存在するが、共有defaultは別プロジェクトの影響で22系へ変わる可能性がある。OrderScopeには現在`.nvmrc`と`package.json`の`engines`指定がない。

実施内容:

- `.nvmrc`でNode.js 24系を指定する、または`package.json`へ`engines.node`を追加する。
- WSL shellでNode.js 24を選択する。
- `npm ci`、`npm test`、`npm run typecheck`、`npm run deploy:check`を再実行する。

完了条件:

- 新しいshellでもOrderScopeがNode.js 24系を選択できる。
- Node 24でNodeテスト199件が成功する。

### 2. `uv.lock`をレビューして確定

`pyproject.toml`に存在した`httpx2`依存を反映し、`uv.lock`に49行を追加済みである。

追加内容:

- `httpcore2 2.13.0`
- `httpx2 2.13.0`
- `httpx2-jsfetch 1.0`
- `truststore 0.10.4`

実施内容:

- lockfile差分をレビューする。
- 既存packageの意図しない更新・削除がないことを確認する。
- `uv lock --check`と`uv sync --locked`を実行する。

完了条件:

- lockfile差分がレビュー済みである。
- `uv lock --check`が成功する。
- sync後にlockfileが変更されない。

### 3. 移行資料とlockfileをGitに確定

現在の候補ファイル:

- `uv.lock`
- `MIGRATION_WSL2_LOCAL_STATE_2026-09-19.md`
- `MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256`
- `docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_WSL_TO_CODEX_DESKTOP_WINDOWS_2026-09-19.md`
- `docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_EXECUTION_2026-09-20.md`
- 本レポート

実施内容:

- lockfileと文書を同一commitにするか、lockfileと文書を分けるか決定する。
- secret、`.venv`、`node_modules`、cacheがcommit対象外であることを確認する。
- commit前に`git diff --check`とGit statusを確認する。

完了条件:

- 移行に必要なlockfileと資料がGitで確定している。
- secret値、依存directory、cacheが追跡されていない。

### 4. 実行場所を固定

運用上の役割分担を固定する。

| 操作 | 実行場所 |
|---|---|
| Codexでの編集・保存 | Windows側source |
| `uv sync`、`uv run` | WSL |
| `npm ci`、Nodeテスト | WSL |
| Local API | WSL |
| Wrangler、deploy dry-run | WSL |
| Windows native Python/Node実行 | 行わない |

完了条件:

- READMEまたは運用手順にこの役割分担を記載する。
- Windows nativeから`.venv`・`node_modules`を直接実行しない。

実施結果（2026-09-20）:

- README.mdの「Local environment operation boundary」に、Windows側sourceでの編集・保存、WSLでの依存関係構築・テスト・Local API・Wrangler実行、およびWindows nativeのPython/Node実行禁止を記載した。
- WSL側退避コピー `/home/y/code/OrderScope` は編集・実行せず、Windows側sourceを唯一の実行対象とする方針を明記した。

### 5. ローカルデータ・DBをWSL正本に一本化し、同時利用を防止（完了）

対象:

- `ORDERSCOPE_DATA_ROOT`配下のSQLite、DuckDB、Parquet、raw/import、lock
- local Wrangler/D1 emulatorのpersistence
- 移行前に存在するWindows側`var/`および`.wrangler/state/`

移行前はWindows側source workspaceの`var/`と`.wrangler/state/`が可変データの参照先だったため、source正本と可変データ正本を分離した。

- source正本: `/mnt/c/Users/Y/Projects/codex_work/OrderScope`
- 可変データ正本: `/home/y/data/orderscope/`、checkout外のWSL native filesystem
- Python local analysis: `ORDERSCOPE_DATA_ROOT=/home/y/data/orderscope/local`
- local Wrangler persistence: `wrangler dev --local --persist-to /home/y/data/orderscope/wrangler-state`

実施結果（2026-09-21）:

- 全書き込みprocessが停止していることを確認したうえで、Windows側の`var/`と`.wrangler/state/`をWSL data rootへコピーした。
- SQLite本体、`-wal`、`-shm`は一組として扱い、`/home/y/data/orderscope/migration-manifest-20260920T225347Z.txt`へmanifest/hashを保存した。
- source/targetの比較は`var/` 14ファイル、Wrangler state 9ファイルで一致し、全SQLiteの`PRAGMA integrity_check`が`ok`となった。
- `scripts/run-local-wsl.sh`で`ORDERSCOPE_DATA_ROOT=/home/y/data/orderscope/local`とWranglerの`--persist-to /home/y/data/orderscope/wrangler-state`を固定した。Local API healthはHTTP 200、Wrangler local Worker healthもHTTP 200となった。
- `Path("var/...")`を持っていた収集・検証スクリプト3本をdata root参照へ修正し、直接参照が残っていないことを確認した。
- Windows側とWSL側checkoutのデータは稼働中の正本として併用しない。旧コピーの削除は別途判断する。

完了条件・判定:

- source正本と可変データ正本が別々に文書化されている。
- `ORDERSCOPE_DATA_ROOT`がWSL native filesystemの絶対pathを指す。
- local Wranglerのpersistenceが`--persist-to`でWSL native filesystemへ固定されている。
- Windows側source内の`var/`および`.wrangler/state/`が稼働中のDB正本ではない。
- SQLite integrity、migration、manifest/hash、Local API health、必要なlocal Wrangler確認が成功する。
- SQLite本体、WAL、SHMを複数process・複数copyから同時に開かない。

タスク5は完了。resticによるDB世代管理・バックアップは、別レポート記載のとおり未実装の後続タスクとする。

整理の詳細は `docs/REPORT_LOCAL_DB_WSL_CANONICALIZATION_2026-09-20.md` に記録した。DB世代管理のrestic方針は `docs/REPORT_RESTIC_LOCAL_DB_GENERATION_FOLLOWUP_2026-09-20.md` に分離し、今回は未実装とする。

### 6. npm警告を調査

調査結果は `docs/REPORT_LOCAL_NPM_AUDIT_TASK_6_2026-09-21.md` に記録した。取得済みの監査応答で確認できた高severityは、次の2 advisory系統である。`undici@7.28.0`にはModerate advisoryも4件ある。

- `sharp@0.35.2`（`miniflare`経由）: GHSA-rgj7-g3m4-5g8c、High
- `undici@7.28.0`（rootの`miniflare@4`経由）: GHSA-4cwx-7wf7-3272、High
- `esbuild@0.28.1`、`workerd@1.20260730.1`、`workerd@1.20260828.1`: install-script未承認警告

実施内容:

- `npm audit`で依存経路と影響範囲を確認する。
- production bundleに含まれるかを確認する。
- install-scriptの承認が必要かを確認する。
- `npm audit fix`は差分と回帰試験を確認してから実施する。
- `npm audit fix --force`は、互換性レビューなしには実施しない。

完了条件:

- 原因package、依存経路、production bundleへの影響、対応方針が記録されている。
- install-scriptは対象とバージョンを`package.json`の`allowScripts`で固定している。
- 依存更新を行う場合はpackage-lock差分と全試験結果を記録する。今回は脆弱性修正の依存更新は未実施。

### 7. Wrangler environmentを明示

deploy dry-runは成功しているが、複数environmentが定義されているため、対象未指定の警告が出ている。

実施内容:

- `wrangler deploy --dry-run --env <対象>`を使用する。
- remote操作では`--env`または`CLOUDFLARE_ENV`を必須とする。
- `live-canary`等の対象名とCloudflare resource IDをread-onlyで再確認する。

完了条件:

- environment未指定の警告なしでdry-runできる。
- remote D1やWorkerを誤environmentへ向けない手順がある。

### 8. secret設定を用途別に確認

確認対象:

- `.env`
- `.env.cloudflare`
- `ORDERSCOPE_SECRET_ALPACA_API_KEY`
- `ORDERSCOPE_SECRET_ALPACA_API_SECRET`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

実施内容:

- 値を表示せず、必要な変数名だけ確認する。
- `.env`と`.env.cloudflare`がGit非追跡であることを確認する。
- WSL側ファイルのmode`600`を維持する。
- Worker用secretとPython local adapter用secretを混同しない。

完了条件:

- Local API、必要なPython adapter、Wrangler read-only確認が用途別に実行できる。
- secretがレポート、manifest、Git diffに含まれていない。

### 9. 移行後の最終受入を再記録

Windows側source + WSL実行の最終構成で、次を記録する。

```bash
sha256sum --check MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256
uv lock --check
uv sync --locked
npm ci
npm test
npm run typecheck
npm run deploy:check -- --env <対象>
uv run pytest -q
curl --fail --silent --show-error http://127.0.0.1:8000/health
```

完了条件:

- 移行データhashが全項目`OK`。
- Node 199件、Python 696件、typecheck、dry-run、healthが成功する。
- Local APIが`127.0.0.1`以外へbindしない。

### 10. WSL側完全コピーを保留

対象:

```text
/home/y/code/OrderScope
```

Windows側sourceでの継続運用、Git変更確定、最終受入が完了するまで保持する。保留中は検証用コピーとして参照するだけで、実行や編集には使用しない。

### 11. 保留期間後にWSL側コピーを整理

実施条件:

- Windows側sourceのcommitが確定している。
- 最終受入試験が成功している。
- 移行manifestと重要データのバックアップがある。
- `/home/y/code/OrderScope`を退避として保持する必要がないと判断できる。

削除する場合は、対象pathを明示してから行い、削除後にWindows側sourceが単独で正本になることを確認する。判断前に`/home/y`や広い範囲を対象にした削除は行わない。

### 12. 移行手順を運用文書化

最低限、以下を文書化する。

- Codex DesktopはWindows側sourceを開く。
- 依存関係のインストールと実行はWSLから行う。
- Node.js 24を選択してからnpmコマンドを実行する。
- Pythonコマンドはuv管理Python 3.13を使用する。
- `var/`と`.wrangler/state/`は単一copyだけを実行対象にする。
- remote Wrangler操作ではenvironmentを明示する。
- secretはGitと通常の移行manifestに含めない。

完了条件:

- 新しい担当者がこの手順だけで同じ構成を再現できる。
- Windows側sourceとWSL実行環境の境界が明確である。

## 4. 推奨実施順

次の順序で実施する。

1. Node.js 24を固定する。
2. lockfileをレビューし、`uv lock --check`を確認する。
3. Windows側source + WSL実行で依存再生成と全試験を実行する。
4. Wrangler environmentを明示したdry-runを実行する。
5. secret設定とGit非追跡を確認する。
6. npm警告を調査する。
7. 移行資料とlockfileをcommitする。
8. 運用手順を文書化する。
9. WSL側退避コピーを保留する。
10. 保留期間後に退避コピーの削除可否を判断する。

## 5. 移行完了判定

次をすべて満たした時点で移行を完了とする。

- Codexの編集対象がWindows側sourceに統一されている。
- WSLからWindows側sourceの依存関係とアプリケーションを再現可能に実行できる。
- Node.js 24とPython 3.13が固定されている。
- 移行manifest、lockfile、レポートがGitで確定している。
- Node/Python試験、型検査、Wrangler dry-run、Local API healthが成功している。
- secretと可変データの境界が維持されている。
- npm警告とWrangler environment警告の扱いが記録されている。
- WSL側退避コピーの保留・削除方針が決定されている。


## 6. 2026-09-21 時点の残存タスク整理

タスク5・6の完了を反映し、移行完了までの残作業を次のように整理する。

| タスク | 状態 | 今回の扱い |
|---|---|---|
| 1. Node.js 24固定 | 設定済み・最終検収待ち | `.nvmrc=24.21.0` は存在するため、タスク9で新shell・Node試験を再確認する |
| 2. `uv.lock`確定 | 概ね完了・最終検収待ち | タスク9で `uv lock --check` / `uv sync --locked` 後の無差分を確認する |
| 3. 移行資料とlockfileをGit確定 | 進行済み | 最終文書更新後のcommit確認をタスク9前後で実施する |
| 4. 実行場所固定 | 完了 | README記載済み |
| 5. ローカルデータ・DB WSL正本化 | 完了 | 追加作業なし。resticは別タスク |
| 6. npm警告調査 | 完了 | advisory、依存経路、bundle非包含、allowScripts、後続方針を記録済み |
| 7. Wrangler environment明示 | **次の実施対象** | remote操作のenv明示とresource誤操作防止を確定する |
| 8. secret用途別確認 | 未実施 | タスク7後に実施する |
| 9. 移行後の最終受入 | 未実施 | タスク7・8・12完了後の最終ゲート |
| 10. WSL側完全コピー保留 | 継続中 | 削除せず保持することが現在の正しい状態 |
| 11. 保留期間後のコピー整理 | 後工程 | 今回の移行完了条件から除外し、後日判断する |
| 12. 移行手順の運用文書化 | 一部完了 | タスク7・8の結果を反映して最終化する |

### 6.1 タスク6からの持越し

タスク6ではnpm警告の調査自体は完了したが、次の事項はタスク9の最終受入で再確認する。

- `npm test` が現行WSL runtimeで最後まで完走すること
- Node testの受入件数を現行実装に対して再記録すること
- `npm ci` の実行条件と、`/mnt/c` 配置に起因する `EPERM` が最終構成でブロッカーにならないこと
- `npm run typecheck` と `npm run deploy:check -- --env <対象>` が成功すること

これらはタスク6の未完了事項ではなく、移行全体の最終受入条件としてタスク9へ集約する。

### 6.2 移行完了までの推奨順序

```text
7. Wrangler environment明示
        ↓
8. secret用途別確認
        ↓
12. 運用文書を最終構成へ更新
        ↓
9. 最終受入
        ↓
移行完了

10. WSL退避copyは保留継続
11. 削除判断は移行完了後の別工程
```

したがって、次の実施対象は **タスク7** とする。
