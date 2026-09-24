import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { prioritizeAcquisitionJobs } from "./job-priority.ts";
import { SchedulePolicy } from "./schedule.ts";
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

function snapshot(): StoredCoverageCheckpoint[] {
  return [
    {
      coverageKey: "AMD|1Min|REGULAR|stock:iex:raw",
      symbol: "AMD", interval: "1Min", sessionScope: "REGULAR",
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-02T13:51:00.000Z",
      missingRanges: [{ startInclusive: "2026-09-02T13:51:00.000Z", endExclusive: "2026-09-02T13:52:00.000Z" }],
      version: 40, state: "PARTIAL", universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "QQQ|1Min|REGULAR|stock:iex:raw",
      symbol: "QQQ", interval: "1Min", sessionScope: "REGULAR",
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-02T15:57:00.000Z",
      missingRanges: [{ startInclusive: "2026-09-02T15:57:00.000Z", endExclusive: "2026-09-02T15:58:00.000Z" }],
      version: 9, state: "PARTIAL", universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "SPY|1Min|REGULAR|stock:iex:raw",
      symbol: "SPY", interval: "1Min", sessionScope: "REGULAR",
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-02T16:49:00.000Z",
      missingRanges: [], version: 43, state: "COMPLETE", universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
      symbol: "NVDA", interval: "1Min", sessionScope: "REGULAR",
      logicalDataVariant: "stock:iex:raw", completeThrough: "2026-09-22T20:00:00.000Z",
      missingRanges: [], version: 58, state: "COMPLETE", universeRevision: "stock-monitoring-canary-v0.1",
    },
    {
      coverageKey: "BTCUSD|1Min|ALL_TRADING|crypto:us",
      symbol: "BTCUSD", interval: "1Min", sessionScope: "ALL_TRADING",
      logicalDataVariant: "crypto:us", completeThrough: "2026-09-13T13:01:00.000Z",
      missingRanges: [{ startInclusive: "2026-09-13T13:01:00.000Z", endExclusive: "2026-09-13T13:03:00.000Z" }],
      version: 45, state: "PARTIAL", universeRevision: "stock-monitoring-canary-v0.1",
    },
  ];
}

function policy(now: string): SchedulePolicy {
  const floor = new Date(Date.parse(now) - 1_440 * 60_000).toISOString();
  return new SchedulePolicy({
    retentionFloor: floor,
    overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
    finalizationLagMs: { "1Min": 60_000, "15Min": 120_000, "1Day": 1_800_000 },
    maxBarsPerJob: 100,
    logicalDataVariant: (instrument) => instrument.providerRoute === "alpaca_crypto_bars"
      ? "crypto:us" : "stock:iex:raw",
  });
}

function selectedAt(
  checkpoints: StoredCoverageCheckpoint[],
  now: string,
): ReturnType<SchedulePolicy["plan"]> {
  const universe = loadUniverseSnapshot("canary-v0.1", "2026-08-29T00:00:00.000Z");
  const planned = policy(now).plan(universe, calendar, checkpoints, new Date(now));
  return prioritizeAcquisitionJobs(planned, checkpoints).slice(0, 2);
}

function markSucceeded(
  checkpoints: StoredCoverageCheckpoint[],
  jobs: ReturnType<SchedulePolicy["plan"]>,
): void {
  for (const job of jobs) {
    const key = job.checkpointExpectations[0]!.coverageKey;
    const item = checkpoints.find((checkpoint) => checkpoint.coverageKey === key)!;
    item.completeThrough = job.requestedRange.endExclusive;
    item.missingRanges = [];
    item.state = "COMPLETE";
    item.version += 1;
  }
}

test("PB-06 safe scheduler reaches NVDA within three unchanged priority opportunities", () => {
  const checkpoints = snapshot();

  const first = selectedAt(checkpoints, "2026-09-24T09:58:33.000Z");
  assert.deepEqual(first.map((job) => job.instruments[0]!.symbol), ["AMD", "QQQ"]);
  assert.ok(first.every((job) => job.instruments.length === 1));
  assert.ok(first.every((job) => job.requestedRange.startInclusive === "2026-09-23T13:30:00.000Z"));
  assert.ok(first.every((job) => job.requestedRange.endExclusive === "2026-09-23T15:10:00.000Z"));
  markSucceeded(checkpoints, first);

  const second = selectedAt(checkpoints, "2026-09-24T09:59:33.000Z");
  assert.deepEqual(second.map((job) => job.instruments[0]!.symbol), ["SPY", "BTCUSD"]);
  assert.ok(second.every((job) => job.instruments.length === 1));
  markSucceeded(checkpoints, second);

  const third = selectedAt(checkpoints, "2026-09-24T10:00:33.000Z");
  assert.equal(third[0]?.instruments[0]?.symbol, "NVDA");
  assert.equal(third[0]?.dueReason, "FORWARD_COVERAGE");
  assert.equal(third[0]?.mode, "INCREMENTAL");
  assert.deepEqual(third[0]?.requestedRange, {
    startInclusive: "2026-09-23T13:30:00.000Z",
    endExclusive: "2026-09-23T15:10:00.000Z",
  });
  assert.deepEqual(third[0]?.checkpointExpectations[0], {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    expectedVersion: 58,
    observedCompleteThrough: "2026-09-22T20:00:00.000Z",
  });
});
