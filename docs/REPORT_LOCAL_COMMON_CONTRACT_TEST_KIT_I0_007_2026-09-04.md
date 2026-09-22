# OrderScope — 共通provider contract test kit実装報告

Status: `I0-007` integrated; formal local acceptance pending
Date: 2026-09-04
Local session: `01a06629-cc5d-7d33-99c7-eaa309911188` continuation

## 1. 実装範囲

provider固有のHTTP・payload・保存方式を持ち込まず、adapterが返す共通ページ契約を同じ検査関数とfixtureで検証できるkitを追加した。

- `AdapterRequest`: source単位のhalf-open bounded window、cursor、page size
- `AdapterPage`: normalized items、next cursor、partial/error、provider revision、取得・利用可能時刻
- `ErrorInfo`: error category、retryable、bounded retry-after
- pagination collector: cursor進行、loop、最大ページ数、秘密非露出を検査
- timestamp validation: explicit timezoneと`available_at <= retrieved_at`
- secret boundary: credential、authorization、provider response body、Bearer/PEM風値を拒否

実装場所:

- `analysis/app/orderscope_local/contracts/provider.py`
- `analysis/app/orderscope_local/contracts/__init__.py`
- `analysis/tests/contracts/test_provider_contract.py`

## 2. 検証結果

共通fixtureで次を確認した。

- 複数ページのcursor再開と元のbounded window保持
- partial responseとretryable errorの同時表現
- retry-afterの上限検査
- cursor loopと未タイムゾーン時刻の拒否
- page size超過の拒否
- credential／authorization／raw provider response bodyの境界拒否

実行結果（2026-09-04）:

```text
58 passed
```

## 3. 受入境界

2026-09-22時点で `I0-003 / I0-004 / I0-006` はすべてAcceptedとなり、共通kitへの統合も完了した。

正式受入レビューではprovider境界のoperational timestampをI0-002/I0-003と同じUTC必須へ統一し、bounded paginationの `max_pages` 超過fixtureを追加した。追加差分後のローカルpytestは未実行のため、正式状態は **local acceptance pending** とする。

詳細は `REPORT_DEV_I0_007_PROVIDER_NEUTRAL_CONTRACT_TEST_ACCEPTANCE_2026-09-22.md` を参照する。

本変更はnetwork、provider credential、remote D1、raw bodyをテストへ持ち込まない。
