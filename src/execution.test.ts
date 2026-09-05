import assert from "node:assert/strict";
import test from "node:test";
import { executeAcquisitionJob } from "./execution.ts";
import type { AcquisitionJob } from "./schedule.ts";

const calendar = {
  market: "US_EQUITIES", dateRange: { startInclusive: "2026-08-28", endExclusive: "2026-08-29" },
  generatedAt: "2026-08-28T00:00:00Z", revision: "cal-1", sessions: [{
    marketDate: "2026-08-28", sessionKind: "REGULAR" as const,
    opensAt: "2026-08-28T14:30:00.000Z", closesAt: "2026-08-28T21:00:00.000Z",
    isShortened: false, calendarRevision: "cal-1",
  }],
};

const extendedCalendar = {
  ...calendar,
  revision: "cal-extended-1",
  sessions: [{
    marketDate: "2026-08-28", sessionKind: "PREMARKET" as const,
    opensAt: "2026-08-28T08:00:00.000Z", closesAt: "2026-08-28T13:30:00.000Z",
    isShortened: false, calendarRevision: "cal-extended-1",
  }, { ...calendar.sessions[0]!, calendarRevision: "cal-extended-1" }],
};

const job: AcquisitionJob = {
  jobId: "job-1", jobKind: "MARKET_BARS", createdAt: "2026-08-28T14:33:00Z",
  universeRevision: "u1", calendarRevision: "cal-1",
  instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
  interval: "1Min", requestedRange: { startInclusive: "2026-08-28T14:30:00.000Z", endExclusive: "2026-08-28T14:32:00.000Z" },
  sessionScope: "REGULAR", mode: "CATCH_UP", providerRoute: "alpaca_stock_bars",
  checkpointExpectations: [{ coverageKey: "SPY|1Min|REGULAR|stock:iex:raw" }],
  attempt: 0, dueReason: "NO_CHECKPOINT",
};

function source(timestamp: string) {
  return { symbol: "SPY", timestamp, open: 100, high: 101, low: 99, close: 100,
    volume: 10, provider: "alpaca" as const, dataVariant: "stock:iex:raw" };
}

class Checkpoints {
  attempts: Array<Record<string, unknown>> = [];
  proposed?: Record<string, unknown>;
  async recordAttempt(value: Record<string, unknown>) { this.attempts.push(value); }
  async get() { return undefined; }
  async compareAndSet(_version: number | undefined, proposed: Record<string, unknown>) {
    this.proposed = proposed;
    return { outcome: "UPDATED" as const, checkpoint: proposed };
  }
}

class ConflictingCheckpoints extends Checkpoints {
  override async compareAndSet(_version: number | undefined, proposed: Record<string, unknown>) {
    this.proposed = proposed;
    return { outcome: "VERSION_CONFLICT" as const, current: undefined };
  }
}

test("paginates, accepts bars, and advances only contiguous expected coverage", async () => {
  const checkpoints = new Checkpoints();
  let page = 0;
  const result = await executeAcquisitionJob(job, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (candidate, provenance) => ({
      identity: candidate.outcome === "NORMALIZED" ? candidate.bar.barStartUtc : undefined,
      outcome: candidate.outcome === "NORMALIZED" ? "INSERTED" as const : "REJECTED" as const,
      acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true,
    }) },
    feed: "iex", maxPages: 10, maxBars: 100, now: () => new Date("2026-08-28T14:33:00Z"),
    fetchPage: async () => ++page === 1
      ? { bars: [source("2026-08-28T14:30:00Z")], nextPageToken: "next" }
      : { bars: [source("2026-08-28T14:31:00Z")] },
  });
  assert.equal(result.outcome, "SUCCEEDED");
  assert.equal(result.pages, 2);
  assert.equal(checkpoints.proposed?.completeThrough, "2026-08-28T14:32:00.000Z");
  assert.equal(checkpoints.attempts.at(-1)?.outcome, "SUCCEEDED");
});

test("computes expected coverage only from the requested session scope", async () => {
  const checkpoints = new Checkpoints();
  const premarketJob: AcquisitionJob = {
    ...job,
    jobId: "job-premarket",
    calendarRevision: "cal-extended-1",
    createdAt: "2026-08-28T08:03:00Z",
    requestedRange: { startInclusive: "2026-08-28T08:00:00.000Z", endExclusive: "2026-08-28T08:02:00.000Z" },
    sessionScope: "PREMARKET",
    checkpointExpectations: [{ coverageKey: "SPY|1Min|PREMARKET|stock:iex:raw" }],
  };
  const result = await executeAcquisitionJob(premarketJob, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar: extendedCalendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (candidate, provenance) => ({
      identity: candidate.outcome === "NORMALIZED" ? candidate.bar.barStartUtc : undefined,
      outcome: candidate.outcome === "NORMALIZED" ? "INSERTED" as const : "REJECTED" as const,
      acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true,
    }) },
    feed: "iex", maxPages: 10, maxBars: 100, now: () => new Date("2026-08-28T08:03:00Z"),
    fetchPage: async () => ({ bars: [source("2026-08-28T08:00:00Z"), source("2026-08-28T08:01:00Z")] }),
  });

  assert.equal(result.outcome, "SUCCEEDED");
  assert.equal(result.missing, 0);
  assert.equal(checkpoints.proposed?.completeThrough, "2026-08-28T08:02:00.000Z");
  assert.equal(checkpoints.proposed?.sessionScope, "PREMARKET");
});

test("records a missing expected bar and does not advance across it", async () => {
  const checkpoints = new Checkpoints();
  const result = await executeAcquisitionJob(job, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (_candidate, provenance) => ({ outcome: "INSERTED", acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true }) },
    feed: "iex", maxPages: 10, maxBars: 100, now: () => new Date("2026-08-28T14:33:00Z"),
    fetchPage: async () => ({ bars: [source("2026-08-28T14:31:00Z")] }),
  });
  assert.equal(result.outcome, "PARTIAL");
  assert.equal(result.missing, 1);
  assert.equal(checkpoints.proposed?.completeThrough, undefined);
  assert.deepEqual(checkpoints.proposed?.missingRanges, [{
    startInclusive: "2026-08-28T14:30:00.000Z", endExclusive: "2026-08-28T14:31:00.000Z",
  }]);
});

test("fails safely when a provider repeats its pagination token", async () => {
  const checkpoints = new Checkpoints();
  await assert.rejects(executeAcquisitionJob(job, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (_candidate, provenance) => ({ outcome: "INSERTED", acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true }) },
    feed: "iex", maxPages: 10, maxBars: 100, now: () => new Date("2026-08-28T14:33:00Z"),
    fetchPage: async () => ({ bars: [], nextPageToken: "same" }),
  }), /repeated/);
  assert.equal(checkpoints.attempts.at(-1)?.outcome, "FAILED");
});

test("fails before fetching beyond the configured page limit without advancing coverage", async () => {
  const checkpoints = new Checkpoints();
  let calls = 0;
  await assert.rejects(executeAcquisitionJob(job, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (_candidate, provenance) => ({ outcome: "INSERTED", acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true }) },
    feed: "iex", maxPages: 1, maxBars: 100, now: () => new Date("2026-08-28T14:33:00Z"),
    fetchPage: async () => { calls += 1; return { bars: [], nextPageToken: "next" }; },
  }), /page limit exceeded: 1/);
  assert.equal(calls, 1);
  assert.equal(checkpoints.proposed, undefined);
  assert.equal(checkpoints.attempts.at(-1)?.outcome, "FAILED");
});

test("fails a page atomically when it would exceed the total bar limit", async () => {
  const checkpoints = new Checkpoints();
  let accepted = 0;
  await assert.rejects(executeAcquisitionJob(job, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (_candidate, provenance) => { accepted += 1; return { outcome: "INSERTED", acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true }; } },
    feed: "iex", maxPages: 10, maxBars: 1, now: () => new Date("2026-08-28T14:33:00Z"),
    fetchPage: async () => ({ bars: [source("2026-08-28T14:30:00Z"), source("2026-08-28T14:31:00Z")] }),
  }), /bar limit exceeded: 1/);
  assert.equal(accepted, 0);
  assert.equal(checkpoints.proposed, undefined);
  assert.equal(checkpoints.attempts.at(-1)?.outcome, "FAILED");
});

test("records exhausted provider retries as failed without advancing coverage", async () => {
  const checkpoints = new Checkpoints();
  await assert.rejects(executeAcquisitionJob(job, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (_candidate, provenance) => ({ outcome: "INSERTED", acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true }) },
    feed: "iex", maxPages: 10, maxBars: 100, now: () => new Date("2026-08-28T14:33:00Z"),
    fetchPage: async () => { throw new Error("alpaca stock bars failed: 503 after 3 attempts"); },
  }), /503 after 3 attempts/);
  assert.equal(checkpoints.proposed, undefined);
  assert.equal(checkpoints.attempts.at(-1)?.outcome, "FAILED");
});

test("defers a checkpoint CAS conflict to the next cron by recording failure", async () => {
  const checkpoints = new ConflictingCheckpoints();
  await assert.rejects(executeAcquisitionJob(job, {
    credentials: { keyId: "key", secretKey: "secret" }, calendar,
    checkpoints: checkpoints as never,
    bars: { accept: async (candidate, provenance) => ({
      identity: candidate.outcome === "NORMALIZED" ? candidate.bar.barStartUtc : undefined,
      outcome: "INSERTED", acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true,
    }) },
    feed: "iex", maxPages: 10, maxBars: 100, now: () => new Date("2026-08-28T14:33:00Z"),
    fetchPage: async () => ({ bars: [source("2026-08-28T14:30:00Z"), source("2026-08-28T14:31:00Z")] }),
  }), /compare-and-set conflict/);
  assert.equal(checkpoints.attempts.at(-1)?.outcome, "FAILED");
  assert.match(String((checkpoints.attempts.at(-1)?.diagnostic as Record<string, unknown>)?.message), /compare-and-set conflict/);
});
