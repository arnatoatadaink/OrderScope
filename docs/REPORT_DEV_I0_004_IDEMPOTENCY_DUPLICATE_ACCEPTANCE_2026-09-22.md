# OrderScope — DEV-I0-004 idempotency / duplicate boundary 受入記録

作成日: 2026-09-22（Asia/Tokyo）
Status: accepted
対象: `DEV-I0-004 / I0-004 Implement idempotency/duplicate boundary`

## 1. 結論

`DEV-I0-004` は既存実装をレビューし、WBSの完了条件を満たしているため **完了 / Accepted** とする。

追加のコード変更は不要である。既存のstable identity / content identity / explicit revision contractを正として、後続adapter・Fact Store・News canonicalizationから利用する。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/contracts/identity.py`
- `analysis/app/orderscope_local/contracts/provider.py`
- `analysis/app/orderscope_local/contracts/__init__.py`

専用テスト:

- `analysis/tests/contracts/test_identity_contract.py`
- `analysis/tests/contracts/test_provider_contract.py`

## 3. WBS完了条件との対応

WBS `I0-004` の完了条件:

> Distinguish duplicate, update, and conflict using stable accession/article/signal IDs and content hash.

| 要求 | 実装 |
|---|---|
| SEC accession stable ID | `StableIdentity.filing_accession()` |
| article stable ID | `StableIdentity.provider_article()` |
| official signal stable ID | `StableIdentity.provider_signal()` |
| provider scope | article / signal identityの `provider_key` |
| content hash | `ContentIdentity(..., ContentHash)` |
| new | `IdempotencyClassification.NEW` |
| duplicate | `IdempotencyClassification.DUPLICATE` |
| update | `IdempotencyClassification.UPDATE` |
| conflict | `IdempotencyClassification.CONFLICT` |
| explicit revision assertion | `RevisionRelationship` |
| provider handoff | `classify_adapter_item()` |

## 4. 判定規則

`classify_idempotency()` は次の規則を固定している。

- stable identityが異なる → `NEW`
- stable identityが同一、content hashも同一 → `DUPLICATE`
- stable identityが同一、content hashが異なる、revision証拠なし → `CONFLICT`
- stable identityが同一、content hashが異なり、accepted predecessor → candidate successor の明示的 `RevisionRelationship` がある → `UPDATE`

content変更だけでUPDATEと推定しない。timestamp、URL、provider revision等からrevisionを推測して上書きすることもない。

## 5. Stable identity境界

### SEC filing

SEC accessionはglobal identityとして扱い、provider scopeを付与しない。

形式:

`0000000000-00-000000`

### Article / Official Signal

article IDとofficial signal IDはprovider内でのみstableとみなし、必ず `provider_key` を要求する。

同一article IDでもproviderが異なれば別identityである。

## 6. 安全性・曖昧性対策

- identity / content identity / revision relationshipはimmutable。
- SHA-256は共通 `ContentHash` 契約を再利用。
- padded value、control character、過大なidentifierを拒否。
- credential-like materialをstable ID / provider keyへ保存することを拒否。
- revision predecessor/successorは同じstable identityを必須化。
- hashが同じsnapshotをrevisionとして扱わない。
- reverse/mismatched revision relationshipを拒否。
- normalized adapter itemから同じclassifierを利用し、provider-specific判定をCoreへ持ち込まない。

## 7. 検証根拠

`test_identity_contract.py` では以下を確認している。

- provider-neutral durable representation
- SEC accession validation
- article/signal provider scoping
- secret/control/unbounded input rejection
- distinct identity => NEW
- same identity/hash => DUPLICATE
- changed hash without revision => CONFLICT
- changed hash with explicit revision => UPDATE
- invalid/mismatched revision rejection
- immutable values

`test_provider_contract.py` ではadapter handoffで同じidempotency classifierが利用されることを確認している。

本実装はPC移行時の全Python suite 696件PASSに含まれており、今回の `DEV-I0-004` レビューではコード変更を行っていない。

## 8. 判定

`DEV-I0-004`: **完了 / Accepted**

I0共通契約の次のクリティカルパスは `DEV-I0-005 Fact Store logical schema Accepted化` とする。
