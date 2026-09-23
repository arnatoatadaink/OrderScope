import assert from "node:assert/strict";
import test from "node:test";
import { SchedulerRunEvidenceSession } from "./run-evidence-session.ts";
import type {
  SchedulerRunEvidenceStore,
  SchedulerRunJobRecord,
  SchedulerRunJobStatus,
  SchedulerRunRecord,
  SchedulerRunStatus,
} from "./run-evidence.ts";

class MemoryEvidenceStore implements SchedulerRunEvidenceStore {
  runs: SchedulerRunRecord[] = [];
  jobs: SchedulerRunJobRecord[] = [];
  finishedRuns: Array<{ runId: string; status: Exclude<SchedulerRunStatus, "RUNNING"> }> = [];
  finishedJobs: Array<{
    runId: string;
    jobId: string;
    status: Exclude<SchedulerRunJobStatus, "RUNNING">;
    failureCategory?: string;
  }> = [];
  superseded: Array<{ staleBefore: string; replacementRunId: string }> = [];

  async startRun(record: SchedulerRunRecord) { this.runs.push(record); }
  async finishRun(runId: string, status: Exclude<SchedulerRunStatus, "RUNNING">) {
    this.finishedRuns.push({ runId, status });
  }
  async startJob(record: SchedulerRunJobRecord) { this.jobs.push(record); }
  async finishJob(
    runId: string,
    jobId: string,
    status: Exclude<SchedulerRunJobStatus, "RUNNING">,
    _finishedAt: string,
    options: { failureCategory?: string } = {},
  ) {
    this.finishedJobs.push({ runId, jobId, status, ...(options.failureCategory ? { failureCategory: options.failureCategory } : {}) });
  }
  async supersedeStaleJobs(staleBefore: string, _finishedAt: string, replacementRunId: string) {
    this.superseded.push({ staleBefore, replacementRunId });
    return 2;
  }
}

function clock(...values: string[]) {
  let index = 0;
  return () => new Date(values[Math.min(index++, values.length - 1)]!);
}

test("run session binds stale recovery and bounded job evidence to one run id", async () => {
  const store = new MemoryEvidenceStore();
  const session = await SchedulerRunEvidenceSession.start({
    store,
    runId: "run-1",
    scheduledAt: "2026-09-12T00:00:00Z",
    schedulerRevision: "packet-d-v1",
    workerMode: "live",
    clock: clock("2026-09-12T00:00:01Z", "2026-09-12T00:00:02Z", "2026-09-12T00:00:03Z", "2026-09-12T00:00:04Z"),
  });

  assert.equal(await session.supersedeStaleJobs("2026-09-11T23:45:00Z"), 2);
  const value = await session.runJob({
    jobId: "market-job-1",
    jobKind: "MARKET_BARS",
    source: "alpaca_stock_bars",
    boundaryStart: "2026-09-11T23:59:00Z",
    boundaryEnd: "2026-09-12T00:00:00Z",
  }, async () => ({ value: 42, completion: { status: "SUCCEEDED" as const } }));
  await session.finish("SUCCEEDED");

  assert.equal(value, 42);
  assert.equal(store.runs[0]?.runId, "run-1");
  assert.deepEqual(store.superseded, [{ staleBefore: "2026-09-11T23:45:00Z", replacementRunId: "run-1" }]);
  assert.deepEqual(store.jobs[0], {
    runId: "run-1", jobId: "market-job-1", jobKind: "MARKET_BARS", source: "alpaca_stock_bars",
    startedAt: "2026-09-12T00:00:03.000Z", status: "RUNNING",
    boundaryStart: "2026-09-11T23:59:00Z", boundaryEnd: "2026-09-12T00:00:00Z",
  });
  assert.equal(store.finishedJobs[0]?.status, "SUCCEEDED");
  assert.equal(store.finishedRuns[0]?.status, "SUCCEEDED");
});

test("locked work is explicit and never masquerades as a successful job", async () => {
  const store = new MemoryEvidenceStore();
  const session = await SchedulerRunEvidenceSession.start({
    store,
    runId: "run-lock",
    scheduledAt: "2026-09-12T00:05:00Z",
    schedulerRevision: "packet-d-v1",
    workerMode: "live",
    clock: () => new Date("2026-09-12T00:05:01Z"),
  });
  await session.recordLocked({
    jobId: "market-locked",
    jobKind: "MARKET_BARS",
    source: "alpaca_stock_bars",
    boundaryStart: "2026-09-12T00:04:00Z",
    boundaryEnd: "2026-09-12T00:05:00Z",
  });
  assert.deepEqual(store.finishedJobs[0], {
    runId: "run-lock", jobId: "market-locked", status: "SKIPPED_LOCKED", failureCategory: "LEASE_NOT_ACQUIRED",
  });
});

test("partial provider work keeps the explicit sanitized failure category", async () => {
  const store = new MemoryEvidenceStore();
  const session = await SchedulerRunEvidenceSession.start({
    store,
    runId: "run-partial",
    scheduledAt: "2026-09-12T00:10:00Z",
    schedulerRevision: "packet-d-v1",
    workerMode: "live",
    clock: () => new Date("2026-09-12T00:10:01Z"),
  });
  await session.runJob({
    jobId: "news-job-1", jobKind: "NEWS_METADATA", source: "alpaca-news",
    boundaryStart: "2026-09-11T23:55:00Z", boundaryEnd: "2026-09-12T00:10:00Z",
  }, async () => ({ value: undefined, completion: { status: "PARTIAL", failureCategory: "TRANSPORT" } }));
  assert.deepEqual(store.finishedJobs[0], {
    runId: "run-partial", jobId: "news-job-1", status: "PARTIAL", failureCategory: "TRANSPORT",
  });
});

test("unhandled execution errors become failed evidence and are rethrown", async () => {
  const store = new MemoryEvidenceStore();
  const session = await SchedulerRunEvidenceSession.start({
    store,
    runId: "run-failed",
    scheduledAt: "2026-09-12T00:15:00Z",
    schedulerRevision: "packet-d-v1",
    workerMode: "live",
    clock: () => new Date("2026-09-12T00:15:01Z"),
  });
  await assert.rejects(session.runJob({
    jobId: "market-failed", jobKind: "MARKET_BARS", source: "alpaca_stock_bars",
  }, async () => { throw new Error("raw provider detail must not be persisted"); }), /raw provider detail/);
  assert.deepEqual(store.finishedJobs[0], {
    runId: "run-failed", jobId: "market-failed", status: "FAILED", failureCategory: "UNHANDLED_JOB_FAILURE",
  });
});
