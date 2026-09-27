import assert from "node:assert/strict";
import test from "node:test";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { runHistoricalRecoveryChunk } from "./historical-recovery-runner.ts";
import type { HistoricalRecoveryRequest } from "./historical-recovery.ts";

const calendar = {
  market: "US_EQUITIES" as const, dateRange: { startInclusive: "2026-09-02", endExclusive: "2026-09-03" },
  generatedAt: "2026-09-01T00:00:00.000Z", revision: "calendar-recovery-v1",
  sessions: [{ marketDate: "2026-09-02", sessionKind: "REGULAR" as const,
    opensAt: "2026-09-02T14:30:00.000Z", closesAt: "2026-09-02T14:32:00.000Z",
    isShortened: false, calendarRevision: "calendar-recovery-v1" }],
};

function checkpoint(overrides: Partial<StoredCoverageCheckpoint> = {}): StoredCoverageCheckpoint {
  return { coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw", symbol: "NVDA", interval: "1Min",
    sessionScope: "REGULAR", logicalDataVariant: "stock:iex:raw", state: "COMPLETE",
    completeThrough: "2026-09-02T14:30:00.000Z", missingRanges: [], version: 7, ...overrides };
}

function request(overrides: Partial<HistoricalRecoveryRequest> = {}): HistoricalRecoveryRequest {
  return { recoveryId: "L1-003-nvda-001", providerRevision: "alpaca-bars-v2", universeRevision: "canary-v1",
    calendarRevision: "calendar-recovery-v1", instrument: { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw", sessionScope: "REGULAR", logicalDataVariant: "stock:iex:raw",
    mode: "CATCH_UP", recoveryRange: { startInclusive: "2026-09-02T14:30:00.000Z", endExclusive: "2026-09-02T14:32:00.000Z" },
    checkpointBefore: checkpoint(), maxBarsPerJob: 2, createdAt: "2026-09-16T00:00:00.000Z", ...overrides };
}

function options(current: StoredCoverageCheckpoint | undefined = checkpoint()) {
  const attempts: Array<Record<string, unknown>> = [];
  let proposed: StoredCoverageCheckpoint | undefined;
  let fetched = 0;
  return {
    state: { attempts, get proposed() { return proposed; }, get fetched() { return fetched; } },
    value: {
      credentials: { keyId: "key", secretKey: "secret" }, feed: "iex" as const, maxPages: 1, maxBars: 2,
      checkpoints: {
        get: async () => current,
        getMany: async () => current ? [current] : [], listDue: async () => [],
        recordAttempt: async (attempt: Record<string, unknown>) => { attempts.push(attempt); },
        summarizeStaleAttempts: async () => ({ count: 0 }), supersedeStaleAttempts: async () => 0,
        compareAndSet: async (_version: number | undefined, value: StoredCoverageCheckpoint) => {
          proposed = value; return { outcome: "UPDATED" as const, checkpoint: value };
        },
      },
      bars: { accept: async (_candidate: unknown, provenance: { idempotencyKey: string }) =>
        ({ outcome: "INSERTED" as const, acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true }) },
      now: () => new Date("2026-09-16T00:00:00.000Z"),
      fetchPage: async () => { fetched += 1; return { bars: [{ symbol: "NVDA", timestamp: "2026-09-02T14:30:00.000Z",
        open: 100, high: 101, low: 99, close: 100, volume: 10, provider: "alpaca" as const, dataVariant: "stock:iex:raw" },
      { symbol: "NVDA", timestamp: "2026-09-02T14:31:00.000Z", open: 100, high: 101, low: 99, close: 100,
        volume: 10, provider: "alpaca" as const, dataVariant: "stock:iex:raw" }] }; },
    },
  };
}

test("runs exactly the preflighted next historical chunk through the normal executor", async () => {
  const fixture = options();
  const result = await runHistoricalRecoveryChunk(request(), calendar, fixture.value as never);
  assert.equal(result.outcome, "SUCCEEDED");
  assert.equal(fixture.state.fetched, 1);
  assert.equal(fixture.state.proposed?.completeThrough, "2026-09-02T14:32:00.000Z");
});

test("rejects checkpoint drift before a provider request or checkpoint update", async () => {
  const fixture = options(checkpoint({ version: 8 }));
  await assert.rejects(runHistoricalRecoveryChunk(request(), calendar, fixture.value as never), /drifted since preflight/);
  assert.equal(fixture.state.fetched, 0);
  assert.equal(fixture.state.proposed, undefined);
});

test("rejects feed and bar-bound drift before execution", async () => {
  const fixture = options();
  await assert.rejects(runHistoricalRecoveryChunk(request(), calendar, { ...fixture.value, maxBars: 1 } as never), /maxBars/);
  await assert.rejects(runHistoricalRecoveryChunk(request(), calendar, { ...fixture.value, feed: "sip" } as never), /logical data variant/);
  assert.equal(fixture.state.fetched, 0);
});
