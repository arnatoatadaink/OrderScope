import assert from "node:assert/strict";
import test from "node:test";
import {
  CANARY_V01_UNIVERSE_REVISION,
  V01_UNIVERSE,
  V01_UNIVERSE_REVISION,
  loadUniverseSnapshot,
} from "./universe.ts";

test("canary profile contains only the reviewed instruments and routes", () => {
  const snapshot = loadUniverseSnapshot("canary-v0.1", "2026-08-30T00:00:00.000Z");

  assert.equal(snapshot.revision, CANARY_V01_UNIVERSE_REVISION);
  assert.deepEqual(snapshot.instruments, [
    { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    { symbol: "QQQ", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    { symbol: "AMD", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    { symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" },
  ]);
});

test("full profile preserves the complete v0.1 universe", () => {
  const snapshot = loadUniverseSnapshot("full-v0.1");
  assert.equal(snapshot.revision, V01_UNIVERSE_REVISION);
  assert.equal(snapshot.instruments, V01_UNIVERSE);
});

test("unknown profiles fail closed", () => {
  assert.throws(() => loadUniverseSnapshot("typo"), /unsupported UNIVERSE_PROFILE: typo/);
});
