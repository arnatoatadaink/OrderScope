import assert from "node:assert/strict";
import test from "node:test";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import {
  createHistoricalRecoveryHttpInvoker,
  freezeHistoricalRecoveryCampaign,
  runHistoricalRecoveryCampaign,
  type HistoricalRecoveryCampaignPorts,
  type HistoricalRecoveryChunkResponse,
} from "./historical-recovery-campaign.ts";
import type { HistoricalRecoveryRequest } from "./historical-recovery.ts";

const revision = "calendar-campaign-v1";
const session = { marketDate: "2026-09-04", sessionKind: "REGULAR" as const,
  opensAt: "2026-09-04T13:30:00.000Z", closesAt: "2026-09-04T20:00:00.000Z",
  isShortened: false, calendarRevision: revision };
const calendar = { market: "US_EQUITIES" as const,
  dateRange: { startInclusive: "2026-09-03", endExclusive: "2026-09-05" },
  generatedAt: "2026-09-18T00:00:00.000Z", revision, sessions: [session] };

function checkpoint(completeThrough = "2026-09-03T20:00:00.000Z", version = 10): StoredCoverageCheckpoint {
  return { coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw", symbol: "NVDA", interval: "1Min",
    sessionScope: "REGULAR", logicalDataVariant: "stock:iex:raw", state: "COMPLETE",
    completeThrough, missingRanges: [], version, universeRevision: "stock-monitoring-canary-v0.1" };
}

function request(): HistoricalRecoveryRequest {
  return { recoveryId: "L1-003-NVDA-PB03", providerRevision: "alpaca-stock-bars-v1",
    universeRevision: "stock-monitoring-canary-v0.1", calendarRevision: revision,
    instrument: { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw", sessionScope: "REGULAR",
    logicalDataVariant: "stock:iex:raw", mode: "CATCH_UP",
    recoveryRange: { startInclusive: "2026-09-03T20:00:00.000Z", endExclusive: session.closesAt },
    checkpointBefore: checkpoint(), maxBarsPerJob: 100, createdAt: "2026-09-18T00:00:00.000Z" };
}

function harness(start = checkpoint(), mutate?: (response: HistoricalRecoveryChunkResponse, ordinal: number) => void) {
  const campaign = freezeHistoricalRecoveryCampaign("PB03-SEP04", request(), calendar, session);
  let current = start;
  const invoked: string[] = [];
  const records: unknown[] = [];
  const ports: HistoricalRecoveryCampaignPorts = {
    readCheckpoint: async () => current,
    invokeNextChunk: async (input) => {
      const chunk = campaign.chunks.find((candidate) => candidate.jobId === input.jobId)!;
      invoked.push(input.jobId);
      current = checkpoint(chunk.checkpointAfter.completeThrough, chunk.checkpointAfter.version);
      const response: HistoricalRecoveryChunkResponse = {
        accepted: true, recoveryId: campaign.request.recoveryId, expectedJobId: chunk.jobId,
        checkpointBefore: chunk.checkpointBefore, requestedRange: chunk.requestedRange,
        expectedBarCount: chunk.expectedBarCount,
        result: { outcome: "SUCCEEDED", summary: { jobId: chunk.jobId, outcome: "SUCCEEDED", pages: 1,
          inserted: chunk.expectedBarCount, matched: 0, conflicts: 0, rejected: 0, missing: 0 } },
        checkpointAfter: { completeThrough: chunk.checkpointAfter.completeThrough, state: "COMPLETE",
          missingRanges: [], version: chunk.checkpointAfter.version },
        budget: { externalSubrequests: 1, d1Queries: 15 }, stoppedAfterOneChunk: true,
      };
      mutate?.(response, chunk.ordinal);
      return response;
    },
    inspectChunk: async (jobId, range) => ({ jobId, successfulAttempts: 1,
      receiptCount: (Date.parse(range.endExclusive) - Date.parse(range.startInclusive)) / 60_000,
      canonicalBarCount: (Date.parse(range.endExclusive) - Date.parse(range.startInclusive)) / 60_000,
      conflicts: 0, rejected: 0, missing: 0 }),
    persistEvidence: async (record) => { records.push(record); },
  };
  return { campaign, ports, invoked, records, get current() { return current; } };
}

test("freezes one session as deterministic 100/100/100/90 chunks", () => {
  const campaign = freezeHistoricalRecoveryCampaign("PB03-SEP04", request(), calendar, session);
  assert.deepEqual(campaign.chunks.map((chunk) => chunk.expectedBarCount), [100, 100, 100, 90]);
  assert.deepEqual(campaign.chunks.map((chunk) => chunk.checkpointBefore.version), [10, 11, 12, 13]);
  assert.equal(new Set(campaign.chunks.map((chunk) => chunk.jobId)).size, 4);
  assert.equal(campaign.chunks.at(-1)?.requestedRange.endExclusive, session.closesAt);
});

test("runs four independent chunks with checkpoint reread and allow-listed records", async () => {
  const fixture = harness();
  const result = await runHistoricalRecoveryCampaign(fixture.campaign, fixture.ports);
  assert.equal(result.outcome, "COMPLETED");
  assert.equal(result.resumedAtOrdinal, 1);
  assert.equal(fixture.invoked.length, 4);
  assert.equal(fixture.records.length, 4);
  assert.deepEqual(fixture.current, checkpoint(session.closesAt, 14));
  assert.deepEqual(Object.keys(fixture.records[0] as object).sort(), ["budget", "calendarRevision", "campaignId",
    "checkpointAfter", "checkpointBefore", "expectedBarCount", "jobId", "ordinal", "persisted", "recoveryId",
    "requestedRange", "result", "session"].sort());
});

test("stops immediately on response mismatch without invoking a later chunk", async () => {
  const fixture = harness(checkpoint(), (response, ordinal) => {
    if (ordinal === 2) response.result.summary.missing = 1;
  });
  await assert.rejects(runHistoricalRecoveryCampaign(fixture.campaign, fixture.ports), /chunk 2 response evidence mismatch/);
  assert.equal(fixture.invoked.length, 2);
  assert.equal(fixture.records.length, 1);
});

test("resumes from the last accepted frozen checkpoint", async () => {
  const frozen = freezeHistoricalRecoveryCampaign("PB03-SEP04", request(), calendar, session);
  const fixture = harness(checkpoint(frozen.chunks[1]!.checkpointAfter.completeThrough, 12));
  const result = await runHistoricalRecoveryCampaign(fixture.campaign, fixture.ports);
  assert.equal(result.resumedAtOrdinal, 3);
  assert.equal(fixture.invoked.length, 2);
  assert.equal(fixture.records.length, 2);
});

test("closes completed replay and rejects non-boundary or cross-session plans", async () => {
  const complete = harness(checkpoint(session.closesAt, 14));
  const result = await runHistoricalRecoveryCampaign(complete.campaign, complete.ports);
  assert.equal(result.resumedAtOrdinal, 5);
  assert.equal(complete.invoked.length, 0);

  const drifted = harness(checkpoint("2026-09-04T16:00:00.000Z", 12));
  await assert.rejects(runHistoricalRecoveryCampaign(drifted.campaign, drifted.ports), /not a resumable frozen boundary/);

  const twoSessions = { ...calendar, sessions: [session, { ...session, marketDate: "2026-09-08",
    opensAt: "2026-09-08T13:30:00.000Z", closesAt: "2026-09-08T20:00:00.000Z" }] };
  const frozen = freezeHistoricalRecoveryCampaign("PB03-SEP04", request(), twoSessions, session);
  assert.equal(frozen.chunks.at(-1)?.requestedRange.endExclusive, session.closesAt);
});

test("enforces campaign shape and per-invocation budgets", async () => {
  assert.throws(() => freezeHistoricalRecoveryCampaign("PB03-SHORT", request(), calendar,
    { ...session, closesAt: "2026-09-04T17:00:00.000Z" }), /exactly one 390-bar/);
  const fixture = harness(checkpoint(), (response, ordinal) => {
    if (ordinal === 1) response.budget.d1Queries = 41;
  });
  await assert.rejects(runHistoricalRecoveryCampaign(fixture.campaign, fixture.ports), /chunk 1 response evidence mismatch/);
  assert.equal(fixture.invoked.length, 1);
  assert.equal(fixture.records.length, 0);
});

test("HTTP adapter calls only the authenticated next-chunk boundary", async () => {
  const fixture = harness();
  const chunk = fixture.campaign.chunks[0]!;
  let observed: Request | undefined;
  const invoke = createHistoricalRecoveryHttpInvoker("https://worker.example/control/historical-recovery/nvda/next-chunk",
    "secret", async (input, init) => {
      observed = new Request(input, init);
      const response = await fixture.ports.invokeNextChunk({ recoveryId: fixture.campaign.request.recoveryId,
        jobId: chunk.jobId, checkpointVersion: chunk.checkpointBefore.version,
        completeThrough: chunk.checkpointBefore.completeThrough });
      return Response.json(response);
    });
  await invoke({ recoveryId: fixture.campaign.request.recoveryId, jobId: chunk.jobId,
    checkpointVersion: chunk.checkpointBefore.version, completeThrough: chunk.checkpointBefore.completeThrough });
  assert.equal(observed?.method, "POST");
  assert.equal(observed?.headers.get("authorization"), "Bearer secret");
  assert.equal(observed?.headers.get("x-orderscope-job-id"), chunk.jobId);
  assert.equal(await observed?.text(), "");
  assert.throws(() => createHistoricalRecoveryHttpInvoker("https://worker.example/health", "secret"),
    /exact HTTPS next-chunk/);
});
