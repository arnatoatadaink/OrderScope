# OrderScope — WSL移行チェックポイント後の残作業一覧

作成日: 2026-09-21（Asia/Tokyo）
Status: active remaining-work ledger (non-normative)
起点: `docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_EXECUTION_2026-09-20.md` の 2026-09-21 checkpoint

## 1. 目的

Windows側source + WSL runtimeへの移行作業を一区切りとし、次回以降は本書を再開入口として残作業を管理する。移行作業と通常開発作業を混在させず、完了条件・依存条件・後工程を明示する。

現時点では移行は完了ではない。タスク9の最終受入中に `/mnt/c` でEIOが発生し、runtime dependency配置の安定性確認が必要になった。

## 2. 区切り時点の状態

| 領域 | 状態 | 備考 |
|---|---|---|
| source正本 | 確定 | `/mnt/c/Users/Y/Projects/codex_work/OrderScope` |
| 可変データ正本 | 確定 | `/home/y/data/orderscope/local` |
| local Wrangler state | 確定 | `/home/y/data/orderscope/wrangler-state` |
| Node.js | 固定済み | `.nvmrc=24.21.0` |
| Python | 固定済み | uv管理 Python `>=3.13,<3.14` |
| npm警告調査 | 完了 | advisory・bundle非包含・allowScriptsを記録 |
| Wrangler environment安全策 | 完了 | remote操作でenv明示、deploy入口fail-closed |
| secret境界 | 完了 | Worker / Python / Wrangler管理を分離 |
| 運用runbook | 完了 | `RUNBOOK_LOCAL_ENVIRONMENT_WSL_WINDOWS_2026-09-21.md` |
| タスク9最終受入 | **ブロック中** | `/mnt/c`上の`npm ci`でEIO、後続で`package.json`/`uv.toml`もEIO |
| WSL退避copy | 保留継続 | `/home/y/code/OrderScope`。編集・実行しない |

## 3. 移行完了までの残作業

| ID | 作業 | 優先度 | 依存 | 完了条件 |
|---|---|---:|---|---|
| MIG-09A | `/mnt/c` EIOの切り分け | 最優先 | なし | **完了**。修正版再試験で通常read / small I/O / isolated `npm ci` / post-heavy readが全PASS。EIOは非再現として記録 |
| MIG-09B | runtime dependency配置の再設計 | 最優先 | MIG-09A | **完了**。Python environmentはWSL nativeへ移動、Node `node_modules`は現配置維持。詳細はMIG-09B decision report |
| MIG-09C | wrapper / path設計の実装 | 高 | MIG-09B | **実装済み・ローカル検証待ち**。PythonはWSL native envへ固定、Node pathは現行維持 |
| MIG-09D | README / runbook / migration report更新 | 高 | MIG-09B〜09C | 実際の最終構成と文書が一致する |
| MIG-09E | タスク9最終受入を再実行 | 最優先 | MIG-09D | hash、uv、npm、Node tests、typecheck、Wrangler dry-run、Python tests、Local API healthが全て成功 |
| MIG-09F | Git最終確定確認 | 高 | MIG-09E | migration資料、lockfile、runbook、修正scriptがremoteに確定し、secret / runtime dependency / cacheが追跡されていない |
| MIG-DONE | PC移行完了判定 | 最優先 | MIG-09E〜09F | 移行実施レポートを「完了」へ更新し、本流開発へ戻れる |

### 3.1 MIG-09Aで最低限確認する事項

- `package.json` / `pyproject.toml` / Git metadataが `/mnt/c` 上で安定して読み取れるか。
- EIOが `npm ci` の大量削除・展開時だけ発生するか、通常readでも再現するか。
- WSL restart後に再発するか。
- Windows側のディスク/NTFS、WSL drvfs、セキュリティソフト、同時アクセスのどこに相関があるか。
- 同じ依存展開をWSL native filesystemで行った場合にEIOが消えるか。

### 3.2 MIG-09A 診断準備状況

Web側の診断設計は完了。ローカル実測のみ未実施。

追加済み:

- `scripts/diagnose-mig09a-eio.sh`
- `docs/REPORT_MIG_09A_MNTC_EIO_DIAGNOSTIC_2026-09-21.md`

診断scriptはrepository直下の `node_modules` / `.venv` を変更せず、repository外の一時directoryで `/mnt/c` とWSL native filesystemを比較する。通常実行でsource readと小規模I/O、`--heavy`でisolated `npm ci` とheavy I/O後のsource readまで確認する。

MIG-09Aは **完了**。正式証跡は `docs/evidence/mig09a/20260921T092425Z/summary.tsv` と `diagnostic.log`。修正版runでは全項目PASSで、WSL restart後にEIOは再現しなかった。直接原因は未特定だが、再現条件を記録できたためMIG-09Aの完了条件を満たす。



### 3.3 MIG-09B runtime dependency配置決定

MIG-09Bは **完了**。

採用方針:

- Windows側source正本は維持する。
- Python project environmentは `UV_PROJECT_ENVIRONMENT` を使いWSL nativeへ分離する。既定候補は `${HOME}/.local/share/orderscope/venv`。
- Node `node_modules` は当面source直下に維持する。
- `NODE_PATH`、WSL symlink、bind mountは採用しない。
- `/mnt/c` EIOが再発し、WSL nativeとの差が再現できた場合はgenerated WSL runtime mirrorを第一fallbackとして評価する。

判断根拠とMIG-09Cへの実装要求は `docs/REPORT_MIG_09B_RUNTIME_DEPENDENCY_PLACEMENT_2026-09-22.md` を正とする。

次の実施対象は **MIG-09C wrapper / path設計の実装**。



### 3.4 MIG-09C wrapper / path実装状況

MIG-09Cのコード実装は完了し、**ローカル検証待ち**。

追加・変更:

- `scripts/run-local-wsl.sh`
- `docs/REPORT_MIG_09C_RUNTIME_PATH_IMPLEMENTATION_2026-09-22.md`

実装内容:

- `ORDERSCOPE_PYTHON_ENV` を追加。
- default Python environmentを `${HOME}/.local/share/orderscope/venv` に固定。
- `UV_PROJECT_ENVIRONMENT` を同pathへexport。
- Python environmentがsource checkout内またはWindows/9p/NTFS上の場合はfail-closed。
- 予期しないactive `VIRTUAL_ENV` を拒否。
- source直下legacy `.venv` はwarningのみで使用しない。
- `sync` subcommandを追加し、固定environmentへ `uv sync --locked` を実行。
- `env` subcommandへPython environment path表示を追加。
- Node / Wranglerはsource直下 `node_modules` と既存module resolutionを維持。

MIG-09Cの完了判定はローカル検証後に行う。検証項目はMIG-09C実装レポートを正とする。


## 4. 移行完了後に再開する通常開発

`WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md` と既存WBS上の現在地から、通常開発の再開地点は `I0-002` とする。

### 4.1 クリティカルパス

```text
I0-002 provenance / timestamp共通型
  ├─> I0-003
  ├─> I0-004
  └─> I0-005 Fact Store ADR Accepted化
         ↓
      I0-006 temporary content lifecycle
         ↓
      I0-007 formal acceptance
         ↓
      S0-002 / S0-003 / S0-005 / S0-006
         ↓
      S0-007
         ↓
      E0-001〜E0-007
         ↓
      N1 / O0 / X0
```

### 4.2 再開順

| ID | 作業 | 状態 | 備考 |
|---|---|---|---|
| DEV-I0-002 | provenance / timestamp共通型 | 次の本流 | Corporate Intelligenceの現在のクリティカルパス |
| DEV-I0-003 | provider contract系の後続 | I0-002待ち | I0-007受入へ接続 |
| DEV-I0-004 | idempotency / evidence系の後続 | I0-002待ち | I0-007受入へ接続 |
| DEV-I0-005 | Fact Store論理schema ADR Accepted化 | preimplemented | I0-002 provenance型・fixture待ち |
| DEV-I0-006 | temporary content lifecycle | 後続 | I0-005系とI0-007へ接続 |
| DEV-I0-007 | provider-neutral contract test正式受入 | 部分実装済み | I0-003/004/006統合待ち |
| DEV-S0-004 | strict SEC form filter | 完了 | 追加作業なし |
| DEV-S0-007 | SEC統合受入 | 部分完了 | S0-002/003/005/006待ち |

## 5. Web調査側の保留タスク

`WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md`では、即時着手可能なWeb調査はなく、次はlocal contract / adapterの進展待ちである。

| Web ID | 状態 | 解放条件 |
|---|---|---|
| WEB-010 | 保留（依存） | E0-004〜006のfield / identity形状確定 |
| WEB-013 | 保留（依存） | WEB-007とI0-005のcontract方針確定 |
| WEB-014 | 保留（依存） | WEB-008、WEB-010、local評価形状 |
| WEB-019 | 保留（依存） | local official adapter / Relationship形状確定 |
| WEB-020 | 保留（依存） | local official feed実装・試験証跡 |

これらはlocal実装が進んだ時点で再評価する。現時点で追加Web調査を先行させない。

## 6. 移行とは分離する後続保守

| ID | 作業 | 扱い |
|---|---|---|
| OPS-NPM-001 | `sharp` / `undici` advisoryのupstream更新追跡 | production bundle非包含のため移行ブロッカーではない |
| OPS-BACKUP-001 | resticによるDB世代管理 | タスク5とは分離済み。別レポートに従う |
| OPS-COPY-001 | `/home/y/code/OrderScope`の退避copy整理 | 移行完了後に削除可否を判断 |

## 7. 次回セッションの開始手順

1. 本書を開く。
2. `MIG-09A`の状態を確認する。
3. 移行が完了していなければ通常開発へ戻らず、MIG-09A〜MIG-DONEを優先する。
4. `MIG-DONE`後、`DEV-I0-002`から通常開発を再開する。
5. local contractが進んだ時点でWeb保留タスクを再評価する。

## 8. 関連資料

- `docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_EXECUTION_2026-09-20.md`
- `docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_REMAINING_TASKS_2026-09-20.md`
- `docs/RUNBOOK_LOCAL_ENVIRONMENT_WSL_WINDOWS_2026-09-21.md`
- `docs/REPORT_LOCAL_DB_WSL_CANONICALIZATION_2026-09-20.md`
- `docs/REPORT_LOCAL_NPM_AUDIT_TASK_6_2026-09-21.md`
- `docs/REPORT_LOCAL_WRANGLER_ENVIRONMENT_TASK_7_2026-09-21.md`
- `docs/REPORT_LOCAL_SECRET_BOUNDARY_TASK_8_2026-09-21.md`
- `docs/WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md`
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`

## 9. 区切り時点の判定

2026-09-21時点で、WSL移行の設計・データ正本化・安全境界・運用文書化は完了した。最終受入でruntime dependencyを`/mnt/c`上へ配置する構成のI/O安定性問題を検出したため、移行完了判定だけを保留する。

次回の唯一の再開入口は `MIG-09A` とする。
