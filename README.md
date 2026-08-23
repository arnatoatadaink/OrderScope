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

### Documentation conventions

- `docs/MERMAID_CONVENTIONS.md`
  - Non-normative, reusable guidance for Mermaid diagrams and requirement → high-level design → detailed design traceability.
  - This guide does not add a fifth Code of Truth document; authoritative rules remain in the four normative specifications above.

## Baseline

- Status: v0.1 fixed for implementation
- Target market: U.S. market
- Initial Universe: approximately 100 fixed instruments, with cadence defined in the Universe specification
- Initial market-data candidate: Alpaca
- SEC / Fundamental baseline: SEC EDGAR / XBRL
- Internal timestamps: UTC
- Market classification timezone: America/New_York
- Display timezone: Asia/Tokyo

## Core principle

The system records what changed as Fact and separates Fact / Derived Metric / Interpretation / Prediction.

Provider-specific schemas must remain behind provider interfaces so the Core can evolve independently of individual API vendors.

## Implementation entry point

Implementation should be checked against the v0.1 Definition of Done in `docs/stock_monitoring_v0.1_spec.md`. Domain-specific behavior must also conform to the corresponding reference specification.
