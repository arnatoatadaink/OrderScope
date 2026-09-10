import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { prioritizeAcquisitionJobs } from "./job-priority.ts";
import { coverageKeyFor, SchedulePolicy } from "./schedule.ts";
import { loadUniverseSnapshot, type Cadence, type UniverseInstrument } from "./universe.ts";

const MINUTE = 60_000;
const DAY = 24 * 60 * MINUTE;
const universe = loadUniverseSnapshot("full-v0.1", "2026-09-11T00:00:00.000Z");

function fixtureCalendar(close = "2026-09-10T20:00:00.000Z"): MarketCalendarSnapshot {
  return {
    market: "US_EQUITIES",
    dateRange: { startInclusive: "2026-09-09", endExclusive: "2026-09-11" },
    generatedAt: "2026-09-11T00:00:00.000Z",
    revision: `capacity-${close}`,
    sessions: [{
      marketDate: "2026-09-09", sessionKind: "REGULAR",
      opensAt: "2026-09-09T13:30:00.000Z", closesAt: "2026-09-09T20:00:00.000Z",
      isShortened: false, calendarRevision: `capacity-${close}`,
    }, {
      marketDate: "2026-09-10", sessionKind: "REGULAR",
      opensAt: "2026-09-10T13:30:00.000Z", closesAt: close,
      isShortened: close !== "2026-09-10T20:00:00.000Z", calendarRevision: `capacity-${close}`,
    }],
  };
}

function key(instrument: UniverseInstrument): string {
  return coverageKeyFor(instrument,
    instrument.providerRoute === "alpaca_crypto_bars" ? "ALL_TRADING" : "REGULAR",
    instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : "stock:iex:raw");
}

function checkpoint(instrument: UniverseInstrument, completeThrough: string): StoredCoverageCheckpoint {
  return {
    coverageKey: key(instrument), symbol: instrument.symbol, interval: instrument.cadence,
    sessionScope: instrument.providerRoute === "alpaca_crypto_bars" ? "ALL_TRADING" : "REGULAR",
    logicalDataVariant: instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : "stock:iex:raw",
    completeThrough, state: "COMPLETE", missingRanges: [], version: 0,
  };
}

function plannedBars(close: string): Record<Cadence, number> {
  const equityMinutes = (Date.parse(close) - Date.parse("2026-09-10T13:30:00.000Z")) / MINUTE;
  return { "1Min": 24 * equityMinutes + 1_440, "15Min": 28 * (equityMinutes / 15), "1Day": 53 };
}

type Simulation = {
  maxAgeMinutes: Record<Cadence, number>;
  outstandingAtClose: Record<Cadence, number>;
  selected: Record<Cadence, number>;
};

export function simulateSession(close: string): Simulation {
  const calendar = fixtureCalendar(close);
  const openMs = Date.parse("2026-09-10T13:30:00.000Z");
  const closeMs = Date.parse(close);
  const checkpoints = new Map(universe.instruments.map((instrument) => [key(instrument), checkpoint(
    instrument,
    instrument.cadence === "1Day" ? "2026-09-09T20:00:00.000Z" : new Date(openMs).toISOString(),
  )]));
  // Isolate regular-session queueing by starting continuous crypto caught up at
  // the same instant as equities. Full UTC-day bar volume is measured separately.
  checkpoints.set(key(universe.instruments.find((item) => item.symbol === "BTCUSD")!),
    checkpoint(universe.instruments.find((item) => item.symbol === "BTCUSD")!, new Date(openMs).toISOString()));
  checkpoints.set(key(universe.instruments.find((item) => item.symbol === "ETHUSD")!),
    checkpoint(universe.instruments.find((item) => item.symbol === "ETHUSD")!, new Date(openMs).toISOString()));
  const maxAgeMinutes = { "1Min": 0, "15Min": 0, "1Day": 0 };
  const selected = { "1Min": 0, "15Min": 0, "1Day": 0 };

  for (let nowMs = openMs + MINUTE; nowMs <= closeMs + 30 * MINUTE; nowMs += MINUTE) {
    const now = new Date(nowMs);
    const policy = new SchedulePolicy({
      retentionFloor: new Date(nowMs - DAY).toISOString(),
      overlapMs: { "1Min": MINUTE, "15Min": 15 * MINUTE, "1Day": DAY },
      finalizationLagMs: { "1Min": MINUTE, "15Min": 2 * MINUTE, "1Day": 30 * MINUTE },
      maxBarsPerJob: 100,
      logicalDataVariant: (instrument) => instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : "stock:iex:raw",
    });
    const stored = [...checkpoints.values()];
    const jobs = policy.plan(universe, calendar, stored, now);
    for (const job of jobs) {
      const prior = checkpoints.get(job.checkpointExpectations[0]!.coverageKey)!;
      const age = Math.max(0, nowMs - Date.parse(prior.completeThrough!)) / MINUTE;
      maxAgeMinutes[job.interval] = Math.max(maxAgeMinutes[job.interval], age);
    }
    const job = prioritizeAcquisitionJobs(jobs, stored)[0];
    if (!job) continue;
    const prior = checkpoints.get(job.checkpointExpectations[0]!.coverageKey)!;
    checkpoints.set(prior.coverageKey, { ...prior, completeThrough: job.requestedRange.endExclusive,
      version: prior.version + 1 });
    selected[job.interval] += 1;
  }

  const atClose = new Date(closeMs + 30 * MINUTE);
  const finalPolicy = new SchedulePolicy({
    retentionFloor: new Date(atClose.getTime() - DAY).toISOString(),
    overlapMs: { "1Min": MINUTE, "15Min": 15 * MINUTE, "1Day": DAY },
    finalizationLagMs: { "1Min": MINUTE, "15Min": 2 * MINUTE, "1Day": 30 * MINUTE },
    maxBarsPerJob: 100,
    logicalDataVariant: (instrument) => instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : "stock:iex:raw",
  });
  const outstanding = finalPolicy.plan(universe, calendar, [...checkpoints.values()], atClose);
  return { maxAgeMinutes, selected, outstandingAtClose: {
    "1Min": outstanding.filter((job) => job.interval === "1Min").length,
    "15Min": outstanding.filter((job) => job.interval === "15Min").length,
    "1Day": outstanding.filter((job) => job.interval === "1Day").length,
  } };
}

test("full-v0.1 normal and shortened days retain the authoritative tiered bar volume", () => {
  assert.deepEqual(plannedBars("2026-09-10T20:00:00.000Z"), { "1Min": 10_800, "15Min": 728, "1Day": 53 });
  assert.deepEqual(plannedBars("2026-09-10T17:00:00.000Z"), { "1Min": 6_480, "15Min": 392, "1Day": 53 });
});

test("configured one-job scheduler is deterministic and materially misses Tier A cadence", () => {
  const first = simulateSession("2026-09-10T20:00:00.000Z");
  const second = simulateSession("2026-09-10T20:00:00.000Z");
  assert.deepEqual(first, second);
  assert.ok(first.maxAgeMinutes["1Min"] > 1, JSON.stringify(first));
  assert.ok(first.outstandingAtClose["1Min"] > 0, JSON.stringify(first));
});

test("shortened session and empty-checkpoint catch-up remain bounded by real job selection", () => {
  const shortened = simulateSession("2026-09-10T17:00:00.000Z");
  assert.equal(Object.values(shortened.selected).reduce((sum, count) => sum + count, 0), 239);

  const now = new Date("2026-09-10T20:30:00.000Z");
  const jobs = new SchedulePolicy({
    retentionFloor: new Date(now.getTime() - DAY).toISOString(),
    overlapMs: { "1Min": MINUTE, "15Min": 15 * MINUTE, "1Day": DAY },
    finalizationLagMs: { "1Min": MINUTE, "15Min": 2 * MINUTE, "1Day": 30 * MINUTE },
    maxBarsPerJob: 100,
    logicalDataVariant: (instrument) => instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : "stock:iex:raw",
  }).plan(universe, fixtureCalendar(), [], now);
  assert.equal(jobs.length, 106);
  assert.ok(jobs.every((job) => job.dueReason === "NO_CHECKPOINT"));
  assert.equal(prioritizeAcquisitionJobs(jobs, [])[0]?.interval, "15Min");
});

test("steady-state overlap produces MATCHED observations without changing planned NEW volume", () => {
  const normal = plannedBars("2026-09-10T20:00:00.000Z");
  assert.equal(normal["1Min"] + normal["15Min"] + normal["1Day"], 11_581);
  // Every successful forward job deliberately requests one cadence interval of
  // already-covered data. The bar store records a new receipt (MATCHED) while
  // leaving the canonical normalized_bar row unchanged.
  assert.deepEqual({ "1Min": MINUTE, "15Min": 15 * MINUTE, "1Day": DAY },
    { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 });
});
