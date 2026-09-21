# OrderScope npm警告調査レポート（移行残作業タスク6）

作成日: 2026-09-21（Asia/Tokyo）
対象: `REPORT_LOCAL_ENVIRONMENT_MIGRATION_REMAINING_TASKS_2026-09-20.md` のタスク6

## 1. 判定

タスク6の調査を完了した。`npm audit` の監査応答として確認できた高 severity は、次の2 advisory系統である。

- `sharp@0.35.2` の libheif 脆弱性（High）
- `undici@7.28.0` の cross-user information disclosure / parse-time crash（High）

同じ `undici@7.28.0` には Moderate advisoryも4件ある。移行資料に記載されていた「high severity vulnerability: 4件」という表記とは一致しないため、本調査では監査応答の advisory単位を正として記録する。`npm audit fix` および `npm audit fix --force` は、依存経路と回帰試験の追加確認が必要なため実施していない。

## 2. 監査対象

検証時の主要バージョン:

| 項目 | 値 |
|---|---|
| Node.js | 24.21.0 |
| npm | 11.19.0 |
| `sharp` | 0.35.2 |
| `undici`（top-level） | 7.28.0 |
| `undici`（Wrangler配下） | 7.29.0 |
| `miniflare`（root） | 4.20260730.0 |
| `wrangler` | 4.127.1 |

監査応答は、2026-09-20に npm registry から取得された npm debug log とローカル npm cache に残る advisory recordで再確認した。今回の実行環境では監査APIへの新規通信が制限されたため、`npm audit --offline` のゼロ件結果を最新監査の根拠にはしていない。

## 3. 脆弱性と依存経路

| package / version | severity | advisory | 依存経路 | 修正版の目安 |
|---|---:|---|---|---|
| `sharp@0.35.2` | High | GHSA-rgj7-g3m4-5g8c | `miniflare@4.20260730.0` および Wrangler配下の `miniflare@5.20260828.0-alpha` が `sharp@0.35.2` を要求 | `sharp@0.35.4` |
| `undici@7.28.0` | High | GHSA-4cwx-7wf7-3272 | rootの `miniflare@4.20260730.0` | `undici@7.29.0` 以上 |

`undici@7.28.0` については、次のModerate advisoryも同じ脆弱バージョン範囲に該当する。

- GHSA-8xcm-r25x-g524
- GHSA-m8rv-5g2x-5cg5
- GHSA-jr45-8vmc-qm54
- GHSA-v3r7-h72x-cjcm

`wrangler@4.127.1` 配下の `undici@7.29.0` は、上記の `>=7.0.0 <7.29.0` の範囲外である。一方、`sharp@0.35.2` は rootの `miniflare` とWrangler配下のMiniflareから共有されているため、単純なroot依存の削除では解消しない。

## 4. 本番Worker bundleへの影響

脆弱性対象のpackageは、`package.json` の `devDependencies` に属する。Worker source (`src/index.ts` とその依存) は `sharp`、`undici`、`miniflare`、`workerd`、`esbuild`、`wrangler` をruntime importしていない。

`wrangler deploy --dry-run --env live-canary --outdir <temporary-dir>` を実行して生成bundleを確認した結果:

- upload: 164.64 KiB（gzip 36.11 KiB）
- esbuild inputs: 29
- inputsはsource TypeScriptのみ
- `index.js`に `sharp`、`undici`、`miniflare`、`workerd`、`esbuild`、`wrangler` の文字列・module実体は含まれない

したがって、今回のadvisoryは現在のデプロイWorker本体ではなく、WSL上のlocal test、Miniflare、Wrangler実行環境に限定されたリスクである。ただしlocal toolingをCIや開発端末で実行するため、依存更新候補として残す。

## 5. install script警告

`npm ci` で未承認として報告されていたのは次の3 packageである。

- `esbuild@0.28.1` — `postinstall: node install.js`
- `workerd@1.20260730.1` — `postinstall: node install.js`
- `workerd@1.20260828.1` — `postinstall: node install.js`

両packageのscriptは、任意のアプリケーション処理を行うものではなく、現在のLinux x86_64に対応するoptional binaryを配置し、実行ファイルのversionを検証する。移行時のscript実行済み環境と、今回の`--ignore-scripts`復旧環境で次を確認した。

- `@esbuild/linux-x64/bin/esbuild` はLinux x86_64 ELF、version `0.28.1`
- `@cloudflare/workerd-linux-64/bin/workerd` はLinux x86_64 ELF、version `2026-08-28`
- `npm install-scripts ls` で対象3 packageを特定

確認したバージョンだけを許可するため、`package.json` に次を追加した。

```json
"allowScripts": {
  "esbuild@0.28.1": true,
  "workerd@1.20260730.1": true,
  "workerd@1.20260828.1": true
}
```

`fsevents` はLinuxではactive dependencyではなく、今回の未承認リストには含まれていない。`npm install-scripts approve --all` は使用していない。

## 6. 検証結果

- `npm install-scripts ls`: `No packages with unreviewed install scripts.`
- `npm ci --offline --no-audit --ignore-scripts`: 成功（43 packages）。これは現在の`/mnt/c` 9p mount上で生成したLinux ELFをNode child processから起動できないための復旧確認である。
- `npm ci --offline --no-audit`（script許可後）: `esbuild` postinstallのLinux ELF検証で `EPERM`。`/mnt/c`のNTFS/9p配置に起因し、脆弱性対応の失敗ではない。
- `npm run typecheck`: 成功。
- `npm run deploy:check -- --env live-canary`: 成功。`164.64 KiB / gzip 36.11 KiB`、environment警告なし。
- `npm test`: 既存テスト開始後に2件出力したまま進行しなかったため中断。ソース変更はなく、移行前の受入結果（199 passed）を維持する扱いとし、local runtimeの再構築問題は別途扱う。

## 7. 対応方針

今回の変更では、install scriptの承認範囲だけを固定した。脆弱性対応については、次のいずれかを別変更として実施する。

1. `miniflare` / `wrangler` の修正版リリースで `sharp>=0.35.4` と `undici>=7.29.0` に更新できるかを確認する。
2. upstreamが固定依存を更新していない場合は、`overrides` による上書きを一時候補として、`npm ci`、Node test、typecheck、deploy dry-run、Miniflare integration testを実施する。
3. 互換性またはpackage-lockの差分が大きい場合は、bundle非包含であることを根拠に現行lockを維持し、local toolingの更新期限を別途設定する。

`npm audit fix --force` は、Wrangler/Miniflareのmajor変更やlocal runtime差し替えを招く可能性があるため、承認なしには実施しない。

## 8. 参照

- [sharp advisory GHSA-rgj7-g3m4-5g8c](https://github.com/advisories/GHSA-rgj7-g3m4-5g8c)
- [undici security advisories](https://github.com/nodejs/undici/security/advisories)
- [Cloudflare Workers SDKのMiniflare package定義](https://github.com/cloudflare/workers-sdk/blob/main/packages/miniflare/package.json)
