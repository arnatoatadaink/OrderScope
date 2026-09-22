# OrderScope — DEV-I0-006 temporary content lifecycle 受入記録

作成日: 2026-09-22（Asia/Tokyo）
Status: accepted
対象: `DEV-I0-006 / I0-006 Define temporary-content lifecycle`

## 1. 結論

`DEV-I0-006` は既存のlifecycle contract、provider handoff、contract fixtureを再レビューし、WBS完了条件を満たしているため **完了 / Accepted** とする。

追加コード変更は不要である。既存の `TemporaryContent` 契約をtemporary source contentのv0.1 lifecycle境界として採用する。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/contracts/temporary_content.py`
- `analysis/app/orderscope_local/contracts/fact_store.py`
- `analysis/app/orderscope_local/contracts/provider.py`
- `analysis/app/orderscope_local/contracts/__init__.py`

専用テスト:

- `analysis/tests/contracts/test_temporary_content_contract.py`
- `analysis/tests/contracts/test_provider_contract.py`

## 3. WBS完了条件との対応

WBS `I0-006` の完了条件:

> Schema for content ref, retention class, expiry, delete proof, exception reason.

| 要求 | 実装 |
|---|---|
| content reference | `TemporaryContent.content_ref` |
| retention class | `RetentionClass.TEMPORARY_SUCCESS / TEMPORARY_EXCEPTION` |
| captured timestamp | `captured_at` |
| expiry | `expires_at` |
| lifecycle state | `TemporaryContentState` |
| extraction completion | `extraction_completed_at` |
| exception reason | `exception_reason` |
| deletion time | `deleted_at` |
| delete proof | `deletion_proof` |

## 4. Lifecycle state

`TemporaryContentState` は以下を分離する。

- `STAGED`
- `EXTRACTION_SUCCEEDED`
- `EXCEPTION`
- `DELETED`

各stateは必要なaudit fieldとretention classを契約で制約する。

### STAGED

まだ抽出完了・例外・削除を主張できない。

### EXTRACTION_SUCCEEDED

`TEMPORARY_SUCCESS` を必須とし、`extraction_completed_at` を要求する。
exception/deletion fieldを同時に保持しない。

### EXCEPTION

`TEMPORARY_EXCEPTION` と `exception_reason` を必須とする。
成功抽出を同時に主張しない。

### DELETED

`deleted_at` と `deletion_proof` を必須とする。
例外contentの場合はexception reasonも履歴として保持する。

## 5. Retention境界

- `DURABLE_METADATA` はTemporaryContentでは使用できない。
- temporary exception contentはcaptureから **30日以内** のexpiryを必須とする。
- successful raw contentとexception raw contentはFact Storeのdurable metadataとは分離する。
- bodyそのものは `TemporaryContent` に保持しない。
- content削除後もmetadata / hash / deletion proofは別境界で保持可能とする。

成功contentの具体的なphysical deletion cadenceやretention workerはI0-006のschema責務外であり、N1-005 retention controllerで実行する。

## 6. I0-005 Fact Storeとの境界

Fact Storeの `Evidence` はdurableなlocator/hash/quality/retention metadataを保持するが、temporary bodyそのものは保持しない。

`TemporaryContent` はFact Store recordではなく、外部contentへのtemporary storage lifecycle auditである。

この分離により:

- Fact/Evidence履歴を残したままraw bodyを削除できる。
- temporary body削除がFactの削除を意味しない。
- Evidenceのexcerpt hashやsource provenanceはraw content消去後も保持できる。

## 7. Provider adapterとの境界

`AdapterItem.temporary_content` によりprovider adapterからtemporary lifecycleへhandoffする。

`assert_adapter_item_contract()` は:

- `TemporaryContent` 型であること
- lifecycle contractを満たすこと
- raw provider bodyやsecret-like fieldを含まないこと

を検証する。

## 8. 安全性

- content body fieldを持たない。
- provider response bodyを持たない。
- credential-like materialを `content_ref` / `exception_reason` / `deletion_proof` へ保存することを拒否する。
- timestampはUTCを必須とする。
- expiryがcaptureより前になることを拒否する。
- successful extractionとexceptionを同時に主張できない。
- deletion proofなしのDELETED状態を拒否する。

## 9. Fixture受入

`test_temporary_content_contract.py` は以下を確認する。

- successful temporary content
- body非保持
- deleted exception + proof
- exception reason必須
- exception expiry 30日上限
- durable metadata classの拒否
- secret-like lifecycle metadata拒否
- deletion proof必須
- state / retention class整合

`test_provider_contract.py` ではadapter itemからtemporary content lifecycleへのhandoffとsecret/raw body非混入を確認している。

本実装はPC移行時の全Python suite 696件PASSに含まれており、今回のDEV-I0-006レビューではコード変更を行っていない。

## 10. 判定

`DEV-I0-006`: **完了 / Accepted**

これにより `I0-007 Build common contract-test kit` の依存である `I0-003 / I0-004 / I0-006` がすべて充足した。

次のローカル主作業:

`DEV-I0-007 — provider-neutral contract test正式受入`

また、`N0-004 temporary body access` はI0-006側のlifecycle依存を充足した。N0-002 adapter実装後に接続可能となる。
