import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import { batchAcquisitionJobs, SchedulePolicy } from "./schedule.ts";
import { prioritizeAcquisitionJobs } from "./job-priority.ts";
import { loadUniverseSnapshot } from "./universe.ts";

const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-09-23", endExclusive: "2026-09-24" },
  generatedAt: "2026-09-24T09:58:33.000Z",
  revision: "pb06-frozen-sep23",
  sessions: [{
    marketDate: "2026-09-23",
    sessionKind: "REGULAR",
    opensAt: "2026-09-23T13:30:00.000Z",
    closesAt: "2026-09-23T20:00:00.000Z",
    isShortened: false,
    calendarRevision: "pb06-frozen-sep23",
  }],
};

test("PB-06 unchanged scheduler batches NVDA into the Sep23 stock handoff job", () => {
  const universe = loadUniverseSnapshot("canary-v0.1", "2026-08-29T00:00:00.000Z");
  const checkpoints = [
    {
      coverageKey: "AMD|1Min|REGULAR|stock:iex:raw",
      symbol: "AMD", interval: "1Min" as const, sessionScope: "REGULAR" as const,
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-02T13:51:00.000Z",
      missingRanges: [{ startInclusive: "2026-09-02T13:51:00.000Z", endExclusive: "2026-09-02T13:52:00.000Z" }],
      version: 40, state: "PARTIAL" as const, universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "QQQ|1Min|REGULAR|stock:iex:raw",
      symbol: "QQQ", interval: "1Min" as const, sessionScope: "REGULAR" as const,
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-02T15:57:00.000Z",
      missingRanges: [{ startInclusive: "2026-09-02T15:57:00.000Z", endExclusive: "2026-09-02T15:58:00.000Z" }],
      version: 9, state: "PARTIAL" as const, universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "SPY|1Min|REGULAR|stock:iex:raw",
      symbol: "SPY", interval: "1Min" as const, sessionScope: "REGULAR" as const,
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-02T16:49:00.000Z",
      missingRanges: [], version: 43, state: "COMPLETE" as const, universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
      symbol: "NVDA", interval: "1Min" as const, sessionScope: "REGULAR" as const,
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-22T20:00:00.000Z",
      missingRanges: [], version: 58, state: "COMPLETE" as const, universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "BTCUSD|1Min|ALL_TRADING|crypto:us",
      symbol: "BTCUSD", interval: "1Min" as const, sessionScope: "ALL_TRADING" as const,
      logicalDataVariant: "crypto:us", completeThrough: "2026-09-13T13:01:00.000Z",
      missingRanges: [{ startInclusive: "2026-09-13T13:01:00.000Z", endExclusive: "2026-09-13T13:03:00.000Z" }],
      version: 45, state: "PARTIAL" as const, universeRevision: "stock-monitoring-canary-v0.1",
    },
  ];

  const policy = new SchedulePolicy({
    retentionFloor: "2026-09-23T09:58:33.000Z",
    overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
    finalizationLagMs: { "1Min": 60_000, "15Min": 120_000, "1Day": 1_800_000 },
    maxBarsPerJob: 100,
    logicalDataVariant: (instrument) => instrument.providerRoute === "alpaca_crypto_bars"
      ? "crypto:us" : "stock:iex:raw",
  });

  const planned = policy.plan(universe, calendar, checkpoints, new Date("2026-09-24T09:58:33.000Z"));
  const runnable = batchAcquisitionJobs(prioritizeAcquisitionJobs(planned, checkpoints)).slice(0, 2);
  const stockBatch = runnable.find((job) => job.providerRoute === "alpaca_stock_bars");
  assert.ok(stockBatch);
  assert.deepEqual(stockBatch.requestedRange, {
    startInclusive: "2026-09-23T13:30:00.000Z",
    endExclusive: "2026-09-23T15:10:00.000Z",
  });
  assert.equal(stockBatch.mode, "INCREMENTAL");
  assert.equal(stockBatch.dueReason, "FORWARD_COVERAGE");
  assert.deepEqual(
    stockBatch.instruments.map((item) => item.symbol),
    ["AMD", "NVDA", "QQQ", "SPY"],
  );
  assert.ok(stockBatch.checkpointExpectations.some((item) =>
    item.coverageKey === "NVDA|1Min|REGULAR|stock:iex:raw"
    && item.expectedVersion === 58
    && item.observedCompleteThrough === "2026-09-22T20:00:00.000Z"));
});
