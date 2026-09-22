# MIG-09E final acceptance rerun

作成日: 2026-09-22（Asia/Tokyo）
Status: prepared, local execution pending
親タスク: `MIG-09E` in `docs/REPORT_REMAINING_WORK_AFTER_WSL_MIGRATION_CHECKPOINT_2026-09-21.md`

## 1. 目的

MIG-09A〜MIG-09Dで確定したWindows-source + WSL-runtime構成について、旧タスク9の最終受入を最初から再実行し、移行完了前の最終runtime acceptance evidenceを残す。

## 2. 受入runner

`scripts/run-mig09e-acceptance.sh` を追加した。

証跡はrepository外へ保存する。

```text
${HOME}/data/orderscope/mig09e/<UTC timestamp>/
  acceptance.log
  summary.tsv
  local-api.log
  health.json
```

repositoryへruntime logやsecret値を自動保存しない。

## 3. 検証項目

runnerは次を順番に検証する。

1. canonical sourceが `/mnt/c` 上にある。
2. 実行前Git working treeがclean。
3. Node.js `v24.21.0` / Linux runtime。
4. `MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256` が全項目OK。
5. `uv lock --check`。
6. wrapper経由 `uv sync --locked`。
7. Python 3.13.x。
8. Python environmentが `${HOME}/.local/share/orderscope/venv`。
9. Python environmentがWSL native filesystem。
10. `npm ci`。
11. Node test。
12. TypeScript typecheck。
13. Python pytest。
14. `live-canary` Wrangler deploy dry-run。
15. Local API `/health` HTTP 200。
16. Local API listenerが `127.0.0.1:8000`。
17. secret/runtime/cache pathがGit追跡されていない。
18. `.env` / `.env.cloudflare` がGit ignore対象。
19. 実行後Git working treeがclean。
20. `git diff --check`。

## 4. hashの意味

`MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256` は現在の稼働data rootのhashではなく、移行元snapshotの完全性証跡として検証する。

現在の稼働正本は、

- `${HOME}/data/orderscope/local`
- `${HOME}/data/orderscope/wrangler-state`

であり、旧source-local `var/` / `.wrangler/state/` をruntime正本として再利用しない。

## 5. EIO再発時

`npm ci` またはsource readで `EIO` / `Input/output error` が再発した場合、MIG-09Eを完了扱いにしない。

その場合:

1. `acceptance.log` を保存する。
2. MIG-09Aを再オープンする。
3. `/mnt/c` とWSL-native controlを再比較する。
4. 再現差が得られた場合はMIG-09BのNode配置を再評価する。
5. generated WSL-native runtime mirrorを第一fallback候補とする。

## 6. 完了条件

`summary.tsv` が全てPASSし、受入後Git working treeがcleanならMIG-09Eを完了とする。

MIG-09E完了後の次工程はMIG-09F Git最終確定確認。
