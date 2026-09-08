# OrderScope — E0-003 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-08
Task: `E0-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_IR_FALLBACK_WEB_008_2026-09-04.md`
Depends on: Accepted `E0-002`

## 1. Web implementation scope

Implemented provider-neutral issuer-IR fallback reconciliation and focused fixture tests without running the local test suite.

Changed/added files:

- `analysis/app/orderscope_local/earnings/__init__.py`
- `analysis/app/orderscope_local/earnings/ir_fallback.py`
- `analysis/tests/earnings/test_ir_fallback.py`

## 2. Contract decisions carried from WEB-008

The implementation preserves these distinctions:

- SEC filing evidence and issuer IR release evidence remain independent records for one earnings event.
- SEC is first in discovery/reference priority when present; issuer IR is fallback/second reference, not a replacement for SEC.
- IR `discovery_url` and individual `canonical_release_url` are separate roles.
- AMD IR URLs are constrained to `ir.amd.com`.
- NVIDIA IR URLs may use official `investor.nvidia.com` or `nvidianews.nvidia.com` because the official IR flow crosses those NVIDIA-owned surfaces.
- IR URL patterns are not generated from IDs/slugs; callers provide the listing-discovered URL.
- Each IR release retains a SHA-256 `ContentHash`, issuer fiscal label/quarter, `period_end`, and optional source-established publication timestamp.
- Missing publication time is not inferred.

## 3. Reconciliation / dedupe rules

`reconcile_sec_ir_evidence` is event-scoped by Corporate Canary instrument and established `period_end`.

- repeated SEC discovery of the same accession with identical candidate semantics collapses to one candidate;
- conflicting semantics for the same SEC accession raise an explicit contract error;
- repeated IR discovery of the same canonical release URL and identical content hash collapses to one IR evidence record even when discovered through different listing/archive paths;
- the same canonical IR URL with a changed content hash is not silently treated as duplicate and raises an update/conflict boundary;
- SEC and IR are never collapsed into one evidence object;
- cross-instrument or cross-period inputs cannot be reconciled into one event;
- SEC candidates lacking an established `period_end` are not guessed into an event identity.

## 4. Canary fixtures encoded

Focused tests cover:

- AMD Q2 2026 SEC + IR reconciliation;
- AMD Financial Results and Press Releases archive duplicate discovery of the same release;
- SEC accession duplicate and conflict behavior;
- same IR URL / changed hash update-conflict boundary;
- NVIDIA IR-only fallback and preservation of `FY2027` while `period_end` remains in calendar 2026;
- cross-event reconciliation rejection;
- missing SEC period rejection;
- official issuer-host and issuer/source identity boundaries.

## 5. Local verification boundary

Before promoting `E0-003` to Accepted, run:

```bash
uv run pytest -q analysis/tests/earnings/test_ir_fallback.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full suite, and diff check to pass. A semantic review should confirm that source priority means discovery/reference order only and does not discard either SEC or IR evidence.

## 6. Explicit non-scope

E0-003 does not yet:

- parse live AMD/NVIDIA listing HTML;
- perform HTTP retry/ETag/redirect handling;
- extract revenue/EPS values;
- choose between conflicting SEC/IR numeric values;
- infer fiscal labels or release timestamps;
- persist raw IR bodies long term.

Those concerns remain later extraction/quality or adapter-runtime work. This cycle fixes the provider-neutral fallback and reconciliation boundary needed by E0-004.

## 7. Next action after acceptance

If local verification passes, promote `E0-003` to Accepted and begin `E0-004` basic earnings Fact extraction as a separate cycle. E0-004 may consume SEC/IR evidence but must keep period, unit, accounting basis, and source explicit and must never invent missing values.
