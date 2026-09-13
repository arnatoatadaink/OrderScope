# Prediction Registry — Semiconductor Canary v0.1

Status: provisional research configuration; prediction shadow only.

Activation date: 2026-08-31. Input revision: `prediction-input:semiconductor-canary-v0.1`. Target revision: `prediction-target:semiconductor-canary-v0.1`.

This document records the evidence, decisions and unresolved items behind the first executable Japan-to-U.S. prediction canary. It is non-normative and does not modify the fixed U.S. monitoring Universe or the v0.1 Definition of Done.

## 1. Boundary

Configuration facts:

- The profile contains eight Japanese input instruments, two U.S. theme targets and nine distinct U.S. target-acquisition instruments.
- Japanese instruments remain only in `PredictionInputRegistry`; they are not added to `UniverseSnapshot`.
- U.S. target instruments are resolved from the fixed full monitoring Universe and copied into a separate 1-minute Premarket acquisition snapshot. Their normative monitoring cadences are not changed.
- `validFrom = 2026-08-31` is the registry activation date, not a listing date or a claim about historical data availability.
- The Worker plans Premarket jobs in prediction shadow mode. It does not execute those jobs, write Premarket bars, acquire Japanese data, train a model or emit a prediction.

Research hypothesis, not a fact:

- Same-day observations from Japanese semiconductor equipment and materials companies may add out-of-sample information to the four defined U.S. return horizons.
- Theme membership is an initial modelling grouping. It does not prove causality, lead-lag behavior or investability.

Measured results:

- None. No accuracy, correlation, coverage, latency or economic-value number is asserted by this registry.

## 2. Japanese input registry

The security codes and business classifications below are supported by issuer sources. The final theme column is the canary's modelling decision.

| Instrument ID | Issuer | Verified issuer evidence | Canary theme |
|---|---|---|---|
| `tse:8035` | Tokyo Electron | [Investor FAQ](https://www.tel.com/ir/faq/index.html) identifies code 8035; the company describes semiconductor production equipment | Semiconductor Manufacturing |
| `tse:6857` | Advantest | [Investor FAQ](https://www.advantest.com/en/investors/individual-investors/faq/) identifies code 6857; [business overview](https://www.advantest.com/en/investors/individual-investors/understand/) describes semiconductor test systems | Semiconductor Manufacturing |
| `tse:6146` | DISCO | [Corporate outline](https://www.disco.co.jp/eg/corporate/outline/index.html) identifies code 6146 and precision cutting, grinding and polishing equipment | Semiconductor Manufacturing |
| `tse:7735` | SCREEN Holdings | [Stock information](https://www.screen.co.jp/en/ir/stock) identifies code 7735; the [official site](https://www.screen.co.jp/en) describes semiconductor production equipment | Semiconductor Manufacturing |
| `tse:6920` | Lasertec | [Stock information](https://www.lasertec.co.jp/en/ir/stock/outline.html) identifies code 6920; [Investor FAQ](https://www.lasertec.co.jp/en/ir/faq.html) describes semiconductor inspection and measurement solutions | Semiconductor Manufacturing |
| `tse:6525` | Kokusai Electric | [Investor FAQ](https://www.kokusai-electric.com/en/ir/faq) identifies code 6525; the [official site](https://www.kokusai-electric.com/en/index.html) describes semiconductor manufacturing equipment | Semiconductor Manufacturing |
| `tse:4063` | Shin-Etsu Chemical | [Investor FAQ](https://www.shinetsu.co.jp/en/ir/ir-faq/) identifies code 4063 and semiconductor silicon products | Semiconductor Materials |
| `tse:3436` | SUMCO | [Corporate data](https://www.sumcosi.com/english/corporate/profile.html) identifies code 3436 and silicon wafers for the semiconductor industry | Semiconductor Materials |

Each entry currently has only a `jquants` provider mapping using the four-digit code. The [J-Quants minute-bars specification](https://jpx-jquants.com/ja/spec/eq-bars-minute) accepts four- or five-digit codes and defines the ordinary-stock resolution rule for a four-digit code. A desktop/local provider mapping is intentionally absent until that provider is selected and its symbol format is verified.

`baseCadence = 1Min` is the requested canonical cadence. It is not a claim that the J-Quants delivery is real time; the availability and fallback rules in `PROVISIONAL_DESIGN_JP_US_PREDICTION_v0.1.md` still apply.

## 3. U.S. target registry

The target constituents already exist in the fixed monitoring Universe. The profile does not auto-add symbols.

| Target | Constituent label basket | Label policy | Primary ETF |
|---|---|---|---|
| `us-theme:semiconductor-manufacturing` | TSM, ASML, AMAT, LRCX, KLAC | Cross-sectional median constituent return, v0.1 | None selected |
| `us-theme:semiconductor-materials` | ENTG, Q, MKSI, MTRN | Cross-sectional median constituent return, v0.1 | None selected |

The manufacturing basket is a deliberately narrow fabrication-equipment/foundry canary selected from the broader `Semiconductor / AI Supply Chain` group. The materials basket matches the existing `Semiconductor Materials` group. Both use all four horizons: `PM_OPEN`, `PM_SESSION`, `REG_OPEN` and `REG_SESSION`.

The absence of a primary ETF is explicit. The constituent median is a provisional label design, not a measured best label. ETF selection and constituent weighting require a later evidence-backed decision.

## 4. Worker shadow behavior

`PREDICTION_MODE = shadow` with `PREDICTION_TARGET_PROFILE = semiconductor-canary-v0.1` has two safe states:

1. While outer `WORKER_MODE = shadow`, the digest reports the configured prediction mode/profile and performs no market-data acquisition.
2. After outer `WORKER_MODE = live`, the regular acquisition path remains unchanged and executable. In parallel, the prediction path requests authoritative Premarket sessions, loads separate Premarket checkpoints and publishes a bounded plan summary. It never sends those jobs to the acquisition executor.

The digest summary exposes registry revisions, configured counts, planned job count and bounded job ranges. It does not expose credentials, provider responses or Japanese raw data.

## 5. Unresolved before execution or interpretation

- measured same-day availability and completeness for each Japanese input,
- local provider choice, verified symbol mappings and provider-neutral snapshot transport,
- corporate-action handling and historical point-in-time membership,
- weighting and outlier policy for Japanese features,
- minimum history and training eligibility for `Q` and other recent listings,
- exact anchor estimator and fallback order,
- ETF candidates and whether they outperform the ETF-less constituent labels,
- predictive validity versus intercept/base-rate and U.S.-only baselines,
- model, calibration and promotion thresholds,
- authorization to execute and persist Premarket acquisition rather than shadow-plan it.

Unknowns must remain explicit. No missing mapping, metric or threshold may be filled with a guessed value.
