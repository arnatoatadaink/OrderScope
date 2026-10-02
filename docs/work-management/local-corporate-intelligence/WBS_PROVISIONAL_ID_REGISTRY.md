# OrderScope — WBS Provisional ID Registry

Status: **CURRENT CANONICAL PROVISIONAL-ID REGISTRY**
Scope: Local Corporate Intelligence / WBS-unreflected backlog governance
Branch: `docs/v0-1-10-release-cp`

## 1. Purpose

This registry resolves provisional `UWBS-*` identifier collisions without rewriting historical append-only backlog evidence.

Historical backlog rows retain their original text as provenance. When a historical row uses a colliding legacy provisional ID, all new planning, WBS incorporation, CP references, implementation handoffs and acceptance records must use the canonical ID defined here.

The formal Analyst / Cross-Market WBS mappings already incorporated before this registry remain unchanged.

## 2. Incorporated IDs that remain authoritative

These IDs were already consumed by formal WBS packages and are therefore reserved.

| Provisional ID | Final task | State |
|---|---|---|
| UWBS-001 | R0-001 | Incorporated |
| UWBS-002 | R0-002 | Incorporated |
| UWBS-003 | R0-003 | Incorporated |
| UWBS-004 | R0-004 | Incorporated |
| UWBS-011 | A0-003 | Incorporated |
| UWBS-012 | A0-004 | Incorporated |
| UWBS-013 | A0-005 | Incorporated |
| UWBS-014 | A0-006 | Incorporated |
| UWBS-015 | A0-007 | Incorporated |
| UWBS-016 | R0-005 | Incorporated |
| UWBS-023 | R0-006 | Incorporated |
| UWBS-024 | R0-007 | Incorporated |
| UWBS-025 | R0-008 | Incorporated |
| UWBS-026 | R0-009 | Incorporated |
| UWBS-027 | A0-008 | Incorporated |
| UWBS-028 | A0-009 | Incorporated |
| UWBS-029 | A0-010 | Incorporated |
| UWBS-030 | A0-011 | Incorporated |
| UWBS-031 | A0-012 | Incorporated |
| UWBS-032 | A0-013 | Incorporated |
| UWBS-033 | A0-014 | Incorporated |
| UWBS-034 | A0-015 | Incorporated |
| UWBS-035 | A0-016 | Incorporated |
| UWBS-036 | A0-017 | Incorporated |

`UWBS-005..010`, `UWBS-017..022` remain valid non-colliding legacy backlog IDs until separately incorporated or remapped.

## 3. Canonical remap for later colliding backlog rows

### AI theme lane

| Historical backlog alias | Canonical provisional ID | Task |
|---|---|---|
| UWBS-030 | UWBS-062 | Define AI / adjacent theme ontology and multi-theme exposure contract |
| UWBS-031 | UWBS-063 | Define event × theme reaction-coefficient contract |
| UWBS-032 | UWBS-064 | Implement cross-sectional theme reaction observation and confirmation |
| UWBS-033 | UWBS-065 | Define theme activation / rotation / repricing interpretation state machine |
| UWBS-034 | UWBS-066 | Historical calibration and Canary fixtures for event-theme reaction coefficients |

### Listing-compliance lane

| Historical backlog alias | Canonical provisional ID | Task |
|---|---|---|
| UWBS-035 | UWBS-067 | LVWR exchange-listing-compliance / earnings-repricing Canary extension |

### Crypto market-structure lane

| Historical backlog alias | Canonical provisional ID | Task |
|---|---|---|
| UWBS-036 | UWBS-068 | Define crypto derivatives Fact / Derived Metric contract |
| UWBS-037 | UWBS-069 | Define BTC macro-leader / altcoin relative-context model |
| UWBS-038 | UWBS-070 | Survey BTC institutional-flow / market-structure sources |
| UWBS-039 | UWBS-071 | Define 24/7 crypto time-window / weekend-liquidity contract |
| UWBS-040 | UWBS-072 | NEAR/BTC multi-layer Canary and false-positive suite |
| UWBS-041 | UWBS-073 | Implement multi-venue futures/perpetual acquisition adapters |
| UWBS-042 | UWBS-074 | Implement durable derivatives snapshot archive and catch-up lifecycle |
| UWBS-043 | UWBS-075 | Implement liquidation normalization and cascade metrics |
| UWBS-044 | UWBS-076 | Implement price-zone OI retention / Position Map analysis |
| UWBS-045 | UWBS-077 | Add cross-venue divergence and data-quality guards |
| UWBS-046 | UWBS-078 | Futures-position tracking Canary for NEAR reference episode |
| UWBS-047 | UWBS-079 | Validate Pacific weekend handoff and weekday re-risking selection hypotheses |

### Oil / commodity / cross-asset lane

| Historical backlog alias | Canonical provisional ID | Task |
|---|---|---|
| UWBS-048 | UWBS-080 | Define direct WTI / Brent Macro Instrument contract and provider survey |
| UWBS-049 | UWBS-081 | Implement / select structured commodity supply and fundamental acquisition |
| UWBS-050 | UWBS-082 | Define commodity supply / shipping / geopolitical event taxonomy |
| UWBS-051 | UWBS-083 | Define oil-down-reason and inflation / growth-risk interpretation |
| UWBS-052 | UWBS-084 | Implement BTC spot ETF flow acquisition / normalization |
| UWBS-053 | UWBS-085 | Define cross-asset Risk-On / Crypto Risk-On market-regime contract |
| UWBS-054 | UWBS-086 | Oil/BTC cross-asset Canary and Worker/D1 capacity acceptance |

### Physical-SaaS lane

| Historical backlog alias | Canonical provisional ID | Task |
|---|---|---|
| UWBS-055 | UWBS-087 | Define Physical-SaaS deployment lifecycle Fact contract |
| UWBS-056 | UWBS-088 | Implement operational-milestone extraction and reconciliation |
| UWBS-057 | UWBS-089 | Implement deployment-funnel Derived Metrics and slippage interpretation |
| UWBS-058 | UWBS-090 | Define recurring-revenue quality, cash-conversion and deleveraging model |
| UWBS-059 | UWBS-091 | Define M&A integration / legacy-system evidence overlay |
| UWBS-060 | UWBS-092 | Add Physical-SaaS classifier and applicability guard |
| UWBS-061 | UWBS-093 | Powerfleet deployment-lifecycle Canary and false-positive suite |

### VIX / cross-asset volatility lane

The following IDs are new canonical provisional IDs and do not remap historical aliases. Source planning extension: `WBS_UNREFLECTED_VIX_CROSS_ASSET_VOLATILITY_EXTENSION_2026-09-27.md`.

| Canonical provisional ID | Task |
|---|---|
| UWBS-094 | Survey volatility data sources and define source-neutral volatility instrument contract |
| UWBS-095 | Implement VIX spot + F1/F2 observation and term-structure metrics |
| UWBS-096 | Define VIX level/change/curve interpretation contract |
| UWBS-097 | Implement BTC 30-day implied-volatility acquisition and normalization |
| UWBS-098 | Implement MSTR 30-day option-implied-volatility acquisition and normalization |
| UWBS-099 | Define MSTR/BTC IV differential and cross-asset volatility interpretation |
| UWBS-100 | Historical calibration, Canary/false-positive and Worker/D1 capacity acceptance |

### Crypto on-chain event-intelligence lane — v0.1.10

The following IDs are new canonical provisional IDs and do not remap historical aliases. Source planning record: `WBS_UNREFLECTED_CRYPTO_ONCHAIN_SECURITY_EXTENSION_2026-10-02.md`. They are incorporated into the active release/feature CP for `v0.1.10`.

| Canonical provisional ID | Task |
|---|---|
| UWBS-101 | Define cross-chain protocol wallet/component registry and confirmed on-chain transfer Fact contract |
| UWBS-102 | Implement abnormal on-chain flow Derived Metrics and candidate-state machine |
| UWBS-103 | Join on-chain anomaly candidates with price/OI/funding/liquidation market confirmation |
| UWBS-104 | Build historical crypto exploit price-impact dataset and NEAR Intents replay fixture |

## 4. Canonical dependency references

All new dependency and CP references use canonical IDs.

```text
AI theme
UWBS-062 -> UWBS-063 -> UWBS-064 -> UWBS-065 -> UWBS-066
UWBS-020 -> UWBS-064 / UWBS-066
UWBS-021 -> UWBS-065 / UWBS-066

Crypto market structure
UWBS-068 -> UWBS-069
UWBS-068 -> UWBS-073 -> UWBS-074 -> UWBS-075
UWBS-074 + UWBS-075 -> UWBS-076
UWBS-073 + UWBS-074 -> UWBS-077
UWBS-073..077 -> UWBS-078
UWBS-071 + UWBS-073..078 -> UWBS-079

Oil / cross-asset
UWBS-080 -> UWBS-081
UWBS-080 + UWBS-081 + UWBS-082 -> UWBS-083
UWBS-070 -> UWBS-084
UWBS-068 / UWBS-073..077 + UWBS-083 + UWBS-084 -> UWBS-085
UWBS-085 -> UWBS-086

Physical-SaaS
UWBS-087 -> UWBS-088 -> UWBS-089
UWBS-087 -> UWBS-090
UWBS-088 -> UWBS-091
UWBS-087 -> UWBS-092
UWBS-089 + UWBS-090 + UWBS-091 + UWBS-092 -> UWBS-093

VIX / cross-asset volatility
UWBS-094 -> UWBS-095 -> UWBS-096
UWBS-094 -> UWBS-097
UWBS-094 -> UWBS-098
UWBS-097 + UWBS-098 -> UWBS-099
UWBS-096 + UWBS-099 -> UWBS-100

Crypto on-chain event intelligence / v0.1.10
UWBS-101 -> UWBS-102 -> UWBS-103 -> UWBS-104
UWBS-068..079 + UWBS-102 -> UWBS-103
UWBS-068..079 + UWBS-101..103 -> UWBS-104
```

## 5. Discovery-reference normalization

Historical Discovery rows remain immutable evidence. Their canonical interpretation is:

```text
DISC-008 -> UWBS-062..066
DISC-009 -> UWBS-080..086
DISC-010 -> UWBS-087..093
```

The crypto market-structure lane sourced from the crypto macro-leader / derivatives reports is canonicalized as `UWBS-068..079`.

The VIX / cross-asset volatility lane is registered directly through the dedicated 2026-09-27 WBS-unreflected extension as `UWBS-094..100`; no historical colliding Discovery alias is required.

The crypto on-chain event-intelligence lane is registered through the 2026-10-02 extension as `UWBS-101..104` and assigned to `v0.1.10` in the active release CP.

## 6. Usage rule

From this registry onward:

1. never create a new task using a historical colliding alias;
2. use canonical `UWBS-062..104` IDs for the remapped/new lanes;
3. when quoting an older report, preserve the legacy alias but add `canonical: UWBS-xxx` when ambiguity matters;
4. final WBS incorporation updates this registry with the final package/task ID;
5. do not renumber already incorporated formal tasks merely to make historical numbering contiguous;
6. release numbering does not alter canonical UWBS identifiers.

## 7. Current CP effect

The previous market-independent restart at `UWBS-080` is superseded by accepted later evidence. Current release/feature sequencing is defined by:

`docs/release/V0_1_7_TO_V0_1_10_RELEASE_CP_2026-10-02.md`

Current selected sequence:

```text
REL-07 v0.1.7 boundary confirmation
  -> REL-08 v0.1.8 boundary confirmation
  -> REL-09 v0.1.9 boundary confirmation
  -> UWBS-101 -> UWBS-102 -> UWBS-103 -> UWBS-104
  -> REL-10C v0.1.10 cumulative acceptance
```

No provider activation, Worker/Cron change, D1 mutation, PB authorization, paid procurement, automated trading action, or security-incident assertion is authorized by this registry.
