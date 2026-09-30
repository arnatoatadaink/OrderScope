# v0.1.5 Listing Compliance implementation progress — 2026-09-30

Status: **EXPERIMENTAL ACCEPTED; SYNTHETIC RELEASE BOUNDARY PENDING**

## Parent and branch

Accepted parent boundary:

```text
v0.1.4 = a798622f839b836f8b60f52dd700b8fd87147991
```

Implementation branch:

```text
codex/uwbs-067-listing-compliance
```

The branch is based directly on the accepted v0.1.4 boundary and contains only the UWBS-067 listing-compliance package and focused tests.

## Implemented scope

UWBS-067 is implemented as a compact Python package:

```text
analysis/app/orderscope_local/listing_compliance/
  __init__.py
  models.py
  rules.py
analysis/tests/listing_compliance/
  test_listing_compliance.py
```

Implemented contracts:

- `ListingComplianceEvent` with source/evidence lineage, venue, rule reference and event/available/accepted UTC semantics;
- conservative listing states for deficiency, cure window, regained compliance, active delisting risk and effective delisting;
- state derivation that rejects unsupported cure/regained transitions;
- `ListingRepricingAssessment` that preserves listing, company/earnings and market-metric inputs as distinct evidence classes;
- conversion to the existing Fact Store `Interpretation` contract;
- no universal $1 threshold, rolling-window duration or venue-specific cure rule is hard-coded;
- price recovery alone cannot clear an active listing deficiency.

## Accepted source commits

```text
5410f77247ba6ab774ba16a3add6e8ec15a4df48  contracts
 e6fc865cb917c32669cf9fe8e5ffa5c47ef87229  state/repricing rules
0cfb1102a26e4cdb94300656c22d802bb97fb392  public exports
44e7a2d31c6ef5ebebafb77fbe44ac307625b014  focused tests
```

## Local acceptance results

Local validation on 2026-09-30:

- Focused UWBS-067 tests: **9 passed** in 2.28s.
- Full Python regression: **635 passed, 1 warning** in 54.15s.
- Python compileall: **PASS** (no output / exit success).
- Diff check against v0.1.4: **PASS** (no output / exit success).
- TypeScript: **not required**, because the accepted diff changes only Python package/test paths and no TypeScript/shared-generated/build surface.

The single warning is an upstream Starlette/AnyIO deprecation warning and is not introduced by UWBS-067.

## Acceptance classification

UWBS-067 is accepted for the v0.1 development series as:

```text
Experimental Accepted
```

The implementation contract and repository regression are accepted. Empirical market calibration remains intentionally non-blocking for v0.1.x.

## Experimental limitations

The release does not claim:

- a universal delisting probability;
- venue-independent minimum-price thresholds;
- causal attribution that compliance restoration caused a price move;
- empirically calibrated repricing thresholds;
- automatic exchange-rule inference from price alone.

## Remaining release work

1. Freeze the four accepted source commits in `v0.1.5-replay-manifest.json`.
2. Publish `V0_1_5_LISTING_COMPLIANCE_BOUNDARY_REPORT_2026-09-30.md`.
3. Construct one cumulative synthetic v0.1.5 checkpoint on top of `a798622f839b836f8b60f52dd700b8fd87147991`.
4. Push the resulting boundary to `release/reconstructed-v0.1` and record its SHA.
5. Do not create a tag or integrate main as a side effect unless separately approved.
