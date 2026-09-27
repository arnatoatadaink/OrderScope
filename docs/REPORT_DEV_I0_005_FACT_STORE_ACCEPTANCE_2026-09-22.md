# OrderScope — DEV-I0-005 Fact Store logical schema 受入記録

作成日: 2026-09-22（Asia/Tokyo）
Status: accepted
対象: `DEV-I0-005 / I0-005 Finalize Fact Store logical schema`

## 1. 結論

`DEV-I0-005` は既存ADR、実装、contract fixtureを再レビューし、I0-002〜I0-004との整合およびWBS完了条件を満たしているため **完了 / Accepted** とする。

追加コード変更は不要である。既存の `ADR_FACT_STORE_LOGICAL_SCHEMA_v0.1.md` と `fact_store.py` をv0.1 Fact Store論理境界の正とする。

## 2. 受入対象

ADR:

- `docs/ADR_FACT_STORE_LOGICAL_SCHEMA_v0.1.md`

実装:

- `analysis/app/orderscope_local/contracts/fact_store.py`
- `analysis/app/orderscope_local/contracts/provenance.py`
- `analysis/app/orderscope_local/contracts/identity.py`
- `analysis/app/orderscope_local/contracts/__init__.py`

fixture / contract test:

- `analysis/tests/contracts/test_fact_store_contract.py`
- `analysis/tests/contracts/test_provenance_contract.py`
- `analysis/tests/contracts/test_identity_contract.py`

## 3. WBS完了条件との対応

WBS `I0-005` の完了条件:

> Store Fact, Evidence, Relationship, Derived Metric, and Interpretation as distinct historical records.

| 要求 | 実装 |
|---|---|
| Fact | `Fact` |
| Evidence | `Evidence` |
| Relationship | `Relationship` |
| Derived Metric | `DerivedMetric` |
| Interpretation | `Interpretation` |
| 共通record envelope | `RecordEnvelope` |
| append-only history | `supersedes_record_id` + predecessor保持 |
| cross-record validation | `validate_fact_store()` |
| as-of visibility | `records_available_as_of()` |

## 4. I0-002 provenanceとの整合

source-grounded `Fact` / `Evidence` / `Relationship` はaccepted I0-002 `Provenance` を利用する。

- source ref
- SHA-256 content hash
- provider revision
- event / publish / file / source-accept時刻
- available / retrieved / Store accepted時刻

は一つの時刻へ潰さず保持する。

Fact Storeの `accepted_at` と `Provenance.accepted_at` は一致を必須とし、source時刻がunknownの場合にStore時刻から補完しない。

`records_available_as_of()` はStore acceptanceだけでなく `Provenance.available_at` も確認し、look-aheadを防止する。

## 5. I0-003 checkpointとの境界

I0-003 checkpointは取得streamのresume stateであり、Fact Store recordへ混在させない。

checkpointのprovider/source window、cursor、partial/error stateは取得運用境界として保持し、Fact Storeはaccepted informationの履歴を保持する。

この責務分離により、provider retry/resume状態がFactやEvidenceの意味論へ混入しない。

## 6. I0-004 idempotencyとの整合

I0-004のstable external identityとFact Storeの `record_id` は別概念である。

- I0-004: accession/article/signal stable ID + content hashからNEW/DUPLICATE/UPDATE/CONFLICTを判定
- I0-005: accepted logical recordをimmutableなinternal `record_id` で履歴化

UPDATEやcorrectionが成立した場合も既存recordを上書きせず、新recordを作成し `supersedes_record_id` で履歴を接続する。

content hash差異だけでUPDATEを推測しないI0-004契約と整合する。

## 7. Record境界

### Fact

source-grounded observation / correction / amendment / withdrawal / pending reviewを保持する。
非pending source-grounded FactにはEvidenceを要求する。

### Evidence

supporting / contradicting / context / extraction spanをFact Storeの独立recordとして保持する。
source bodyそのものではなくlocator/hash/quality/retention metadataを保持する。

### Relationship

entity/record間のtyped edgeを保持する。
source-grounded relationshipとregistry-internal relationshipを分離し、後者へ架空のprovenanceを付与しない。

### DerivedMetric

deterministic calculationをFactと分離し、method versionと完全なrecord/dataset lineageを要求する。

### Interpretation

human/rule/modelによるassessmentをFactと分離し、basis recordとmethodを明示する。

## 8. 履歴・参照整合性

`validate_fact_store()` は以下を検証する。

- record IDの一意性
- supersession対象の存在
- supersessionが同一logical record typeであること
- acceptance timeを逆行しないこと
- supersession cycleがないこと
- Fact / RelationshipとEvidenceの相互参照
- Evidence targetの存在
- DerivedMetric inputの存在
- Interpretation basisの存在
- secret/provider raw body非混入

## 9. Fixture受入

`test_fact_store_contract.py` は少なくとも以下を含む。

- filing Fact
- supporting Evidence
- contradicting Evidence
- amended Fact
- source-grounded Relationship
- registry Relationship
- DerivedMetric with two inputs
- Interpretation
- append-only amendment history
- availability-aware as-of query
- broken lineage / mixed supersession rejection
- missing Evidence rejection
- secret-like field rejection
- immutable record/value
- numeric value unit constraint

本実装とfixtureはPC移行時の全Python suite 696件PASSに含まれる。今回のDEV-I0-005レビューではコード変更を行っていないため、新規local test差分はない。

## 10. 判定

`DEV-I0-005`: **完了 / Accepted**

これによりI0-006の依存条件を満たす。

次のローカル主作業:

`DEV-I0-006 — temporary content lifecycle`

また、Web側では `WEB-013 / N1-001 event taxonomy` の `WEB-007 + I0-005` 依存が充足するため、着手可能となる。
