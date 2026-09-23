# OrderScope — DEV-S0-005 Filing Document Acquisition 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: implementation complete / local acceptance pending
対象: `S0-005 / Implement filing-document acquisition`

## 1. 結論

既存の `SecFilingDocumentAcquirer` を、Accepted済みの `S0-003` FilingRecord、`I0-006` temporary-content lifecycle、`I0-007` provider-neutral error/secret boundaryと再照合した。

WBS完了条件:

> Store document as hashed temporary content; acquisition failure remains retryable.

に対し、既存実装は主要条件を満たしている。

今回、受入fixtureを追加して以下を明示した。

- successful acquisitionは `TEMPORARY_SUCCESS` retention classでSTAGEDされる
- temporary storage failureもprovider body/secretを漏らさず `transport_error / retryable=True` へsanitizationされる

コード差分はtest強化のみで、acquirer本体の変更は不要だった。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/sec/filing_documents.py`
- `analysis/app/orderscope_local/sec/filing_records.py`
- `analysis/app/orderscope_local/contracts/temporary_content.py`

fixture:

- `analysis/tests/sec/test_filing_documents.py`
- `analysis/tests/sec/test_filing_detection_acceptance.py`

## 3. Hash / temporary content境界

取得したprimary document bodyはdurable FilingRecordへ埋め込まず、SHA-256を計算する。

- `content_hash = sha256(body)`
- `content_ref = tmp:sha256:<digest>`

temporary storeへbodyを渡した後、metadata側には `TemporaryContent` のみを返す。

successful acquisitionでは:

- retention class: `TEMPORARY_SUCCESS`
- initial state: `STAGED`
- default retention: 24 hours
- maximum configured retention: 30 days

となる。

## 4. Source / identity境界

入力は `FilingRecord` とし、primary document refがcanonical EDGAR filing root配下であることを検証する。

reporting-owner filingなどでissuer CIKとaccession prefixのfiler CIKが異なる場合も、archive pathはaccession prefix側を使用する。

primary document refが欠損、外部host/root、非canonical SEC metadataの場合はnetwork access前にrejectする。

## 5. Bounded acquisition

- default max document size: 25 MiB
- configured upper bound: 100 MiB
- empty documentをreject
- size超過をnonretryable `document_too_large` とする
- declared SEC User-Agentを要求
- SEC limiterを取得ごとに使用

## 6. Failure / retry境界

`SecRequestFailure` はsanitized `ErrorInfo`へ変換する。

- provider category
- retryable
- generic message
- bounded retry_after

のみを返す。

retry-afterは0〜24時間だけ境界を通し、それ以外は `None` とする。

unknown transport failureおよびtemporary store failureは:

- category: `transport_error`
- retryable: `True`
- message: generic SEC filing document request failed

とし、例外本文・provider body・secret-like文字列を返さない。

失敗時は `content_hash=None`、`temporary_content=None` とする。

## 7. I0-006整合

bodyそのものは `TemporaryContent` contractへ入れない。

TemporaryContentにはhash-derived bounded refとlifecycle metadataのみを保持するため、durable metadataとtemporary bodyの境界を維持する。

抽出成功後のstate transition、削除、deletion proofは後続retention/extraction controllerの責務であり、S0-005ではSTAGEDまでを責務とする。

## 8. Fixture coverage

既存 + 今回追加fixtureで以下を確認する。

- SHA-256 hash
- temporary content ref
- TEMPORARY_SUCCESS retention
- STAGED state
- expiry
- provider failure retry
- bounded retry-after
- unknown exception sanitization
- temporary store exception sanitization
- empty / oversize reject
- canonical document reference
- UTC clock
- User-Agent / retention / size limit
- reporting-owner accession archive path

## 9. ローカル受入

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/sec/test_filing_documents.py \
  analysis/tests/contracts/test_temporary_content_contract.py \
  analysis/tests/sec/test_filing_detection_acceptance.py
```

より広いSEC slice:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/sec \
  analysis/tests/contracts/test_temporary_content_contract.py
```

## 10. 判定

`DEV-S0-005`: **実装完了 / local acceptance pending**

fixture追加後のlocal test PASSでAccepted化する。

Accepted後は `S0-006 Company Facts/XBRL adapter` を正式受入し、S0-002〜006が揃った時点で `S0-007 Filing-detection acceptance test` へ進む。
