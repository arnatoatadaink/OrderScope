# OrderScope — DEV-E0-004 Basic Earnings Facts 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: accepted
対象: `E0-004 / Extract basic earnings Facts`

## 1. 結論

既存の `analysis/app/orderscope_local/earnings/basic_facts.py` と
専用fixtureを、Accepted済みE0-002/E0-003およびI0-005 Fact Store contractへ再照合した。

WBS完了条件:

> Store revenue, net income, EPS, etc. with period/unit/source; never infer missing values.

は既存実装で充足している。

本体コードの追加修正は不要。現在は **実装完了 / local acceptance pending** とする。

## 2. 対応metric

`BasicEarningsMetricType`:

- revenue
- net_income
- basic_eps
- diluted_eps

EPS系はper-share unitとしてFact化する。

## 3. 明示入力境界

`ObservedEarningsMetric` は以下を明示入力として要求する。

- instrument_id
- fiscal_year_label
- fiscal_quarter
- period_end
- metric_type
- value
- currency
- accounting_basis
- assertion_kind
- provenance

optional:

- period_start
- extraction_confidence

valueはfinite Decimal、currencyは明示的なuppercase 3-letter code、period_end/provenanceは必須。

## 4. 推測禁止

E0-004は既に観測された値だけをFact化する。

次を推測・補完しない。

- 欠損value
- currency
- fiscal label
- period_end
- period_start
- published/event/source timestamps

period_startが不明ならnullのまま保持する。

## 5. Fact / Evidence

各observationから:

- source-grounded Fact
- supporting Evidence

を作成する。

Fact:

- `earnings.<metric_type>`
- amount
- currency
- accounting_basis
- fiscal year/quarter
- unit
- period
- provenance

Evidence:

- source locator
- Tier-1 official quality
- durable metadata retention
- reciprocal Fact/Evidence reference

生成後に `validate_fact_store` を通す。

## 6. GAAP / non-GAAP

accounting basisはFact value内へ明示保存する。

同じmetric_typeでも:

- GAAP
- NON_GAAP

は別Fact identityとなり、上書き・統合しない。

## 7. SEC / IR source境界

同じsemantic valueがSECとIR両方で観測されても、それぞれ独立したsource-grounded Fact/Evidenceとして保持する。

cross-source reconciliationはE0-007の責務であり、E0-004では一方へ潰さない。

## 8. Idempotency

Fact identityには:

- instrument
- fiscal label
- period
- metric type
- value
- currency
- accounting basis
- assertion kind
- source_ref
- content_hash

を含める。

同一source/hash・同一source semanticsの再取得はidempotentにcollapseする。

operational retrieval/acceptance時刻だけが異なる場合は、最初のobservationを保持する。

published_at等のsource semanticsが変わる場合はsilent duplicateにせずContractViolationとする。

## 9. Canary / source discipline

v0.1 corporate canaryはAMD/NVDAに限定する。

unsupported instrumentはrejectする。

source ref/hashはI0-002 Provenanceを使用する。

## 10. Fixture coverage

既存fixtureで以下を確認する。

- revenue Fact/Evidence
- exact Decimal保持
- diluted EPS per-share unit
- GAAP/non-GAAP分離
- SEC/IR同値の別source Fact保持
- exact duplicate idempotency
- NVDA FY2027 label保持
- invalid value reject
- invalid currency reject
- canary外instrument reject
- period_start/source time非推測
- repeat retrieval時のfirst observation保持
- conflicting source timestamp reject

## 11. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/earnings/test_basic_facts.py \
  analysis/tests/earnings/test_basic_facts_idempotency.py \
  analysis/tests/contracts/test_fact_store_contract.py
```

E0連携まで広く確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/earnings \
  analysis/tests/contracts/test_earnings_contract.py \
  analysis/tests/contracts/test_fact_store_contract.py
```

## 12. 判定

`DEV-E0-004`: **完了 / Accepted**

2026-09-23にCodexDesktop側で指定受入テストを実行し、`18 passed in 4.09s` を確認したため **Accepted** とする。

次の主経路は `E0-005 — segment-revenue fallback chain` とする。
