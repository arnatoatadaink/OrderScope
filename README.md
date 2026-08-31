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
- `docs/PROVISIONAL_DESIGN_JP_US_PREDICTION_v0.1.md`
  - Non-normative Japan-to-U.S. prediction extension: separate predictor/target registries, Japan provider fallback, four U.S. Premarket/Regular horizons, as-of/leakage rules, provisional labels and probabilistic output contracts.

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

The Worker defaults to `WORKER_MODE = "shadow"`. Shadow mode exposes `/health` and `/digest/latest` and accepts Cron Trigger wake-ups, but intentionally performs no Alpaca acquisition until an authoritative market calendar/session path, Alpaca secrets and D1 operational state binding are configured.

## Implementation entry point

Implementation should be checked against the v0.1 Definition of Done in `docs/stock_monitoring_v0.1_spec.md`. Domain-specific behavior must also conform to the corresponding reference specification.

Use `docs/REQUIREMENTS_TRACEABILITY_v0.1.md` as the stable bridge from normative requirements into design and verification. Use `docs/HIGH_LEVEL_DESIGN_v0.1.md` for architectural responsibility, the `docs/DETAILED_DESIGN_*_v0.1.md` files for contract-level design slices, and `docs/DESIGN_DECISIONS_v0.1.md` for reversible deployment/implementation choices. Use the volume/activity report, deployment runbook and Worker implementation-decision document as implementation guidance; if they conflict with Code of Truth or contract-level design, the normative/contract documents win.

The Japan-to-U.S. prediction document is a provisional research extension. It keeps Japanese predictor instruments outside the fixed monitoring Universe and does not add prediction accuracy to the current v0.1 Definition of Done.
