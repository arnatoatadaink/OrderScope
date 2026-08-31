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
  assert.equal(snapshot.instruments.length, 106);
  assert.equal(snapshot.instruments.filter((instrument) => instrument.cadence === "1Min").length, 25);
  assert.equal(snapshot.instruments.filter((instrument) => instrument.cadence === "15Min").length, 28);
  assert.equal(snapshot.instruments.filter((instrument) => instrument.cadence === "1Day").length, 53);
  for (const symbol of ["ENTG", "Q", "MKSI", "MTRN"]) {
    assert.deepEqual(snapshot.instruments.find((instrument) => instrument.symbol === symbol), {
      symbol,
      cadence: "15Min",
      providerRoute: "alpaca_stock_bars",
    });
  }
});

test("unknown profiles fail closed", () => {
  assert.throws(() => loadUniverseSnapshot("typo"), /unsupported UNIVERSE_PROFILE: typo/);
});
