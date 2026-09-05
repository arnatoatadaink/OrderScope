import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import { coverageKeyFor, SchedulePolicy, type SchedulePolicyConfig } from "./schedule.ts";
import type { UniverseInstrument, UniverseSnapshot } from "./universe.ts";

const config: SchedulePolicyConfig = {
  retentionFloor: "2026-11-27T14:30:00.000Z",
  overlapMs: { "1Min": 60_000, "15Min": 15 * 60_000, "1Day": 24 * 60 * 60_000 },
  finalizationLagMs: { "1Min": 30_000, "15Min": 60_000, "1Day": 5 * 60_000 },
  maxBarsPerJob: 10_000,
  logicalDataVariant: (instrument) => instrument.providerRoute === "alpaca_crypto_bars" ? "crypto-us" : "raw-iex",
};

function universe(instruments: readonly UniverseInstrument[]): UniverseSnapshot {
  return { revision: "universe-test-v1", generatedAt: "2026-11-27T00:00:00.000Z", instruments };
}

function calendar(close = "2026-11-27T18:00:00.000Z"): MarketCalendarSnapshot {
  return {
    market: "US_EQUITIES",
    dateRange: { startInclusive: "2026-11-27", endExclusive: "2026-11-28" },
    generatedAt: "2026-11-27T00:00:00.000Z",
    revision: "calendar-test-v1",
    sessions: [{
      marketDate: "2026-11-27",
      sessionKind: "REGULAR",
      opensAt: "2026-11-27T14:30:00.000Z",
      closesAt: close,
      isShortened: close.endsWith("18:00:00.000Z"),
      calendarRevision: "calendar-test-v1",
    }],
  };
}

function extendedCalendar(): MarketCalendarSnapshot {
  const regular = calendar("2026-11-27T21:00:00.000Z");
  return {
    ...regular,
    revision: "calendar-extended-v1",
    sessions: [{
      marketDate: "2026-11-27", sessionKind: "PREMARKET",
      opensAt: "2026-11-27T09:00:00.000Z", closesAt: "2026-11-27T14:30:00.000Z",
      isShortened: false, calendarRevision: "calendar-extended-v1",
    }, { ...regular.sessions[0]!, calendarRevision: "calendar-extended-v1" }],
  };
}

function twoDayCalendar(): MarketCalendarSnapshot {
  const first = calendar("2026-11-27T21:00:00.000Z").sessions[0]!;
  return {
    market: "US_EQUITIES",
    dateRange: { startInclusive: "2026-11-27", endExclusive: "2026-11-29" },
    generatedAt: "2026-11-28T00:00:00.000Z",
    revision: "calendar-two-day-v1",
    sessions: [
      { ...first, calendarRevision: "calendar-two-day-v1" },
      {
        marketDate: "2026-11-28", sessionKind: "REGULAR",
        opensAt: "2026-11-28T14:30:00.000Z", closesAt: "2026-11-28T21:00:00.000Z",
        isShortened: false, calendarRevision: "calendar-two-day-v1",
      },
    ],
  };
}

test("plans deterministic 1m and 15m jobs on session-aligned boundaries", () => {
  const instruments: UniverseInstrument[] = [
    { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    { symbol: "XLC", cadence: "15Min", providerRoute: "alpaca_stock_bars" },
  ];
  const policy = new SchedulePolicy(config);
  const now = new Date("2026-11-27T16:07:45.000Z");
  const first = policy.plan(universe(instruments), calendar(), [], now);
  const second = policy.plan(universe(instruments), calendar(), [], now);

  assert.deepEqual(first, second);
  assert.equal(first.find((job) => job.interval === "1Min")?.requestedRange.endExclusive, "2026-11-27T16:07:00.000Z");
  assert.equal(first.find((job) => job.interval === "15Min")?.requestedRange.endExclusive, "2026-11-27T16:00:00.000Z");
  assert.ok(first.every((job) => job.universeRevision === "universe-test-v1"));
});

test("plans Premarket coverage as a distinct checkpoint scope when explicitly requested", () => {
  const spy: UniverseInstrument = { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" };
  const premarket = new SchedulePolicy({
    ...config,
    retentionFloor: "2026-11-27T09:00:00.000Z",
    sessionScopeFor: () => "PREMARKET",
  }).plan(universe([spy]), extendedCalendar(), [], new Date("2026-11-27T12:07:45Z"));

  assert.equal(premarket.length, 1);
  assert.equal(premarket[0]?.sessionScope, "PREMARKET");
  assert.equal(premarket[0]?.requestedRange.endExclusive, "2026-11-27T12:07:00.000Z");
  assert.equal(premarket[0]?.checkpointExpectations[0]?.coverageKey, "SPY|1Min|PREMARKET|raw-iex");
});

test("does not invent Premarket coverage without an authoritative Premarket session", () => {
  const spy: UniverseInstrument = { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" };
  const policy = new SchedulePolicy({
    ...config,
    retentionFloor: "2026-11-27T09:00:00.000Z",
    sessionScopeFor: () => "PREMARKET",
  });

  assert.deepEqual(policy.plan(universe([spy]), calendar(), [], new Date("2026-11-27T12:07:45Z")), []);
});

test("does not treat a daily equity bar as a Premarket bar", () => {
  const ewj: UniverseInstrument = { symbol: "EWJ", cadence: "1Day", providerRoute: "alpaca_stock_bars" };
  const jobs = new SchedulePolicy({
    ...config,
    retentionFloor: "2026-11-26T09:00:00.000Z",
    sessionScopeFor: () => "PREMARKET",
  }).plan(universe([ewj]), extendedCalendar(), [], new Date("2026-11-27T22:00:00Z"));

  assert.deepEqual(jobs, []);
});

test("does not plan equity intraday work while the authoritative calendar is closed", () => {
  const instruments: UniverseInstrument[] = [
    { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    { symbol: "XLC", cadence: "15Min", providerRoute: "alpaca_stock_bars" },
  ];
  const closed = { ...calendar(), sessions: [] };
  assert.deepEqual(new SchedulePolicy(config).plan(universe(instruments), closed, [], new Date("2026-11-27T16:00:00Z")), []);
});

test("keeps crypto on its separate continuous route when equities are closed", () => {
  const btc: UniverseInstrument = { symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" };
  const closed = { ...calendar(), sessions: [] };
  const jobs = new SchedulePolicy(config).plan(universe([btc]), closed, [], new Date("2026-11-28T16:07:45Z"));

  assert.equal(jobs.length, 1);
  assert.equal(jobs[0]?.sessionScope, "ALL_TRADING");
  assert.equal(jobs[0]?.requestedRange.endExclusive, "2026-11-28T16:07:00.000Z");
});

test("caps an initial equity backfill at one authoritative session close", () => {
  const spy: UniverseInstrument = { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" };
  const policy = new SchedulePolicy({
    ...config,
    retentionFloor: "2026-11-27T19:30:00.000Z",
    maxBarsPerJob: 100,
  });
  const job = policy.plan(universe([spy]), twoDayCalendar(), [], new Date("2026-11-28T16:07:45Z"))[0]!;

  assert.equal(job.dueReason, "NO_CHECKPOINT");
  assert.deepEqual(job.requestedRange, {
    startInclusive: "2026-11-27T19:30:00.000Z",
    endExclusive: "2026-11-27T21:00:00.000Z",
  });
});

test("advances from a prior equity close to the next authoritative session open", () => {
  const spy: UniverseInstrument = { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" };
  const coverageKey = coverageKeyFor(spy, "REGULAR", "raw-iex");
  const policy = new SchedulePolicy({
    ...config,
    retentionFloor: "2026-11-27T19:30:00.000Z",
    maxBarsPerJob: 100,
  });
  const job = policy.plan(universe([spy]), twoDayCalendar(), [{
    coverageKey,
    completeThrough: "2026-11-27T21:00:00.000Z",
    missingRanges: [],
    version: 1,
  }], new Date("2026-11-28T16:07:45Z"))[0]!;

  assert.equal(job.dueReason, "FORWARD_COVERAGE");
  assert.deepEqual(job.requestedRange, {
    startInclusive: "2026-11-28T14:30:00.000Z",
    endExclusive: "2026-11-28T16:07:00.000Z",
  });
});

test("bounds an initial crypto backfill and deterministically continues from its checkpoint", () => {
  const btc: UniverseInstrument = { symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" };
  const bounded = { ...config, maxBarsPerJob: 100 };
  const policy = new SchedulePolicy(bounded);
  const first = policy.plan(universe([btc]), { ...calendar(), sessions: [] }, [], new Date("2026-11-28T16:07:45Z"))[0]!;
  assert.equal(first.requestedRange.startInclusive, config.retentionFloor);
  assert.equal(first.requestedRange.endExclusive, "2026-11-27T16:10:00.000Z");

  const second = policy.plan(universe([btc]), { ...calendar(), sessions: [] }, [{
    coverageKey: first.checkpointExpectations[0]!.coverageKey,
    completeThrough: first.requestedRange.endExclusive,
    missingRanges: [],
    version: 0,
  }], new Date("2026-11-28T16:07:45Z"))[0]!;
  assert.equal(second.requestedRange.startInclusive, "2026-11-27T16:09:00.000Z");
  assert.equal(second.requestedRange.endExclusive, "2026-11-27T17:49:00.000Z");
});

test("plans daily work only after the actual shortened-session close and finalization lag", () => {
  const daily: UniverseInstrument = { symbol: "EWJ", cadence: "1Day", providerRoute: "alpaca_stock_bars" };
  const policy = new SchedulePolicy(config);

  assert.equal(policy.plan(universe([daily]), calendar(), [], new Date("2026-11-27T18:04:59Z")).length, 0);
  assert.equal(policy.plan(universe([daily]), calendar(), [], new Date("2026-11-27T18:05:00Z")).length, 1);
});

test("caps shortened-session intraday coverage at the actual close after finalization", () => {
  const spy: UniverseInstrument = { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" };
  const policy = new SchedulePolicy(config);

  assert.equal(
    policy.plan(universe([spy]), calendar(), [], new Date("2026-11-27T18:00:29Z")).length,
    0,
  );
  const finalized = policy.plan(universe([spy]), calendar(), [], new Date("2026-11-27T18:00:30Z"));
  assert.equal(finalized[0]?.requestedRange.endExclusive, "2026-11-27T18:00:00.000Z");

  const coverageKey = coverageKeyFor(spy, "REGULAR", "raw-iex");
  assert.deepEqual(policy.plan(universe([spy]), calendar(), [{
    coverageKey,
    completeThrough: "2026-11-27T18:00:00.000Z",
    missingRanges: [],
    version: 0,
  }], new Date("2026-11-27T18:15:00Z")), []);
});

test("prioritizes missing coverage and overlaps without crossing retention", () => {
  const spy: UniverseInstrument = { symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" };
  const coverageKey = coverageKeyFor(spy, "REGULAR", "raw-iex");
  const jobs = new SchedulePolicy(config).plan(universe([spy]), calendar(), [{
    coverageKey,
    completeThrough: "2026-11-27T16:00:00.000Z",
    missingRanges: [{ startInclusive: "2026-11-27T14:30:00.000Z", endExclusive: "2026-11-27T14:32:00.000Z" }],
    version: 4,
  }], new Date("2026-11-27T16:07:45Z"));

  assert.equal(jobs[0]?.dueReason, "MISSING_RANGE");
  assert.equal(jobs[0]?.requestedRange.startInclusive, config.retentionFloor);
  assert.equal(jobs[0]?.requestedRange.endExclusive, "2026-11-27T14:32:00.000Z");
  assert.equal(jobs[0]?.checkpointExpectations[0]?.expectedVersion, 4);
});

test("ignores retention-expired gaps and resumes bounded forward coverage", () => {
  const btc: UniverseInstrument = { symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" };
  const coverageKey = coverageKeyFor(btc, "ALL_TRADING", "crypto-us");
  const jobs = new SchedulePolicy({ ...config, maxBarsPerJob: 100 }).plan(
    universe([btc]),
    { ...calendar(), sessions: [] },
    [{
      coverageKey,
      completeThrough: "2026-11-27T12:00:00.000Z",
      missingRanges: [{
        startInclusive: "2026-11-27T12:30:00.000Z",
        endExclusive: config.retentionFloor,
      }],
      version: 7,
    }],
    new Date("2026-11-27T18:00:45.000Z"),
  );

  assert.equal(jobs.length, 1);
  assert.equal(jobs[0]?.dueReason, "FORWARD_COVERAGE");
  assert.equal(jobs[0]?.mode, "INCREMENTAL");
  assert.equal(jobs[0]?.requestedRange.startInclusive, config.retentionFloor);
  assert.equal(jobs[0]?.requestedRange.endExclusive, "2026-11-27T16:10:00.000Z");
  assert.equal(jobs[0]?.checkpointExpectations[0]?.expectedVersion, 7);
});
