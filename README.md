# OrderScope

OrderScope is the Code of Truth repository for the Stock Monitoring Fact project.

## Code of Truth v0.1

The v0.1 Code of Truth consists of four normative documents under `docs/`.

### Parent specification

- `docs/stock_monitoring_v0.1_spec.md`
  - Integrated v0.1 specification and entry point.
  - Defines project purpose, scope, market analysis, calendar/session handling, corporate intelligence, source tiers, SEC/fundamental handling, Regime overview, Fact model, and Definition of Done.

### Reference specifications

- `docs/stock_monitoring_v0.1_universe_spec.md`
  - Fixed initial Universe, Tier A/B/C price cadences, themes, characters, and Universe update policy.
- `docs/stock_monitoring_v0.1_regime_spec.md`
  - Regime strength/status/history, provisional decay, contract handling, negative evidence, and reactivation.
- `docs/stock_monitoring_v0.1_provider_research.md`
  - Provider boundary, candidate APIs, current research notes, costs, and provider STUB requirements.

The parent specification is the entry point. The three reference specifications are part of the same v0.1 Code of Truth and are normative for their respective domains.

### Documentation conventions and traceability

- `docs/MERMAID_CONVENTIONS.md`
  - Non-normative, reusable guidance for Mermaid diagrams and requirement → high-level design → detailed design traceability.
- `docs/REQUIREMENTS_TRACEABILITY_v0.1.md`
  - Non-normative stable requirement IDs derived from the four v0.1 Code of Truth documents, including acceptance/verification links and unresolved design questions.
- `docs/HIGH_LEVEL_DESIGN_v0.1.md`
  - Provisional, non-normative high-level component boundaries mapped to the requirement IDs.
- `docs/DETAILED_DESIGN_CFG_PROVIDER_v0.1.md`
  - Detailed-design Slice 01 for `HLD-CFG-001 + HLD-PROV-001`: Universe configuration, provider-neutral schemas, provider contracts, timestamps, cursors, completeness and error boundaries.
- `docs/DETAILED_DESIGN_SCHEDULER_MARKET_v0.1.md`
  - Detailed-design Slice 02 for `HLD-SCH-001 + HLD-MKT-001`: acquisition jobs, coverage checkpoints, catch-up overlap, cadence/session normalization, idempotent bar acceptance and retry/failure boundaries.
- `docs/DESIGN_DECISIONS_v0.1.md`
  - Reversible implementation-level decisions. `DD-DEPLOY-001` currently selects Cloud + Main PC for the initial v0.1 deployment while keeping module contracts placement-independent.
- `docs/REPORT_VOLUME_FLOW_ALPACA_2026-08-28.md`
  - Non-normative report defining the volume / relative-volume / traded-notional proxy boundary, IEX-vs-SIP validation loop, and the distinction between observed OHLCV, Derived Metrics, and capital-flow interpretation.
- `docs/RUNBOOK_CLOUDFLARE_WORKER_SCHEDULE_v0.1.md`
  - Non-normative deployment/operations runbook for Cloudflare Worker + Cron acquisition and ChatGPT Scheduled Task digest consumption.
- `docs/IMPLEMENTATION_DECISIONS_WORKER_v0.1.md`
  - Provisional Worker implementation choices derived from the functional requirements, including D1/R2 responsibilities, cadence-vs-Attention semantics, RVOL baseline, notional activity proxy, digest exposure, IEX/SIP quality gating, volatility baseline and shadow-mode promotion criteria.
- `docs/WORK_PLAN_INITIAL_VALIDATION_AND_LONG_TERM_OPERATIONS_2026-09-01.md`
  - Non-normative phased work plan separating bounded live validation and D1-export-based local analysis from R2-backed long-term retention, reconciliation, recovery and prediction-research preparation.
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
  - Reviewable task breakdown for the next local-analysis, SEC/earnings, news, official-context, retention, and localhost integration phase; keeps remaining Worker operational checks as a separate backlog.
- `docs/REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md`
  - Cross-session map of the corporate-intelligence research and documentation that ChatGPT Web can complete or prepare, with explicit local handoff boundaries.
- `docs/WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md`
  - Active ledger for `WEB-001` through `WEB-020`, including dependencies, evidence links, session ownership, handoff state and next action.
- `docs/ADR_LOCAL_ANALYSIS_STACK_v0.1.md`
  - Accepted `L0-001` stack decision for the local MVP: Python/uv, SQLite/DuckDB, Arrow/Parquet, localhost API and the Windows/WSL execution boundary.
- `docs/ADR_FACT_STORE_LOGICAL_SCHEMA_v0.1.md`
  - Proposed `I0-005` logical boundary separating Fact, Evidence, Relationship, Derived Metric and Interpretation; acceptance remains gated by I0-002 provenance types and contract fixtures.
- `docs/REPORT_LOCAL_SEC_FORM_FILTER_S0_004_S0_007_2026-09-04.md`
  - Local `S0-004` strict SEC form filter implementation evidence and the completed fixture-only portion / remaining dependency boundary for `S0-007`.
- `docs/REPORT_LOCAL_COMMON_CONTRACT_TEST_KIT_I0_007_2026-09-04.md`
  - Local `I0-007` provider-neutral contract test kit for bounded pagination, timestamps, partial/retryable errors and secret non-exposure; adapter integration remains dependency-gated.
- `docs/REPORT_JAPAN_LOCAL_MARKET_DATA_OPTIONS_2026-09-03.md`
  - Current research on MARKET SPEED II RSS/Excel constraints, kabu Station API, J-Quants plans and safe Windows-to-WSL handoff options for local Japanese market data.
- `docs/PROVISIONAL_DESIGN_JP_US_PREDICTION_v0.1.md`
  - Non-normative Japan-to-U.S. prediction extension: separate predictor/target registries, Japan provider fallback, four U.S. Premarket/Regular horizons, as-of/leakage rules, provisional labels and probabilistic output contracts.
- `docs/PREDICTION_REGISTRY_SEMICONDUCTOR_CANARY_v0.1.md`
  - Evidence and limits for the first versioned Japanese semiconductor-input / U.S. theme-target canary profile.
- `docs/HANDOFF_LOCAL_JP_US_PREDICTION_2026-08-31.md`
  - Local continuation handoff for the provider-neutral immutable Japanese-input snapshot slice, including safety boundaries, required tests and completion criteria.

These derived documents do not add to or replace the four-document Code of Truth. Authoritative rules remain in the normative specifications above.

## Baseline

- Status: v0.1 fixed for implementation
- Target market: U.S. market
- Initial Universe: 106 fixed instruments (Tier A 25 / Tier B 28 / Tier C 53), with cadence defined in the Universe specification
- Initial market-data candidate: Alpaca
- SEC / Fundamental baseline: SEC EDGAR / XBRL
- Initial deployment design: Cloud acquisition + Main PC heavy analysis (reversible design decision)
- Initial Worker runtime: Cloudflare Worker shadow-mode scaffold with per-minute Cron wake-up
- Initial operational storage split: D1 for hot scheduler/checkpoint/digest state; R2 for long-lived/batched OHLCV archive (provisional implementation decision)
- Internal timestamps: UTC
- Market classification timezone: America/New_York
- Display timezone: Asia/Tokyo

## Core principle

The system records what changed as Fact and separates Fact / Derived Metric / Interpretation / Prediction.

Provider-specific schemas must remain behind provider interfaces so the Core can evolve independently of individual API vendors.

Deployment placement must also remain behind module contracts: moving acquisition from Cloud to a future always-on server must not require rewriting Core-facing provider contracts.

## Worker scaffold

The repository now includes a minimal deployable Cloudflare Worker scaffold:

- `src/index.ts`
- `wrangler.jsonc`
- `package.json`
- `tsconfig.json`

The Worker defaults to `WORKER_MODE = "shadow"`. Shadow mode exposes `/health` and `/digest/latest` and accepts Cron Trigger wake-ups without market-data writes. The live acquisition path requires Alpaca secrets and the D1 binding. Regular acquisition remains unchanged. The separate `PREDICTION_MODE = "shadow"` profile records its configured registry in the digest while the outer Worker is in shadow mode; after the outer Worker is promoted to `live`, it also plans target-only Premarket coverage without executing those Premarket jobs or writing bars.

The provisional prediction implementation is isolated in `src/prediction.ts` and `src/prediction-registry.ts`. It provides executable contracts for versioned predictor/target registries, the four horizon/anchor chain, Premarket anchor windows, readiness deadlines, leakage guards, a reviewed semiconductor canary profile and bounded Premarket shadow planning without adding Japanese instruments to the fixed monitoring Universe.

## Implementation entry point

Implementation should be checked against the v0.1 Definition of Done in `docs/stock_monitoring_v0.1_spec.md`. Domain-specific behavior must also conform to the corresponding reference specification.

Use `docs/REQUIREMENTS_TRACEABILITY_v0.1.md` as the stable bridge from normative requirements into design and verification. Use `docs/HIGH_LEVEL_DESIGN_v0.1.md` for architectural responsibility, the `docs/DETAILED_DESIGN_*_v0.1.md` files for contract-level design slices, and `docs/DESIGN_DECISIONS_v0.1.md` for reversible deployment/implementation choices. Use the volume/activity report, deployment runbook and Worker implementation-decision document as implementation guidance; if they conflict with Code of Truth or contract-level design, the normative/contract documents win.

The Japan-to-U.S. prediction document is a provisional research extension. It keeps Japanese predictor instruments outside the fixed monitoring Universe and does not add prediction accuracy to the current v0.1 Definition of Done.
