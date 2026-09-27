# MIG-09B runtime dependency placement decision

作成日: 2026-09-22（Asia/Tokyo）
Status: Accepted
親タスク: `MIG-09B` in `docs/REPORT_REMAINING_WORK_AFTER_WSL_MIGRATION_CHECKPOINT_2026-09-21.md`

## 1. 結論

Windows側source正本 `/mnt/c/Users/Y/Projects/codex_work/OrderScope` は維持する。

runtime dependency配置は次を採用する。

| dependency | 採用配置 | 判定 |
|---|---|---|
| Python project environment | WSL native | **採用** |
| Node `node_modules` | Windows側source直下 `/mnt/c/.../OrderScope/node_modules` | **当面維持** |
| local mutable data | WSL native | 既決定を維持 |
| local Wrangler state | WSL native | 既決定を維持 |

Pythonは `UV_PROJECT_ENVIRONMENT` を使い、既定の候補を `${HOME}/.local/share/orderscope/venv` とする。

NodeはMIG-09Aの修正版再試験で `/mnt/c` isolated `npm ci`、small I/O、post-heavy readが全てPASSし、EIOが再現しなかったため、移行完了前にsymlink / bind mount / generated runtime mirrorを導入しない。

## 2. MIG-09Aからの入力

正式証跡:

- `docs/evidence/mig09a/20260921T092425Z/diagnostic.log`
- `docs/evidence/mig09a/20260921T092425Z/summary.tsv`

修正版runでは以下が全てPASS。

- source read
- 250 iterations x 4 files repeated read
- `/mnt/c` 2,000 file create/read/delete
- WSL native 2,000 file create/read/delete
- `/mnt/c` isolated `npm ci`
- WSL native isolated `npm ci`
- heavy I/O後のsource read

従って、2026-09-21の初回最終受入で観測したEIOは事実として保持するが、恒常的な `/mnt/c` dependency配置障害としては再現できなかった。

## 3. Node配置の比較

### 3.1 案A: `node_modules`をsource直下に維持

利点:

- npm / Node / TypeScript / Wranglerの標準module resolutionを変更しない。
- package scriptsをそのまま利用できる。
- MIG-09A修正版でisolated `npm ci`が成功済み。
- Windows側source正本という既存境界を変えない。

欠点:

- 過去に一度EIOが発生している。
- Linux dependencyの多数のsmall fileがdrvfs/9p上に存在する。

判定: **採用**。ただし再発監視を継続する。

### 3.2 案B: arbitrary WSL-native `node_modules` + `NODE_PATH`

不採用。

OrderScopeは `package.json` で `"type": "module"` を使用し、integration testでは `esbuild`、`miniflare`、`wrangler` 等をbare ESM importしている。

Node.js v24のESM resolverは `NODE_PATH` をimport specifier解決に使用しない。そのため、外部directoryへ `npm ci --prefix` するだけではsource側ESM importの一貫した解決経路にならない。

### 3.3 案C: source直下 `node_modules` をWSL nativeへsymlink

技術的にはmodule resolutionを維持できる可能性が高いが、今回は不採用。

理由:

- Windows側source正本にWSL固有linkを作る。
- Codex Desktop / Windows toolingから見たpath semanticsを複雑化する。
- 過去のEIOが再現していない段階で導入するには変更範囲が大きい。

### 3.4 案D: bind mount

不採用。

理由:

- WSL起動ごとのmount lifecycle管理が必要。
- 権限・fstab・bootstrap依存を増やす。
- source checkout内の見た目と実体が分離し、障害診断を難しくする。

### 3.5 案E: generated WSL runtime mirror

将来のfallback候補として保留。

tracked sourceをWSL native runtime workspaceへ同期し、`node_modules`もそこで生成する方法はI/O分離として最も強い。ただし、

- source同期wrapperが必須
- stale runtime copy防止が必要
- secret / mutable data除外設計が必要
- 現在の「Windows側sourceを唯一の実行対象」とするrunbookを変更する

ため、MIG-09Bでは導入しない。

EIOが再度再現し、`/mnt/c`とWSL nativeの差が明確になった場合の第一fallbackとする。

## 4. Python配置の比較

### 4.1 source直下 `.venv`

現状構成。動作実績はあるが、Linux用virtual environmentの大量small fileをdrvfs上へ置く必要はない。

### 4.2 WSL-native project environment

**採用**。

uvは `UV_PROJECT_ENVIRONMENT` に絶対pathを指定できる。OrderScopeでは次を既定候補とする。

```text
/home/y/.local/share/orderscope/venv
```

実装ではusername固定を避け、

```bash
${HOME}/.local/share/orderscope/venv
```

を使用する。

このpathはsource checkout外かつWSL native filesystemであり、Windows native Pythonから利用しない。

## 5. 採用後の最終境界

```text
/mnt/c/Users/Y/Projects/codex_work/OrderScope
  ├─ tracked source                 Windows正本
  ├─ package.json / package-lock    Windows正本
  ├─ node_modules/                  WSL/Linux用、当面ここ
  ├─ pyproject.toml / uv.lock       Windows正本
  └─ .venv/                         使用しない

/home/y/.local/share/orderscope/venv
  └─ Python project environment     WSL native

/home/y/data/orderscope/local
  └─ mutable local data             WSL native

/home/y/data/orderscope/wrangler-state
  └─ local Wrangler state           WSL native
```

## 6. MIG-09Cへの実装要求

MIG-09Cでは以下を実装する。

1. `scripts/run-local-wsl.sh` が `UV_PROJECT_ENVIRONMENT` をWSL native absolute pathへ固定する。
2. defaultを `${HOME}/.local/share/orderscope/venv` とする。
3. override用に `ORDERSCOPE_PYTHON_ENV` を許可する場合もWSL native filesystemのみ許可する。
4. `env` subcommandでPython environment pathを表示する。
5. `uv sync --locked` / `uv run` が同じenvironmentを使う入口を用意する。
6. source直下 `.venv` が存在する場合は、誤使用を避けるため検出・警告または停止方針を決める。
7. Nodeは現行resolutionを維持し、`node_modules` externalizationは行わない。
8. EIO再発時のfallbackをgenerated WSL runtime mirrorとしてrunbookに記録する。

## 7. 完了判定

MIG-09Bは以下により完了とする。

- Windows側source正本を維持する。
- Python `.venv` のWSL-native化を採用した。
- Node `node_modules` は、MIG-09AでEIO非再現かつESM resolver制約があるため現配置を維持すると決定した。
- symlink / bind mount / NODE_PATH方式は採用しない。
- generated WSL runtime mirrorをEIO再発時のfallbackとして残した。
- MIG-09Cの実装要求を定義した。
