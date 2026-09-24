import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { prioritizeAcquisitionJobs } from "./job-priority.ts";
import { SchedulePolicy } from "./schedule.ts";
import { loadUniverseSnapshot } from "./universe.ts";

const now0 = "2026-09-24T11:28:48.000Z";
const floor = "2026-09-23T11:28:48.000Z";
const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-09-23", endExclusive: "2026-09-24" },
  generatedAt: now0,
  revision: "pb07-competition-sep23",
  sessions: [{
    marketDate: "2026-09-23",
    sessionKind: "REGULAR",
    opensAt: "2026-09-23T13:30:00.000Z",
    closesAt: "2026-09-23T20:00:00.000Z",
    isShortened: false,
    calendarRevision: "pb07-competition-sep23",
  }],
};

function cp(
  symbol: string,
  scope: "REGULAR"|"ALL_TRADING",
  variant: string,
  completeThrough: string,
  version: number,
): StoredCoverageCheckpoint {
  return {
    coverageKey: `${symbol}|1Min|${scope}|${variant}`,
    symbol, interval: "1Min", sessionScope: scope, logicalDataVariant: variant,
    completeThrough, sourceObservedThrough: completeThrough,
    state: "COMPLETE", missingRanges: [], version,
    universeRevision: "stock-monitoring-canary-v0.1",
  };
}

test("PB-07 frozen competition reaches NVDA twice within seven unchanged Cron opportunities", () => {
  const universe = loadUniverseSnapshot("canary-v0.1");
  const checkpoints: StoredCoverageCheckpoint[] = [
    cp("AMD","REGULAR","stock:iex:raw","2026-09-02T13:51:00.000Z",40),
    cp("QQQ","REGULAR","stock:iex:raw","2026-09-02T15:57:00.000Z",9),
    cp("SPY","REGULAR","stock:iex:raw","2026-09-02T16:49:00.000Z",43),
    cp("NVDA","REGULAR","stock:iex:raw","2026-09-23T15:10:00.000Z",59),
    cp("BTCUSD","ALL_TRADING","crypto:us","2026-09-23T10:54:00.000Z",46),
  ];
  const p = new SchedulePolicy({
    retentionFloor: floor,
    overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
    finalizationLagMs: { "1Min": 60_000, "15Min": 120_000, "1Day": 1_800_000 },
    maxBarsPerJob: 100,
    logicalDataVariant: i => i.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : "stock:iex:raw",
  });

  const selected: string[][] = [];
  const nvdaEnds: string[] = [];
  for (let i=0;i<7;i++) {
    const now = new Date(Date.parse(now0)+i*60_000);
    const jobs = prioritizeAcquisitionJobs(p.plan(universe, calendar, checkpoints, now), checkpoints).slice(0,2);
    selected.push(jobs.map(j=>j.instruments[0]!.symbol));
    for (const job of jobs) {
      const key=job.checkpointExpectations[0]!.coverageKey;
      const item=checkpoints.find(c=>c.coverageKey===key)!;
      item.completeThrough=job.requestedRange.endExclusive;
      item.sourceObservedThrough=job.requestedRange.endExclusive;
      item.version+=1;
      if(item.symbol==="NVDA") nvdaEnds.push(job.requestedRange.endExclusive);
    }
  }

  assert.deepEqual(selected, [
    ["AMD","QQQ"],
    ["SPY","BTCUSD"],
    ["BTCUSD","AMD"],
    ["BTCUSD","NVDA"],
    ["QQQ","SPY"],
    ["BTCUSD","AMD"],
    ["NVDA","QQQ"],
  ]);
  assert.deepEqual(nvdaEnds, [
    "2026-09-23T16:49:00.000Z",
    "2026-09-23T18:28:00.000Z",
  ]);
});
