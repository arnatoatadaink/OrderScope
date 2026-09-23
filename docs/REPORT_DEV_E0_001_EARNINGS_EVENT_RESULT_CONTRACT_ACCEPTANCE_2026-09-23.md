# OrderScope — DEV-E0-001 Earnings Event/Result Contract 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: implementation complete / local acceptance pending
対象: `E0-001 / Define earnings event/result contract`

## 1. 結論

既存の `analysis/app/orderscope_local/contracts/earnings.py` と
`analysis/tests/contracts/test_earnings_contract.py` を、WBSおよび
`REPORT_EARNINGS_EVENT_RESULT_CONTRACT_WEB_007_2026-09-04.md` と再照合した。

E0-001の主要完了条件:

> Keep scheduled time, actual release time, fiscal period, currency, GAAP/non-GAAP, and source distinct.

は既存contractで充足している。

本体コードの追加修正は不要だった。現在は **実装完了 / local acceptance pending** とする。

## 2. Event contract

`EarningsEvent` は以下を分離して保持する。

- instrument_id
- event_kind
- fiscal_year_label
- fiscal_quarter
- period_end
- scheduled_at
- scheduled_release_window
- actual_release_at
- evidence

releaseとcallは `EarningsEventKind` で分離する。

## 3. Scheduled / actual release境界

release予定が日付 + market windowしか確定していない場合:

- scheduled_at = DATE_ONLY
- scheduled_release_window = AFTER_MARKET_CLOSE等

として保持し、固定clock timeを発明しない。

`actual_release_at` はnullable。

exact release instantがsourceで確認できない場合は `None` のまま保持する。

SEC accepted timestampやearnings call scheduled timeからactual release timeを補完しない。

## 4. Call境界

earnings callはrelease eventとは別event。

callでは:

- scheduled_atはestablished instant必須
- release window禁止
- actual_release_at禁止

とする。

## 5. Fiscal period

issuer fiscal labelingをそのまま保持する。

例えばNVIDIAの `FY2027 / Q2` とcalendar year 2026を同一視しない。

period_endはcalendar dateとして独立保持する。

## 6. Result metric contract

`EarningsResultMetric` は:

- metric_type
- value
- unit
- currency
- accounting_basis
- fiscal label
- period_end
- evidence

を保持する。

GAAP / NON_GAAPは別recordとして保持し、同じmetric_typeでも上書き・統合しない。

currencyは明示的な3-letter codeのみを受け入れる。

## 7. Source role

`EarningsEvidenceRef` と `EarningsEvidenceRole` でsource roleを分離する。

既存role:

- issuer schedule announcement
- issuer result release
- SEC 8-K
- SEC Exhibit 99.1
- issuer event page

同一event/resultへ複数Evidenceを紐付けられるが、duplicate referenceはrejectする。

## 8. WEB-007 negative contract

専用fixtureで以下を確認している。

- SEC source accepted時刻をunknown actual releaseへ代入しない
- call scheduled timeをrelease timeへ転用しない
- date-only actual releaseをreject
- issuer fiscal yearをcalendar yearから再計算しない
- GAAP/non-GAAPを別recordとして維持
- invalid currencyをreject
- duplicate evidenceをreject

## 9. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/contracts/test_earnings_contract.py \
  analysis/tests/sec/test_earnings_detection.py
```

E0-002との接続を広く確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/contracts/test_earnings_contract.py \
  analysis/tests/sec
```

## 10. 判定

`DEV-E0-001`: **実装完了 / local acceptance pending**

local test PASS後にAccepted化する。

Accepted後の次の主経路は `E0-002 — Implement SEC earnings detection` とする。
