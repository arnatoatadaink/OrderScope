# OrderScope — DEV-E0-007 Earnings Canary Quality Report 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: implementation complete / local acceptance pending
対象: `E0-007 / Produce earnings Canary quality report`

## 1. 結論

既存の `analysis/app/orderscope_local/earnings/quality_report.py` を、
Accepted済みE0-004〜006とWBSへ再照合した。

WBS完了条件:

> Reconcile multiple AMD/NVDA quarters across sources; report extraction success and unresolved differences.

は既存実装でほぼ充足していた。

今回、quality reconciliationの意味境界を補強した。

- amount一致だけではagreementにしない
- currency / unitも一致した場合のみagreement
- SEC / issuer IR source判定をofficial hostnameで固定
- amount一致・currency不一致をconflict化するfixture
- hostname部分一致による偽SEC sourceをrejectするfixture

現在は **実装完了 / local acceptance pending** とする。

## 2. Basic earnings reconciliation

E0-004で生成したFactを以下でgroupする。

- instrument
- issuer fiscal year
- issuer fiscal quarter
- period_end
- fact_type
- accounting_basis

source:

- SEC
- issuer IR

を別Evidenceとして保持する。

## 3. Reconciliation status

status:

- AGREEMENT
- SINGLE_SOURCE
- CONFLICT

AGREEMENTは今回の補強により、比較可能なsource間で:

- amount
- currency
- unit

がすべて一致した場合のみ成立する。

同じamountでもUSD / JPYやUSD / USD_per_share等のsemantic差があればCONFLICTとする。

## 4. Conflict handling

E0-007はconflict時にwinning sourceを選ばない。

SEC優先はE0-003のdiscovery/reconciliation順序であり、quality reportで異なる値を自動上書きする規則ではない。

conflictは:

- source別value
- source別currency
- source別unit
- Fact record ID

を保持したまま可視化する。

## 5. Source boundary

SEC source:

- www.sec.gov
- data.sec.gov

issuer IR:

- ir.amd.com
- investor.nvidia.com
- nvidianews.nvidia.com

を正規hostnameとして判定する。

文字列中に `sec.gov` を含むだけの外部hostはSEC Evidenceとして認めない。

## 6. Multiple-period Canary

fixtureはAMD/NVDAの複数quarterを同時に含む。

例:

- AMD FY2026 Q1
- AMD FY2026 Q2
- NVIDIA FY2027 Q1
- NVIDIA FY2027 Q2

agreement / conflict / single-sourceを同じreport内で集計する。

## 7. Segment quality

E0-005の `SegmentRevenueResolution` をquality inputにする。

各segmentについて:

- EXTRACTED
- UNRESOLVED
- successful fallback method
- complete failure path

を保持する。

failure path例:

- company_facts:entity_wide_only
- xbrl_dimension:context_member_unresolved
- filing_table:table_layout_unresolved

## 8. Quality rates

report summary:

- metric_checks
- metric_agreements
- metric_single_source
- metric_conflicts
- metric_agreement_rate
- segment_checks
- segment_extracted
- segment_unresolved
- segment_extraction_rate

single-source rowはagreement rateの分母から除外する。

## 9. Deterministic report

Markdown rendererはdeterministic orderで:

- reconciliation summary
- source values
- conflicts
- segment extraction method/failure path

を出力する。

未解決差分を隠さず、人間レビュー可能な形で保持する。

## 10. Fixture coverage

既存 + 今回追加fixture:

- AMD/NVDA multiple-period reconciliation
- SEC/IR agreement
- SEC/IR value conflict
- single-source
- no winning source selection
- segment successful fallback method
- complete unresolved failure path
- deterministic Markdown
- agreement-rate denominator
- segment extraction rate
- same amount / different currency conflict
- fake SEC hostname reject

## 11. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/earnings/test_quality_report.py \
  analysis/tests/earnings/test_basic_facts.py \
  analysis/tests/earnings/test_segment_revenue.py \
  analysis/tests/earnings/test_segment_identity.py
```

E0 work package全体を確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/earnings \
  analysis/tests/contracts/test_earnings_contract.py \
  analysis/tests/sec/test_earnings_detection.py
```

## 12. 判定

`DEV-E0-007`: **実装完了 / local acceptance pending**

local test PASS後にAccepted化する。

Accepted後はE0-001〜007を完了扱いとし、M3 SEC/Earnings CanaryのE0側を完了する。
