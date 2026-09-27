import assert from "node:assert/strict";
import test from "node:test";
import {
  SEMICONDUCTOR_CANARY_PROFILE,
  loadPredictionRegistries,
} from "./prediction-registry.ts";
import { buildPredictionPremarketUniverse } from "./prediction.ts";
import { loadUniverseSnapshot } from "./universe.ts";

test("loads the exact versioned semiconductor canary registries", () => {
  const registries = loadPredictionRegistries(SEMICONDUCTOR_CANARY_PROFILE);
  assert.equal(registries.input.revision, "prediction-input:semiconductor-canary-v0.1");
  assert.deepEqual(registries.input.instruments.map((instrument) => instrument.instrumentId), [
    "tse:8035", "tse:6857", "tse:6146", "tse:7735",
    "tse:6920", "tse:6525", "tse:4063", "tse:3436",
  ]);
  assert.equal(registries.input.instruments.every((instrument) =>
    instrument.providerSymbolMappings.jquants === instrument.displaySymbol
    && instrument.baseCadence === "1Min"
    && instrument.enabled), true);
  assert.deepEqual(registries.target.targets.map((target) => target.targetId), [
    "us-theme:semiconductor-manufacturing",
    "us-theme:semiconductor-materials",
  ]);
  assert.equal(registries.target.targets.every((target) =>
    target.primaryLabelInstrumentId === undefined
    && target.labelPolicyVersion === "constituent-median-return-v0.1"), true);
  assert.throws(() => loadPredictionRegistries("typo"), /unsupported PREDICTION_TARGET_PROFILE: typo/);
});

test("builds a separate 1-minute Premarket target Universe without mutating monitoring cadence", () => {
  const registries = loadPredictionRegistries(SEMICONDUCTOR_CANARY_PROFILE);
  const monitoringUniverse = loadUniverseSnapshot("full-v0.1");
  const originalCadences = new Map(monitoringUniverse.instruments.map((instrument) => [
    instrument.symbol, instrument.cadence,
  ]));
  const acquisitionUniverse = buildPredictionPremarketUniverse(registries.target, monitoringUniverse);

  assert.deepEqual(acquisitionUniverse.instruments.map((instrument) => instrument.symbol), [
    "AMAT", "ASML", "ENTG", "KLAC", "LRCX", "MKSI", "MTRN", "Q", "TSM",
  ]);
  assert.equal(acquisitionUniverse.instruments.every((instrument) =>
    instrument.cadence === "1Min" && instrument.providerRoute === "alpaca_stock_bars"), true);
  assert.equal(monitoringUniverse.instruments.find((instrument) => instrument.symbol === "TSM")?.cadence,
    originalCadences.get("TSM"));
  assert.equal(monitoringUniverse.instruments.find((instrument) => instrument.symbol === "ENTG")?.cadence,
    originalCadences.get("ENTG"));
});

test("fails closed when a target is not in the approved monitoring Universe", () => {
  const registries = loadPredictionRegistries(SEMICONDUCTOR_CANARY_PROFILE);
  assert.throws(() => buildPredictionPremarketUniverse(registries.target, {
    revision: "fixture", generatedAt: "2026-08-31T00:00:00.000Z", instruments: [],
  }), /prediction target instrument is absent from monitoring Universe: AMAT/);
});
