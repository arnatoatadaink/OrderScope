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
  assert.deepEqual(
    snapshot.instruments.map(({ symbol, cadence }) => `${symbol}:${cadence}`),
    [
      "SPY:1Min", "QQQ:1Min", "IWM:1Min", "RSP:1Min", "XLK:1Min", "XLF:1Min",
      "XLE:1Min", "XLI:1Min", "XLU:1Min", "NVDA:1Min", "AMD:1Min", "AVGO:1Min",
      "CBRS:1Min", "VRT:1Min", "ANET:1Min", "CEG:1Min", "VST:1Min", "MSFT:1Min",
      "GOOGL:1Min", "AMZN:1Min", "META:1Min", "MSTR:1Min", "RIOT:1Min", "COIN:1Min",
      "BTCUSD:1Min",
      "XLC:15Min", "XLY:15Min", "XLP:15Min", "XLV:15Min", "XLB:15Min", "XLRE:15Min",
      "MRVL:15Min", "INTC:15Min", "TSM:15Min", "ASML:15Min", "AMAT:15Min", "LRCX:15Min",
      "KLAC:15Min", "MU:15Min", "ARM:15Min", "ENTG:15Min", "Q:15Min", "MKSI:15Min",
      "MTRN:15Min", "ETN:15Min", "PWR:15Min", "GEV:15Min", "NEE:15Min", "MARA:15Min",
      "CLSK:15Min", "CORZ:15Min", "IREN:15Min", "CIFR:15Min",
      "EWJ:1Day", "EWU:1Day", "EWG:1Day", "EWC:1Day", "EWA:1Day", "MCHI:1Day",
      "EWT:1Day", "EWY:1Day", "INDA:1Day", "EWZ:1Day", "EWW:1Day", "TLT:1Day",
      "IEF:1Day", "HYG:1Day", "LQD:1Day", "GLD:1Day", "SLV:1Day", "USO:1Day",
      "ETHUSD:1Day", "ORCL:1Day", "PLTR:1Day", "CRM:1Day", "NOW:1Day", "SNOW:1Day",
      "WDC:1Day", "STX:1Day", "SNDK:1Day", "HOOD:1Day", "JPM:1Day", "BAC:1Day",
      "GS:1Day", "SCHW:1Day", "COF:1Day", "CAT:1Day", "DE:1Day", "UPS:1Day",
      "FDX:1Day", "UNP:1Day", "LMT:1Day", "RTX:1Day", "NOC:1Day", "GD:1Day",
      "XOM:1Day", "CVX:1Day", "FCX:1Day", "NEM:1Day", "WMT:1Day", "COST:1Day",
      "HD:1Day", "TSLA:1Day", "LLY:1Day", "UNH:1Day", "MRNA:1Day",
    ],
  );
});

test("full profile preserves reviewed representative cadence and provider routes", () => {
  const bySymbol = new Map(loadUniverseSnapshot("full-v0.1").instruments
    .map((instrument) => [instrument.symbol, instrument]));
  for (const [symbol, cadence, providerRoute] of [
    ["NVDA", "1Min", "alpaca_stock_bars"],
    ["AMD", "1Min", "alpaca_stock_bars"],
    ["MRVL", "15Min", "alpaca_stock_bars"],
    ["MU", "15Min", "alpaca_stock_bars"],
    ["EWJ", "1Day", "alpaca_stock_bars"],
    ["TLT", "1Day", "alpaca_stock_bars"],
    ["BTCUSD", "1Min", "alpaca_crypto_bars"],
    ["ETHUSD", "1Day", "alpaca_crypto_bars"],
  ] as const) {
    assert.deepEqual(bySymbol.get(symbol), { symbol, cadence, providerRoute });
  }
});

test("unknown profiles fail closed", () => {
  assert.throws(() => loadUniverseSnapshot("typo"), /unsupported UNIVERSE_PROFILE: typo/);
});
