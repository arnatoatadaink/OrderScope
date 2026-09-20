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


## 7. 追加調査結果とタスク5の残作業整理（2026-09-21）

タスク5を閉じる前に、Git上の実装を対象に、`ORDERSCOPE_DATA_ROOT` と repository-relative な `var/` 参照の関係を追加確認した。

### 7.1 確認済みの設定経路

Pythonローカル実行系の共通設定は `analysis/app/orderscope_local/config.py` にまとまっており、次の境界が存在する。

- 環境変数: `ORDERSCOPE_DATA_ROOT`
- 未指定時の既定値: `Path("var")`
- CLI側の主要な書き込み経路は `load_local_config(os.environ)` から取得した `config.data_root` を使用する

`analysis/app/orderscope_local/cli.py` では、ニュースrecall候補、label template、finalize出力、scheduler lock、replay、temporary news deletionなどが `config.data_root` を利用している。この系統は `ORDERSCOPE_DATA_ROOT=/home/y/data/orderscope/local` を設定すれば、Windows側sourceをカレントディレクトリにしてもWSL native filesystemへ向けられる。

したがって、アプリ本体側の主要経路は「設定対応済み」と分類する。

### 7.2 repository-relative `var/` が残る確認済み箇所

次の補助スクリプトは、共通設定を経由せず repository-relative な `var/` を直接参照していることを確認した。

| ファイル | 現在の参照 | 分類 |
|---|---|---|
| `scripts/a0_002_collect_alpaca_daily.py` | `Path("var/cross-market/a0-002/alpaca-daily-observations.json")` | コード修正またはdata root経由化が必要 |
| `scripts/a0_002_collect_official_macro.py` | `Path("var/cross-market/a0-002/...")` をinput/outputに使用 | コード修正またはdata root経由化が必要 |
| `scripts/r0_008_validate_first_remote_custody.py` | `Path("var/d1-custody/r0-007-first-remote")` | 検証用読み取りだが、正本一本化後はdata root基準へ合わせる必要あり |

この3ファイルは、`ORDERSCOPE_DATA_ROOT` を設定するだけでは参照先が変わらない。Windows側source配下の `var/` を残したまま運用すると、ローカルアプリはWSL data rootを使用する一方で、補助スクリプトだけがWindows側 `var/` を読み書きし、二重化が再発する可能性がある。

### 7.3 追加作業の優先順位

タスク5の残作業は次の順序で進める。

1. **直接 `var/` 参照の全件確認**
   - `scripts/`
   - `analysis/app/`
   - 必要に応じて `analysis/tests/`
   - `src/` はWorker側でありPython local data rootとは別系統だが、local artifact pathを持つ箇所がないか確認する。
2. **実行時書き込みと検証専用読み取りを分離**
   - 実運用で書き込むものは `ORDERSCOPE_DATA_ROOT` へ寄せる。
   - fixtureや固定検証artifactのみを参照するものは、Git管理対象かdata root対象かを明示する。
3. **A0-002系collectorのdata root対応**
   - `analysis/config/...` のmanifestはGit/source側に残す。
   - 生成観測JSONは `config.data_root / "cross-market" / "a0-002" / ...` へ移す。
   - Alpaca collectorとofficial macro collectorのinput/outputが同じdata rootを使うことを確認する。
4. **R0-008 custody検証のdata root対応**
   - `var/d1-custody/...` の固定rootを、共通data rootまたは明示的CLI引数へ置き換える。
   - 過去artifactのgeneration ID確認ロジックは変更しない。
5. **Wrangler persistenceの固定**
   - local Wranglerは毎回 `--persist-to /home/y/data/orderscope/wrangler-state` を付けるか、同等のproject run scriptで固定する。
   - `.wrangler/state/` を再び稼働正本として使用しない。
6. **旧Windows側可変データの非稼働化確認**
   - `/mnt/c/.../OrderScope/var/`
   - `/mnt/c/.../OrderScope/.wrangler/state/`
   を残す場合も、移行退避としてのみ扱い、新規更新が発生しないことを確認する。
7. **最終検収**
   - `ORDERSCOPE_DATA_ROOT` を設定した状態でLocal API、collector、scheduler/quality系CLIを実行する。
   - WSL data root側だけに新規ファイル・更新時刻が発生することを確認する。
   - Windows側 `var/` および `.wrangler/state/` に意図しない更新がないことを確認する。
   - SQLite/DuckDB/Parquet/manifest/hashとlocal Wrangler stateの整合を再確認する。

### 7.4 実装方針

現時点では、すべてのpathを独立した新環境変数へ分割する必要はない。

基本方針は次のとおりとする。

- Git管理対象・静的設定: repository-relative pathを維持
- 可変ローカルデータ: `ORDERSCOPE_DATA_ROOT` 配下
- Wrangler local persistence: `--persist-to` で専用WSL path
- 一時的な検証artifact: 性質に応じてdata rootまたは明示的CLI引数

これにより、source正本と可変データ正本の二重管理を避けつつ、既存の `LocalConfig` 境界を再利用できる。

### 7.5 更新後のタスク5完了判定

タスク5は、従来の完了条件に加えて次を満たした時点で完了とする。

- 実運用で repository-relative `var/` へ直接書き込むコードが残っていない。
- A0-002 collector群が同一のWSL data rootを使用する。
- R0-008等の検証スクリプトが旧Windows側 `var/` を稼働正本として要求しない。
- `ORDERSCOPE_DATA_ROOT=/home/y/data/orderscope/local` を設定した状態で主要ローカルCLIが動作する。
- local Wranglerが `/home/y/data/orderscope/wrangler-state` を唯一のlocal persistenceとして使用する。
- Windows側 `var/` と `.wrangler/state/` に新規runtime書き込みが発生しないことを検収で確認する。

現時点の判定は **タスク5継続中** とする。data root抽象化そのものは既に存在するため、大規模な設計変更は不要であり、残作業の中心は補助スクリプトのpath統一と移行後検収である。
