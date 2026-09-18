import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import { planNextHistoricalRecoveryChunk, type HistoricalRecoveryRequest } from "./historical-recovery.ts";

const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES", dateRange: { startInclusive: "2026-09-02", endExclusive: "2026-09-05" },
  generatedAt: "2026-09-01T00:00:00.000Z", revision: "calendar-recovery-v1",
  sessions: ["2026-09-02", "2026-09-03"].map((marketDate) => ({ marketDate, sessionKind: "REGULAR" as const,
    opensAt: `${marketDate}T14:30:00.000Z`, closesAt: `${marketDate}T14:34:00.000Z`, isShortened: false,
    calendarRevision: "calendar-recovery-v1" })),
};

function request(overrides: Partial<HistoricalRecoveryRequest> = {}): HistoricalRecoveryRequest {
  return {
    recoveryId: "L1-003-nvda-001", providerRevision: "alpaca-bars-v2", universeRevision: "canary-v1",
    calendarRevision: "calendar-recovery-v1", instrument: { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw", sessionScope: "REGULAR", logicalDataVariant: "stock:iex:raw",
    mode: "CATCH_UP", recoveryRange: { startInclusive: "2026-09-02T14:30:00.000Z", endExclusive: "2026-09-03T14:34:00.000Z" },
    checkpointBefore: { coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw", symbol: "NVDA", interval: "1Min", sessionScope: "REGULAR",
      logicalDataVariant: "stock:iex:raw", state: "COMPLETE", completeThrough: "2026-09-02T14:30:00.000Z", missingRanges: [], version: 7 },
    maxBarsPerJob: 2, createdAt: "2026-09-16T00:00:00.000Z", ...overrides,
  };
}

test("plans only the next deterministic, session-bounded historical chunk", () => {
  const first = planNextHistoricalRecoveryChunk(request(), calendar)!;
  assert.deepEqual(first.requestedRange, { startInclusive: "2026-09-02T14:30:00.000Z", endExclusive: "2026-09-02T14:32:00.000Z" });
  assert.equal(first.dueReason, "HISTORICAL_RECOVERY");
  assert.equal(first.checkpointExpectations[0]?.expectedVersion, 7);
  assert.deepEqual(first.historicalRecovery, { recoveryId: "L1-003-nvda-001", providerRevision: "alpaca-bars-v2",
    recoveryStartInclusive: "2026-09-02T14:30:00.000Z", recoveryEndExclusive: "2026-09-03T14:34:00.000Z",
    checkpointBefore: "2026-09-02T14:30:00.000Z" });

  const next = planNextHistoricalRecoveryChunk(request({ checkpointBefore: {
    ...request().checkpointBefore, completeThrough: "2026-09-02T14:32:00.000Z", version: 8,
  } }), calendar)!;
  assert.deepEqual(next.requestedRange, { startInclusive: "2026-09-02T14:32:00.000Z", endExclusive: "2026-09-02T14:34:00.000Z" });
  assert.equal(next.checkpointExpectations[0]?.expectedVersion, 8);
});

test("moves across an overnight close only after the persisted checkpoint reaches the next session", () => {
  const job = planNextHistoricalRecoveryChunk(request({ checkpointBefore: {
    ...request().checkpointBefore, completeThrough: "2026-09-02T14:34:00.000Z", version: 9,
  } }), calendar)!;
  assert.deepEqual(job.requestedRange, { startInclusive: "2026-09-03T14:30:00.000Z", endExclusive: "2026-09-03T14:32:00.000Z" });
});

test("never makes one provider request span an absent calendar interval", () => {
  const job = planNextHistoricalRecoveryChunk(request({ maxBarsPerJob: 100 }), calendar)!;
  assert.deepEqual(job.requestedRange, {
    startInclusive: "2026-09-02T14:30:00.000Z",
    endExclusive: "2026-09-02T14:34:00.000Z",
  });
});

test("fails closed for a partial checkpoint, noncanonical bound, and identity mismatch", () => {
  assert.throws(() => planNextHistoricalRecoveryChunk(request({ checkpointBefore: {
    ...request().checkpointBefore, missingRanges: [{ startInclusive: "2026-09-02T14:30:00.000Z", endExclusive: "2026-09-02T14:31:00.000Z" }],
  } }), calendar), /unresolved missing ranges/);
  assert.throws(() => planNextHistoricalRecoveryChunk(request({ checkpointBefore: {
    ...request().checkpointBefore, state: "PARTIAL",
  } }), calendar), /COMPLETE checkpoint/);
  assert.throws(() => planNextHistoricalRecoveryChunk(request({ checkpointBefore: {
    ...request().checkpointBefore, logicalDataVariant: "stock:sip:raw",
  } }), calendar), /checkpoint identity/);
  assert.throws(() => planNextHistoricalRecoveryChunk(request({ recoveryRange: {
    startInclusive: "2026-09-02T14:30:00Z", endExclusive: "2026-09-03T14:34:00.000Z",
  } }), calendar), /canonical UTC/);
  assert.throws(() => planNextHistoricalRecoveryChunk(request({ coverageKey: "wrong" }), calendar), /coverage key/);
});

test("does not use normal retention and returns no job once the explicit range is complete", () => {
  assert.equal(planNextHistoricalRecoveryChunk(request({ checkpointBefore: {
    ...request().checkpointBefore, completeThrough: "2026-09-03T14:34:00.000Z", version: 12,
  } }), calendar), undefined);
});
