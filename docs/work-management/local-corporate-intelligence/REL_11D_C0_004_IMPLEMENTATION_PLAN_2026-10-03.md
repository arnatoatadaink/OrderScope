# OrderScope — REL-11D / C0-004 Implementation Plan — 2026-10-03

Status: **IMPLEMENTATION PLAN — REL-11D START**
Release: `v0.1.11`
Formal WBS: `C0-004`
Canonical source: `UWBS-109`

## 1. Goal

Build a deterministic historical exploit/security-event replay contract that preserves timestamp provenance and computes consistent post-event market windows without treating article-reported percentage moves as quantitative truth.

## 2. Required timestamp classes

Historical event records keep these timestamps independently nullable:

- `first_onchain_detectable_at`
- `first_public_at`
- `first_official_at`

They must never be silently collapsed into one incident timestamp.

## 3. Required event windows

```text
+15m
+1h
+6h
+24h
+48h
+5d
+30d
```

Each window stores token return, BTC return, BTC-relative return, source provenance, and optional derivatives context.

## 4. Replay rules

- quantitative returns come from accepted market observations, not article prose;
- each return window starts from the selected source-grounded anchor timestamp;
- missing observations remain missing rather than interpolated silently;
- no-lookahead and provenance boundaries are retained;
- market correlation does not establish exploit causality;
- first on-chain/public/official timestamps remain separately inspectable.

## 5. NEAR Intents reference fixture

The historical QA fixture must be able to preserve the observed 2026-10-01 phase split used in project planning:

```text
~17:00 JST  price down + OI down  -> deleveraging-candidate phase
~22:00 JST  price down + OI up    -> new-short-candidate phase
```

The fixture validates replay semantics; it does not by itself establish the cause of the market move.

## 6. Initial implementation boundary

Create:

- `analysis/app/orderscope_local/crypto_onchain/historical_replay.py`
- `analysis/tests/crypto_onchain/test_c0_004_historical_replay.py`

Reuse accepted C0-003 market-context and existing crypto return/derivatives contracts where possible.

## 7. Acceptance before REL-11D completion

- timestamp classes remain distinct;
- window set is exact and deterministic;
- token/BTC-relative returns are reproducible;
- missing data fails closed;
- NEAR Intents two-phase replay is representable;
- no causal incident conclusion is inferred from market response;
- C0-001..004 focused tests pass;
- full `analysis/tests` passes;
- compileall and `git diff --check` pass.

Release-level cumulative acceptance remains at REL-11X.
