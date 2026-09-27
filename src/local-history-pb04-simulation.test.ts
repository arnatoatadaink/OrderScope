import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { validateRegularSession } from "./local-history-collector.ts";
import type { LocalHistoryEvidenceSession } from "./local-history-evidence.ts";
import { simulateLocalPb04Session } from "./local-history-pb04-simulation.ts";

function stableHash(session: Omit<LocalHistoryEvidenceSession, "contentSha256"> & { contentSha256?: string }): string {
  return createHash("sha256").update(JSON.stringify({
    coverageKey: session.coverageKey,
    providerRevision: session.providerRevision,
    feed: session.feed,
    adjustment: session.adjustment,
    plan: session.plan,
    validation: session.validation,
    pages: session.pages,
    bars: session.bars,
  }), "utf8").digest("hex");
}

function denseSession(): LocalHistoryEvidenceSession {
  const plan = {
    marketDate: "2026-09-09",
    startInclusive: "2026-09-09T13:30:00.000Z",
    endExclusive: "2026-09-09T20:00:00.000Z",
    expectedBars: 390,
  };
  const bars = Array.from({ length: 390 }, (_, index) => ({
    symbol: "NVDA",
    timestamp: new Date(Date.parse(plan.startInclusive) + index * 60_000).toISOString(),
    open: 1, high: 1, low: 1, close: 1, volume: 1,
    provider: "alpaca" as const,
    dataVariant: "stock:iex:raw",
  }));
  const session: LocalHistoryEvidenceSession = {
    schemaVersion: "l1-003-local-history-session-v3",
    contentSha256: "",
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    providerRevision: "alpaca-stock-bars-v1",
    feed: "iex",
    adjustment: "raw",
    plan,
    validation: validateRegularSession(plan, bars),
    pages: 1,
    bars,
  };
  session.contentSha256 = stableHash(session);
  return session;
}

function checkpoint() {
  return {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    symbol: "NVDA",
    interval: "1Min" as const,
    sessionScope: "REGULAR" as const,
    logicalDataVariant: "stock:iex:raw",
    state: "COMPLETE" as const,
    completeThrough: "2026-09-08T20:00:00.000Z",
    missingRanges: [],
    version: 18,
    universeRevision: "stock-monitoring-canary-v0.1",
  };
}

test("simulates the Sep9 local evidence through the real executor contract", async () => {
  const result = await simulateLocalPb04Session({
    session: denseSession(),
    coverageAbsences: [],
    checkpointBefore: checkpoint(),
    calendarRevision: "local-evidence:2026-09-09",
    createdAt: "2026-09-23T11:00:00.000Z",
  });
  assert.equal(result.remoteMutation, false);
  assert.equal(result.chunks.length, 4);
  assert.deepEqual(result.chunks.map((chunk) => chunk.summary.inserted), [100, 100, 100, 90]);
  assert.deepEqual(result.chunks.map((chunk) => chunk.summary.missing), [0, 0, 0, 0]);
  assert.equal(result.finalCheckpoint.completeThrough, "2026-09-09T20:00:00.000Z");
  assert.equal(result.finalCheckpoint.version, 22);
  assert.equal(result.finalCheckpoint.state, "COMPLETE");
});


test("simulates the Sep11 sparse evidence with one acknowledged absence", async () => {
  const session = denseSession();
  session.plan = {
    marketDate: "2026-09-11",
    startInclusive: "2026-09-11T13:30:00.000Z",
    endExclusive: "2026-09-11T20:00:00.000Z",
    expectedBars: 390,
  };
  const missing = "2026-09-11T16:57:00.000Z";
  session.bars = Array.from({ length: 390 }, (_, index) => ({
    symbol: "NVDA",
    timestamp: new Date(Date.parse(session.plan.startInclusive) + index * 60_000).toISOString(),
    open: 1, high: 1, low: 1, close: 1, volume: 1,
    provider: "alpaca" as const,
    dataVariant: "stock:iex:raw",
  })).filter((bar) => bar.timestamp !== missing);
  session.validation = validateRegularSession(session.plan, session.bars);
  session.reproducible = true;
  session.contentSha256 = stableHash(session);

  const result = await simulateLocalPb04Session({
    session,
    coverageAbsences: [{
      symbol: "NVDA",
      identityStart: missing,
      reason: "REPRODUCIBLE_PROVIDER_ABSENCE",
      evidenceHash: session.contentSha256,
    }],
    checkpointBefore: {
      ...checkpoint(),
      completeThrough: "2026-09-10T20:00:00.000Z",
      version: 26,
    },
    calendarRevision: "local-evidence:2026-09-11",
    createdAt: "2026-09-24T02:00:00.000Z",
  });

  assert.equal(result.remoteMutation, false);
  assert.deepEqual(result.chunks.map((chunk) => chunk.summary.inserted), [100, 100, 99, 90]);
  assert.deepEqual(result.chunks.map((chunk) => chunk.summary.acknowledgedAbsent ?? 0), [0, 0, 1, 0]);
  assert.deepEqual(result.chunks.map((chunk) => chunk.summary.missing), [0, 0, 0, 0]);
  assert.equal(result.finalCheckpoint.completeThrough, "2026-09-11T20:00:00.000Z");
  assert.equal(result.finalCheckpoint.version, 30);
  assert.equal(result.finalCheckpoint.state, "COMPLETE");
});
