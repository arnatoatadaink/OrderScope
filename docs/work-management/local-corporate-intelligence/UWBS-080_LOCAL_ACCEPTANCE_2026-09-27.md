# OrderScope — UWBS-080 Local Acceptance

Status: **ACCEPTED**
Scope: Direct WTI / Brent Macro Instrument contract + provider survey
Branch: `l1-003-local-market-recovery`

## Acceptance basis

Local validation completed with the checked-in Python 3.13 environment.

Observed results:

```text
Python 3.13.15
focused commodity contract tests: 7 passed
fixture importer repair verification: 8 passed
full Python regression: 709 passed
compileall: PASS
git diff --check: PASS
```

The temporary full-suite failure encountered during acceptance was not caused by UWBS-080. It exposed a stale fixture-importer test expectation and then a test-file rollback introduced during repair. The fixture-importer tests were restored to the current `RawImportResult` contract and the migration assertion now follows the discovered current migration set. Final full-suite validation is clean.

## Accepted UWBS-080 boundary

Accepted artifacts include:

- provider-neutral `CommodityPriceObservation` contract;
- WTI and Brent canonical benchmark identities;
- explicit separation of spot-reference and listed-futures identities;
- WTI Cushing / Brent Europe spot-location validation;
- NYMEX WTI / ICE Futures Europe Brent venue validation;
- listed futures contract code and delivery-month requirements;
- finite negative crude futures values remain representable;
- USO remains a proxy and is not canonical WTI/Brent price truth;
- provider survey and activation/terms boundaries documented.

No live provider activation, Worker/Cron mutation, D1 mutation, paid procurement, or PB execution occurred as part of this acceptance.

## Next dependency

The next market-independent dependency is:

```text
UWBS-081 — structured commodity supply/fundamental acquisition
```

`UWBS-082` commodity supply/shipping/geopolitical event taxonomy remains parallelizable after the fundamental acquisition boundary is defined.
