# v0.1.5 Listing Compliance implementation progress — 2026-09-30

Status: **WEB IMPLEMENTATION CANDIDATE CREATED; LOCAL REGRESSION PENDING**

## Parent and branch

Accepted parent boundary:

```text
v0.1.4 = a798622f839b836f8b60f52dd700b8fd87147991
```

Implementation branch:

```text
codex/uwbs-067-listing-compliance
```

The branch is based directly on the accepted v0.1.4 boundary and is currently four commits ahead with no unrelated path changes.

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

## Candidate source commits

```text
5410f77247ba6ab774ba16a3add6e8ec15a4df48  contracts
 e6fc865cb917c32669cf9fe8e5ffa5c47ef87229  state/repricing rules
0cfb1102a26e4cdb94300656c22d802bb97fb392  public exports
44e7a2d31c6ef5ebebafb77fbe44ac307625b014  focused tests
```

## Focused test coverage present

Nine tests cover:

1. UTC and source-time ordering;
2. deficiency -> cure -> regained progression;
3. cure without deficiency rejection;
4. regained compliance without prior deficiency rejection;
5. temporary price recovery not clearing listing risk;
6. explicit compliance restoration without market/company evidence remaining listing-overhang removal only;
7. listing, earnings/company and market metric evidence remaining separate in interpretation lineage;
8. reuse of one record across evidence classes rejected;
9. explicit effective delisting state.

These tests have been committed but have not yet been executed by the web GitHub connector. They require local/CI execution before release-boundary acceptance.

## Diff audit

Compared with v0.1.4, the branch changes only the new listing-compliance package and its tests. No TypeScript, PB, v0.1.6 Crypto, provider activation, remote mutation or existing runtime path is changed.

## Required local acceptance

Run from a checkout of `codex/uwbs-067-listing-compliance`:

```bash
uv run pytest -q analysis/tests/listing_compliance
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check a798622f839b836f8b60f52dd700b8fd87147991..HEAD
```

TypeScript tests/typecheck are not required unless later changes touch TypeScript/shared generated/build surfaces. Record the omission explicitly.

## Release posture

v0.1.5 may be accepted as an experimental development release once contract tests and full regression pass. The following remain intentionally uncalibrated/non-goals:

- universal delisting probability;
- venue-independent minimum-price thresholds;
- causal claim that compliance restoration caused a price move;
- empirical repricing thresholds;
- automatic exchange-rule inference from price alone.

After local PASS, freeze the four source commits in `v0.1.5-replay-manifest.json`, create the boundary report, and construct one cumulative synthetic v0.1.5 checkpoint on `release/reconstructed-v0.1`.
