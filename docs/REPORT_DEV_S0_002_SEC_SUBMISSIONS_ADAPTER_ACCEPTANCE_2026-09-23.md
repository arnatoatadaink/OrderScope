# OrderScope — DEV-S0-002 SEC CIK/submissions adapter 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: implementation complete / local acceptance pending
対象: `S0-002 / Implement CIK/submissions adapter`

## 1. 結論

`S0-002` は先行実装済みの `SecSubmissionsAdapter` とfixtureを、Accepted済みのI0共通contract chainおよびWEB-005/S0-001接続条件と再照合した。

WBS完了条件:

> Incrementally fetch AMD/NVDA filing lists in bounded windows without leaking vendor JSON into Core.

に対し、既存実装は必要な境界を満たしている。今回、新規コード変更は不要と判断した。

ただしI0-007でprovider timestamp UTC契約を更新した後、SEC submissions専用testはまだ再実行していないため、状態は **実装完了 / local acceptance pending** とする。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/sec/submissions.py`
- `analysis/app/orderscope_local/sec/__init__.py`
- `analysis/app/orderscope_local/config.py`

共通契約:

- `analysis/app/orderscope_local/contracts/provider.py`
- `analysis/app/orderscope_local/contracts/checkpoint.py`
- `analysis/app/orderscope_local/contracts/identity.py`

fixture:

- `analysis/tests/sec/test_submissions.py`
- `analysis/tests/sec/test_filing_detection_acceptance.py`

接続条件:

- `docs/REPORT_SEC_ACCESS_CONDITIONS_WEB_005_2026-09-04.md`

## 3. Corporate Canary境界

v0.1 S0-002はAMD/NVDAのみを対象とする。

| key | ticker | CIK |
|---|---|---|
| `sec:submissions:amd` | AMD | `0000002488` |
| `sec:submissions:nvda` | NVDA | `0001045810` |

canary外source keyはnetwork access前に拒否する。

## 4. SEC access条件への対応

WEB-005で引き渡された条件に対して:

- declared User-Agentを必須化
- User-Agentにcontact addressを要求
- SEC source-wide limiter interfaceを利用
- default limiterは8 requests/sec
- public ceiling 10 requests/sec超を拒否
- `data.sec.gov/submissions/CIK##########.json` をprimary endpointとする
- referenced historical submissions JSONを必要なwindowに限って取得
- authentication/API keyを要求しない

を実装済みである。

実rate coordinationを複数process/machine間で共有することはS0-002のin-process adapter contract外であり、運用scheduler/limiter統合時に扱う。

## 5. Bounded incremental取得

`AdapterRequest` の:

- `source_key`
- half-open `window_start / window_end`
- opaque cursor
- bounded `page_size`

を使用する。

root submissionsのrecent rowsと、windowに交差するhistorical fileだけを読み込み、filing dateがrequest window内のrowだけを残す。

normalized rowsをdeterministicに:

`(filingDate, accessionNumber)`

でsortし、`offset:N` cursorでpage化する。

page間でoriginal bounded windowは共通I0 contractにより維持される。

## 6. Provider JSON境界

SEC columnar JSON shapeは `submissions.py` 内でdecodeし、Coreへそのまま渡さない。

AdapterItemへ出すnormalized metadata:

- CIK
- ticker
- accession
- raw form
- filing date
- period end
- SEC source acceptance timestamp文字列
- primary document name

のみとする。

`filings` / `recent` / historical provider response structureはnormalized Core modelへ漏らさない。

## 7. Stable identity / idempotency境界

各filingは:

`StableIdentity.filing_accession(accession)`

を使用する。

normalized metadataをcanonical JSONへ変換し、SHA-256 `ContentHash` を生成する。

したがって後続S0-003はaccepted I0-004 classifierとaccession identityを利用してNEW / DUPLICATE / CONFLICTを判断できる。

## 8. Checkpoint / retry境界

transport failureはprovider bodyや例外文字列をCoreへ露出させず、sanitized `ErrorInfo` へ変換する。

- category
- retryable
- bounded retry_after
- generic message

のみを返す。

error pageはcursorをadvanceしないため、I0-003 `checkpoint_for_page()` でsafe resume stateへ変換できる。

## 9. Fixture coverage

`test_submissions.py` は以下を確認している。

- AMD bounded recent取得
- provider JSON正規化
- intersectするhistoryのみ取得
- bounded pagination / cursor
- canary外source拒否
- malformed cursor拒否
- declared User-Agent必須
- retryable transport failureのsanitization
- malformed responseのnonretryable error化
- root CIK mismatch拒否
- cross-company historical file拒否
- non-UTC / invalid page sizeをnetwork前に拒否
- limiter 8 req/s動作
- SEC public ceiling 10 req/s超拒否

`test_filing_detection_acceptance.py` ではAMD/NVDA両方をfixture replayし、後続S0-003/S0-004との接続も既に部分検証されている。

## 10. ローカル受入

推奨最小テスト:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/sec/test_submissions.py \
  analysis/tests/contracts/test_provider_contract.py
```

SEC統合sliceも同時に確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/sec/test_submissions.py \
  analysis/tests/sec/test_filing_detection_acceptance.py \
  analysis/tests/contracts/test_provider_contract.py
```

WSL書き込み制限が続く場合は、前回I0-007と同様にデータ・Python環境・uv cacheのみ `/tmp` へ切り替えてよい。source checkoutとtest対象はremote同期済み正本を使用する。

## 11. 判定

`DEV-S0-002`: **実装完了 / local acceptance pending**

local test PASS後に **Accepted** へ更新する。

Accepted後の次の主作業は `S0-003 Persist FilingRecord` とする。

なお `S0-004` form filterは既に実装済みで、S0-007 full acceptanceはS0-003/005/006完了後に行う。
