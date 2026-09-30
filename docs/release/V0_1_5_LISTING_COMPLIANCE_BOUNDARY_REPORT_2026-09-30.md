# v0.1.5 Listing Compliance boundary report — 2026-09-30

Status: **EXPERIMENTAL ACCEPTED; SYNTHETIC BOUNDARY PENDING**

## Decision

UWBS-067 is accepted for the v0.1 development series as an experimental capability. Contract behavior and repository regression are accepted. Empirical repricing calibration and universal exchange/listing thresholds remain explicitly unvalidated and are not release blockers for v0.1.5.

Accepted parent boundary:

```text
v0.1.4 = a798622f839b836f8b60f52dd700b8fd87147991
```

Accepted source commits:

```text
5410f77247ba6ab774ba16a3add6e8ec15a4df48
 e6fc865cb917c32669cf9fe8e5ffa5c47ef87229
0cfb1102a26e4cdb94300656c22d802bb97fb392
44e7a2d31c6ef5ebebafb77fbe44ac307625b014
```

## Accepted capability

v0.1.5 provides a conservative Listing Compliance / Earnings Repricing lane that:

- records source-grounded listing-compliance events with venue/rule/timestamp/evidence lineage;
- derives deficiency, cure-window, regained-compliance, active-risk and effective-delisting states conservatively;
- rejects unsupported cure/regained transitions;
- preserves listing evidence, company/earnings evidence and market metrics as separate basis classes;
- materializes repricing assessment through the existing Fact Store Interpretation contract;
- does not infer restored listing compliance from a temporary price move alone;
- does not hard-code LVWR-specific $1 / 30-trading-day details as universal rules.

## Verification

Local acceptance results supplied on 2026-09-30:

- focused Listing Compliance tests: **9 passed**;
- full Python regression: **635 passed, 1 warning**;
- Python compileall: **PASS**;
- diff check versus v0.1.4: **PASS**;
- TypeScript: **not required**, because the accepted diff is Python-only and does not alter shared/generated/build surfaces.

The single warning is an upstream Starlette/AnyIO deprecation warning and is outside UWBS-067.

## Experimental limitations

The boundary does not claim:

- universal delisting probability;
- venue-independent minimum-price or cure-window thresholds;
- causal proof that compliance restoration caused a price move;
- empirically calibrated repricing thresholds;
- exchange-rule inference from price behavior alone.

These limitations must remain visible in downstream use and may be refined in later v0.1.x work without invalidating the v0.1.5 development boundary.

## Release construction

The accepted source allowlist is frozen in `docs/release/v0.1.5-replay-manifest.json` with `apply_allowed=true`.

The remaining mechanical step is to create one cumulative synthetic v0.1.5 commit on top of v0.1.4, preserving the source commits unchanged in history.

Target lineage:

```text
v0.1.4  a798622f839b836f8b60f52dd700b8fd87147991
   |
   v
v0.1.5  <synthetic boundary SHA>
```

No tag or main integration is implied by this acceptance.
