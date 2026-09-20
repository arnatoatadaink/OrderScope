# OrderScope local DB世代管理 — restic対応フォローアップ

作成日: 2026-09-20（Asia/Tokyo）
状態: **未実装・別タスクとして保留**

## 1. 目的と境界

OrderScopeの可変データ・ローカルDBはWSL native filesystem上の専用data rootを正本とし、将来の世代管理・バックアップにresticを使用する方針を記録する。

このレポートでは、resticのインストール、repositoryの初期化、password/keyの設定、初回backup、世代削除、restore drill、cron/systemd timerの設定を行わない。今回の作業は設計上の境界と検討項目の記録だけである。

## 2. resticの役割

resticはファイル単位のバックアップ世代を保持する層であり、稼働中のDBそのもの、SQLiteのmigration履歴、Gitのsource管理を置き換えない。

役割は次のように分ける。

| 層 | 正本・役割 |
|---|---|
| Git | source、SQL migration、設定・運用文書の版管理 |
| WSL data root | 現在参照・更新するローカルSQLite/DuckDB/Parquet/raw dataの正本 |
| restic | WSL data rootから取得した、暗号化されたバックアップ世代 |
| Cloudflare D1 | remote D1の正本。local resticとは別のデータ境界 |

したがって、restic snapshotを直接アプリのDB参照先にはしない。復旧時に検証済みの世代を別のrestore rootへ復元し、integrity・migration・manifestを確認してから正本へ切り替える。

## 3. DBスナップショット時の整合性

resticはファイルの変更を把握して保存するが、SQLiteのトランザクション整合性をアプリケーションの代わりに保証するものではない。特にSQLite本体、`-wal`、`-shm`を、書き込み中に個別ファイルとして取得する運用は避ける。

将来の取得手順では、少なくとも次のどちらかを採用する。

- 書き込みprocessを停止し、DBを閉じた状態で対象directoryをsnapshotする。
- SQLiteのonline backup等で一貫したDB artifactを作成し、その閉じたartifactと必要なmanifestをresticへ保存する。

local Wrangler/D1 emulator stateを継続保存する場合も、Wranglerを停止した上でstate directory全体を扱い、SQLite本体、WAL、SHMを分離しない。cacheなど再生成可能なものは、保持対象から除外できるかを別途判断する。

Parquetやimmutable raw artifactは、manifestとSHA-256を同じ世代に含め、restore後にhashと内容を検証する。DBのschemaはGit管理のversioned migrationsと照合する。

## 4. 将来決める項目

- restic repositoryの配置先。WSL内の別disk、外部disk、またはremote backendのどれを使うか。
- repository password/keyの保管経路。Git、通常のshell history、プロジェクト内secret fileには置かない。
- backup対象。local catalog、raw/import、Parquet、必要なWrangler state、manifest、運用ログの範囲。
- 世代識別。restic snapshot IDに加え、取得時刻、data-root revision、Git revision、schema migration、manifest hashを記録する。
- RPO/RTO、取得頻度、保持世代数、月次・週次・日次のretention。
- `restic check`、restore先を分離したrestore drill、SQLite integrity、migration、Parquet hashの受入条件。
- 正本切替時の停止時間、lock、operator承認、復旧後の再取り込み境界。
- restic repository自体のバックアップ・鍵紛失時の復旧手順。

## 5. 未実施項目

本レポート作成時点で、以下は未実施である。

- resticの導入確認
- repository作成
- password/keyの作成・保存
- WSL data rootの初回snapshot
- retention policyの設定
- restoreおよびrestore drill
- 定期実行の登録

DBのWSL正本化を先に確定し、resticはその後の独立したバックアップ／復旧タスクとして実施する。
