# OrderScope — DEV-I0-003 cursor / checkpoint contract 実装・受入記録

作成日: 2026-09-22（Asia/Tokyo）
Status: accepted
対象: `DEV-I0-003 / I0-003 Implement cursor/checkpoint contract`

## 1. 結論

`DEV-I0-003` の既存実装をレビューし、WBS完了条件の大部分が既に実装済みであることを確認した。

追加レビューで、provider境界では禁止されている「partial page without error」が、永続checkpoint単体では表現可能という不整合を1点確認したため、`AcquisitionCheckpoint` 側にも `PARTIAL => error required` の不変条件を追加した。

実装差分と専用テスト追加は完了している。新しい差分に対するローカルpytest実行証跡は未取得のため、現時点の状態は **実装完了 / local acceptance pending** とする。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/contracts/checkpoint.py`
- `analysis/app/orderscope_local/contracts/provider.py`
- `analysis/app/orderscope_local/contracts/__init__.py`

専用テスト:

- `analysis/tests/contracts/test_checkpoint_contract.py`
- `analysis/tests/contracts/test_provider_contract.py`

## 3. WBS完了条件との対応

WBS `I0-003` の完了条件:

> Persist provider/source bounded window, cursor, resume state, partial/error state.

| 要求 | 実装 |
|---|---|
| provider/source scope | `CheckpointScope(provider_key, source_key)` |
| bounded window | `BoundedWindow(start, end)` |
| cursor | `OpaqueCursor` / `resume_cursor` |
| resume state | `AcquisitionCheckpoint.resume_request()` |
| in-progress state | `CheckpointState.IN_PROGRESS` |
| complete state | `CheckpointState.COMPLETE` |
| partial state | `CheckpointState.PARTIAL` |
| error state | `CheckpointState.ERROR` |
| retry metadata | `CheckpointError.retry_after` / `retry_not_before` |
| persistence | `to_record()` / `from_record()` |
| provider handoff | `checkpoint_for_page()` |

## 4. 契約上の重要点

- checkpointは `provider_key + source_key` にscopeされる。
- resumeは保存済みのhalf-open windowを広げない。
- provider cursorはopaqueな値として保持し、意味を推測しない。
- complete checkpointはresumeできない。
- initial request failureはcursorを捏造せず `None` のまま再開可能。
- partial/errorではunsafeなcursor advanceを行わず、最後のsafe request boundaryを保持する。
- retry metadataは最大24時間へboundedされる。
- durable recordへprovider response bodyやerror messageを保存しない。
- record schemaは明示field以外を拒否する。
- `PARTIAL` は必ずsanitized `CheckpointError` を伴う。

## 5. 今回の追加差分

`AcquisitionCheckpoint.__post_init__` に次の不変条件を追加した。

- `CheckpointState.PARTIAL` かつ `error is None` を `ContractViolation` とする。

対応テストとして `test_checkpoint_rejects_unbounded_or_ambiguous_state` に ambiguous partial checkpoint fixtureを追加した。

これにより `assert_page_contract()` とdurable checkpoint contractでpartial/error semanticsが一致する。

## 6. 検証状況

既存テストは以下をカバーしている。

- provider/source scope
- bounded resume window
- cursor round-trip
- partial/error persistence
- initial request error resume
- complete non-resumability
- retryable/error constraints
- unknown durable fields rejection
- invalid persisted types
- provider page -> checkpoint handoff
- terminal page -> complete checkpoint
- partial page safe-boundary resume
- secret/raw provider body exclusion

今回追加したコードとテストはremoteへ反映済みであり、2026-09-22にCodexDesktop側で同期後の専用テストを実行し、`28 passed in 2.85s`、作業ツリーcleanを確認した。

推奨受入コマンド:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/contracts/test_checkpoint_contract.py analysis/tests/contracts/test_provider_contract.py
```

全体回帰を行う場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q
```

## 7. 判定

`DEV-I0-003`: **完了 / Accepted**

CodexDesktop側の専用テストPASSとclean working treeを受入根拠として **Accepted** とする。

次作業は `DEV-I0-004 idempotency / duplicate boundary` とする。
