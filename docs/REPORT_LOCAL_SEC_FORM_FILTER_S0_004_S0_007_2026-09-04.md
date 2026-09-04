# OrderScope — SEC Form Filterローカル実装・受入試験報告

Status: `S0-004` implemented; `S0-007` fixture slice implemented / full acceptance pending dependencies
Date: 2026-09-04
Local session: `01a06629-cc5d-7d33-99c7-eaa309911188` continuation
Web handoff: `WEB-006`

## 1. 実装結果

`REPORT_SEC_FORM_FILTER_WEB_006_2026-09-04.md`のstrict allowlistを、provider-neutralなPython contractとして実装した。

- raw EDGAR form typeは入力どおり保持する。
- accept時は`family`と`is_amendment`を明示する。
- scope外・未知のformは`unsupported_form_type`として観測可能にrejectする。
- trim、case-fold、prefix一致によるcoercionは行わない。
- amendmentはbase filingを上書きせず、別accessionとして扱える分類結果を返す。
- beneficial ownershipはlegacy `SC 13D/G`とcurrent `SCHEDULE 13D/G`のraw表記を保持したまま同じfamilyへ写像する。

実装場所:

- `analysis/app/orderscope_local/sec/form_filter.py`
- `analysis/tests/fixtures/sec_form_filter_cases.json`
- `analysis/tests/sec/test_form_filter.py`

## 2. S0-004判定

対象28 raw form typeを次の10 familyへ明示的に写像した。

`8-K`、`10-Q`、`10-K`、`S-1`、`S-3`、`424B`、`DEF 14A`、`13D`、`13G`、`4`

`S-3ASR`、`DEFA14A`、`424B6`、空白・省略表記等のnear-missをacceptしないfixtureも含む。SECの履歴取得で現れるlegacy `SC 13D/G`とcurrent `SCHEDULE 13D/G`の双方を明示的にacceptする。したがって、S0-004のローカル実装条件は満たす。

## 3. S0-007判定

### 実施済み

- 全allowlistのfixture replay
- base/amendmentの同一family・別raw form判定
- 同一amendment fixture再生時の決定的な同一結果
- near-missとunknown formの明示的reject
- legacy/current 13D/G raw formの同一family写像とraw値保持

### 未実施

親計画上のS0-007全体は完了扱いにしない。次の依存が現ブランチに未実装である。

- `S0-002`: AMD/NVDA CIK submissions adapter
- `S0-003`: accession単位の冪等なFilingRecord保存
- `S0-005`: filing document取得とpartial/retry
- `S0-006`: Company Facts/XBRL adapter
- declared User-Agentを用いたAMD/NVDA限定live取得

このため、新規・重複の永続化、document/XBRL partial、live amendment検出率・coverageは未測定であり、成功を主張しない。

## 4. 次の受入条件

S0-002/003/005/006の実装後、同じfixture contractをadapter出力へ接続し、次を追加検証する。

1. AMD（CIK `0000002488`）とNVIDIA（CIK `0001045810`）だけをbounded windowで取得する。
2. 初回をnew、同一accession再取得をduplicateとして記録する。
3. baseとamendmentを別accessionの同一familyとして保持する。
4. submissions、document、Company Factsのpartial/errorとbounded retryを記録する。
5. credential、provider response body、temporary document本文をtest artifactやログへ出さない。
