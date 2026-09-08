# OrderScope — E0-002 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-08
Task: `E0-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `S0-007`, Accepted `E0-001`

## 1. Web implementation scope

Implemented deterministic SEC earnings-candidate detection and focused tests without running the local suite.

Changed/added files:

- `analysis/app/orderscope_local/sec/earnings_detection.py`
- `analysis/app/orderscope_local/sec/__init__.py`
- `analysis/tests/sec/test_earnings_detection.py`

## 2. Detection boundary

The implementation treats the following as earnings candidates:

- `10-Q` / `10-Q/A`
- `10-K` / `10-K/A`
- `8-K` / `8-K/A` only when explicit Item `2.02` is present or when a bounded filing attachment is both an Exhibit `99.x` and explicitly described as earnings/financial results.

The implementation does **not** classify a generic 8-K or generic Exhibit 99.1 as earnings merely from form/exhibit number.

This task creates candidates only. It does not extract revenue/EPS, construct E0-001 `EarningsEvent` values, infer fiscal labels, infer actual release time, or fill missing values.

## 3. Tests encoded

Focused tests cover:

- 10-Q and 10-K candidate detection
- amendments preserved as separate accession-scoped candidates
- plain 8-K rejection
- Item 2.02 8-K acceptance
- earnings-result Exhibit 99.1 acceptance
- generic investor-presentation Exhibit 99.1 rejection
- combined Item 2.02 + attachment evidence
- non-earnings SEC forms ignored
- attachment URLs constrained to the filing root
- bounded canonical input validation

## 4. Design consequence

E0-002 intentionally requires explicit filing-index/document metadata for 8-K attachment relevance. Parsing filing bodies or extracting earnings values remains downstream work. This keeps the S0 temporary-content boundary intact and prevents E0-002 from inventing earnings semantics from provider payload shape.

## 5. Local verification boundary

Before promoting `E0-002` to Accepted, run:

```bash
uv run pytest -q analysis/tests/sec/test_earnings_detection.py
uv run pytest -q
git diff --check
```

If focused and full tests pass, review the 8-K Item 2.02 / Exhibit 99.x boundary and then promote E0-002 to Accepted.

## 6. Next action after acceptance

The next Core task is `E0-003` company-IR fallback. Reuse the existing `WEB-008` IR fallback research; preserve stable IR URL/hash, retain source priority, and deduplicate SEC/IR evidence without discarding provenance.
