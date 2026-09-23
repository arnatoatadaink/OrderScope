# OrderScope — DEV-E0-003 Company IR Fallback 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: accepted
対象: `E0-003 / Design/implement company-IR fallback`

## 1. 結論

既存の `analysis/app/orderscope_local/earnings/ir_fallback.py` を
WEB-008 / E0-001 / E0-002 / I0-002 / I0-004 と再照合した。

既存実装は以下を既に満たしていた。

- issuer別official host boundary
- discovery URLとcanonical release URLの分離
- content hash保持
- issuer fiscal label / quarter / period_end保持
- SEC / IR Evidence両方の保持
- SEC-first source priority
- duplicate SEC accession collapse
- duplicate IR discovery collapse
- same canonical URL + changed hashをsilent duplicateにしない

今回不足していた acquisition stateを追加した。

- retrieved_at
- COMPLETE / PARTIAL / ERROR
- error_category
- partial時に成功releaseを保持可能
- ERROR時は成功releaseを同時保持不可

現在は **実装完了 / local acceptance pending** とする。

## 2. Official issuer boundary

AMD IR source:

- `ir.amd.com`

NVIDIA source:

- `investor.nvidia.com`
- `nvidianews.nvidia.com`

configured issuer/sourceとinstrument identityが一致しない場合はrejectする。

URLはHTTPS、credential/fragmentなし、bounded textを要求する。

## 3. Discovery / canonical URL

`IrReleaseRecord` は:

- discovery_url
- canonical_release_url

を別fieldで保持する。

listing/archive URL自体をcanonical earnings releaseとして扱わない。

URL patternからrelease URLを生成せず、discoveryで得た個別release URLを保持する前提とする。

## 4. Hash / update boundary

canonical release contentは `ContentHash` で識別する。

複数のlisting/archive pathから:

- same canonical URL
- same hash

へ到達した場合はduplicate discoveryとしてcollapseする。

same canonical URLでhashが変わった場合はsilent duplicateにせず、update/conflictとして上位処理へ残す。

## 5. SEC / IR reconciliation

`reconcile_sec_ir_evidence` はevent identityを:

- instrument
- period_end

で照合する。

SEC candidateとIR releaseが同一eventなら、片方を捨てず両方保持する。

source priority:

1. SEC
2. issuer IR

はdiscovery/reconciliation順序であり、IR Evidenceを破棄する順位ではない。

## 6. Acquisition status boundary

今回追加した `IrFallbackPage`:

- source
- discovery_url
- releases
- status
- retrieved_at
- error_category

を保持する。

status:

- COMPLETE
- PARTIAL
- ERROR

COMPLETEではerror_category禁止。

PARTIALでは成功releaseとerror_categoryを併存可能。

ERRORではerror_category必須、成功releaseの保持は禁止。

retrieved_atはUTC必須。

## 7. Fiscal semantics

issuer fiscal labelをそのまま保持する。

NVIDIAのFY2027等をcalendar yearから再計算しない。

period_endは別fieldで保持する。

published_atはsourceが確認できた精度のみ `SourceTimestamp` で保持する。

## 8. Fixture coverage

既存 + 今回追加fixture:

- SEC + IR reconciliation
- SEC-first source priority
- duplicate IR discovery collapse
- duplicate SEC accession collapse
- conflicting SEC evidence reject
- same IR URL changed hash reject
- IR-only fallback
- issuer fiscal label保持
- cross-event reject
- missing SEC period reject
- cross-issuer/generated URL reject
- COMPLETE acquisition
- PARTIAL acquisition
- ERROR + release reject
- non-UTC retrieved_at reject

## 9. Local acceptance

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/earnings/test_ir_fallback.py \
  analysis/tests/sec/test_earnings_detection.py \
  analysis/tests/contracts/test_earnings_contract.py
```

より広く確認する場合:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/earnings \
  analysis/tests/sec/test_earnings_detection.py \
  analysis/tests/contracts/test_earnings_contract.py
```

## 10. 判定

`DEV-E0-003`: **完了 / Accepted**

2026-09-23にCodexDesktop側で指定受入テストを実行し、`27 passed in 5.01s` を確認したため **Accepted** とする。

次の主経路は `E0-004 — Extract basic earnings Facts` とする。
