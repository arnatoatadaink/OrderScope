# OrderScope v0.1.6 Crypto lane source audit — 2026-09-30

Status: **AUDIT COMPLETE / IMPLEMENTATION REQUIRED**

## 1. Accepted parent boundary

v0.1.6 must be built cumulatively on the accepted v0.1.5 synthetic boundary:

```text
v0.1.5 = 415de1f1dd42f70bd66992961cb43be7edba6ade
```

Do not branch from historical `main`, the old pre-reconstruction line, or a later implementation commit.

## 2. Canonical v0.1.6 scope

Canonical registry authority:

```text
cfc850c94738820f3b12e783791c9030edd216dc
```

The v0.1.6 lane owns canonical `UWBS-068..079`:

| Canonical ID | Historical alias | Scope |
| --- | --- | --- |
| UWBS-068 | UWBS-036 | Crypto derivatives Fact / Derived Metric contract |
| UWBS-069 | UWBS-037 | BTC macro-leader / altcoin relative-context model |
| UWBS-070 | UWBS-038 | BTC institutional-flow / market-structure source survey |
| UWBS-071 | UWBS-039 | 24/7 crypto time-window / weekend-liquidity contract |
| UWBS-072 | UWBS-040 | NEAR/BTC multi-layer Canary and false-positive suite |
| UWBS-073 | UWBS-041 | Multi-venue futures/perpetual acquisition adapters |
| UWBS-074 | UWBS-042 | Durable derivatives snapshot archive and catch-up lifecycle |
| UWBS-075 | UWBS-043 | Liquidation normalization and cascade metrics |
| UWBS-076 | UWBS-044 | Price-zone OI retention / Position Map analysis |
| UWBS-077 | UWBS-045 | Cross-venue divergence and data-quality guards |
| UWBS-078 | UWBS-046 | Futures-position tracking Canary for NEAR reference episode |
| UWBS-079 | UWBS-047 | Pacific weekend handoff / weekday re-risking validation |

Historical aliases must not be used as implementation selectors because `UWBS-036` is already consumed by accepted v0.1.3 work and the other historical IDs belong to append-only planning provenance.

## 3. Canonical dependency graph

The canonical registry defines the main implementation order:

```text
UWBS-068 -> UWBS-069
UWBS-068 -> UWBS-073 -> UWBS-074 -> UWBS-075
UWBS-074 + UWBS-075 -> UWBS-076
UWBS-073 + UWBS-074 -> UWBS-077
UWBS-073..077 -> UWBS-078
UWBS-071 + UWBS-073..078 -> UWBS-079
```

`UWBS-070` is primarily source/governance work and may proceed in parallel with the base contract work. `UWBS-072` is the early multi-layer Canary and should be implemented only after the minimal contracts needed to represent BTC/NEAR, derivatives and time-window context exist.

## 4. Historical design provenance found

The following commits are useful design/research provenance but are not accepted implementation source commits for v0.1.6:

| SHA | Classification | Relevance |
| --- | --- | --- |
| `e7e93aeef59b34c7d07fb533e41c2de3dde784f0` | DESIGN_PROVENANCE_ONLY | Crypto macro-leader / derivatives context gap report; defines UWBS-036..040 concepts |
| `c180cec2c3036ba193e738f7186f6797020c895c` | DESIGN_PROVENANCE_ONLY | Backlog capture for crypto macro-leader / derivatives gaps |
| `fc8a9a11d3690129619aa4a1825f08bd03d968c7` | DESIGN_PROVENANCE_ONLY | OI/funding/liquidation, exchange collection, Position Map and archive design |
| `4d842af1dd9165ee08aa05292f3fd8072ace15c3` | DESIGN_PROVENANCE_ONLY | Futures-position tracking backlog |
| `07d957ba56b301794357e11e2ccb564c72191e68` | DESIGN_PROVENANCE_ONLY | BTC/altcoin synchronization and weekend validation plan |
| `1b5d2d27897cd5925fe81a5e3bbc9ab925453581` | DESIGN_PROVENANCE_ONLY | NEAR liquidation-regime transition / Canary evidence |
| `cfc850c94738820f3b12e783791c9030edd216dc` | DOC_ONLY / GOVERNANCE | Canonical ID registry and dependency authority |

These documents are valuable specification inputs, but none proves accepted implementation of canonical `UWBS-068..079`.

## 5. Existing code discovered outside the v0.1.6 boundary

Repository `main` contains a crypto package:

```text
analysis/app/orderscope_local/crypto/
  __init__.py
  btc_spot_etf_flow.py
```

The related implementation history includes:

```text
18a3392a35a0f0a00efcb60da571f5aea90202e2  Add UWBS-084 BTC spot ETF flow contract
c5762ae59ad8764293b72222ce7f82cc791c5172  Add UWBS-084 BTC spot ETF flow normalizer
122aaee0e268f67ac13d21d17b885271d15cbc8a  Test UWBS-084 BTC spot ETF flow contract
55d25d643282d3441e2c48104c7f4644b3dec38f  Test UWBS-084 BTC spot ETF flow normalizer
ffc1d846d44d72efd19de3e2627772aea52d4472  Document UWBS-084 BTC spot ETF flow normalization
1ea6604abb5ef00c6d0de31b0f223e05723291ec  Add crypto acquisition package
```

This is **later-version work**. `UWBS-084` belongs to the Oil / cross-asset lane, not v0.1.6. It may provide architectural inspiration or a future shared package surface, but it must not be replayed into v0.1.6 merely because it lives under `orderscope_local/crypto/`.

Classification:

```text
UWBS-084 BTC ETF flow implementation = OTHER_VERSION / EXCLUDE_FROM_V0.1.6_REPLAY
```

## 6. Audit result by canonical task

### UWBS-068 — Crypto derivatives Fact / Derived Metric contract

Status: **DESIGN READY / IMPLEMENTATION REQUIRED**

Design provenance is strong. Required normalized concepts already identified include:

- venue / instrument / contract type;
- OI in contracts/base/USD where available;
- funding and funding interval;
- mark/index/spot reference price;
- basis / premium;
- derivatives volume;
- long/short liquidation;
- source timestamp / retrieved_at / revision;
- strict Fact vs Derived Metric vs Interpretation separation.

Recommended first implementation task.

### UWBS-069 — BTC macro-leader / altcoin relative-context model

Status: **DESIGN READY / IMPLEMENTATION REQUIRED**

Required concepts include:

- BTC-relative return;
- rolling BTC beta;
- residual return;
- lagged cross-correlation;
- breadth / synchronized direction;
- local-amplification vs BTC-led context;
- no causal claim from correlation alone.

Depends on the base derivatives/market observation contract.

### UWBS-070 — BTC institutional-flow / market-structure source survey

Status: **RESEARCH PARTIALLY DONE / FORMAL SURVEY REQUIRED**

Design documents identify candidate channels such as BTC ETF flows, CME futures/OI/basis, major spot-market context and regulatory events. A later `UWBS-084` implementation exists, but it is not v0.1.6 source.

For v0.1.6 this task should remain a provider/source survey and contract-governance deliverable; no live provider activation is required.

### UWBS-071 — 24/7 crypto time-window / weekend-liquidity contract

Status: **DESIGN READY / IMPLEMENTATION REQUIRED**

Required semantics:

- continuous UTC timeline;
- UTC day boundaries;
- analysis windows for Asia/Europe/U.S. participation periods;
- weekend/weekday flags;
- traditional-market boundary context;
- provider outage/maintenance awareness;
- no participant-nationality inference.

### UWBS-072 — NEAR/BTC multi-layer Canary

Status: **HISTORICAL CASE AVAILABLE / REPRODUCIBLE FIXTURE NOT YET IMPLEMENTED**

The 2026-09-18..24 NEAR case provides useful scenario phases, but some observations came from supplied charts rather than normalized source records. It must therefore remain an experimental Canary until reproducible acquisition exists.

### UWBS-073 — Multi-venue futures/perpetual acquisition adapters

Status: **PROVIDER DESIGN READY / IMPLEMENTATION REQUIRED**

Design candidates include Binance, Bybit, OKX and Hyperliquid. Initial v0.1.6 implementation should favor a normalized adapter boundary and fixture/offline payload support before live activation.

### UWBS-074 — Durable derivatives snapshot archive / catch-up lifecycle

Status: **DESIGN READY / IMPLEMENTATION REQUIRED**

Motivation is strong because some official historical endpoints have bounded retention. Required semantics include append-safe snapshots, source revision, gap/catch-up handling and reproducibility. Do not couple acceptance to remote D1 or live Worker mutation.

### UWBS-075 — Liquidation normalization / cascade metrics

Status: **DESIGN READY / IMPLEMENTATION REQUIRED**

Required distinction:

```text
long liquidation != new short
short liquidation != new long
```

Support both event-level and provider-bucketed liquidation inputs without fabricating individual events. Derived metrics may include liquidation imbalance / side ratio / cascade candidates.

### UWBS-076 — Position Map / OI retention

Status: **DESIGN READY / IMPLEMENTATION REQUIRED**

Must be a Derived Metric estimate, never a reconstructed position ledger. The design already proposes price buckets, OI added/removed, estimated retention, funding-at-build and later liquidation context.

### UWBS-077 — Cross-venue divergence / data-quality guards

Status: **DESIGN READY / IMPLEMENTATION REQUIRED**

Need explicit missingness and venue-specific provenance. Cross-venue disagreement should be detectable without silently averaging incompatible fields or contract definitions.

### UWBS-078 — NEAR futures-position tracking Canary

Status: **HISTORICAL CASE AVAILABLE / IMPLEMENTATION REQUIRED**

Use the NEAR episode only as an experimental reference fixture; do not hard-code observed price/OI/funding values as universal thresholds.

### UWBS-079 — Pacific weekend handoff / weekday re-risking validation

Status: **VALIDATION PLAN EXISTS / IMPLEMENTATION + MULTI-WEEK SAMPLE REQUIRED**

The synchronization report defines pre-event features, lag windows, breadth, volume confirmation and alternative explanations. v0.1 development release may ship this as experimental if the distinction between observation, hypothesis and validated recurrence is explicit.

## 7. Overall progress estimate

By development phase rather than raw file count:

```text
Problem discovery / research       ~90%
Canonical UWBS decomposition       100%
Dependency graph                   100%
Provider/source concept survey     ~60%
Normalized contracts               ~10%
Acquisition adapters               ~0%
Archive/catch-up                    ~0%
Derived metrics                     ~0%
Canary fixtures                     ~15% (research evidence only)
Focused tests                       ~0%
Release acceptance                  0%
```

Overall v0.1.6 engineering completion is approximately **20-25%**. The lane is specification-rich but implementation-light.

## 8. Recommended CP decomposition

Use the following implementation sequence:

```text
CP-068A  Crypto derivatives core contracts              [UWBS-068]
CP-071A  24/7 / weekend time-window contract            [UWBS-071]
CP-069A  BTC-relative context metrics                    [UWBS-069]
CP-070A  Source/provider survey closeout                 [UWBS-070]
CP-073A  Normalized multi-venue adapter interface        [UWBS-073]
CP-073B  Offline fixture adapters / venue normalization  [UWBS-073]
CP-074A  Snapshot archive contract                       [UWBS-074]
CP-074B  Gap/catch-up lifecycle                          [UWBS-074]
CP-075A  Liquidation normalization                       [UWBS-075]
CP-075B  Cascade / imbalance metrics                     [UWBS-075]
CP-076A  Position Map / OI retention metrics             [UWBS-076]
CP-077A  Cross-venue quality/divergence guards           [UWBS-077]
CP-072A  NEAR/BTC multi-layer Canary                     [UWBS-072]
CP-078A  Futures-position NEAR Canary                    [UWBS-078]
CP-079A  Weekend handoff / re-risking experimental test  [UWBS-079]
CP-16X   Full regression + v0.1.6 boundary acceptance
```

Parallelism:

- CP-068A and CP-071A can start immediately in parallel.
- CP-070A can proceed independently.
- CP-069A should follow minimal core market/derivatives contracts.
- CP-073A must precede archive/liquidation/cross-venue implementation.
- CP-072A / CP-078A / CP-079A should be late-stage validation tasks.

## 9. Suggested package boundary

Do not reuse the later-version `btc_spot_etf_flow.py` as the v0.1.6 implementation root.

Suggested package structure:

```text
analysis/app/orderscope_local/crypto_market_structure/
  __init__.py
  models.py
  time_windows.py
  relative_context.py
  adapters.py
  archive.py
  liquidations.py
  position_map.py
  quality.py

analysis/tests/crypto_market_structure/
```

If repository conventions favor `orderscope_local/crypto/`, that package name may be reused only after checking that later `UWBS-084` history will not create replay contamination. A separate `crypto_market_structure` package is safer for v0.1.6 reconstruction.

## 10. Development-release posture

v0.1.6 may follow the same experimental-release policy as v0.1.4 and v0.1.5.

Required:

- contract behavior tests;
- provenance / UTC / as-of semantics;
- full Python regression;
- compileall / diff check;
- Fact / Derived Metric / Interpretation separation;
- explicit missingness and cross-venue provenance;
- no later-version contamination.

May remain experimental:

- universal liquidation-cascade thresholds;
- universal OI-retention thresholds;
- BTC causal leadership claim;
- weekend re-risking recurrence strength;
- provider-specific live operational acceptance;
- empirical false-positive rates.

## 11. Immediate next action

Start with `CP-068A / UWBS-068` on a branch based exactly on v0.1.5:

```text
codex/uwbs-068-crypto-derivatives-contract
base = 415de1f1dd42f70bd66992961cb43be7edba6ade
```

Implement only source-neutral contracts and focused tests first. Do not bring in `UWBS-084`, live provider calls, archive mutation, or later CPs during the first commit set.

## 12. Audit decision

```text
v0.1.6 historical replay-only reconstruction: NO
v0.1.6 new implementation required: YES
existing design provenance sufficient to begin: YES
existing canonical implementation closeout: NO
later-version contamination risk: HIGH around orderscope_local/crypto and UWBS-084
recommended first task: UWBS-068 / CP-068A
```
