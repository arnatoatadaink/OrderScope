# OrderScope ローカルDBのWSL正本化整理レポート

作成日: 2026-09-21（Asia/Tokyo、実施結果追記）
対象: `REPORT_LOCAL_ENVIRONMENT_MIGRATION_REMAINING_TASKS_2026-09-20.md` のタスク5

## 1. 結論

Windows側source workspaceを編集・保存する構成は維持しつつ、可変データとlocal Wrangler stateをWSL native filesystemへ移行した。現在の正本は次の2つに分離されている。

- Git管理対象のsource正本: `/mnt/c/Users/Y/Projects/codex_work/OrderScope`
- Git管理外の可変データ正本: `/home/y/data/orderscope/local`
- Git管理外のlocal Wrangler/D1 state正本: `/home/y/data/orderscope/wrangler-state`

移行manifestは `/home/y/data/orderscope/migration-manifest-20260920T225347Z.txt` に保存した。Windows側の `var/` と `.wrangler/state/` は移行元の退避として残しているが、稼働中の正本ではない。`/home/y/code/OrderScope` も編集・実行しない。

## 2. 現状確認

| 対象 | 現行の位置付け |
|---|---|
| `/mnt/c/Users/Y/Projects/codex_work/OrderScope` | Codex Desktopが編集・保存し、WSLコマンドをここから実行する正式source workspace |
| `/home/y/data/orderscope/local` | `ORDERSCOPE_DATA_ROOT`。Pythonのlocal data正本 |
| `/home/y/data/orderscope/wrangler-state` | `wrangler dev --local --persist-to` のlocal Wrangler/D1 state正本。SQLite本体、WAL、SHMを含む |
| `/mnt/c/Users/Y/Projects/codex_work/OrderScope/var` | 移行元の退避。稼働中の正本ではない |
| `/mnt/c/Users/Y/Projects/codex_work/OrderScope/.wrangler/state` | 移行元の退避。稼働中の正本ではない |
| `/home/y/code/OrderScope` | 移行時の退避・比較用コピー。現行文書では編集・実行しない |
| `/home/y/code/OrderScope/var`、`.wrangler/state` | Windows側のコピーと同じ内容を持つが、現行方針では非稼働 |

根拠は次のとおり。

- 移行残作業レポートとREADMEは、Windows側sourceを編集・保存対象、WSL native data rootを可変データの正本としている。
- READMEと `scripts/run-local-wsl.sh` は、Pythonの `ORDERSCOPE_DATA_ROOT` とWranglerの `--persist-to` を外部rootへ固定している。
- `.gitignore`では`var/`と`.wrangler/`がGit除外である。
- Python側の既定値はrepository-relative `var`だが、`ORDERSCOPE_DATA_ROOT`で外部絶対pathを指定できる。
- ADRは、永続SQLite/DuckDB/Parquet/raw/import/lock stateをWSL native filesystemに置き、WSL2を可変データのauthoritative environmentとする方針である。

## 3. 推奨する最終配置

例として、次のようにsourceとデータを分離する。

```text
/mnt/c/Users/Y/Projects/codex_work/OrderScope/  # Git/source正本
  src/
  analysis/
  migrations/
  ...

/home/y/data/orderscope/                         # WSL/可変データ正本
  local/                                         # ORDERSCOPE_DATA_ROOT
    catalog/
    raw/
    datasets/
    locks/
    temporary/
    d1-custody/
  wrangler-state/                                # wrangler --persist-to の指定先
    v3/
```

`local/`と`wrangler-state/`は同じWSL filesystem内に置くが、ライフサイクルが異なるため別directoryにする。Python local analysisのDB・Parquet・raw dataは`ORDERSCOPE_DATA_ROOT=/home/y/data/orderscope/local`に集約し、local Wrangler/D1 emulator stateは`--persist-to /home/y/data/orderscope/wrangler-state`で分離する。

Wranglerの現在のproject-local版には、local persistenceの既定値を`.wrangler/state`から変更する`--persist-to`がある。したがって、local Wranglerを起動するコマンドは、例えば次の形に固定できる。

```bash
export ORDERSCOPE_DATA_ROOT=/home/y/data/orderscope/local
wrangler dev --local --persist-to /home/y/data/orderscope/wrangler-state
```

`scripts/run-local-wsl.sh` は上記2つのpathを作成・WSL native filesystemか検証し、Python APIには `ORDERSCOPE_DATA_ROOT`、Wranglerには `--persist-to` を設定する。`npm run dev` もこのラッパーを使用する。

## 4. 実施した移行と検証

1. Uvicorn、local Wrangler/Miniflare、Pythonの書き込みCLIが停止していることを確認した。
2. Windows側 `var/` と `.wrangler/state/` を `/home/y/data/orderscope/local` と `/home/y/data/orderscope/wrangler-state` へコピーした。SQLite本体、`-wal`、`-shm` は分離していない。
3. 移行前後のファイル一覧とSHA-256を比較し、`var/` 14ファイル、Wrangler state 9ファイルの一致を確認した。
4. 全SQLiteについて `PRAGMA integrity_check` が `ok` となった。
5. Windows側sourceをcwdにした `bash scripts/run-local-wsl.sh api --port 8000` で、Local API `/health` がHTTP 200、`bind_host=127.0.0.1`となった。
6. `bash scripts/run-local-wsl.sh wrangler --port 8787` でlocal Wranglerを起動し、Worker `/health` がHTTP 200となった。起動後のobservability stateを含むSQLite/WAL/SHMは `/home/y/data/orderscope/wrangler-state` 配下に生成された。
7. Windows側 `var/` と `.wrangler/state/`、および `/home/y/code/OrderScope` は稼働中の正本として使用しない。削除は別途判断する。

## 5. 注意点

収集・検証スクリプトに残っていたrepository-relative `Path("var/...")` は、`load_local_config(os.environ).data_root` 配下へ出力・参照するよう修正した。`rg`で `scripts/` と `analysis/app/` の直接参照が残っていないことを確認した。未設定時のPython既定値はテスト互換性のため `var/` のままだが、運用時はラッパーが外部絶対pathを必ず設定する。

## 6. タスク5の完了判定

- sourceの正本と可変データの正本が別々に文書化されている。
- `ORDERSCOPE_DATA_ROOT`がWSL native filesystemの絶対pathに設定されている。
- local Wranglerのpersistenceが`--persist-to`でWSL native filesystemへ固定されている。
- Windows側source内の`var/`および`.wrangler/state/`が稼働中のDB正本ではない。
- `var/`へ直接書く補助スクリプトがない、または全てWSL data rootへ明示的に向くことを確認している。
- SQLite本体、WAL、SHMをWindows側とWSL側の複数copy/processから同時に開かない。
- 移行manifest/hash、SQLite integrity、Local API health、local Wrangler health検証が成功している。

判定: **完了**。resticによる世代管理・バックアップは、当初の境界どおり別タスクとして未実装である。

DBの世代管理とバックアップ方式については、別レポート [`REPORT_RESTIC_LOCAL_DB_GENERATION_FOLLOWUP_2026-09-20.md`](REPORT_RESTIC_LOCAL_DB_GENERATION_FOLLOWUP_2026-09-20.md) に分離した。resticの導入・初回snapshot・運用設定は今回実施しない。
