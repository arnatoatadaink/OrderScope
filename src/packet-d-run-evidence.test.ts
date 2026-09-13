import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { Miniflare } from "miniflare";
import { unstable_splitSqlQuery } from "wrangler";
import { D1SchedulerRunEvidenceStore } from "./run-evidence.ts";

async function evidenceDb(t: test.TestContext): Promise<D1Database> {
  const mf = new Miniflare({
    modules: true,
    script: "export default { fetch() { return new Response('ok'); } }",
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  const sql = await readFile(new URL("../migrations/0008_scheduler_run_evidence.sql", import.meta.url), "utf8");
  for (const statement of unstable_splitSqlQuery(sql)) await db.prepare(statement).run();
  return db as unknown as D1Database;
}

test("persists bounded run/job evidence without becoming checkpoint truth", async (t) => {
  const db = await evidenceDb(t);
  const store = new D1SchedulerRunEvidenceStore(db);
  await store.startRun({
    runId: "run-1",
    scheduledAt: "2026-09-12T00:00:00Z",
    startedAt: "2026-09-12T00:00:01Z",
    status: "RUNNING",
    schedulerRevision: "packet-d-v1",
    workerMode: "shadow",
  });
  await store.startJob({
    runId: "run-1",
    jobId: "news-job-1",
    jobKind: "NEWS_METADATA",
    source: "alpaca-news",
    startedAt: "2026-09-12T00:00:02Z",
    status: "RUNNING",
    boundaryStart: "2026-09-11T23:45:00Z",
    boundaryEnd: "2026-09-12T00:00:00Z",
  });
  await store.finishJob("run-1", "news-job-1", "SUCCEEDED", "2026-09-12T00:00:04Z");
  await store.finishRun("run-1", "SUCCEEDED", "2026-09-12T00:00:05Z");

  const row = await db.prepare(`SELECT r.run_id, r.status AS run_status, r.scheduler_revision,
    j.job_id, j.status AS job_status, j.boundary_start, j.boundary_end
    FROM scheduler_run r JOIN scheduler_run_job j ON j.run_id = r.run_id
    WHERE r.run_id = ? AND j.job_id = ?`).bind("run-1", "news-job-1").first();
  assert.deepEqual(row, {
    run_id: "run-1", run_status: "SUCCEEDED", scheduler_revision: "packet-d-v1",
    job_id: "news-job-1", job_status: "SUCCEEDED",
    boundary_start: "2026-09-11T23:45:00Z", boundary_end: "2026-09-12T00:00:00Z",
  });
  const columns = await db.prepare("PRAGMA table_info(scheduler_run_job)").all<{ name: string }>();
  assert.equal(columns.results.some((column) => column.name === "complete_through"), false);
});

test("stale RUNNING jobs are superseded with explicit replacement run evidence", async (t) => {
  const db = await evidenceDb(t);
  const store = new D1SchedulerRunEvidenceStore(db);
  await store.startRun({
    runId: "stale-run", scheduledAt: "2026-09-11T23:00:00Z", startedAt: "2026-09-11T23:00:01Z",
    status: "RUNNING", schedulerRevision: "packet-d-v1", workerMode: "shadow",
  });
  await store.startJob({
    runId: "stale-run", jobId: "market-job-1", jobKind: "MARKET_BARS", source: "alpaca-bars",
    startedAt: "2026-09-11T23:00:02Z", status: "RUNNING",
    boundaryStart: "2026-09-11T22:59:00Z", boundaryEnd: "2026-09-11T23:00:00Z",
  });
  assert.equal(await store.supersedeStaleJobs(
    "2026-09-11T23:30:00Z", "2026-09-12T00:00:00Z", "replacement-run",
  ), 1);
  const row = await db.prepare(`SELECT status, failure_category, diagnostic_json
    FROM scheduler_run_job WHERE run_id = ? AND job_id = ?`).bind("stale-run", "market-job-1").first();
  assert.deepEqual(row, {
    status: "SUPERSEDED", failure_category: "STALE_RUN_JOB",
    diagnostic_json: JSON.stringify({ replacementRunId: "replacement-run" }),
  });
});

test("retry/replay relationship is explicit and bounded by the selected window", async (t) => {
  const db = await evidenceDb(t);
  const store = new D1SchedulerRunEvidenceStore(db);
  await store.startRun({
    runId: "retry-run", scheduledAt: "2026-09-12T00:05:00Z", startedAt: "2026-09-12T00:05:01Z",
    status: "RUNNING", schedulerRevision: "packet-d-v1", workerMode: "shadow",
  });
  await store.startJob({
    runId: "retry-run", jobId: "news-job-retry", jobKind: "NEWS_METADATA", source: "alpaca-news",
    startedAt: "2026-09-12T00:05:02Z", status: "RUNNING", retryOfJobId: "news-job-original",
    boundaryStart: "2026-09-11T23:50:00Z", boundaryEnd: "2026-09-12T00:05:00Z",
  });
  await store.finishJob("retry-run", "news-job-retry", "PARTIAL", "2026-09-12T00:05:03Z", {
    failureCategory: "TRANSPORT", diagnostic: { retryable: true },
  });
  const row = await db.prepare(`SELECT retry_of_job_id, boundary_start, boundary_end, status,
    failure_category, diagnostic_json FROM scheduler_run_job WHERE run_id = ? AND job_id = ?`)
    .bind("retry-run", "news-job-retry").first();
  assert.deepEqual(row, {
    retry_of_job_id: "news-job-original",
    boundary_start: "2026-09-11T23:50:00Z", boundary_end: "2026-09-12T00:05:00Z",
    status: "PARTIAL", failure_category: "TRANSPORT",
    diagnostic_json: JSON.stringify({ retryable: true }),
  });
});

test("durable evidence identities cannot be silently reused", async (t) => {
  const db = await evidenceDb(t);
  const store = new D1SchedulerRunEvidenceStore(db);
  const run = {
    runId: "immutable-run", scheduledAt: "2026-09-12T00:10:00Z", startedAt: "2026-09-12T00:10:01Z",
    status: "RUNNING" as const, schedulerRevision: "packet-d-v1", workerMode: "shadow",
  };
  await store.startRun(run);
  await assert.rejects(store.startRun(run), /already exists/);
  const job = {
    runId: run.runId, jobId: "immutable-job", jobKind: "NEWS_METADATA", source: "alpaca-news",
    startedAt: "2026-09-12T00:10:02Z", status: "RUNNING" as const,
  };
  await store.startJob(job);
  await assert.rejects(store.startJob(job), /already exists/);
});
