# MIG-09C wrapper / runtime path implementation

作成日: 2026-09-22（Asia/Tokyo）
Status: implemented, local validation pending
親タスク: `MIG-09C` in `docs/REPORT_REMAINING_WORK_AFTER_WSL_MIGRATION_CHECKPOINT_2026-09-21.md`

## 1. 実装目的

MIG-09BでAcceptedとしたruntime dependency配置を実装する。

- source正本はWindows側 `/mnt/c/Users/Y/Projects/codex_work/OrderScope`
- Node `node_modules` はsource直下を維持
- Python project environmentだけWSL nativeへ分離
- Python / Local API / pytestが同一environmentを使用
- mutable data / Wrangler persistenceは既存のWSL native配置を維持

## 2. 実装内容

対象:

- `scripts/run-local-wsl.sh`

Python environment default:

```text
${HOME}/.local/share/orderscope/venv
```

override:

```text
ORDERSCOPE_PYTHON_ENV
```

wrapperは以下をexportする。

```text
ORDERSCOPE_PYTHON_ENV
UV_PROJECT_ENVIRONMENT
ORDERSCOPE_DATA_ROOT
ORDERSCOPE_WRANGLER_PERSIST_TO
```

## 3. fail-closed path validation

次を拒否する。

1. Python environmentがabsolute pathでない。
2. Python environmentがsource checkout内。
3. Python environmentが `9p` / `drvfs` / `ntfs` / `fuseblk` 上。
4. OrderScope用pathと異なるvirtual environmentが既にactivateされている。
5. mutable data / Wrangler stateが従来の境界違反を起こしている。

source直下にlegacy `.venv` が存在するだけでは停止しない。ただしwarningを表示し、wrapper経由では使用しない。

この扱いは、既存environmentの削除をMIG-09C実装と同時に強制せず、MIG-09D/09Eまでrollback可能性を残すためである。

## 4. wrapper command

### environment確認

```bash
bash scripts/run-local-wsl.sh env
```

以下を表示する。

- `REPO_ROOT`
- `ORDERSCOPE_DATA_ROOT`
- `ORDERSCOPE_WRANGLER_PERSIST_TO`
- `ORDERSCOPE_PYTHON_ENV`
- `UV_PROJECT_ENVIRONMENT`

### dependency sync

```bash
bash scripts/run-local-wsl.sh sync
```

内部では、

```bash
uv sync --locked
```

を、固定済み `UV_PROJECT_ENVIRONMENT` で実行する。

追加引数も透過する。

### Python / pytest / Local API

既存の以下は、全て同じ `UV_PROJECT_ENVIRONMENT` を使用する。

```bash
bash scripts/run-local-wsl.sh python ...
bash scripts/run-local-wsl.sh pytest ...
bash scripts/run-local-wsl.sh api --port 8000
```

### Wrangler

Node module resolutionは変更しない。

```bash
bash scripts/run-local-wsl.sh wrangler ...
```

はsource直下の既存 `node_modules` を使用する。Node.js runtimeは既存どおり `.nvmrc` に従いWSL/Linuxであることを検証する。

## 5. Node側を変更しない理由

MIG-09Aの正式再試験では `/mnt/c` isolated `npm ci` とheavy I/O後readがPASSし、EIOは非再現だった。

またOrderScopeはESM構成でbare package importを含むため、外部 `node_modules` への単純切替はmodule resolution変更を伴う。

従ってMIG-09CではNode pathは変更しない。

## 6. ローカル検証条件

以下を満たしたらMIG-09Cを完了扱いにできる。

1. `bash -n scripts/run-local-wsl.sh` が成功。
2. `env` がWSL native Python environmentを表示。
3. `sync` が `${HOME}/.local/share/orderscope/venv` にenvironmentを構築。
4. `uv run python --version` 相当をwrapper経由で実行しPython 3.13.x。
5. wrapper経由pytestが実行可能。
6. source直下 `.venv` を参照していないことを確認。
7. Wrangler wrapperが既存Node pathで起動可能。
8. repositoryにruntime dependency/cacheの新規追跡がない。

## 7. MIG-09Dへの引継ぎ

MIG-09Cローカル検証後、MIG-09Dで次を更新する。

- README
- WSL/Windows runbook
- migration execution report
- source直下 `.venv` の扱い
- dependency構築手順を `run-local-wsl.sh sync` ベースへ変更
- EIO再発時のgenerated WSL runtime mirror fallback


## 8. 2026-09-22 first local validation interruption

初回ローカル検証ではPython側のMIG-09C項目は成功した。

- WSL-native Python environment: `/home/y/.local/share/orderscope/venv`
- filesystem: ext4
- Python: 3.13.15
- source-local `.venv` 非使用
- Python tests: 696 passed

Node testでは7件が `ERR_MODULE_NOT_FOUND` で失敗し、`node_modules/miniflare/index.js` を解決できなかった。

これはMIG-09C wrapperによるNode path変更ではない。MIG-09CではNode module resolutionを変更しておらず、初回検証コマンドにworkspace側 `npm ci` が含まれていなかったため、過去のEIO受入時に不完全となった可能性があるsource-local `node_modules` をそのまま使用した。

修正後の検証順序では、Node test前に必ず以下を実行する。

```bash
npm ci
npm test
npm run typecheck
```

`npm ci` 自体でEIOが再発した場合はMIG-09Aの再発証跡として扱い、MIG-09BのNode配置判断を再オープンする。
