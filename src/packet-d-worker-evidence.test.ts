import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { build } from "esbuild";
import { Miniflare } from "miniflare";
import { unstable_splitSqlQuery } from "wrangler";

const BASE_BINDINGS = {
  MARKET_TIMEZONE: "America/New_York",
  DISPLAY_TIMEZONE: "Asia/Tokyo",
  ALPACA_FEED: "iex",
  UNIVERSE_PROFILE: "canary-v0.1",
  ACQUISITION_RETENTION_MINUTES: "2",
  ACQUISITION_OVERLAP_1MIN_MINUTES: "1",
  ACQUISITION_OVERLAP_15MIN_MINUTES: "15",
  ACQUISITION_OVERLAP_1DAY_MINUTES: "1440",
  ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES: "1",
  ACQUISITION_FINALIZATION_LAG_15MIN_MINUTES: "2",
  ACQUISITION_FINALIZATION_LAG_1DAY_MINUTES: "30",
  ACQUISITION_MAX_JOBS_PER_TICK: "1",
  ACQUISITION_MAX_PAGES_PER_JOB: "10",
  ACQUISITION_MAX_BARS_PER_JOB: "100",
  ACQUISITION_STALE_ATTEMPT_MINUTES: "15",
  ACQUISITION_GAP_RETRY_MINUTES: "15",
  ACQUISITION_PROVIDER_MAX_ATTEMPTS: "3",
  ACQUISITION_PROVIDER_BASE_BACKOFF_MS: "250",
  ACQUISITION_PROVIDER_MAX_BACKOFF_MS: "2000",
  ACQUISITION_PROVIDER_MAX_RETRY_AFTER_MS: "5000",
  ACQUISITION_RETRY_POLICY: "NEXT_CRON",
  PREDICTION_MODE: "off",
  NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL: "2",
  NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN: "200",
  NEWS_ACQUISITION_CANARY_SYMBOLS: "AMD,NVDA",
  SCHEDULER_RUN_EVIDENCE_ENABLED: "true",
} as const;

async function bundleWorker(entry: string): Promise<string> {
  const bundle = await build({
    stdin: { contents: entry, resolveDir: new URL(".", import.meta.url).pathname, sourcefile: "packet-d-worker-entry.ts" },
    bundle: true,
    format: "esm",
    platform: "browser",
    target: "es2022",
    write: false,
  });
  return bundle.outputFiles[0]?.text ?? "";
}

async function migrateStateDb(db: D1Database): Promise<void> {
  for (const migration of [
    "0001_state.sql", "0002_attempt_coverage_key.sql", "0003_normalized_bar.sql",
    "0004_acquisition_lease.sql", "0005_gap_retry_eligibility.sql", "0006_digest_history.sql",
    "0007_news_metadata.sql", "0008_scheduler_run_evidence.sql",
  ]) {
    const sql = await readFile(new URL(`../migrations/${migration}`, import.meta.url), "utf8");
    for (const statement of unstable_splitSqlQuery(sql)) await db.prepare(statement).run();
  }
}

function liveScript(): Promise<string> {
  return bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-08-27", endExclusive: "2026-08-31" },
      sessions: [{
        marketDate: "2026-08-28", sessionKind: "REGULAR",
        opensAt: "2026-08-28T13:30:00.000Z", closesAt: "2026-08-28T20:00:00.000Z",
        isShortened: false, calendarRevision: "packet-d-calendar-v1",
      }],
      generatedAt: "2026-08-28T14:32:00.000Z", revision: "packet-d-calendar-v1",
    };
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "packet-d-universe-v1", generatedAt: calendar.generatedAt,
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async (_credentials, request) => ({ bars: [{
        symbol: request.instrument.symbol, timestamp: "2026-08-28T14:30:00.000Z",
        open: 100, high: 102, low: 99, close: 101, volume: 500, tradeCount: 7, vwap: 100.5,
        provider: "alpaca", dataVariant: "stock:iex:raw",
      }] }),
      fetchNewsPage: async () => ({ articles: [] }),
    });
  `);
}

test("live Market and News jobs persist one bounded scheduler run and share the D1 budget", async (t) => {
  const mf = new Miniflare({
    modules: true,
    script: await liveScript(),
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: {
      ...BASE_BINDINGS,
      WORKER_MODE: "live",
      ALPACA_API_KEY: "packet-d-key",
      ALPACA_API_SECRET: "packet-d-secret",
      NEWS_ACQUISITION_ENABLED: "true",
      NEWS_ACQUISITION_CADENCE_MINUTES: "1",
      NEWS_ACQUISITION_OVERLAP_MINUTES: "1",
    },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);

  await db.prepare(`INSERT INTO scheduler_run
    (run_id, scheduled_at, started_at, status, scheduler_revision, worker_mode)
    VALUES (?, ?, ?, 'RUNNING', 'packet-d-old', 'live')`
  ).bind("stale-run", "2026-08-28T14:00:00.000Z", "2026-08-28T14:00:01.000Z").run();
  await db.prepare(`INSERT INTO scheduler_run_job
    (run_id, job_id, job_kind, source, started_at, status, boundary_start, boundary_end)
    VALUES (?, ?, 'MARKET_BARS', 'alpaca-market-data', ?, 'RUNNING', ?, ?)`
  ).bind(
    "stale-run", "stale-market-job", "2026-08-28T14:00:02.000Z",
    "2026-08-28T13:59:00.000Z", "2026-08-28T14:00:00.000Z",
  ).run();

  const scheduledTime = new Date("2026-08-28T14:32:00.000Z");
  const result = await (await mf.getWorker()).scheduled({ cron: "* * * * *", scheduledTime });
  assert.equal(result.outcome, "ok", JSON.stringify(result));

  const stale = await db.prepare(`SELECT r.status AS run_status, j.status AS job_status,
    j.failure_category, r.diagnostic_json AS run_diagnostic, j.diagnostic_json AS job_diagnostic
    FROM scheduler_run r JOIN scheduler_run_job j ON j.run_id = r.run_id
    WHERE r.run_id = 'stale-run'`).first();
  assert.equal(stale?.run_status, "SUPERSEDED");
  assert.equal(stale?.job_status, "SUPERSEDED");
  assert.equal(stale?.failure_category, "STALE_RUN_JOB");
  assert.match(String(stale?.run_diagnostic), /replacementRunId/);
  assert.match(String(stale?.job_diagnostic), /replacementRunId/);

  const run = await db.prepare(`SELECT run_id, scheduled_at, status, scheduler_revision, worker_mode
    FROM scheduler_run WHERE scheduled_at = ? AND run_id <> 'stale-run'`
  ).bind(scheduledTime.toISOString()).first<{ run_id: string; scheduled_at: string; status: string;
    scheduler_revision: string; worker_mode: string }>();
  assert.ok(run);
  assert.equal(run.status, "SUCCEEDED");
  assert.equal(run.scheduler_revision, "packet-d-v1");
  assert.equal(run.worker_mode, "live");

  const jobs = await db.prepare(`SELECT job_kind, source, status, boundary_start, boundary_end,
    failure_category FROM scheduler_run_job WHERE run_id = ? ORDER BY job_kind`
  ).bind(run.run_id).all<Record<string, unknown>>();
  assert.deepEqual(jobs.results, [{
    job_kind: "MARKET_BARS", source: "alpaca-market-data", status: "SUCCEEDED",
    boundary_start: "2026-08-28T14:30:00.000Z", boundary_end: "2026-08-28T14:31:00.000Z",
    failure_category: null,
  }, {
    job_kind: "NEWS_METADATA", source: "alpaca-news", status: "SUCCEEDED",
    boundary_start: "2026-08-28T14:31:00.000Z", boundary_end: "2026-08-28T14:32:00.000Z",
    failure_category: null,
  }]);

  const envelope = await (await mf.dispatchFetch("http://packet-d.test/digest/latest")).json() as {
    payload: { budget: Record<string, unknown>; runEvidence: Record<string, unknown> };
  };
  assert.equal(envelope.payload.runEvidence.mode, "active");
  assert.equal(envelope.payload.runEvidence.schedulerRevision, "packet-d-v1");
  assert.equal(envelope.payload.runEvidence.supersededStaleRunJobs, 1);
  assert.equal(envelope.payload.budget.marketD1Queries, 21);
  assert.equal(envelope.payload.budget.newsD1Queries, 5);
  assert.equal(envelope.payload.budget.totalD1Queries, 30);
  assert.equal(envelope.payload.budget.withinBudget, true);
  assert.equal(JSON.stringify(envelope).includes("packet-d-key"), false);
  assert.equal(JSON.stringify(envelope).includes("packet-d-secret"), false);
});

test("active run evidence records a lease collision as SKIPPED_LOCKED without executing Market work", async (t) => {
  const mf = new Miniflare({
    modules: true,
    script: await liveScript(),
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: {
      ...BASE_BINDINGS,
      WORKER_MODE: "live",
      ALPACA_API_KEY: "packet-d-key",
      ALPACA_API_SECRET: "packet-d-secret",
      NEWS_ACQUISITION_ENABLED: "false",
      NEWS_ACQUISITION_CADENCE_MINUTES: "5",
      NEWS_ACQUISITION_OVERLAP_MINUTES: "15",
    },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  await db.prepare(`INSERT INTO acquisition_lease
    (coverage_key, owner_id, acquired_at, expires_at)
    VALUES (?, ?, ?, ?)`
  ).bind(
    "SPY|1Min|REGULAR|stock:iex:raw", "reused-owner-name",
    "2026-08-28T14:31:00.000Z", "2026-08-28T14:37:00.000Z",
  ).run();

  const result = await (await mf.getWorker()).scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-08-28T14:32:00.000Z"),
  });
  assert.equal(result.outcome, "ok", JSON.stringify(result));
  assert.deepEqual(await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM coverage_checkpoint) AS checkpoints
  `).first(), { bars: 0, checkpoints: 0 });
  const evidence = await db.prepare(`SELECT status, failure_category FROM scheduler_run_job
    WHERE job_kind = 'MARKET_BARS'`).first();
  assert.deepEqual(evidence, { status: "SKIPPED_LOCKED", failure_category: "LEASE_NOT_ACQUIRED" });
  const run = await db.prepare("SELECT status FROM scheduler_run ORDER BY started_at DESC LIMIT 1").first();
  assert.deepEqual(run, { status: "PARTIAL" });
});

test("shadow mode never mutates scheduler run evidence even when the activation flag is true", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    export default createWorker({
      calendarProvider: () => { throw new Error("shadow must not acquire calendar"); },
      universe: () => { throw new Error("shadow must not load universe"); },
    });
  `);
  const mf = new Miniflare({
    modules: true,
    script,
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: {
      ...BASE_BINDINGS,
      WORKER_MODE: "shadow",
      NEWS_ACQUISITION_ENABLED: "false",
      NEWS_ACQUISITION_CADENCE_MINUTES: "5",
      NEWS_ACQUISITION_OVERLAP_MINUTES: "15",
    },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);

  const result = await (await mf.getWorker()).scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-08-28T14:32:00.000Z"),
  });
  assert.equal(result.outcome, "ok", JSON.stringify(result));
  assert.deepEqual(await db.prepare(`SELECT
    (SELECT COUNT(*) FROM scheduler_run) AS runs,
    (SELECT COUNT(*) FROM scheduler_run_job) AS jobs
  `).first(), { runs: 0, jobs: 0 });
});
