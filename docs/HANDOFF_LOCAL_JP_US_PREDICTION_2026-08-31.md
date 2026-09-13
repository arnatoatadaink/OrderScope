# Local implementation handoff — Japan-to-U.S. prediction

Status: ready for local continuation  
Handoff date: 2026-08-31  
Remote branch: `docs/mermaid-conventions-v0.1`  
Verified implementation baseline: `bff980a54ac632a405c99715c0815d6d5a644f69`

## 1. Objective of the next local slice

Implement the provider-neutral, immutable Japanese-input snapshot boundary used by the provisional Japan-to-U.S. prediction extension.

This slice should make same-day Japanese observations representable and testable without selecting or embedding MARKET SPEED II RSS, kabu Station API, J-Quants, a transport product, a prediction model or a production storage product.

The intended output is a validated snapshot contract plus an injectable persistence/handoff port. It is not a live Japanese collector and it must not execute U.S. Premarket acquisition.

## 2. Current verified state

The baseline already provides:

- a fixed 106-instrument U.S. monitoring Universe,
- Regular-session acquisition with durable D1 checkpoints and idempotent bar acceptance,
- `PREMARKET` as a separate calendar, normalization, checkpoint and planning scope,
- four prediction horizons: `PM_OPEN`, `PM_SESSION`, `REG_OPEN` and `REG_SESSION`,
- versioned `PredictionInputRegistry` and `PredictionTargetRegistry` contracts,
- the provisional `semiconductor-canary-v0.1` registry,
- a target-only 1-minute Premarket acquisition Universe derived without mutating monitoring cadence,
- Worker prediction shadow planning and sanitized digest projection,
- timestamp leakage checks based on `eventTime`, `retrievedAt` and `availableAt`.

Prediction shadow has two deliberately different states:

1. `WORKER_MODE=shadow`: report the configured prediction profile; perform no acquisition or detailed Premarket planning.
2. `WORKER_MODE=live` and `PREDICTION_MODE=shadow`: execute the existing Regular acquisition path and independently plan Premarket target coverage, but do not execute or persist those Premarket jobs.

The second state is covered by dependency-injected integration tests. Do not use production credentials merely to exercise it locally.

## 3. Start locally

```bash
git fetch origin
git switch docs/mermaid-conventions-v0.1
git pull --ff-only
npm ci
npm test
npm run typecheck
npm run deploy:check
```

Expected baseline verification as of this handoff:

- 87 tests pass,
- TypeScript type checking succeeds,
- Wrangler dry-run succeeds,
- dry-run upload size is approximately 87.61 KiB / 20.14 KiB gzip.

The size is an observed baseline, not an acceptance threshold. Toolchain changes can alter it.

## 4. Read these files first

Read in this order before editing:

1. `docs/stock_monitoring_v0.1_spec.md`
2. `docs/stock_monitoring_v0.1_universe_spec.md`
3. `docs/PROVISIONAL_DESIGN_JP_US_PREDICTION_v0.1.md`
4. `docs/PREDICTION_REGISTRY_SEMICONDUCTOR_CANARY_v0.1.md`
5. `docs/DETAILED_DESIGN_CFG_PROVIDER_v0.1.md`
6. `docs/DETAILED_DESIGN_SCHEDULER_MARKET_v0.1.md`
7. `docs/IMPLEMENTATION_DECISIONS_WORKER_v0.1.md`
8. `src/prediction.ts`
9. `src/prediction-registry.ts`
10. `src/worker.ts`

If a provisional prediction document conflicts with the four-document Code of Truth, the normative Code of Truth wins. The prediction extension must remain outside the v0.1 Definition of Done unless explicitly promoted by a later decision.

## 5. Required implementation boundary

Add a provider-neutral contract, preferably in a focused module such as `src/prediction-snapshot.ts`, containing at least the following concepts:

- immutable snapshot identity and schema revision,
- input-registry revision,
- provider-neutral instrument identity,
- observation cadence and market/session identity,
- observed OHLCV fields without fabricated values,
- `eventTime`, `retrievedAt` and `availableAt`,
- source/provider reference and logical data variant,
- completeness/quality state and explicit reason codes,
- snapshot-level cutoff or `asOf`,
- deterministic validation and stable serialization/hash inputs,
- an injectable read/write handoff port with no Cloudflare-, Windows- or provider-specific dependency.

Reuse existing canonical value, timestamp and provenance semantics where they fit. Do not create a second incompatible bar model merely for Japanese data. If Japan's split-session representation requires a new market-session type, add it explicitly and do not interpolate across the lunch break.

The contract must be capable of distinguishing:

- an event that occurred before the cutoff but arrived too late,
- an event retrieved before the cutoff but not usable until later,
- missing input,
- partial input,
- rejected or malformed input,
- a complete usable snapshot.

## 6. Required tests

Add deterministic tests covering at least:

- valid immutable snapshot construction,
- registry-revision mismatch rejection,
- unknown or disabled instrument rejection,
- duplicate observation identity handling,
- out-of-order observations normalized without changing their timestamps,
- future `eventTime` rejection,
- `retrievedAt > cutoff` exclusion,
- `availableAt > cutoff` exclusion,
- missing and partial coverage reason codes,
- no interpolation across the Japanese lunch break,
- stable identity/hash for identical canonical input,
- different identity/hash when canonical content changes,
- provider-specific payload fields not leaking into the Core snapshot,
- port behavior through an in-memory test adapter.

Use fixtures and injected clocks. Tests must not call live providers or require secrets.

## 7. Safety and scope constraints

Do not do any of the following in this slice:

- add Japanese instruments to the fixed U.S. monitoring Universe,
- alter the normative cadence of existing U.S. instruments,
- execute or persist Premarket acquisition jobs,
- enable a real Japanese provider,
- guess desktop-provider symbol mappings,
- store broker account data, balances, orders, credentials or write controls,
- select an ETF, prediction model, feature weighting or promotion threshold,
- generate placeholder probability, return or volatility predictions,
- make D1, R2, local filesystem or Windows IPC part of the Core interface,
- deploy to Cloudflare or change production secrets.

The current eight Japanese inputs and two U.S. targets are provisional canary configuration. Their registration is not evidence of predictive validity.

## 8. Definition of done for the local slice

The local slice is complete when:

1. the provider-neutral snapshot and handoff contracts are implemented,
2. invalid or late information fails closed with explicit reasons,
3. the split-session boundary cannot create synthetic lunch-break observations,
4. no existing monitoring or prediction-shadow behavior regresses,
5. all tests, type checking and Worker dry-run succeed,
6. the provisional design and implementation-status documentation are updated,
7. one focused commit is created with no secrets or generated local state.

Suggested commit subject:

```text
feat: add immutable Japan prediction snapshots
```

## 9. Decisions that remain open after this slice

- MARKET SPEED II RSS versus kabu Station API for same-day local acquisition,
- verified provider-symbol mappings for the selected adapter,
- transport from the local Windows collector to the durable handoff port,
- storage retention and encryption policy,
- corporate-action and point-in-time membership handling,
- feature aggregation, weighting and outlier policy,
- anchor estimator and fallback order,
- ETF mapping and label comparison,
- minimum history requirements, especially for `Q`,
- model, calibration and measured promotion thresholds,
- authorization to execute U.S. Premarket jobs.

Keep these unresolved unless evidence or an explicit user decision resolves them.

## 10. Completion report expected from the local agent

Report:

- commit SHA and branch,
- files added or changed,
- contract and validation decisions made,
- tests added and measured results,
- Worker dry-run size,
- any deviation from this handoff,
- unresolved questions requiring user choice,
- confirmation that no live provider, deployment or Premarket execution was enabled.
