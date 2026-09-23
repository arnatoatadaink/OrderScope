# OrderScope — DEV-S0-006 Company Facts/XBRL Adapter 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: accepted
対象: `S0-006 / Implement Company Facts/XBRL adapter`

## 1. 結論

既存の `SecCompanyFactsAdapter` とprovider-neutral XBRL型を、WBS、WEB-009、I0-007のerror/retry境界へ再照合した。

WBS完了条件:

> Normalize XBRL facts into provider-neutral types while preserving unit/period/dimension/source.

に対し、既存実装は主要条件を満たしている。

今回、`retry_after` がprovider値のまま境界を通過していた差分を修正し、24時間を超えるdelayを `None` へ落とすfixtureを追加した。

現在は **実装完了 / local acceptance pending** とする。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/sec/company_facts.py`
- `analysis/app/orderscope_local/sec/submissions.py`

fixture:

- `analysis/tests/sec/test_company_facts.py`
- `analysis/tests/sec/test_filing_detection_acceptance.py`

Web handoff:

- `docs/REPORT_SEGMENT_REVENUE_FALLBACK_WEB_009_2026-09-04.md`

## 3. Provider-neutral XBRL型

`XbrlFact` は以下を保持する。

- concept QName
- numeric Decimal value
- unit
- period
- dimensions
- filing_source_ref
- source_accession
- source_form
- filed_on
- source_ref

SEC provider responseのlabel、description、frame、raw JSON shapeはCoreへ渡さない。

## 4. Period境界

`XbrlPeriod` は:

- instant
- duration(start/end)

を明示的に分離する。

instantとdurationの同時指定を拒否し、durationはordered start/endを要求する。

## 5. Dimension境界

WEB-009で確認した通り、SEC Company Facts APIはentity-wide standard facts向けで、segment dimension/custom taxonomyを完全には供給しない。

そのためCompany Facts decode時は、provider payloadにdimensionが無いものを推測せず:

`dimensions=()`

として保持する。

一方、dimension-aware XBRL / filing-instance側の入力では `normalize_xbrl_fact(... dimensions=...)` が:

- axis QName
- member QName
- canonical sort
- duplicate axis拒否

を保持する。

つまり「dimensionが無いCompany Factsをsegment factへ推定変換する」ことはしない。

## 6. Source境界

各factで:

- source accession
- source form
- filed date
- canonical EDGAR filing root
- Company Facts endpoint source ref

を保持する。

Company Facts root CIKとfact accession prefixが一致しない場合はinvalid responseとしてrejectする。

## 7. Bounded fetch / pagination

adapter input:

- canary source key
- half-open filed-date window
- cursor
- page size

を使用する。

window filter後にdeterministic sortし、`offset:N` cursorでpage化する。

canary外source、invalid cursor、invalid page size、non-emptyでないwindowはrejectする。

## 8. Error / retry境界

provider failureはsanitized `ErrorInfo`へ変換する。

今回、S0-005およびI0-007と揃えて:

- negative retry_after
- 24時間超 retry_after

を境界外として `None` に落とすよう修正した。

unknown transport exceptionは:

- category: `transport_error`
- retryable: `True`
- generic message

のみを返し、provider bodyやsecret-like detailを返さない。

malformed provider responseは:

- category: `invalid_response`
- retryable: `False`

とする。

## 9. Fixture coverage

既存 + 今回追加fixture:

- unit保持
- duration period保持
- instant period保持
- dimension canonicalization
- source accession
- filing source ref
- provider-only metadata非露出
- bounded window
- pagination
- malformed response
- cross-company accession reject
- ambiguous period reject
- invalid cursor
- canary外source reject
- transport error sanitization
- bounded retry_after

## 10. ローカル受入

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/sec/test_company_facts.py \
  analysis/tests/sec/test_filing_detection_acceptance.py \
  analysis/tests/contracts/test_provider_contract.py
```

より広いSEC slice:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/sec \
  analysis/tests/contracts/test_provider_contract.py
```

## 11. 判定

`DEV-S0-006`: **完了 / Accepted**

2026-09-23にCodexDesktop側で指定受入テストを再実行し、`27 passed in 3.19s` を確認したため **Accepted** とする。

これでS0-002〜006が揃ったため、次は `S0-007 Filing-detection acceptance test` を正式完了へ進める。
