# OrderScope — DEV-S0-003 FilingRecord persistence 受入記録

作成日: 2026-09-23（Asia/Tokyo）
Status: accepted
対象: `S0-003 / Persist FilingRecord`

## 1. 結論

`S0-003` の既存 `SqliteFilingRecordRepository` とfixtureを再レビューした。

repository自体は accessionをprimary identityとして NEW / DUPLICATE / conflictを正しく分離し、WBS必須fieldをprovider-neutralに永続化していた。一方、versioned migrationに `filing_records` tableが存在せず、専用testが手動 `CREATE TABLE` していたため、L0-005 migration境界との統合が未完了だった。

この差分を修正し、`0003_filing_records.sql` を追加した。migration schemaとrepository実利用をfixtureで検証するtestも追加した。

migration fixture期待値をSQLite STRICTの実挙動へ修正後、2026-09-23にCodexDesktop側で指定受入テストを再実行し、`21 passed in 2.90s` を確認した。実行後diffなし。

## 2. 受入対象

実装:

- `analysis/app/orderscope_local/sec/filing_records.py`
- `analysis/app/orderscope_local/storage/migrations.py`
- `analysis/app/orderscope_local/storage/sql/0003_filing_records.sql`

fixture:

- `analysis/tests/sec/test_filing_records.py`
- `analysis/tests/storage/test_migrations.py`
- `analysis/tests/sec/test_filing_detection_acceptance.py`

## 3. WBS完了条件

WBS:

> Idempotently store accession, form, filed_at, period_end, primary-document ref, retrieved_at.

対応field:

- accession
- content_hash
- cik
- ticker
- form
- filed_at
- period_end
- primary_document_ref
- source_ref
- retrieved_at

## 4. Idempotency境界

`accession` をSQLite primary keyとする。

- 未登録accession → `NEW`
- 同一accession + 同一content hash → `DUPLICATE`
- 同一accession + 異なるcontent hash → explicit conflictとしてreject

後続で同一filingを再取得しても最初のdurable recordを更新しない。

## 5. Archive reference

SEC accessionからEDGAR archive rootをdeterministicに構築する。

ownership filing等、issuer submissions feed内のfiling accession prefixがreporting owner CIKを持つ場合も、issuer scopeの `cik/ticker` とarchive filer pathを混同しない。

## 6. Migration差分

追加:

`analysis/app/orderscope_local/storage/sql/0003_filing_records.sql`

schema:

- `accession TEXT PRIMARY KEY`
- `content_hash TEXT NOT NULL`
- `cik TEXT NOT NULL`
- `ticker TEXT NOT NULL`
- `form TEXT NOT NULL`
- `filed_at TEXT NOT NULL`
- nullable `period_end`
- nullable `primary_document_ref`
- `source_ref TEXT NOT NULL`
- `retrieved_at TEXT NOT NULL`

query用に `(cik, filed_at, accession)` indexを追加した。

migration runnerのchecksum / contiguous version / rollback契約は既存L0-005を再利用する。

## 7. Fixture追加

`test_migrations.py`:

- current migrationsで `filing_records` が再現されること
- column nullability / primary key
- query index存在

`test_filing_records.py`:

- versioned migrationで作成した実DBへrepositoryが書込み可能なこと

既存fixtureでは:

- NEW
- DUPLICATE
- changed hash conflict
- invalid CIK/ticker
- malformed date
- unsafe document path
- nullable fields
- reporting-owner accession
- UTC retrieved_at
- migration未適用時fail

を検証している。

## 8. ローカル受入

推奨:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q \
  analysis/tests/sec/test_filing_records.py \
  analysis/tests/storage/test_migrations.py \
  analysis/tests/sec/test_filing_detection_acceptance.py
```

必要ならSEC slice全体:

```bash
bash scripts/run-local-wsl.sh python -m pytest -q analysis/tests/sec analysis/tests/storage/test_migrations.py
```

## 9. 判定

`DEV-S0-003`: **完了 / Accepted**

CodexDesktop側の受入テスト `21 passed in 2.90s` とdiffなしを根拠として **Accepted** とする。

S0-004は既に完了済みのため再実装せず、主経路を `S0-005 filing-document acquisition` と `S0-006 Company Facts/XBRL adapter` へ進める。
