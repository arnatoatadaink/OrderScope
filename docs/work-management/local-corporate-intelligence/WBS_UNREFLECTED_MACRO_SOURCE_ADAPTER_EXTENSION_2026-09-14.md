# OrderScope — WBS-Unreflected Macro Source Adapter Extension

Status: **Incorporated into formal A0 WBS/CP on 2026-09-15 — retained as provenance**
Date: 2026-09-14
Parent backlog: `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
Source survey: `UWBS-015_MACRO_PROVIDER_SURVEY_2026-09-14.md`
Formal WBS: `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Critical Path: `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`

This extension converted the accepted UWBS-015 provider survey into bounded implementation tasks. The 2026-09-15 planning revision incorporated the tasks below while preserving their existing local acceptance evidence. No row authorizes live provider activation, Worker/Cron mutation, or remote D1 changes.

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Dependencies | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-032 | Implement U.S. Treasury par-yield source adapter | A0 / Official macro acquisition | Parse official Daily Treasury Par Yield Curve responses into source-neutral 2Y/5Y/10Y/30Y raw points; preserve source date, tenor, unit and source reference; malformed/missing required columns fail closed; no Fact acceptance timestamp is invented by the parser | UWBS-011/012/015; existing A0 official macro collector for compatibility reference | Incorporated | `A0-013`; local implementation accepted 2026-09-14; 4 focused / 645 full Python pass |
| UWBS-033 | Implement New York Fed overnight-rate source adapter | A0 / Official macro acquisition | Parse EFFR and optional SOFR/OBFR official reference-rate responses into distinct short-market-rate raw points; preserve reference date, unit, revision/footnote metadata where available; do not merge EFFR with FOMC target range | UWBS-011/015; UWBS-032 acquisition pattern | Incorporated | `A0-014`; local implementation accepted 2026-09-14; 4 focused / 649 full Python pass |
| UWBS-034 | Implement BOJ/MOF Japan macro source adapters | A0 / Official macro acquisition | Replace validation-only BOJ HTML/MOF 10Y path with normalized BOJ API + MOF 2Y/5Y/10Y/30Y adapters; preserve source semantics and release/observation boundaries without inventing JP-holiday availability | UWBS-011/012/015; official Japanese source contracts | Incorporated | `A0-015`; local implementation accepted 2026-09-14; 4 focused / 653 full Python pass |
| UWBS-035 | Implement FRED/ALFRED revision-aware fallback adapter | A0 / Provider fallback | Provide explicit fallback/history retrieval with vintage/revision lineage; require explicit underlying-source and terms references; never silently replace official-direct series semantics or third-party licensing constraints | UWBS-015; provider/security terms boundary | Incorporated | `A0-016`; parser accepted 4 focused / 657 full Python; official-direct-first selection policy accepted 4 focused / 661 full Python |
| UWBS-036 | Add CFTC positioning evidence adapter | A0 / Positioning Evidence | Normalize selected TFF/COT positioning series as positioning Evidence/Derived Metric; never label positioning changes as fund flow or capital movement | UWBS-013/014/015 | Incorporated | `A0-017`; local implementation accepted 2026-09-14; 4 focused / 665 full Python pass |

## Planning rules

- Official-direct sources are preferred for v0.1 raw macro observations.
- Source adapters stop before Fact Store acceptance. Acquisition/acceptance timestamps and Provenance are attached by the owning acquisition layer.
- Existing `official_macro.py` remains an A0-002 validation collector until an explicit migration/removal task is accepted; new adapters must not silently change accepted A0-002 behavior.
- High-frequency ETF/fund-flow remains deferred pending separate commercial terms/cost review.
- No task in this extension authorizes live scheduling or remote mutations.

## Incorporation mapping — 2026-09-15

| UWBS ID | Final WBS ID |
|---|---|
| UWBS-032 | A0-013 |
| UWBS-033 | A0-014 |
| UWBS-034 | A0-015 |
| UWBS-035 | A0-016 |
| UWBS-036 | A0-017 |
