import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { validateRegularSession } from "./local-history-collector.ts";
import type { LocalHistoryEvidenceSession } from "./local-history-evidence.ts";
import { buildLocalPb04DryRunPacket } from "./local-history-pb04.ts";

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

function session(marketDate = "2026-09-09"): LocalHistoryEvidenceSession {
  const plan = {
    marketDate,
    startInclusive: "2026-09-09T13:30:00.000Z",
    endExclusive: "2026-09-09T20:00:00.000Z",
    expectedBars: 390,
  };
  const bars = Array.from({ length: 390 }, (_, index) => {
    const timestamp = new Date(Date.parse(plan.startInclusive) + index * 60_000).toISOString();
    return {
      symbol: "NVDA",
      timestamp,
      open: 1, high: 1, low: 1, close: 1, volume: 1,
      provider: "alpaca" as const,
      dataVariant: "stock:iex:raw",
    };
  });
  const base: LocalHistoryEvidenceSession = {
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
  base.contentSha256 = stableHash(base);
  return base;
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

test("freezes Sep9 into four deterministic PB-04 chunks without remote mutation", () => {
  const packet = buildLocalPb04DryRunPacket({
    session: session(),
    coverageAbsences: [],
    checkpointBefore: checkpoint(),
    calendarRevision: "local-evidence:2026-09-09",
    createdAt: "2026-09-23T11:00:00.000Z",
  });
  assert.equal(packet.remoteMutation, false);
  assert.equal(packet.chunks.length, 4);
  assert.deepEqual(packet.chunks.map((chunk) => chunk.expectedGridBars), [100, 100, 100, 90]);
  assert.deepEqual(packet.chunks.map((chunk) => chunk.localProviderBars), [100, 100, 100, 90]);
  assert.equal(packet.chunks[0]?.checkpointBefore.version, 18);
  assert.equal(packet.chunks[3]?.checkpointAfter.version, 22);
  assert.equal(packet.chunks[3]?.checkpointAfter.completeThrough, "2026-09-09T20:00:00.000Z");
});

test("attributes a reproducible absence only to its owning chunk", () => {
  const s = session();
  const packet = buildLocalPb04DryRunPacket({
    session: s,
    coverageAbsences: [{
      symbol: "NVDA",
      identityStart: "2026-09-09T16:57:00.000Z",
      reason: "REPRODUCIBLE_PROVIDER_ABSENCE",
      evidenceHash: s.contentSha256,
    }],
    checkpointBefore: checkpoint(),
    calendarRevision: "local-evidence:2026-09-09",
    createdAt: "2026-09-23T11:00:00.000Z",
  });
  assert.deepEqual(packet.chunks.map((chunk) => chunk.acknowledgedAbsent), [0, 0, 1, 0]);
  assert.deepEqual(packet.chunks.map((chunk) => chunk.localProviderBars), [100, 100, 99, 90]);
});
