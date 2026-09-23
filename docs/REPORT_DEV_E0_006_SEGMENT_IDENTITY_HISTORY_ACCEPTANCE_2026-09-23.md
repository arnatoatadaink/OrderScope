# OrderScope — DEV-E0-006 SegmentIdentityHistory 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: implementation complete / local acceptance pending
対象: `E0-006 / Implement SegmentIdentityHistory`

## 1. 結論

既存の `analysis/app/orderscope_local/earnings/segment_identity.py` を、
WEB-009 / E0-005 と再照合した。

WBS完了条件:

> Track rename/merge/split/recast without equating segments by name alone.

は既存実装でほぼ充足していた。

今回、履歴edgeの整合性を補強した。

- cross-instrument edge禁止
- RECASTは同一stable segment identityのみ
- INTRODUCEDは1 identity生成
- RETIREDは1 identity終了

現在は **実装完了 / local acceptance pending** とする。

## 2. Stable identity

`SegmentIdentityVersion` は issuer labelをidentityとして使わず、明示的な `segment_id` を持つ。

保持項目:

- segment_id
- instrument_id
- classification_role
- issuer_label
- valid_from / valid_to
- as_reported_at
- filing_accession
- provenance
- recast flag

## 3. Classification role

role:

- reportable_segment
- disaggregated_business
- market_platform

同じlabelでもroleが違えば別identityとして扱う。

NVIDIAのreportable segmentとmarket-platform presentationを同一視しない。

## 4. History changes

明示的edge:

- INTRODUCED
- RENAMED
- MERGED
- SPLIT
- RECAST
- RETIRED

renameは1→1。

mergeはmany→1。

splitは1→many。

recastは今回の補強により同一stable idの1→1のみ許可する。

introduced/retiredも単一identity境界を要求する。

## 5. Cross-instrument boundary

今回、AMD segmentからNVDA segmentへ直接履歴edgeを張るようなcross-instrument relationをrejectするよう補強した。

edgeが参照する全segment_idは同一instrumentに属する必要がある。

## 6. Recast boundary

WEB-009ではAMD/NVIDIAとも過去periodのrecastが存在する。

RECASTはrename/merge/splitではなく、同じstable segment identityに対する再提示として扱う。

したがって:

- from id = to id
- one-to-one

を必須化した。

## 7. Version interval

同じstable segment_idのversionはvalidity intervalを重複できない。

`resolve_segment_version` は:

- stable segment_id
- on_date
- optional classification role

で解決する。

issuer label検索はidentity resolutionに使わない。

## 8. AMD/NVIDIA Canary fixture

既存fixture:

- AMD Client + Gaming → Client and Gaming merge
- AMD Data Center recast
- NVIDIA same label / different role
- overlapping stable-id versions reject
- merge shape / unknown refs reject
- label-only lookup reject

今回追加:

- AMD↔NVDA cross-instrument edge reject
- RECASTで別stable idへ遷移するcase reject

## 9. Fact / provenance境界

各version/edgeは:

- filing accession
- as_reported_at
- Provenance

を保持する。

表示labelだけを根拠にhistoryを作らない。

## 10. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/earnings/test_segment_identity.py \
  analysis/tests/earnings/test_segment_revenue.py
```

E0全体を広く確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/earnings
```

## 11. 判定

`DEV-E0-006`: **実装完了 / local acceptance pending**

local test PASS後にAccepted化する。

Accepted後の次の主経路は `E0-007 — earnings Canary quality report` とする。
