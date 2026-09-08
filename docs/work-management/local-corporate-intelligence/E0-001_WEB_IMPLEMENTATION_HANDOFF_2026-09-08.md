# OrderScope — E0-001 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-08
Task: `E0-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_EARNINGS_EVENT_RESULT_CONTRACT_WEB_007_2026-09-04.md`
Depends on: Accepted `I0-005`; SEC lane `S0-001..007` Accepted

## 1. Web implementation scope

Implemented the provider-neutral Earnings event/result contract and contract tests without running the local test suite.

Changed/added files:

- `analysis/app/orderscope_local/contracts/earnings.py`
- `analysis/app/orderscope_local/contracts/__init__.py`
- `analysis/tests/contracts/test_earnings_contract.py`

## 2. Contract decisions carried from WEB-007

The implementation preserves the following distinctions rather than collapsing them into one timestamp or metric record:

- earnings release vs earnings call
- scheduled release date/time vs release market window
- scheduled call instant vs actual release instant
- nullable `actual_release_at`; no inference from SEC acceptance time or call time
- issuer fiscal-year label and fiscal quarter vs calendar `period_end`
- GAAP vs non-GAAP metric records
- value, unit, currency, accounting basis, period, and evidence role
- issuer schedule announcement, issuer result release, SEC 8-K, SEC Exhibit 99.1, and issuer event page as distinct evidence roles

Shared source publication/filing/acceptance timestamps remain in the accepted I0-002 `Provenance` contract.

## 3. Canary fixtures encoded in tests

Contract tests encode the WEB-007 AMD/NVIDIA cases:

- AMD Q2 2026 release: scheduled date `2026-08-04` plus `after_market_close`, exact actual release time unknown
- AMD call: exact scheduled instant represented independently from the release
- AMD diluted EPS: GAAP `1.38` and non-GAAP `1.66` retained as separate records
- NVIDIA Q2 FY2027: issuer fiscal label remains `FY2027` while `period_end` remains in calendar year 2026
- SEC source acceptance timestamp remains provenance and does not populate `actual_release_at`

Negative tests reject:

- date-only values used as an exact `actual_release_at`
- date-only call schedule where an exact call instant is required
- release-window semantics attached to a call
- actual-release semantics attached to a call
- lowercase/implicit currency codes
- duplicate evidence references

## 4. Local verification boundary

No local execution result is claimed by this Web cycle. Before promoting `E0-001` to Accepted, run at minimum:

```bash
uv run pytest -q analysis/tests/contracts/test_earnings_contract.py
uv run pytest -q
git diff --check
```

Acceptance requires the focused tests and full suite to pass and a semantic review confirming compatibility with I0-002/I0-005 and the E0-002 detection boundary.

## 5. State and next action

Current recommended runtime state: `E0-001 = Provisional result` until local test evidence is recorded in the integrated Progress Tracker.

After local verification:

1. promote `E0-001` to Accepted if all checks pass;
2. start `E0-002` as a separate cycle;
3. do not infer missing release timestamps or consensus values during E0-002.
