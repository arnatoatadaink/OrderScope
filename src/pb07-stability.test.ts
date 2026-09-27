import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { SchedulePolicy } from "./schedule.ts";
import { loadUniverseSnapshot } from "./universe.ts";

const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-09-23", endExclusive: "2026-09-24" },
  generatedAt: "2026-09-24T10:51:23.000Z",
  revision: "pb07-frozen-sep23",
  sessions: [{
    marketDate: "2026-09-23",
    sessionKind: "REGULAR",
    opensAt: "2026-09-23T13:30:00.000Z",
    closesAt: "2026-09-23T20:00:00.000Z",
    isShortened: false,
    calendarRevision: "pb07-frozen-sep23",
  }],
};

const nvda = loadUniverseSnapshot("canary-v0.1").instruments
  .filter((item) => item.symbol === "NVDA");

function policy(retentionFloor: string): SchedulePolicy {
  return new SchedulePolicy({
    retentionFloor,
    overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
    finalizationLagMs: { "1Min": 60_000, "15Min": 120_000, "1Day": 1_800_000 },
    maxBarsPerJob: 100,
    logicalDataVariant: () => "stock:iex:raw",
  });
}

function checkpoint(version: number, completeThrough: string): StoredCoverageCheckpoint {
  return {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    symbol: "NVDA",
    interval: "1Min",
    sessionScope: "REGULAR",
    logicalDataVariant: "stock:iex:raw",
    completeThrough,
    sourceObservedThrough: completeThrough,
    state: "COMPLETE",
    missingRanges: [],
    version,
    universeRevision: "stock-monitoring-canary-v0.1",
  };
}

test("PB-07 freezes two consecutive NVDA forward-coverage ranges after PB-06", () => {
  const universe = {
    revision: "stock-monitoring-canary-v0.1",
    generatedAt: "2026-08-29T00:00:00.000Z",
    instruments: nvda,
  };
  const p = policy("2026-09-23T11:00:00.000Z");

  const first = p.plan(
    universe,
    calendar,
    [checkpoint(59, "2026-09-23T15:10:00.000Z")],
    new Date("2026-09-24T10:55:00.000Z"),
  )[0]!;
  assert.equal(first.mode, "INCREMENTAL");
  assert.equal(first.dueReason, "FORWARD_COVERAGE");
  assert.deepEqual(first.requestedRange, {
    startInclusive: "2026-09-23T15:09:00.000Z",
    endExclusive: "2026-09-23T16:49:00.000Z",
  });
  assert.deepEqual(first.checkpointExpectations[0], {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    expectedVersion: 59,
    observedCompleteThrough: "2026-09-23T15:10:00.000Z",
  });

  const second = p.plan(
    universe,
    calendar,
    [checkpoint(60, "2026-09-23T16:49:00.000Z")],
    new Date("2026-09-24T10:56:00.000Z"),
  )[0]!;
  assert.equal(second.mode, "INCREMENTAL");
  assert.equal(second.dueReason, "FORWARD_COVERAGE");
  assert.deepEqual(second.requestedRange, {
    startInclusive: "2026-09-23T16:48:00.000Z",
    endExclusive: "2026-09-23T18:28:00.000Z",
  });
  assert.deepEqual(second.checkpointExpectations[0], {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    expectedVersion: 60,
    observedCompleteThrough: "2026-09-23T16:49:00.000Z",
  });
});
