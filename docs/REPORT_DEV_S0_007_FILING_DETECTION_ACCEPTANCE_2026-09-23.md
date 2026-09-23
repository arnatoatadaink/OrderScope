# OrderScope — DEV-S0-007 Filing Detection Acceptance 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: implementation complete / local acceptance pending
対象: `S0-007 / Filing-detection acceptance test`

## 1. 結論

S0-002〜006がAcceptedとなったため、SEC Filing acquisitionの統合受入fixtureを再レビューした。

既存fixtureは以下を既に検証していた。

- AMD/NVDA bounded submissions replay
- NEW
- DUPLICATE
- amendment
- reporting-owner accession
- partial/retryable failure
- sanitized error boundary

今回、統合受入として不足していた成功系を補強した。

- repository fixtureをversioned migration経由へ変更
- `Submissions → FilingRecord → form classification → filing-document acquisition → Company Facts` を同一fixtureで接続
- Company Facts source accession / form / filing source refがFilingRecordと一致することを確認
- successful temporary documentがhash/ref付きでstoreへ渡ることを確認

現在は **実装完了 / local acceptance pending** とする。

## 2. WBS完了条件

WBS:

> Replay fixtures and limited AMD/NVDA fetches; verify new, duplicate, amendment, partial cases.

今回のlocal acceptanceではprovider fixture replayを正式証跡とする。

実ネットワークを使うlimited AMD/NVDA fetchは、credential不要のSEC endpointでは可能だが、受入testの決定性を壊さないためCIではfixtureを正とする。live fetchを行う場合は別途canary smoke evidenceとして扱う。

## 3. 統合対象

- S0-002: SEC Submissions adapter
- S0-003: FilingRecord persistence
- S0-004: target-form filter
- S0-005: filing-document acquisition
- S0-006: Company Facts/XBRL adapter

## 4. Success path

AMD fixture:

1. SEC Submissions provider fixtureをbounded windowで取得
2. versioned migrationで作成したSQLiteへFilingRecordを保存
3. target form familyを分類
4. primary filing documentをtemporary storeへhash付きでstage
5. Company Factsをprovider-neutral XBRL factへnormalize
6. source accession/form/archive refをFilingRecordと照合

## 5. Idempotency / amendment

既存fixtureで:

- 初回write → NEW
- 同一fixture replay → DUPLICATE
- base 10-Qと10-Q/Aは別accession
- familyは同じQUARTERLY_REPORT
- amendment flagのみ分離

を確認する。

## 6. Partial / retry

Submissions / filing document / Company Factsでretryable failureをfixture化する。

- retryable statusを維持
- cursor/bodyを不正に進めない
- raw provider bodyを返さない
- secret-like exception detailを返さない
- failed document bodyをstoreしない

## 7. AMD/NVDA canary

fixtureではAMDとNVIDIAを共に含む。

NVIDIA Form 4のreporting-owner accessionでは、issuer scopeはNVDAを維持しつつ、EDGAR archive pathはaccession prefix側CIKを使う。

## 8. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/sec/test_filing_detection_acceptance.py \
  analysis/tests/sec/test_submissions.py \
  analysis/tests/sec/test_filing_records.py \
  analysis/tests/sec/test_form_filter.py \
  analysis/tests/sec/test_filing_documents.py \
  analysis/tests/sec/test_company_facts.py
```

より広く確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/sec
```

## 9. 判定

`DEV-S0-007`: **実装完了 / local acceptance pending**

local test PASS後にAccepted化する。

Accepted後はS0 SEC Filing acquisition work packageを完了扱いとし、次の主経路は `E0-001 — Define earnings event/result contract` とする。
