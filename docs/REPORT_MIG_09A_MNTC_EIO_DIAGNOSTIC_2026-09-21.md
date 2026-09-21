# MIG-09A /mnt/c EIO diagnostic plan

作成日: 2026-09-21（Asia/Tokyo）
Status: active diagnostic procedure
親タスク: `MIG-09A` in `docs/REPORT_REMAINING_WORK_AFTER_WSL_MIGRATION_CHECKPOINT_2026-09-21.md`

## 1. 目的

タスク9最終受入で発生した `/mnt/c` の `EIO` について、アプリケーション回帰とfilesystem/runtime配置問題を分離し、MIG-09Bのruntime dependency配置判断に必要な再現条件を記録する。

MIG-09Aでは、Windows / NTFS / drvfs / security softwareの単一原因まで断定することを完了条件としない。少なくとも、通常read、小規模I/O、大量dependency展開、WSL native対照試験のどこで差が生じるかを記録する。

## 2. 既知の事実

2026-09-21のタスク9初回受入では以下を確認した。

- `/mnt/c/Users/Y/Projects/codex_work/OrderScope` 上の `npm ci` 中に多数の `EIO` が発生した。
- `node_modules` 配下だけでなく、その後repository直下の `package.json` / `pyproject.toml` のreadでもEIOを確認した。
- 同構成はそれ以前の受入でNode/Python tests、typecheck、Wrangler dry-run、Local API healthに成功した実績がある。
- よって現時点では「npm固有の不具合」とは確定しない。

## 3. 診断レイヤー

| Layer | 試験 | 目的 | repository変更 |
|---|---|---|---|
| A | source metadata /通常read | `/mnt/c` source参照自体の安定性 | なし |
| B | 2,000 file create/read/delete | 小規模I/Oの比較 | なし。一時領域のみ |
| C | isolated `npm ci` on `/mnt/c` | 大量create/delete/extractの再現 | なし。一時領域のみ |
| D | isolated `npm ci` on WSL native | 同一dependency graphの対照 | なし。一時領域のみ |
| E | heavy I/O後source read | 大量I/O後にsource直下readまで劣化するか | なし |

診断scriptは `scripts/diagnose-mig09a-eio.sh` とする。通常実行ではLayer A/Bまで、`--heavy` でLayer C/D/Eも実行する。

## 4. 安全境界

- repository直下の `node_modules` / `.venv` を削除・再生成しない。
- `package.json` / `package-lock.json` を一時directoryへコピーして比較する。
- Windows側試験はrepository外かつ同じ `/mnt/c` filesystem上の一時directoryを使用する。
- WSL native対照試験は `$HOME/.cache` 配下を使用する。
- secret fileの内容を表示・コピーしない。
- 診断ログは `$HOME/data/orderscope/mig09a/<timestamp>/` に保存する。
- temporary probe directoryはscript終了時に削除する。

## 5. 実行前条件

1. Windows PowerShellから一度 `wsl --shutdown` を実行する。
2. WSLを再起動する。
3. OrderScopeのWindows側sourceへ移動する。
4. Git working treeに意図しない変更がないことを確認する。
5. `.nvmrc` に従ってNode.js 24.21.0を選択する。

WSL restart後の再現性確認はMIG-09Aの必須項目である。

## 6. 判定表

| /mnt/c通常read | /mnt/c small I/O | /mnt/c npm ci | WSL native npm ci | 判定 |
|---|---|---|---|---|
| EIO | 任意 | 任意 | 任意 | source参照層の問題。MIG-09Bへ進まずdrvfs/Windows側を追加調査 |
| PASS | EIO | 任意 | PASS | `/mnt/c` write I/O相関が強い |
| PASS | PASS | EIO | PASS | dependency大量展開と`/mnt/c`配置の相関が強い。MIG-09Bへ進める |
| PASS | PASS | EIO | EIO | filesystem配置以外（npm/network/package）の可能性。EIO内容を比較 |
| PASS | PASS | PASS | PASS | 一時障害の可能性。再試験して非再現条件として記録 |
| PASS | PASS | PASS | FAIL（非EIO） | WSL native側の別要因。MIG-09B判断前にlog確認 |

## 7. MIG-09A完了ゲート

次をすべて記録できればMIG-09Aを完了可能とする。

- WSL restart後のsource通常read結果。
- `/mnt/c`小規模I/O結果。
- 同一 `package.json` / `package-lock.json` による `/mnt/c` isolated `npm ci` 結果。
- WSL native isolated `npm ci` 結果。
- heavy I/O後のsource read結果。
- EIO発生時のlog path。
- MIG-09Bへ進むか、追加filesystem調査を行うかの判定。

## 8. MIG-09Bへ進める条件

特に次の結果を得た場合、runtime dependencyをWSL nativeへ分離する設計評価を開始する。

```text
source normal read: PASS
/mnt/c small I/O: PASS または軽微
/mnt/c isolated npm ci: EIO
WSL native isolated npm ci: PASS
```

この場合、原因componentを完全特定できていなくても、「Linux runtime dependencyの大量I/OをNTFS/drvfs上へ置く構成を避ける」ための実測根拠として十分とする。

## 9. ローカルから返す証跡

最低限、以下2ファイルの内容を返す。

- `$HOME/data/orderscope/mig09a/<timestamp>/summary.tsv`
- `$HOME/data/orderscope/mig09a/<timestamp>/diagnostic.log`

EIOが出た場合は該当する `*.out` も追加する。


## 10. 2026-09-21 first local evidence review

Commit `985dbcb` の初回実測をレビューしたところ、診断scriptが存在しない `uv.toml` をread対象に含めていたため、以下3項目はEIO再現ではなく診断scriptの誤指定による偽FAILと判定した。

- `readable:uv.toml`
- `repeated_source_read`
- `post_heavy_source_read`

同runで有効な比較結果は以下。

- `small_io_mntc`: PASS（2,000 files）
- `small_io_wsl`: PASS（2,000 files）
- `npm_ci_mntc`: PASS
- `npm_ci_wsl`: PASS

したがって、このrunでは `/mnt/c` EIOは再現していない。診断scriptは `pyproject.toml` を使用するよう修正し、再実行結果をMIG-09Aの正式証跡とする。
