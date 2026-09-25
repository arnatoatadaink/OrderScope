import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { SchedulePolicy } from "./schedule.ts";
import { loadUniverseSnapshot } from "./universe.ts";

const observedNow = new Date("2026-09-25T02:44:38.000Z");
const retentionFloor = "2026-09-24T02:44:38.000Z";

const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-09-23", endExclusive: "2026-09-25" },
  generatedAt: observedNow.toISOString(),
  revision: "pb08-readonly-snapshot",
  sessions: [
    {
      marketDate: "2026-09-23",
      sessionKind: "REGULAR",
      opensAt: "2026-09-23T13:30:00.000Z",
      closesAt: "2026-09-23T20:00:00.000Z",
      isShortened: false,
      calendarRevision: "pb08-readonly-snapshot",
    },
    {
      marketDate: "2026-09-24",
      sessionKind: "REGULAR",
      opensAt: "2026-09-24T13:30:00.000Z",
      closesAt: "2026-09-24T20:00:00.000Z",
      isShortened: false,
      calendarRevision: "pb08-readonly-snapshot",
    },
  ],
};

function cp(version: number, through: string): StoredCoverageCheckpoint {
  return {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    symbol: "NVDA",
    interval: "1Min",
    sessionScope: "REGULAR",
    logicalDataVariant: "stock:iex:raw",
    completeThrough: through,
    sourceObservedThrough: through,
    state: "COMPLETE",
    missingRanges: [],
    version,
    universeRevision: "stock-monitoring-canary-v0.1",
  };
}

test("PB-08 fresh snapshot requires four clean NVDA jobs to reach the retained Regular frontier", () => {
  const universe = {
    ...loadUniverseSnapshot("canary-v0.1"),
    instruments: loadUniverseSnapshot("canary-v0.1").instruments.filter(x => x.symbol === "NVDA"),
  };
  const policy = new SchedulePolicy({
    retentionFloor,
    overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
    finalizationLagMs: { "1Min": 60_000, "15Min": 120_000, "1Day": 1_800_000 },
    maxBarsPerJob: 100,
    logicalDataVariant: () => "stock:iex:raw",
  });

  const first = policy.plan(universe, calendar, [cp(61, "2026-09-23T18:28:00.000Z")], observedNow)[0]!;
  assert.deepEqual(first.requestedRange, {
    startInclusive: "2026-09-24T13:30:00.000Z",
    endExclusive: "2026-09-24T15:10:00.000Z",
  });

  const second = policy.plan(universe, calendar, [cp(62, "2026-09-24T15:10:00.000Z")], observedNow)[0]!;
  assert.deepEqual(second.requestedRange, {
    startInclusive: "2026-09-24T15:09:00.000Z",
    endExclusive: "2026-09-24T16:49:00.000Z",
  });

  const third = policy.plan(universe, calendar, [cp(63, "2026-09-24T16:49:00.000Z")], observedNow)[0]!;
  assert.deepEqual(third.requestedRange, {
    startInclusive: "2026-09-24T16:48:00.000Z",
    endExclusive: "2026-09-24T18:28:00.000Z",
  });

  const fourth = policy.plan(universe, calendar, [cp(64, "2026-09-24T18:28:00.000Z")], observedNow)[0]!;
  assert.deepEqual(fourth.requestedRange, {
    startInclusive: "2026-09-24T18:27:00.000Z",
    endExclusive: "2026-09-24T20:00:00.000Z",
  });

  const done = policy.plan(universe, calendar, [cp(65, "2026-09-24T20:00:00.000Z")], observedNow);
  assert.equal(done.length, 0);
});
