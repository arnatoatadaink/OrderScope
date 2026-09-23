# OrderScope — DEV-E0-002 SEC Earnings Detection 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: accepted
対象: `E0-002 / Implement SEC earnings detection`

## 1. 結論

既存の `analysis/app/orderscope_local/sec/earnings_detection.py` を、Accepted済みのS0-007 / E0-001とWBSへ再照合した。

WBS完了条件:

> Build earnings candidates from 10-Q/10-K and relevant 8-K/attachments.

は既存実装で充足している。

今回、8-K amendmentの回帰を明示するため `8-K/A + Item 2.02` fixtureを追加した。本体コードの修正は不要。

現在は **実装完了 / local acceptance pending** とする。

## 2. Candidate detection

`detect_sec_earnings_candidate` はFilingRecordから候補を返す。

直接候補:

- 10-Q / 10-Q/A
- 10-K / 10-K/A

8-K / 8-K/Aは、以下の明示Evidenceがある場合のみ候補とする。

- Item 2.02
- earnings/result semanticsをdescriptionで明示した99.x attachment

## 3. 推測禁止

generic 8-Kは候補にしない。

generic Exhibit 99.1も、descriptionにearnings/results意味がなければ候補にしない。

E0-002では数値抽出を行わず、revenueやactual release time等をcandidateへ付与しない。

## 4. Attachment boundary

attachmentはfiling root配下であることを必須とする。

外部URLや別filing rootはrejectする。

`SecFilingAttachmentHint` はdocument ref / exhibit type / descriptionをbounded canonical textとして保持する。

## 5. Amendment boundary

periodic report amendmentはbase filingと別accessionのcandidateとして保持する。

CURRENT_REPORT familyでは8-K/Aも8-Kと同じ検出規則を使う。

今回 `8-K/A + Item 2.02` を専用fixtureへ追加した。

## 6. Detection reason

provider-neutral reason:

- `PERIODIC_REPORT`
- `CURRENT_REPORT_ITEM_202`
- `EARNINGS_ATTACHMENT`

Item 2.02とearnings attachmentが併存する場合は、重複せず両方のreasonを保持する。

## 7. E0-001との境界

E0-002は「earnings candidateであるか」のみ判定する。

以下はE0-001 / 後続E0タスクの責務であり、E0-002では推定しない。

- scheduled release
- actual release
- earnings call time
- metric values
- currency
- GAAP / non-GAAP
- fiscal label normalization

## 8. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/sec/test_earnings_detection.py \
  analysis/tests/contracts/test_earnings_contract.py \
  analysis/tests/sec/test_filing_detection_acceptance.py
```

より広く確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/sec \
  analysis/tests/contracts/test_earnings_contract.py
```

## 9. 判定

`DEV-E0-002`: **完了 / Accepted**

2026-09-23にCodexDesktop側で指定受入テストを実行し、`21 passed in 5.20s` を確認したため **Accepted** とする。

次の主経路は `E0-003 — Design/implement company-IR fallback` とする。
