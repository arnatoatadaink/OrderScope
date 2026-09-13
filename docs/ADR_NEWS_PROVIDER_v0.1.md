# OrderScope — News Provider ADR v0.1

Status: Accepted for v0.1 local personal Canary; reversible
Date: 2026-09-09
Decision ID: `ADR-NEWS-PROVIDER-001`
Work item: `N0-001`

## 1. Context

The News lane must support AMD/NVDA bounded metadata acquisition, duplicate/update handling, temporary body extraction, contradiction review, retention deletion, and later 1–3 month recall measurement against SEC/IR events.

Provider prices, plan limits, history, and usage rights change independently of the application. The WBS therefore requires N0-001 to refresh current official provider information before N0-002 implementation.

## 2. Decision

### 2.1 Primary

Use **Alpaca News API** as the v0.1 primary provider candidate for the local Corporate Canary, under the current **personal/non-commercial local-use boundary only**.

Reasons:

- historical News documented back to 2015;
- REST supports bounded start/end/symbol queries and page tokens;
- real-time News WebSocket exists;
- article body/content is available when supplied, which permits N0-004 to operate through the already Accepted temporary-content lifecycle;
- the project already separates provider-specific adapters from Core contracts.

This is not approval for commercial, redistributed, multi-user, or externally exposed use. Before any such use, recheck the account-specific Alpaca agreement and revise this ADR.

### 2.2 Secondary

Keep **Tiingo News API** as the preferred secondary metadata/recall comparison candidate.

Tiingo's current pricing and Internal Use Only plan limits are explicit, and its Power/Commercial rate limits are suitable for bounded AMD/NVDA acquisition. However, the public News product contract examined for N0-001 establishes metadata/description fields rather than a full-article body contract, so Tiingo does not replace Alpaca for the N0-004 body path without further confirmation.

### 2.3 Not adopted

Do not adopt **Massive News** for the initial News lane. Its current individual Market Data license is personal/non-business/non-commercial and restricts non-display/derived/business use without additional licensing; its News product is also documented as hourly-updated, which is not the preferred first choice for breaking-event discovery.

## 3. Provider-neutral architecture

The News Core must not depend on Alpaca/Benzinga field names.

N0-002 will define a normalized metadata object and isolate:

- authentication
- request parameters
- raw response decoding
- provider IDs/tags
- page token/cursor behavior
- rate-limit headers
- body capability

inside the Alpaca adapter.

Provider body content is never part of durable News metadata.

## 4. Body lifecycle

`ADR_TEMPORARY_CONTENT_LIFECYCLE_v0.1` remains authoritative.

- N0-002 normally fetches metadata without requesting/storing body content.
- N0-004 may acquire body content only into an expiring temporary-content reference.
- successful body content is deleted after extraction;
- exception content expires within 30 days;
- durable metadata may retain hashes, source URL, Facts/Evidence, and deletion proof but not the body.

No adapter may bypass a provider-rights limitation by scraping the article URL directly.

## 5. Rate limits

Do not hard-code an old Alpaca News beta RPM as a permanent contract.

For Alpaca:

- use conservative configurable budgets;
- honor current response rate-limit headers when provided;
- treat 429 as a normal retryable/partial condition through I0-007 contracts;
- run an account-entitlement smoke check before live Canary acquisition.

For Tiingo, published plan rates may seed configuration for the selected tier but remain external configuration rather than schema constants.

## 6. Historical evaluation

N1-006 requires 1–3 month recall evaluation. Both selected candidates can satisfy that window:

- Alpaca: history to 2015;
- Tiingo non-institutional: 3 months queryable history plus ongoing data.

The recall evaluator must compare provider discovery against SEC/IR reference events, not treat either provider as ground truth.

## 7. Security / rights guardrails

- credentials are environment/config secrets only;
- provider response bodies are excluded from logs, DB records, API responses, and Git;
- local read-only APIs never expose News bodies;
- no redistribution or shared display is authorized by this ADR;
- provider source/publisher fields remain Evidence metadata, not ownership assertions invented by OrderScope.

## 8. Revisit triggers

Revise this ADR before:

- commercial/internal-business use under an organization;
- redistribution, shared UI, or external API exposure;
- body retention beyond the accepted temporary lifecycle;
- changing primary News provider;
- introducing a licensed aggregator with different body/storage rights;
- N1-006 showing unacceptable recall/lag/ticker attribution for Alpaca.

## 9. Related documents

- `REPORT_NEWS_PROVIDER_COMPARISON_N0_001_2026-09-09.md`
- `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `ADR_TEMPORARY_CONTENT_LIFECYCLE_v0.1.md`
- `ADR_FACT_STORE_LOGICAL_SCHEMA_v0.1.md`
