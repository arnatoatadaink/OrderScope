# OrderScope — REL-11C / C0-003 Implementation Plan — 2026-10-03

Status: **IMPLEMENTATION PLAN — REL-11C START**
Release: `v0.1.11`
Formal WBS: `C0-003`
Canonical source: `UWBS-108`

## Goal

Join accepted C0-002 abnormal-flow candidate evidence with already accepted crypto market-structure observations without creating a new market-data contract or converting correlation into causal incident attribution.

## Reused accepted contracts

- `crypto_context.CryptoReturnObservation` for token/BTC return windows;
- `crypto_derivatives.CryptoDerivativeObservation` for OI/funding/volume snapshots;
- `crypto_derivatives.LiquidationObservation` for liquidation buckets;
- `crypto_onchain.AbnormalFlowAssessment` for C0-002 candidate state.

## New REL-11C boundary

Create `analysis/app/orderscope_local/crypto_onchain/market_context.py` containing only deterministic join/interpretation output.

The join must preserve:

- on-chain assessment time;
- token return and BTC-relative return;
- OI delta and funding delta where paired snapshots exist;
- liquidation values where accepted evidence overlaps the event context;
- source/observation identifiers;
- no-lookahead using accepted timestamps;
- distinction between price-down + OI-down deleveraging candidate and price-down + OI-up new-short candidate.

## Interpretation boundary

Allowed bounded interpretations:

- `DELEVERAGING_CANDIDATE` — token return < 0 and OI delta < 0;
- `NEW_SHORT_CANDIDATE` — token return < 0 and OI delta > 0;
- `MIXED_OR_INSUFFICIENT` — otherwise.

These labels describe market structure only. They MUST NOT assert that an abnormal on-chain flow caused the market move or that a security incident occurred.

## Acceptance

Focused tests must cover timing compatibility, no-lookahead, BTC-relative return, OI/funding deltas, liquidation preservation, the two required price/OI patterns, and explicit non-causal output.
