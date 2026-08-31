import assert from "node:assert/strict";
import test from "node:test";
import type { ProviderNeutralBar } from "./alpaca.ts";
import { normalizeMarketBar } from "./bar.ts";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { UniverseInstrument } from "./universe.ts";

const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-11-27", endExclusive: "2026-11-28" },
  generatedAt: "2026-11-27T00:00:00.000Z",
  revision: "calendar:test",
  sessions: [{
    marketDate: "2026-11-27", sessionKind: "REGULAR",
    opensAt: "2026-11-27T14:30:00.000Z", closesAt: "2026-11-27T18:00:00.000Z",
    isShortened: true, calendarRevision: "calendar:test",
  }],
};

const stock = (cadence: UniverseInstrument["cadence"]): UniverseInstrument => ({
  symbol: "SPY", cadence, providerRoute: "alpaca_stock_bars",
});
const source = (timestamp: string, overrides: Partial<ProviderNeutralBar> = {}): ProviderNeutralBar => ({
  symbol: "SPY", timestamp, open: 100, high: 104, low: 99, close: 102,
  volume: 10, tradeCount: 2, vwap: 101, provider: "alpaca", dataVariant: "stock:iex:raw",
  ...overrides,
});

test("normalizes an intraday bar on the authoritative shortened-session grid", () => {
  const result = normalizeMarketBar(source("2026-11-27T14:45:00Z"), stock("15Min"), calendar, "REGULAR");
  assert.equal(result.outcome, "NORMALIZED");
  if (result.outcome === "NORMALIZED") {
    assert.equal(result.bar.barEndUtc, "2026-11-27T15:00:00.000Z");
    assert.equal(result.bar.marketDate, "2026-11-27");
    assert.equal(result.bar.isShortenedSession, true);
  }
});

test("rejects misaligned, closed-session, and straddling intraday bars", () => {
  assert.equal(normalizeMarketBar(source("2026-11-27T14:31:00Z"), stock("15Min"), calendar, "REGULAR").outcome, "REJECTED");
  assert.equal(normalizeMarketBar(source("2026-11-27T18:00:00Z"), stock("1Min"), calendar, "REGULAR").outcome, "REJECTED");
  const oddCalendar = { ...calendar, sessions: [{ ...calendar.sessions[0]!, closesAt: "2026-11-27T17:58:00.000Z" }] };
  assert.equal(normalizeMarketBar(source("2026-11-27T17:45:00Z"), stock("15Min"), oddCalendar, "REGULAR").outcome, "REJECTED");
});

test("maps an equity daily source timestamp to actual Regular session bounds", () => {
  const result = normalizeMarketBar(source("2026-11-27T05:00:00Z"), stock("1Day"), calendar, "REGULAR");
  assert.equal(result.outcome, "NORMALIZED");
  if (result.outcome === "NORMALIZED") {
    assert.equal(result.bar.sourceTimestamp, "2026-11-27T05:00:00.000Z");
    assert.equal(result.bar.barStartUtc, "2026-11-27T14:30:00.000Z");
    assert.equal(result.bar.barEndUtc, "2026-11-27T18:00:00.000Z");
  }
});

test("rejects invalid canonical values without fabricating replacements", () => {
  const badOhlc = normalizeMarketBar(source("2026-11-27T14:30:00Z", { high: 101, close: 102 }), stock("1Min"), calendar, "REGULAR");
  assert.deepEqual(badOhlc.outcome === "REJECTED" && badOhlc.code, "INVALID_OHLC");
  const negativeVolume = normalizeMarketBar(source("2026-11-27T14:30:00Z", { volume: -1 }), stock("1Min"), calendar, "REGULAR");
  assert.deepEqual(negativeVolume.outcome === "REJECTED" && negativeVolume.code, "INVALID_ACTIVITY");
});

test("normalizes crypto independently on a continuous UTC grid", () => {
  const instrument: UniverseInstrument = { symbol: "BTCUSD", cadence: "15Min", providerRoute: "alpaca_crypto_bars" };
  const result = normalizeMarketBar(source("2026-11-26T18:00:00Z", {
    symbol: "BTCUSD", dataVariant: "crypto:us",
  }), instrument, { ...calendar, sessions: [] }, "ALL_TRADING");
  assert.equal(result.outcome, "NORMALIZED");
  if (result.outcome === "NORMALIZED") assert.equal(result.bar.sessionKind, "ALL_TRADING");
});
