# OrderScope — DEV-I0-007 provider-neutral contract test 正式受入記録

作成日: 2026-09-22（Asia/Tokyo）
Status: implementation complete / local acceptance pending
対象: `DEV-I0-007 / I0-007 Build common contract-test kit`

## 1. 結論

`DEV-I0-007` の既存provider-neutral contract test kitを、Accepted済みの `I0-003 / I0-004 / I0-006` と再照合した。

既存kitはpagination、partial/error、retry、secret非露出、checkpoint handoff、idempotency classification、temporary content handoffを既に統合していた。

正式受入レビューで、I0-002/I0-003はoperational timestamp / bounded windowをUTC必須としている一方、provider共通境界がexplicit timezoneのみを要求していた差分を確認した。この差分を修正し、provider request/page timestampもUTCへ正規化済みであることを必須化した。

併せて `max_pages` 超過を明示的に検証するpagination negative fixtureを追加した。

コード・fixture更新は完了。追加差分後のローカルpytest実行証跡が未取得のため、現時点は **実装完了 / local acceptance pending** とする。

## 2. 受入対象

共通kit:

- `analysis/app/orderscope_local/contracts/provider.py`

統合契約:

- `analysis/app/orderscope_local/contracts/provenance.py`
- `analysis/app/orderscope_local/contracts/checkpoint.py`
- `analysis/app/orderscope_local/contracts/identity.py`
- `analysis/app/orderscope_local/contracts/temporary_content.py`

fixture:

- `analysis/tests/contracts/test_provider_contract.py`
- `analysis/tests/contracts/test_checkpoint_contract.py`
- `analysis/tests/contracts/test_identity_contract.py`
- `analysis/tests/contracts/test_temporary_content_contract.py`

## 3. WBS完了条件との対応

WBS `I0-007`:

> Verify adapters satisfy timestamp, pagination, partial, retry, and secret-nonexposure contracts.

| 要求 | 共通検査 |
|---|---|
| timestamp | request/page timezone + UTC、available <= retrieved |
| pagination | half-open bounded window、page_size、cursor advance、loop検出、max_pages |
| partial | partialにはerror必須、unsafe cursor advance禁止 |
| retry | retryable metadata、bounded retry_after、checkpoint retry_not_before |
| secret nonexposure | credential / authorization / provider response body / Bearer / PEM rejection |

## 4. I0-003 checkpoint統合

`checkpoint_for_page()` によりvalidated provider pageをdurable checkpointへ変換する。

- next cursorあり → `IN_PROGRESS`
- terminal page → `COMPLETE`
- partial error → `PARTIAL`
- initial/terminal error → `ERROR`

partial/error時は最後のsafe request cursorを保持し、不確定なpageのnext cursorへ進まない。

## 5. I0-004 idempotency統合

`AdapterItem` は `ContentIdentity` を保持し、`classify_adapter_item()` はaccepted I0-004 classifierを利用する。

- NEW
- DUPLICATE
- CONFLICT
- explicit revisionによるUPDATE

provider固有heuristicでUPDATEを推定しない。

## 6. I0-006 temporary content統合

`AdapterItem.temporary_content` はaccepted I0-006 `TemporaryContent` 型に限定する。

adapter contractは:

- raw bodyをnormalized itemへ埋め込まない
- temporary lifecycleを型検証する
- secret-like lifecycle metadataを拒否する

ことを保証する。

## 7. 今回の追加差分

### 7.1 UTC整合

`provider._utc()` をI0-002/I0-003と同じ規則へ統一した。

- naive datetime → reject
- non-UTC offset-aware datetime → reject
- UTC datetime → accept

これによりprovider request/pageからcheckpoint/provenanceへ渡るoperational timestamp contractが一貫する。

### 7.2 bounded pagination fixture

`collect_pages(..., max_pages=1)` に対しnext cursorが継続するfixtureを追加し、`pagination exceeded max_pages` を明示的に検証する。

## 8. 既存fixture coverage

共通kitでは少なくとも以下を確認している。

- bounded multi-page pagination
- cursor resume
- cursor loop rejection
- page size bound
- timestamp ordering
- UTC enforcement
- provider revision type
- partial retryable failure
- partial without error rejection
- error page cursor advance rejection
- checkpoint handoff
- complete checkpoint
- duplicate/update/conflict/new classification
- temporary content lifecycle handoff
- secret/raw provider body rejection
- bounded max_pages

## 9. ローカル受入

推奨コマンド:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/contracts/test_provider_contract.py \
  analysis/tests/contracts/test_checkpoint_contract.py \
  analysis/tests/contracts/test_identity_contract.py \
  analysis/tests/contracts/test_temporary_content_contract.py
```

全体回帰:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q
```

## 10. 判定

`DEV-I0-007`: **実装完了 / local acceptance pending**

ローカル受入テストPASS後に **Accepted** へ更新する。

I0-007 Accepted後は共通I0 contract chainが完了し、`S0-002 Implement CIK/submissions adapter` のI0依存が解除される。
