# OrderScope — N0-001 Web Research Handoff

Status: **Accepted — provider refresh and adoption ADR complete**
Date: 2026-09-09
Task: `N0-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Dependency: `W0-004`

## 1. Completion evidence

N0-001 requires a current comparison of price, history, rate limits, body rights, internal-use terms, and credentials, plus an adoption ADR.

Completed artifacts:

- `docs/REPORT_NEWS_PROVIDER_COMPARISON_N0_001_2026-09-09.md`
- `docs/ADR_NEWS_PROVIDER_v0.1.md`

Current official sources for Alpaca, Tiingo, and Massive were rechecked on 2026-09-09.

## 2. Adopted v0.1 provider strategy

- Primary: Alpaca News API for local personal/non-commercial AMD/NVDA Canary use.
- Secondary comparison candidate: Tiingo News API for metadata/recall comparison and a clearer future internal-commercial tier.
- Not adopted initially: Massive News.

This decision is reversible and does not authorize commercial, redistributed, shared-display, or external API use.

## 3. Why Alpaca is primary

N0-004 requires temporary article-body extraction. Current Alpaca News documentation establishes:

- history back to 2015;
- bounded REST queries with pagination;
- live News WebSocket;
- article `content` when available.

That body capability makes Alpaca the only compared provider for which the public documentation examined in this cycle directly supports the N0-004 extraction path.

The body remains subject to I0-006 temporary-content rules and provider rights. N0-002 should default to metadata-only retrieval; N0-004 is the only boundary that requests temporary body content.

## 4. Rate-limit boundary

Do not implement an old beta News RPM as a schema constant.

The Alpaca adapter must use configurable conservative budgets, honor rate-limit headers when available, and treat 429 as retryable/partial through the common adapter contract. Account entitlement is a local runtime smoke check.

Tiingo's published Power/Commercial rates may be external configuration defaults for those tiers.

## 5. Terms / usage boundary

- Alpaca general Terms establish a personal/non-commercial default for Service Content unless another agreement applies.
- Tiingo explicitly labels current individual/commercial News tiers Internal Use Only and separates redistribution.
- Massive individual Market Data terms restrict business/commercial/non-display/derived use without additional licensing.

A move to commercial or multi-user operation is a mandatory N0-001/ADR revisit trigger.

## 6. N0-002 handoff

N0-002 is now **Ready**.

Implement a provider-neutral News metadata adapter for AMD/NVDA with at least:

- source/provider identity;
- provider article ID;
- headline;
- publisher/source;
- canonical URL as supplied;
- created/published/updated timestamps without inventing missing precision;
- retrieved/available/accepted timestamps;
- provider ticker/tag observations;
- bounded start/end window;
- opaque page token/checkpoint;
- partial/error state;
- provider body-capability flag only, never body content.

For Alpaca, use `include_content=false` in the metadata path. Do not infer Corporate identity solely from Benzinga/Alpaca symbol tags.

N0-003 remains responsible for canonical URL, syndication, duplicate and update semantics. N0-004 remains responsible for temporary body acquisition.

## 7. Current News lane

```text
N0-001 Accepted
N0-002 Ready
N0-003 waiting on N0-002
N0-004 waiting on N0-002
N1-001 independently Ready
N1-002 waiting on N0-003 + N1-001
```

## 8. Next action

Proceed with `N0-002 — Implement news metadata adapter` as the next Core News task. `N1-001 — Freeze event taxonomy` can proceed in parallel in a separate non-overlapping cycle.
