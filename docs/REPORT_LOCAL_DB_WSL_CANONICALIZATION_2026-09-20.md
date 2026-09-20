# OrderScope ローカルDBのWSL正本化整理レポート

作成日: 2026-09-20（Asia/Tokyo）
対象: `REPORT_LOCAL_ENVIRONMENT_MIGRATION_REMAINING_TASKS_2026-09-20.md` のタスク5

## 1. 結論

現行構成では、Windows側source workspaceが正式な編集・実行対象であり、`var/` と `.wrangler/state/` もWindows側sourceに紐づいている。したがって、現状のWindows側を「置いてあるだけ」とみなすのは正確ではない。

WSL側 `/home/y/code/OrderScope` は、現行文書上は退避・比較用コピーであり、編集・実行しない扱いである。両方のコピーの確認対象ファイルは今回の調査時点で同一SHA-256だったが、これは内容が同じという意味にとどまり、WSL側が正本であることを意味しない。

希望する運用にする場合は、次の2つの正本を分離する。

- Git管理対象のsource正本: Windows側 `/mnt/c/Users/Y/Projects/codex_work/OrderScope`
- Git管理外の可変データ・ローカルDB正本: WSL native filesystem上の専用data root

`/home/y/code/OrderScope` のcheckout内をそのままDB正本にすることも可能だが、sourceの退避コピーと可変DBが再び結び付くため、専用data rootをcheckout外に置く方が運用上明確である。

## 2. 現状確認

| 対象 | 現行の位置付け |
|---|---|
| `/mnt/c/Users/Y/Projects/codex_work/OrderScope` | Codex Desktopが編集・保存し、WSLコマンドをここから実行する正式source workspace |
| `/mnt/c/Users/Y/Projects/codex_work/OrderScope/var` | 現行運用で使われるGit除外の可変データroot |
| `/mnt/c/Users/Y/Projects/codex_work/OrderScope/.wrangler/state` | 現行運用で使われるlocal Wrangler/D1状態。SQLite本体、WAL、SHMを含む |
| `/home/y/code/OrderScope` | 移行時の退避・比較用コピー。現行文書では編集・実行しない |
| `/home/y/code/OrderScope/var`、`.wrangler/state` | Windows側のコピーと同じ内容を持つが、現行方針では非稼働 |

根拠は次のとおり。

- 移行残作業レポートは、Windows側sourceを正式workspace、WSL側を退避・比較用コピーとしている。
- READMEも、WSL側コピーから編集・実行しないこと、および`var/`と`.wrangler/state/`を同時に開かないことを記載している。
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

上記は配置方針の確認であり、このレポート作成時点ではdata移動、環境変数の永続設定、起動コマンドの変更は実施していない。

## 4. 一本化の移行手順

1. Uvicorn、local Wrangler/Miniflare、Pythonの書き込みCLIを停止し、SQLiteへの書き込みがない状態にする。
2. WSL native filesystem上に専用data rootを作成する。
3. 現在の実行対象であるWindows側の`var/`を移し、必要なlocal Wrangler状態を`.wrangler/state/`全体から移す。SQLite本体、`-wal`、`-shm`を分離しない。
4. 移行前後でファイル一覧、サイズ、SHA-256を比較する。移行元のWindows側コピーと既存のWSL退避コピーが同一でも、どちらを採用したかをmanifestに記録する。
5. WSL shellの起動設定またはプロジェクト用run scriptで、`ORDERSCOPE_DATA_ROOT`を専用data rootへ明示する。local Wranglerには`--persist-to`を毎回指定する。
6. Windows側sourceをカレントディレクトリにしても、可変データへの書き込み先がWSL native rootになることを確認する。
7. SQLite integrity check、catalog migration確認、Parquet/manifestのhash確認、Local API health、local Wranglerの起動確認を行う。
8. 検証完了後、Windows側`var/`と`.wrangler/state/`は稼働中の正本ではなく、移行退避として扱う。WSL側checkout `/home/y/code/OrderScope`も実行対象には戻さない。
9. 退避コピーの削除や旧dataの整理は、正本確認と別の明示的な作業として行う。今回の整理では削除しない。

## 5. 注意点

`ORDERSCOPE_DATA_ROOT`を設定すれば全ての書き込みが自動で移るわけではない。現状、一部の収集スクリプトには`Path("var/...")`のようなrepository-relative pathが残っているため、一本化を完了するには次のいずれかが必要である。

- それらのスクリプトを設定済みdata rootから出力するよう修正する。
- それらを呼び出す運用ラッパーで、WSL data rootへ明示的に出力する。
- 対象スクリプトを、source checkout内の`var/`を使わないことを検証した後に運用対象へ含める。

この確認を省くと、PythonアプリはWSL側DBを参照していても、補助スクリプトだけがWindows側`var/`へ新しいデータを書き、二重化が再発する。

## 6. タスク5の完了条件案

- sourceの正本と可変データの正本が別々に文書化されている。
- `ORDERSCOPE_DATA_ROOT`がWSL native filesystemの絶対pathに設定されている。
- local Wranglerのpersistenceが`--persist-to`でWSL native filesystemへ固定されている。
- Windows側source内の`var/`および`.wrangler/state/`が稼働中のDB正本ではない。
- `var/`へ直接書く補助スクリプトがない、または全てWSL data rootへ明示的に向くことを確認している。
- SQLite本体、WAL、SHMをWindows側とWSL側の複数copy/processから同時に開かない。
- 移行manifest/hashとrestore/health検証が成功している。

DBの世代管理とバックアップ方式については、別レポート [`REPORT_RESTIC_LOCAL_DB_GENERATION_FOLLOWUP_2026-09-20.md`](REPORT_RESTIC_LOCAL_DB_GENERATION_FOLLOWUP_2026-09-20.md) に分離した。resticの導入・初回snapshot・運用設定は今回実施しない。
