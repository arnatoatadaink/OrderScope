import assert from "node:assert/strict";
import test from "node:test";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import type { CoverageCheckpointPort } from "./checkpoint.ts";
import { gapRetryEligibility } from "./gap-retry.ts";
import { prioritizeAcquisitionJobs } from "./job-priority.ts";
import type { AcquisitionJob } from "./schedule.ts";
import { loadUniverseSnapshot } from "./universe.ts";
import { loadMarketCheckpoints } from "./market-checkpoint-load.ts";

test("full-v0.1 checkpoint fan-out issues 106 point reads before acquisition", async () => {
  const coverageKeys: string[] = [];
  const checkpoints = {
    get: async (coverageKey: string) => { coverageKeys.push(coverageKey); return undefined; },
  } as CoverageCheckpointPort;

  const stored = await loadMarketCheckpoints(loadUniverseSnapshot("full-v0.1"), checkpoints, "iex");

  assert.deepEqual(stored, []);
  assert.equal(coverageKeys.length, 106);
  assert.equal(new Set(coverageKeys).size, 106);
  assert.ok(coverageKeys.includes("BTCUSD|1Min|ALL_TRADING|crypto:us"));
  assert.ok(coverageKeys.includes("ETHUSD|1Day|ALL_TRADING|crypto:us"));
  assert.ok(coverageKeys.includes("NVDA|1Min|REGULAR|stock:iex:raw"));
  assert.ok(coverageKeys.includes("EWJ|1Day|REGULAR|stock:iex:raw"));
});

const partial: StoredCoverageCheckpoint = {
  coverageKey: "BTCUSD|1Min|ALL_TRADING|crypto:us",
  symbol: "BTC/USD",
  interval: "1Min",
  sessionScope: "ALL_TRADING",
  logicalDataVariant: "crypto:us",
  completeThrough: "2026-08-29T16:28:00.000Z",
  state: "PARTIAL",
  missingRanges: [{
    startInclusive: "2026-08-29T16:28:00.000Z",
    endExclusive: "2026-08-29T16:29:00.000Z",
  }],
  lastAttemptAt: "2026-08-30T15:16:00.000Z",
  retryNotBefore: "2026-08-30T15:31:00.000Z",
  version: 2,
};

test("defers a known partial gap until its durable retry eligibility time", () => {
  assert.deepEqual(gapRetryEligibility(partial, new Date("2026-08-30T15:17:00.000Z"), 15), {
    coverageKey: partial.coverageKey,
    retryEligibleAt: "2026-08-30T15:31:00.000Z",
  });
  assert.equal(gapRetryEligibility(partial, new Date("2026-08-30T15:31:00.000Z"), 15), undefined);
});

test("does not defer complete, newly discovered, or malformed checkpoints", () => {
  assert.equal(gapRetryEligibility({ ...partial, state: "COMPLETE", missingRanges: [] }, new Date(), 15), undefined);
  assert.equal(gapRetryEligibility({ ...partial, retryNotBefore: undefined }, new Date(), 15), undefined);
  assert.equal(gapRetryEligibility({ ...partial, retryNotBefore: "invalid" }, new Date(), 15), undefined);
});

function acquisitionJob(
  symbol: string,
  dueReason: AcquisitionJob["dueReason"],
): AcquisitionJob {
  const coverageKey = `${symbol}|1Min|REGULAR|stock:iex:raw`;
  return {
    jobId: `job-${symbol}`,
    jobKind: "MARKET_BARS",
    createdAt: "2026-09-03T00:00:00.000Z",
    universeRevision: "canary-v0.1",
    calendarRevision: "calendar-v1",
    instruments: [{ symbol, cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
    interval: "1Min",
    requestedRange: {
      startInclusive: "2026-09-02T13:30:00.000Z",
      endExclusive: "2026-09-02T14:30:00.000Z",
    },
    sessionScope: "REGULAR",
    mode: dueReason === "MISSING_RANGE" ? "RECONCILE" : "INCREMENTAL",
    providerRoute: "alpaca_stock_bars",
    checkpointExpectations: [{ coverageKey }],
    attempt: 0,
    dueReason,
  };
}

function storedCheckpoint(symbol: string, completeThrough: string): StoredCoverageCheckpoint {
  return {
    coverageKey: `${symbol}|1Min|REGULAR|stock:iex:raw`,
    symbol,
    interval: "1Min",
    sessionScope: "REGULAR",
    logicalDataVariant: "stock:iex:raw",
    completeThrough,
    state: "COMPLETE",
    missingRanges: [],
    version: 1,
  };
}

test("prioritizes eligible gaps, new coverage, then oldest forward coverage deterministically", () => {
  const jobs = [
    acquisitionJob("NVDA", "FORWARD_COVERAGE"),
    acquisitionJob("QQQ", "NO_CHECKPOINT"),
    acquisitionJob("AMD", "MISSING_RANGE"),
    acquisitionJob("SPY", "FORWARD_COVERAGE"),
    acquisitionJob("AAPL", "FORWARD_COVERAGE"),
  ];
  const checkpoints = [
    storedCheckpoint("NVDA", "2026-09-02T20:00:00.000Z"),
    storedCheckpoint("SPY", "2026-09-01T20:00:00.000Z"),
    storedCheckpoint("AAPL", "2026-09-01T20:00:00.000Z"),
  ];

  assert.deepEqual(
    prioritizeAcquisitionJobs(jobs, checkpoints).map((job) => job.instruments[0]?.symbol),
    ["AMD", "QQQ", "AAPL", "SPY", "NVDA"],
  );
});
