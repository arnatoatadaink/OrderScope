# OrderScope — DEV-E0-005 Segment Revenue Fallback 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: accepted
対象: `E0-005 / Implement segment-revenue fallback chain`

## 1. 結論

既存の `analysis/app/orderscope_local/earnings/segment_revenue.py` を、
WEB-009 / S0-006 / E0-004 と再照合した。

WBS完了条件:

> Persist method and failure reason for Company Facts → XBRL Dimension → Filing Fallback.

は既存実装でほぼ充足していた。

ただしXBRL fact選択が accession / period / unit / dimension有無だけで、concept QNameを照合していなかったため、同periodの非revenue factを誤採用し得る差分があった。

今回:

- default revenue concept allowlist
- explicit custom revenue concept allowlist
- concept QName filter
- non-revenue concept negative fixture
- custom concept positive fixture

を追加した。

現在は **実装完了 / local acceptance pending** とする。

## 2. Fallback order

固定順序:

1. `COMPANY_FACTS`
2. `XBRL_DIMENSION`
3. `FILING_TABLE`

成功したmethodでchainを停止する。

attempt順序が崩れたresolutionはrejectする。

## 3. Attempt / failure provenance

各attemptは:

- method
- status
- failure_reason
- source_accession
- source_ref
- concept_qname
- axis/member
- raw_label
- table_role

を保持する。

失敗時もmethod/failure reasonを残し、欠損を0へ変換しない。

## 4. Failure reasons

provider-neutral reason:

- entity_wide_only
- dimension_fact_not_in_companyfacts_scope
- custom_extension_not_normalized
- concept_not_found
- period_mismatch
- unit_mismatch
- context_member_unresolved
- table_layout_unresolved
- transport_error

## 5. Company Facts境界

Company Facts stageでは:

- source accession
- period start/end
- expected unit
- allowed revenue concept
- dimensionsなし

を照合する。

Company Factsでsegment factが取得できない場合は失敗理由を保持して次段へ進む。

## 6. XBRL Dimension境界

Dimension stageでは:

- source accession
- period start/end
- expected unit
- allowed revenue concept
- dimensionsあり

を照合する。

成功時はaxis/memberをObservationとAttemptへ保存する。

複数factが同条件で一致する場合はambiguousとしてrejectし、任意選択しない。

## 7. Revenue concept境界

今回、revenue concept照合を明示化した。

default:

- `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`
- `us-gaap:Revenues`
- `us-gaap:SalesRevenueNet`

custom taxonomy extensionは自動推測せず、呼び出し側が `revenue_concepts` に明示指定する。

これにより、たとえば `us-gaap:NetIncomeLoss` がperiod/unit一致だけでsegment revenueとして採用されることを防ぐ。

## 8. Period / unit / source

3M / 6M / annual等のdurationはperiod_start/end完全一致で区別する。

quarterとYTDを相互代用しない。

XBRL成功時はexplicit Provenance必須で、Provenance source_refとXBRL source_refの一致を要求する。

## 9. Filing fallback

前2段が失敗した場合のみfiling tableへ進む。

filing observationは:

- requested instrument
- raw label
- classification role
- period
- accession

と完全一致することを要求する。

table_role必須。

## 10. Segment identityとの境界

E0-005はraw label / classification roleを保持するが、segment identityを名前だけで正規化しない。

rename / merge / split / recastは次の `E0-006 SegmentIdentityHistory` の責務。

## 11. Fixture coverage

既存 + 今回追加fixture:

- Company Facts success
- Dimension fallback
- Filing table third fallback
- all failures preserve reason
- no invented zero
- quarter vs YTD disambiguation
- explicit provenance required
- source_ref mismatch reject
- ambiguous XBRL fact reject
- non-revenue concept reject
- explicit custom revenue concept accept

## 12. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/earnings/test_segment_revenue.py \
  analysis/tests/sec/test_company_facts.py \
  analysis/tests/earnings/test_basic_facts.py
```

E0全体を広く確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/earnings \
  analysis/tests/sec/test_company_facts.py
```

## 13. 判定

`DEV-E0-005`: **完了 / Accepted**

2026-09-23にCodexDesktop側で指定受入テストを実行し、`26 passed in 3.38s` を確認したため **Accepted** とする。

次の主経路は `E0-006 — SegmentIdentityHistory` とする。
