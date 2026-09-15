# OrderScope — E0-007 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `E0-007`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `E0-004`, Accepted `E0-005`, Accepted `E0-006`

## 1. Web implementation scope

Implemented deterministic AMD/NVDA earnings Canary quality reporting and focused fixtures.

Changed/added files:

- `analysis/app/orderscope_local/earnings/quality_report.py`
- `analysis/app/orderscope_local/earnings/__init__.py`
- `analysis/tests/earnings/test_quality_report.py`

## 2. Quality-report boundary

The report reconciles multiple AMD/NVDA fiscal periods across:

- E0-004 source-grounded basic earnings Facts
- SEC vs issuer-IR evidence
- E0-005 segment-revenue fallback results

It does not silently select a winning source when SEC and IR disagree.

Basic metric reconciliation statuses are:

- `agreement`: SEC and issuer IR both exist and expose the same exact observed amount
- `single_source`: only one of the configured Tier-1 sources is present
- `conflict`: both sources are present and their exact observed amounts differ

The report groups by instrument, issuer fiscal label/quarter, period end, Fact type, and accounting basis. GAAP/non-GAAP are therefore never compared as the same metric.

## 3. Segment quality boundary

Each requested stable segment identity is reported as:

- `extracted`, retaining the successful E0-005 fallback method; or
- `unresolved`, retaining the complete ordered failure path across Company Facts, XBRL Dimension, and Filing Table.

The report receives the E0-006 stable `segment_id` from the caller. It does not resolve identity by raw issuer label and does not equate cross-role labels.

## 4. Aggregate measures

The quality report exposes:

- number of metric checks
- number of cross-source agreements
- number of single-source rows
- number of conflicts
- metric agreement rate over comparable two-source rows only
- number of segment checks
- extracted/unresolved segment counts
- segment extraction rate

Single-source rows are not incorrectly counted as cross-source agreement or disagreement.

## 5. Deterministic human report

`render_earnings_canary_quality_markdown` renders a stable Markdown report containing:

- aggregate quality counts
- every basic metric row with exact values by source
- explicit `conflict` rows
- every segment extraction row
- successful fallback method or full failure path

The renderer reports unresolved differences rather than filling or selecting values.

## 6. Canary fixtures encoded

Focused tests cover multiple periods for both AMD and NVIDIA, including:

- AMD Q1 FY2026 SEC/IR agreement
- AMD Q2 FY2026 deliberate SEC/IR conflict, verifying both values remain visible
- NVIDIA Q1/Q2 FY2027 single-source coverage
- successful filing-table segment fallback
- unresolved three-stage segment fallback with complete failure reasons
- agreement-rate denominator excluding single-source rows
- explicit segment extraction rate
- deterministic Markdown output surfacing conflicts

The deliberate fixture conflict is a quality-contract test case, not a factual claim about the real AMD disclosures.

## 7. Explicit non-scope

E0-007 does not:

- fetch live SEC or IR data itself
- decide which conflicting numeric source is authoritative
- calculate consensus/surprise/growth
- infer missing metrics
- infer stable segment identity from labels
- auto-resolve original-vs-recast values

Those unresolved differences remain visible for later policy/human review.

## 8. Local verification evidence

Local verification completed after fetch/pull:

- focused E0-007 tests: **5 passed**
- full regression suite: **215 passed**
- `git diff --check`: **clean**

Semantic acceptance boundary remains unchanged: conflicting source values stay visible and unresolved segment paths retain the E0-005 failure reasons.

## 9. Acceptance result

`E0-007` is **Accepted**. This completes the WBS E0 Earnings/Fundamental Canary lane.

The next Core work must be selected from the post-E0 `N1 / O0 / X0` branch using the Progress Tracker and remaining dependency gates. X0 remains gated by other lanes; N1 later depends on N0 acquisition work. O0-001 is independently startable from Accepted W0/I0 prerequisites and is the selected next cycle.
