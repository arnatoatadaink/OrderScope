# OrderScope — DEV-I0-002 provenance / timestamp 共通型 受入記録

作成日: 2026-09-22（Asia/Tokyo）
Status: accepted
対象: `DEV-I0-002 / I0-002 Implement common provenance contract`

## 1. 結論

`DEV-I0-002` は既存実装をレビューし、WBSの完了条件を満たしているため **完了 / Accepted** とする。

新規の重複実装は行わない。既存の共通契約を正として後続 `I0-003` / `I0-004` / `I0-005` から利用する。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/contracts/provenance.py`
- `analysis/app/orderscope_local/contracts/__init__.py`

専用テスト:

- `analysis/tests/contracts/test_provenance_contract.py`

既存利用先の代表例:

- `analysis/app/orderscope_local/contracts/provider.py`
- `analysis/app/orderscope_local/contracts/fact_store.py`
- `analysis/tests/contracts/test_fact_store_contract.py`

## 3. WBS完了条件との対応

WBS `I0-002` の完了条件:

> Fix source ref/hash, event/publish/file/retrieve/available/accept timestamps, and provider revision in types and tests.

対応は次のとおり。

| 要求 | 実装 |
|---|---|
| source ref | `SourceReference` |
| source/content hash | `ContentHash`（SHA-256） |
| event timestamp | `Provenance.event_time` |
| publish timestamp | `Provenance.published_at` |
| file timestamp | `Provenance.filed_at` |
| retrieve timestamp | `Provenance.retrieved_at` |
| available timestamp | `Provenance.available_at` |
| accept timestamp | `Provenance.accepted_at` |
| source-side accepted timestamp | `Provenance.source_accepted_at` |
| provider revision | `ProviderRevision` |

## 4. 契約上の重要点

- 外部source時刻と内部運用時刻を分離する。
- source側で時刻が不明な場合は `None` を保持し、retrieve/accept時刻から補完しない。
- date-only sourceは `SourceTimestamp.date_only` として保持し、架空の時刻を生成しない。
- instant型の共通時刻はUTCへ正規化済みであることを必須とする。
- operational timestampは `available_at <= retrieved_at <= accepted_at` を保証する。
- raw body、credential、cursor、duplicate判定はprovenance型へ混在させない。
- provenance value objectはimmutableとする。

## 5. 検証根拠

`test_provenance_contract.py` で以下を確認している。

- source時刻とoperational時刻の分離
- unknown timestampの非補完
- date-only精度保持
- UTC制約
- operational timestamp順序
- source ref / provider revision / hashの入力制約
- immutableかつsecret/raw bodyを含まない境界

また、PC移行最終受入の全Python suite 696件PASSには本テストも含まれる。2026-09-22にCodexDesktop側でも移行後環境の検収合格が確認されたため、環境移行を理由に本契約の再実装を行う必要はない。

## 6. 判定

`DEV-I0-002`: **完了 / Accepted**

後続:

1. `DEV-I0-003` cursor / checkpoint contract
2. `DEV-I0-004` idempotency / duplicate boundary
3. `DEV-I0-005` Fact Store logical schema Accepted化

`I0-003` と `I0-004` はどちらも `I0-002` に依存するため、ここでblockが解除される。クリティカルパス上は `DEV-I0-003` を次の実施対象とする。
