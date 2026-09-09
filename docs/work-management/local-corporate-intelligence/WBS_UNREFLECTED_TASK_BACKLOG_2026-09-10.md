# OrderScope — WBS-Unreflected Task Backlog

Status: **Active append-only planning backlog — not yet incorporated into the main WBS**
Date: 2026-09-10
Primary WBS checked: `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Related extension checked: `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`

## 1. Purpose

This document is the holding area for tasks that have been identified after the current WBS was written but are not yet formally incorporated into a normative/primary work package.

It exists so new task ideas can be appended without silently changing the meaning of accepted WBS items.

Rules:

1. Do not rewrite an existing WBS task merely to absorb a newly discovered scope item.
2. Record every new item here first with source/provenance, proposed owner/package, dependency, and completion condition.
3. Use provisional `UWBS-*` IDs in this file only. They are tracking IDs, not final WBS IDs.
4. When a future WBS revision adopts an item, add the final WBS ID in the `Disposition` column instead of deleting the backlog history.
5. If an item is later shown to be already covered by an existing WBS task, mark it `Covered by existing WBS` and record the evidence.
6. Keep Fact / Derived Metric / Interpretation / Prediction boundaries unchanged while planning extensions.
7. Do not use this backlog to authorize remote D1, Worker mutation, live-provider activation, or another gated operation.

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| `Captured` | Scope is known well enough not to lose it, but task decomposition may still change |
| `Ready for WBS design` | Completion condition and dependencies are sufficiently clear for formal WBS incorporation |
| `Needs source re-link` | Scope is known from prior work/discussion, but the exact remote source report has not yet been located on the active branch |
| `Needs decomposition` | One captured item should probably become multiple formal WBS tasks |
| `Covered by existing WBS` | No new WBS task is required; retain the record for traceability |
| `Deferred` | Intentionally not part of the current completion target |
| `Incorporated` | Added/remapped into a later WBS revision; final ID must be recorded |

## 3. Confirmed WBS-unreflected operational follow-ups

These four items come from `POST_X0_OPERATIONAL_FOLLOWUPS_2026-09-10.md`, itself derived from the accepted X0-006 runbook review. They are not completion gaps for accepted X0 fixture-path work; they are production-operations follow-ups.

| UWBS ID | Source tracking ID | Proposed task | Proposed package | Completion condition summary | Dependencies / related work | Status | Disposition |
|---|---|---|---|---|---|---|---|
| UWBS-001 | PX0-001 | Register reviewed operational scheduler jobs | Operations / Integration | At least one reviewed adapter-owned scheduler plan is registered; dry-run displays intended jobs; zero-job success cannot be mistaken for workload completion; HTTP mutation remains prohibited | X0-004, owning adapters, provider/terms gates | Ready for WBS design | Pending |
| UWBS-002 | PX0-002 | Durable scheduler run evidence and stale-lock recovery | Operations / Recovery | Persist run/job identity, status, completion boundary, revision and sanitized failure state; make last completed boundary inspectable; stale-lock ownership/clearance is testable and robust against PID reuse | X0-004; I0-003 remains provider/source checkpoint owner | Ready for WBS design | Pending |
| UWBS-003 | PX0-003 | Retention and bounded-reprocessing operator CLI | News / Operations integration | Operator can inspect backlog/overdue state, perform bounded delete/retry through concrete storage, and plan/run bounded replay without exposing bodies/secrets | N1-005, L0-006, integration/storage layer | Ready for WBS design | Pending |
| UWBS-004 | PX0-004 | Reproducible backup/restore and restore drill | Storage / Recovery | Freeze data-root layout and backup set; implement consistent SQLite snapshot and dataset/catalog validation; define manifest/hashes, destination protections, generations/RPO, restore validation and drill evidence | L0-005, L1 storage/datasets, X0-006 policy | Ready for WBS design | Pending |

## 4. Corporate-action / M&A / TOB expansion

The current WBS already includes `M&A` as one event-taxonomy category under `N1-001`, so a generic "recognize M&A news" task is **not** missing. The unreflected scope is the deeper corporate-action lifecycle around tender offers, acquisitions, delisting/cash-out, ownership thresholds, and post-transaction company-value/regime changes.

The exact recently added M&A/TOB report referenced in project discussion was not located in the active branch tree during this backlog pass. Therefore the following entries are captured with `Needs source re-link`; they must not be treated as a verbatim reconstruction of a missing report.

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Likely inputs / dependencies | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-005 | Define Corporate Action / Transaction lifecycle contract | New Corporate Action package or I0 extension | Represent announcement, proposal, definitive agreement, tender-open, tender-close, ownership-threshold crossing, shareholder/board/regulatory approval, closing, termination, delisting and cash-out as distinct historical states/events; preserve event/available/accepted times and source provenance | I0-002/004/005; N1-001 taxonomy; SEC/IR/news sources | Needs source re-link | Pending |
| UWBS-006 | Implement M&A / TOB / tender-offer acquisition and reconciliation | Corporate Action acquisition | Detect transaction events from Tier-1 SEC/IR where available and secondary news as discovery; deduplicate/reconcile multiple sources without overwriting conflicting states; retain offeror/target/consideration/terms only when explicit | S0 filing path, N0/N1 news path, company IR, I0 idempotency | Needs source re-link | Pending |
| UWBS-007 | Implement ownership-threshold / control-change monitoring | Corporate Action / SEC | Track relevant 13D/13G and other explicit ownership/control disclosures; distinguish stake-building, control intent, passive ownership, amendment and withdrawal without inferring intent absent source evidence | S0-004 target forms, S0 filing records, Fact Store | Needs decomposition | Pending |
| UWBS-008 | Model delisting, compulsory cash-out and security termination outcomes | Corporate Action / Instrument lifecycle | Track announced vs effective delisting, merger consideration, cash-out/stock conversion, security termination and successor instrument/entity relationships; avoid treating an announced transaction as completed before effective evidence | I0 registry/history, SEC/IR, exchange/official notices | Needs source re-link | Pending |
| UWBS-009 | Post-transaction enterprise-value / Regime-change linkage | Corporate Action + Regime | Keep observed transaction facts separate from derived valuation/repricing and `COMPANY_REGIME_CHANGE`; represent acquired/divested businesses, segment changes, financing/consideration and resulting company-scope changes as evidence for later Regime/valuation analysis rather than immediate prediction | I0 Fact/Derived Metric/Interpretation separation; E0 segment identity/revenue; Regime spec | Needs source re-link | Pending |
| UWBS-010 | Corporate-action Canary acceptance cases | Corporate Action QA | Fixture cases cover pending → amended → completed, failed/withdrawn offer, competing bid, partial ownership threshold, delisting/cash-out, stock-vs-cash consideration and conflicting secondary-news vs SEC/IR assertions | UWBS-005..009 after decomposition | Needs decomposition | Pending |

## 5. Macro rates / carry-unwind / non-price Fact expansion

Source report: `docs/REPORT_MACRO_RATES_CARRY_UNWIND_NON_PRICE_FACTS_2026-09-10.md`.

The existing Cross-Market extension already uses sovereign yields, FX, and policy expectations as context under `A0-001/A0-002`. Therefore these rows do **not** add a duplicate generic "use yields/FX" task. They capture the missing reusable Fact contract, derived-rate structure, interpretation rules, validation cases, and source/provider work needed to make that context systematic.

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Likely inputs / dependencies | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-011 | Define Macro-Market non-price Fact contract | A0 / I0 Cross-Market integration | Define normalized raw Facts for policy rates, short-market rates, sovereign 2Y/5Y/10Y/30Y yields, USD/JPY and eligible volatility/flow context; preserve event/available/accepted/as-of times, units, market/tenor identity and source provenance; inferred capital movement must not be stored as Fact | A0-001; I0-002/004/005; provider/source gates | Ready for WBS design | Pending |
| UWBS-012 | Implement rate-curve and cross-country Derived Metrics | A0 Derived Metrics | Compute tested 2s10s/10s30s slopes, U.S.-Japan 2Y/10Y spreads, fixed-window FX/yield deltas and change velocity; distinguish steepening, flattening and inversion without converting them into causal claims; preserve as-of semantics | UWBS-011; A0-001; I0 Fact/Derived Metric boundary | Ready for WBS design | Pending |
| UWBS-013 | Define carry-unwind / deleveraging Interpretation contract | A0 Interpretation / Regime | Define `CARRY_UNWIND_CANDIDATE`, `DELEVERAGING_REGIME`, `RATE_SHOCK`, `FX_SHOCK_JPY` and related evidence rules using multiple independent signals; support SUPPORT/PARTIAL/CONTRADICT/UNKNOWN and prohibit USD/JPY or one news item from establishing capital movement as Fact | UWBS-011/012; A0-001 hypothesis rules; News evidence | Ready for WBS design | Pending |
| UWBS-014 | Macro stress / carry-unwind validation fixtures and Canary cases | A0 QA / Cross-Market validation | Fixture set covers policy-rate up + long-yield down, steepening/flattening/inversion, rapid JPY appreciation, broad selloff with/without company-specific negative evidence, explicit carry-reduction report, event-risk de-risking and false-positive cases; validates Fact/Derived Metric/Interpretation separation | UWBS-011..013; A0-002 validation pattern | Ready for WBS design | Pending |
| UWBS-015 | Survey and select structured macro-rate / FX / flow data sources | Provider contracts / A0 | Identify permissible official/structured sources for policy rates, sovereign curves, FX, FX-volatility and eligible fund-flow series; record terms, cadence, historical depth, timestamps, revision behavior, cost, rate limits and fallback boundary; do not activate live providers as part of survey | Existing provider/terms/security gates; UWBS-011 data requirements | Needs decomposition | Pending |

Planning notes:

- Bank-specific deposit and lending rates are intentionally not forced into the minimum Macro-Market contract. They may become a later sector/company extension after UWBS-011/012 establish the reusable rate structure.
- The previously discussed rough 1–3 week stabilization window is a scenario estimate, not a system constant or Fact. Historical validation would be required before introducing any duration model.
- Fund-flow values, MMF flows, ETF flows, gross deleveraging, and market-cap changes must not be blindly summed into one observed `capital_outflow` figure because scopes overlap and double counting is likely.

## 6. Worker/Schedule News acquisition

Source design: `docs/work-management/local-corporate-intelligence/NEWS_WORKER_ACQUISITION_DESIGN_2026-09-10.md`.

The current WBS `N0-002` already owns the News metadata adapter. The missing scope is steady-state invocation of that accepted adapter from the Cloudflare Worker/Schedule layer. This is therefore an orchestration/operations task, not a rewrite of N0-002.

| UWBS ID | Proposed task | Proposed package | Completion condition summary | Likely inputs / dependencies | Status | Disposition |
|---|---|---|---|---|---|---|
| UWBS-016 | Implement Worker/Schedule News metadata acquisition job | Worker acquisition / Operations integration | Run reviewed AMD/NVDA metadata-only News jobs on bounded session-aware cadence; reuse I0-003 checkpoint and I0-004 idempotency; preserve cross-symbol article identity; bound pagination/call budget; expose retryable failure state; keep secrets out of persistence/logs; require separate Worker activation review/change window | N0-002; I0-003/004; X0-002; N1-006 measured recall for cadence validation; UWBS-001/PX0-001; SMOKE-006; SMOKE-007 only for approved historical catch-up | Ready for WBS design | Pending |

Planning default:

- Initial Canary: AMD/NVDA only.
- Metadata-only baseline; no News body in steady-state Worker acquisition.
- Initial cadence proposal: every 5 minutes during the configured U.S. observation day, reusing existing market-session configuration rather than a separate hard-coded clock.
- The 5-minute cadence is a planning default, not a frozen constant; N1-006 measured recall/lag should confirm or adjust it before activation.
- Live Worker registration remains separately gated. This backlog entry does not change Worker Shadow mode.

## 7. Existing extension work that is NOT counted as WBS-unreflected

Do not duplicate these in this backlog unless new scope exceeds their completion conditions:

- `A0-001` / `A0-002` already exist in `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`.
- `N1-001` already includes M&A in the news event taxonomy.
- `N0-002` already owns News metadata normalization; `UWBS-016` owns Worker/Schedule orchestration around that accepted adapter.
- `L1-006`, `L1-003`, `N1-006`, and the existing A0 tasks are already represented in WBS/tracker state even when unfinished.
- `SMOKE-*` / `CANARY-*` Worker items are already explicit deferred Worker backlog items in the main WBS.

## 8. Discovery inbox — append new task ideas here first

Use this section for newly proposed work before deciding whether it deserves a full row in §3/§4/§5/§6 or another package-specific section.

| Discovery ID | Date | Proposal / question | Source | Suspected package | Triage state |
|---|---|---|---|---|---|
| DISC-001 | 2026-09-10 | Reserved for next newly discovered WBS-unreflected item | — | — | Empty placeholder; replace/append, do not infer scope |
| DISC-002 | 2026-09-10 | Capture structured rate/FX Facts and carry-unwind/deleveraging interpretation instead of relying on news-only rate context | `docs/REPORT_MACRO_RATES_CARRY_UNWIND_NON_PRICE_FACTS_2026-09-10.md` | A0 / I0 / Provider contracts | Promoted to UWBS-011..015 |
| DISC-003 | 2026-09-10 | Move steady-state News metadata acquisition to Cloudflare Worker/Schedule while keeping Local as analysis layer | `docs/work-management/local-corporate-intelligence/NEWS_WORKER_ACQUISITION_DESIGN_2026-09-10.md` | Worker acquisition / Operations | Promoted to UWBS-016 |

When a proposal is accepted for tracking:

1. append a new `UWBS-*` row in the appropriate section;
2. copy the source report/file/chat decision exactly enough to recover provenance;
3. define completion condition and dependencies;
4. mark the Discovery row `Promoted to UWBS-xxx`;
5. do not delete the original discovery record.

## 9. Add-a-task template

Copy this block when a new idea is raised:

```markdown
### UWBS-XXX — <short task name>

- Date captured: YYYY-MM-DD
- Source: `<report/path>` or explicit project decision
- Status: Captured | Ready for WBS design | Needs source re-link | Needs decomposition | Deferred
- Proposed package: <existing/new package>
- Problem / gap:
- Scope:
- Explicit non-goals:
- Dependencies:
- Completion condition:
- Required fixtures / acceptance evidence:
- Security / retention / provider constraints:
- Candidate final WBS ID: Pending
- Disposition: Pending
```

## 10. WBS incorporation procedure

A future WBS revision should review this file row by row and choose exactly one disposition:

- `Incorporate as new task`
- `Merge with another UWBS item`
- `Covered by existing WBS`
- `Move to another project/WBS`
- `Defer beyond current release`
- `Reject with reason`

The revision must preserve a mapping table:

| UWBS ID | Final WBS ID / disposition | Revision | Reason |
|---|---|---|---|
| UWBS-001 | Pending | — | — |
| UWBS-002 | Pending | — | — |
| UWBS-003 | Pending | — | — |
| UWBS-004 | Pending | — | — |
| UWBS-005 | Pending | — | — |
| UWBS-006 | Pending | — | — |
| UWBS-007 | Pending | — | — |
| UWBS-008 | Pending | — | — |
| UWBS-009 | Pending | — | — |
| UWBS-010 | Pending | — | — |
| UWBS-011 | Pending | — | — |
| UWBS-012 | Pending | — | — |
| UWBS-013 | Pending | — | — |
| UWBS-014 | Pending | — | — |
| UWBS-015 | Pending | — | — |
| UWBS-016 | Pending | — | — |

## 11. Current planning interpretation

This backlog does not authorize remote changes. X0 fixture-path and the complete non-live N1-006 toolchain are accepted; N1-006 itself still requires the real 30-day Alpaca metadata benchmark and measured recall report.

`UWBS-016` is now ready for WBS design but should not be activated before N1-006 supplies real recall/lag evidence that can confirm or adjust the proposed News polling cadence. Worker remains Shadow, and any Worker/Schedule job registration still requires its separately reviewed task/change window.
