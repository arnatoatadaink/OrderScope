import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import {
  PREDICTION_HORIZON_ANCHORS,
  PREDICTION_HORIZONS,
  assertObservationUsableForPrediction,
  predictionAnchorWindows,
  predictionReadinessDeadline,
  planPredictionPremarketAcquisition,
  validatePredictionInputRegistry,
  validatePredictionTargetRegistry,
  type PredictionInputRegistry,
  type PredictionTargetRegistry,
} from "./prediction.ts";

const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-07-06", endExclusive: "2026-07-07" },
  generatedAt: "2026-07-06T00:00:00.000Z",
  revision: "calendar:prediction-test",
  sessions: [{
    marketDate: "2026-07-06", sessionKind: "PREMARKET",
    opensAt: "2026-07-06T08:00:00.000Z", closesAt: "2026-07-06T13:30:00.000Z",
    isShortened: false, calendarRevision: "calendar:prediction-test",
  }, {
    marketDate: "2026-07-06", sessionKind: "REGULAR",
    opensAt: "2026-07-06T13:30:00.000Z", closesAt: "2026-07-06T20:00:00.000Z",
    isShortened: false, calendarRevision: "calendar:prediction-test",
  }],
};

const inputRegistry: PredictionInputRegistry = {
  revision: "prediction-input:test-v1",
  market: "JAPAN_EQUITIES",
  generatedAt: "2026-07-06T06:31:00.000Z",
  instruments: [{
    instrumentId: "tse:fixture-0001",
    displaySymbol: "FIXTURE-0001",
    providerSymbolMappings: { fixture: "0001" },
    exchange: "TSE",
    themes: ["Semiconductor Materials"],
    baseCadence: "1Min",
    enabled: true,
    validFrom: "2026-07-01",
  }],
};

const targetRegistry: PredictionTargetRegistry = {
  revision: "prediction-target:test-v1",
  generatedAt: "2026-07-06T06:31:00.000Z",
  targets: [{
    targetId: "us-theme:fixture",
    themeOrSector: "Fixture Theme",
    constituentInstrumentIds: ["SPY"],
    labelPolicyVersion: "fixture-label-v1",
    enabledHorizons: PREDICTION_HORIZONS,
  }],
};

test("keeps the four agreed prediction horizons and anchor chain explicit", () => {
  assert.deepEqual(PREDICTION_HORIZONS, ["PM_OPEN", "PM_SESSION", "REG_OPEN", "REG_SESSION"]);
  assert.deepEqual(PREDICTION_HORIZON_ANCHORS, {
    PM_OPEN: { start: "PREVIOUS_REGULAR_CLOSE", end: "PM_OPEN_ANCHOR" },
    PM_SESSION: { start: "PM_OPEN_ANCHOR", end: "PREOPEN_ANCHOR" },
    REG_OPEN: { start: "PREOPEN_ANCHOR", end: "REG_OPEN_ANCHOR" },
    REG_SESSION: { start: "REG_OPEN_ANCHOR", end: "REGULAR_CLOSE_ANCHOR" },
  });
});

test("validates separate versioned input and target registries", () => {
  assert.equal(validatePredictionInputRegistry(inputRegistry), inputRegistry);
  assert.equal(validatePredictionTargetRegistry(targetRegistry), targetRegistry);
  assert.throws(() => validatePredictionInputRegistry({
    ...inputRegistry,
    instruments: [{ ...inputRegistry.instruments[0]!, instrumentId: "0001" }],
  }), /must be namespaced/);
  assert.throws(() => validatePredictionTargetRegistry({
    ...targetRegistry,
    targets: [{ ...targetRegistry.targets[0]!, constituentInstrumentIds: [], primaryLabelInstrumentId: undefined }],
  }), /requires a primary label instrument or constituents/);
});

test("enforces event, retrieval, and availability cutoffs without look-ahead", () => {
  const boundary = {
    featureCutoff: "2026-07-06T06:30:00.000Z",
    predictionGeneratedAt: "2026-07-06T07:55:00.000Z",
  };
  assert.doesNotThrow(() => assertObservationUsableForPrediction({
    eventTime: "2026-07-06T06:30:00.000Z",
    retrievedAt: "2026-07-06T06:31:00.000Z",
    availableAt: "2026-07-06T06:31:00.000Z",
  }, boundary));
  assert.throws(() => assertObservationUsableForPrediction({
    eventTime: "2026-07-06T06:31:00.000Z",
    retrievedAt: "2026-07-06T06:31:00.000Z",
    availableAt: "2026-07-06T06:31:00.000Z",
  }, boundary), /eventTime exceeds featureCutoff/);
  assert.throws(() => assertObservationUsableForPrediction({
    eventTime: "2026-07-06T06:30:00.000Z",
    retrievedAt: "2026-07-06T06:31:00.000Z",
    availableAt: "2026-07-06T07:55:01.000Z",
  }, boundary), /availableAt exceeds predictionGeneratedAt/);
});

test("derives the agreed anchor windows and daylight-time readiness deadline", () => {
  assert.deepEqual(predictionAnchorWindows(calendar, "2026-07-06"), [{
    anchor: "PM_OPEN_ANCHOR",
    startInclusive: "2026-07-06T08:00:00.000Z",
    endExclusive: "2026-07-06T08:15:00.000Z",
  }, {
    anchor: "PREOPEN_ANCHOR",
    startInclusive: "2026-07-06T13:25:00.000Z",
    endExclusive: "2026-07-06T13:30:00.000Z",
  }, {
    anchor: "REG_OPEN_ANCHOR",
    startInclusive: "2026-07-06T13:30:00.000Z",
    endExclusive: "2026-07-06T13:45:00.000Z",
  }]);
  assert.equal(predictionReadinessDeadline(calendar, "2026-07-06"), "2026-07-06T07:55:00.000Z");
});

test("refuses anchor materialization when Premarket is absent", () => {
  const regularOnly = { ...calendar, sessions: calendar.sessions.filter((session) => session.sessionKind === "REGULAR") };
  assert.throws(() => predictionAnchorWindows(regularOnly, "2026-07-06"), /exactly one PREMARKET/);
});

test("plans a bounded Premarket acquisition without changing the monitoring Universe", () => {
  const jobs = planPredictionPremarketAcquisition({
    acquisitionUniverse: {
      revision: "prediction-target:test-v1",
      generatedAt: "2026-07-06T00:00:00.000Z",
      instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
    },
    calendar,
    checkpoints: [],
    now: new Date("2026-07-06T08:03:30.000Z"),
    scheduleConfig: {
      retentionFloor: "2026-07-06T08:00:00.000Z",
      overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
      finalizationLagMs: { "1Min": 30_000, "15Min": 60_000, "1Day": 300_000 },
      maxBarsPerJob: 100,
      logicalDataVariant: () => "stock:iex:raw",
    },
  });

  assert.equal(jobs.length, 1);
  assert.equal(jobs[0]?.sessionScope, "PREMARKET");
  assert.equal(jobs[0]?.requestedRange.endExclusive, "2026-07-06T08:03:00.000Z");
  assert.equal(jobs[0]?.checkpointExpectations[0]?.coverageKey, "SPY|1Min|PREMARKET|stock:iex:raw");
});

test("rejects daily and crypto instruments at the Premarket planning boundary", () => {
  const base = {
    calendar,
    checkpoints: [],
    now: new Date("2026-07-06T08:03:30.000Z"),
    scheduleConfig: {
      retentionFloor: "2026-07-06T08:00:00.000Z",
      overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
      finalizationLagMs: { "1Min": 30_000, "15Min": 60_000, "1Day": 300_000 },
      maxBarsPerJob: 100,
      logicalDataVariant: () => "stock:iex:raw",
    },
  } as const;
  assert.throws(() => planPredictionPremarketAcquisition({
    ...base,
    acquisitionUniverse: {
      revision: "test", generatedAt: "2026-07-06T00:00:00.000Z",
      instruments: [{ symbol: "EWJ", cadence: "1Day", providerRoute: "alpaca_stock_bars" }],
    },
  }), /requires an intraday cadence/);
  assert.throws(() => planPredictionPremarketAcquisition({
    ...base,
    acquisitionUniverse: {
      revision: "test", generatedAt: "2026-07-06T00:00:00.000Z",
      instruments: [{ symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" }],
    },
  }), /requires an equity route/);
});
