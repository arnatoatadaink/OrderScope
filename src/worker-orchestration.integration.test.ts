import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { build } from "esbuild";
import { Miniflare } from "miniflare";
import { unstable_splitSqlQuery } from "wrangler";

const SHADOW_BINDINGS = {
  WORKER_MODE: "shadow",
  MARKET_TIMEZONE: "America/New_York",
  DISPLAY_TIMEZONE: "Asia/Tokyo",
  ALPACA_FEED: "iex",
  ACQUISITION_RETENTION_MINUTES: "1440",
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
} as const;

const LIVE_BINDINGS = {
  ...SHADOW_BINDINGS,
  WORKER_MODE: "live",
  ALPACA_API_KEY: "integration-key",
  ALPACA_API_SECRET: "integration-secret",
  ACQUISITION_RETENTION_MINUTES: "2",
} as const;

async function bundleWorker(entry = "import worker from './index.ts'; export default worker;"): Promise<string> {
  const bundle = await build({
    stdin: { contents: entry, resolveDir: new URL(".", import.meta.url).pathname, sourcefile: "integration-entry.ts" },
    bundle: true,
    format: "esm",
    platform: "browser",
    target: "es2022",
    write: false,
  });
  return bundle.outputFiles[0]?.text ?? "";
}

async function migrateStateDb(db: D1Database): Promise<void> {
  for (const migration of ["0001_state.sql", "0002_attempt_coverage_key.sql", "0003_normalized_bar.sql", "0004_acquisition_lease.sql", "0005_gap_retry_eligibility.sql", "0006_digest_history.sql"]) {
    const sql = await readFile(new URL(`../migrations/${migration}`, import.meta.url), "utf8");
    for (const statement of unstable_splitSqlQuery(sql)) await db.prepare(statement).run();
  }
}

test("scheduled shadow tick persists a digest exposed by /digest/latest", async (t) => {
  const mf = new Miniflare({
    modules: true,
    script: await bundleWorker(),
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: SHADOW_BINDINGS,
  });
  t.after(() => mf.dispose());

  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);

  const scheduledTime = new Date("2026-08-30T12:34:00.000Z");
  const worker = await mf.getWorker();
  const result = await worker.scheduled({ cron: "* * * * *", scheduledTime });
  assert.equal(result.outcome, "ok");

  const response = await mf.dispatchFetch("http://integration.test/digest/latest");
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    digestKey: "market",
    generatedAt: scheduledTime.toISOString(),
    schemaVersion: 1,
    payload: {
      generatedAt: scheduledTime.toISOString(),
      mode: "shadow",
      status: "shadow",
      marketTimezone: "America/New_York",
      feed: "iex",
      notes: [
        "alpaca credentials not configured",
        "D1 state binding configured",
        "R2 archive binding not configured",
        "calendar-aware acquisition is intentionally not simulated from weekday/UTC rules",
      ],
    },
  });

  const row = await db.prepare(
    "SELECT digest_key, generated_at, schema_version FROM latest_digest WHERE digest_key = ?",
  ).bind("market").first();
  assert.deepEqual(row, {
    digest_key: "market",
    generated_at: scheduledTime.toISOString(),
    schema_version: 1,
  });

  const staleResult = await worker.scheduled({
    cron: "* * * * *",
    scheduledTime: new Date("2026-08-30T12:33:00.000Z"),
  });
  assert.equal(staleResult.outcome, "ok");
  const afterStaleTick = await mf.dispatchFetch("http://integration.test/digest/latest");
  assert.equal(afterStaleTick.status, 200);
  assert.equal((await afterStaleTick.json() as { generatedAt: string }).generatedAt, scheduledTime.toISOString());

  const historyResponse = await mf.dispatchFetch("http://integration.test/digest/history?limit=2");
  assert.equal(historyResponse.status, 200);
  const history = await historyResponse.json() as { count: number; digests: Array<{ generatedAt: string }> };
  assert.equal(history.count, 2);
  assert.deepEqual(history.digests.map((item) => item.generatedAt), [
    "2026-08-30T12:34:00.000Z",
    "2026-08-30T12:33:00.000Z",
  ]);

  const invalidHistory = await mf.dispatchFetch("http://integration.test/digest/history?limit=101");
  assert.equal(invalidHistory.status, 400);
});

test("prediction shadow plans Premarket target coverage without executing or writing bars", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-07-06", endExclusive: "2026-07-07" },
      sessions: [{
        marketDate: "2026-07-06", sessionKind: "PREMARKET",
        opensAt: "2026-07-06T08:00:00.000Z", closesAt: "2026-07-06T13:30:00.000Z",
        isShortened: false, calendarRevision: "integration-prediction-calendar-v1",
      }, {
        marketDate: "2026-07-06", sessionKind: "REGULAR",
        opensAt: "2026-07-06T13:30:00.000Z", closesAt: "2026-07-06T20:00:00.000Z",
        isShortened: false, calendarRevision: "integration-prediction-calendar-v1",
      }],
      generatedAt: "2026-07-06T08:03:00.000Z", revision: "integration-prediction-calendar-v1",
    };
    export default createWorker({
      calendarProvider: (_credentials, options) => {
        if (!options.includePremarket) throw new Error("prediction shadow must request Premarket");
        return { getCalendar: async () => calendar };
      },
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-07-06T08:03:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      predictionUniverse: () => ({
        revision: "integration-full-universe-v1", generatedAt: "2026-07-06T08:03:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      predictionRegistries: () => ({
        input: {
          revision: "prediction-input:integration-v1", market: "JAPAN_EQUITIES",
          generatedAt: "2026-07-06T08:03:00.000Z", instruments: [{
            instrumentId: "tse:0001", displaySymbol: "0001", providerSymbolMappings: { fixture: "0001" },
            exchange: "TSE", themes: ["Fixture"], baseCadence: "1Min", enabled: true,
            validFrom: "2026-07-06",
          }],
        },
        target: {
          revision: "prediction-target:integration-v1", generatedAt: "2026-07-06T08:03:00.000Z",
          targets: [{
            targetId: "us-theme:fixture", themeOrSector: "Fixture", constituentInstrumentIds: ["SPY"],
            labelPolicyVersion: "constituent-median-return-v0.1",
            enabledHorizons: ["PM_OPEN", "PM_SESSION", "REG_OPEN", "REG_SESSION"],
          }],
        },
      }),
      fetchPage: async () => { throw new Error("prediction shadow must not execute acquisition"); },
    });
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"],
    bindings: {
      ...LIVE_BINDINGS,
      PREDICTION_MODE: "shadow",
      PREDICTION_TARGET_PROFILE: "integration-v1",
      ACQUISITION_RETENTION_MINUTES: "2",
    },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);

  const result = await (await mf.getWorker()).scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-07-06T08:03:00.000Z"),
  });
  assert.equal(result.outcome, "ok");
  const envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as {
    payload: Record<string, unknown>;
  };
  assert.equal(envelope.payload.predictionMode, "shadow");
  assert.equal(envelope.payload.predictionTargetProfile, "integration-v1");
  assert.equal(envelope.payload.plannedJobs, 0);
  assert.deepEqual(envelope.payload.summaries, []);
  const shadow = envelope.payload.predictionShadow as Record<string, unknown>;
  assert.deepEqual({ ...shadow, jobPlans: undefined }, {
    mode: "shadow",
    targetProfile: "integration-v1",
    inputRegistryRevision: "prediction-input:integration-v1",
    targetRegistryRevision: "prediction-target:integration-v1",
    inputInstrumentCount: 1,
    targetCount: 1,
    acquisitionInstrumentCount: 1,
    plannedPremarketJobs: 1,
    deferredGapRetries: 0,
    jobPlans: undefined,
  });
  const jobPlans = shadow.jobPlans as Array<Record<string, unknown>>;
  assert.equal(jobPlans.length, 1);
  assert.equal(jobPlans[0]?.dueReason, "NO_CHECKPOINT");
  assert.equal(jobPlans[0]?.sessionScope, "PREMARKET");
  assert.deepEqual(jobPlans[0]?.requestedRange, {
    startInclusive: "2026-07-06T08:01:00.000Z",
    endExclusive: "2026-07-06T08:02:00.000Z",
  });
  assert.deepEqual(await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM coverage_checkpoint) AS checkpoints
  `).first(), { bars: 0, receipts: 0, attempts: 0, checkpoints: 0 });
});

test("scheduled live tick executes with injected providers and persists a sanitized summary", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-08-27", endExclusive: "2026-08-31" },
      sessions: [{
        marketDate: "2026-08-28", sessionKind: "REGULAR",
        opensAt: "2026-08-28T13:30:00.000Z", closesAt: "2026-08-28T20:00:00.000Z",
        isShortened: false, calendarRevision: "integration-calendar-v1",
      }],
      generatedAt: "2026-08-28T14:32:00.000Z", revision: "integration-calendar-v1",
    };
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-28T14:32:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async (_credentials, request) => ({ bars: [{
        symbol: request.instrument.symbol, timestamp: "2026-08-28T14:30:00.000Z",
        open: 100, high: 102, low: 99, close: 101, volume: 500, tradeCount: 7, vwap: 100.5,
        provider: "alpaca", dataVariant: "stock:iex:raw",
      }] }),
    });
  `);
  const mf = new Miniflare({
    modules: true,
    script,
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: LIVE_BINDINGS,
  });
  t.after(() => mf.dispose());

  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  await db.prepare(`INSERT INTO acquisition_attempt
    (attempt_id, coverage_key, job_id, started_at) VALUES
    (?, ?, ?, ?), (?, ?, ?, ?), (?, ?, ?, ?)`
  ).bind(
    "stale-same", "SPY|1Min|REGULAR|stock:iex:raw", "abandoned-job", "2026-08-28T14:00:00.000Z",
    "stale-other", "QQQ|1Min|REGULAR|stock:iex:raw", "unrelated-job", "2026-08-28T13:59:00.000Z",
    "fresh-same", "SPY|1Min|REGULAR|stock:iex:raw", "recent-job", "2026-08-28T14:20:00.000Z",
  ).run();
  const scheduledTime = new Date("2026-08-28T14:32:00.000Z");
  const result = await (await mf.getWorker()).scheduled({ cron: "* * * * *", scheduledTime });
  assert.equal(result.outcome, "ok");

  const response = await mf.dispatchFetch("http://integration.test/digest/latest");
  assert.equal(response.status, 200);
  const envelope = await response.json() as { payload: Record<string, unknown> };
  assert.deepEqual(envelope.payload.summaries, [{
    jobId: "market-bars:038e620d299135bb", outcome: "SUCCEEDED",
    pages: 1, inserted: 1, matched: 0, conflicts: 0, rejected: 0, missing: 0,
  }]);
  assert.equal(envelope.payload.plannedJobs, 1);
  assert.deepEqual(envelope.payload.jobPlans, [{
    jobId: "market-bars:038e620d299135bb",
    dueReason: "NO_CHECKPOINT",
    requestedRange: {
      startInclusive: "2026-08-28T14:30:00.000Z",
      endExclusive: "2026-08-28T14:31:00.000Z",
    },
  }]);
  assert.equal(envelope.payload.maxJobsPerTick, 1);
  assert.equal(envelope.payload.retryPolicy, "NEXT_CRON");
  assert.equal(envelope.payload.staleAttemptThresholdMinutes, 15);
  assert.equal(envelope.payload.supersededStaleAttempts, 1);
  assert.deepEqual(envelope.payload.staleAttempts, {
    count: 1, oldestStartedAt: "2026-08-28T13:59:00.000Z",
  });
  assert.equal(JSON.stringify(envelope).includes("integration-key"), false);
  assert.equal(JSON.stringify(envelope).includes("integration-secret"), false);

  const counts = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM acquisition_attempt WHERE outcome = 'SUCCEEDED') AS succeeded_attempts,
    (SELECT COUNT(*) FROM coverage_checkpoint WHERE state = 'COMPLETE') AS complete_checkpoints
  `).first();
  assert.deepEqual(counts, { bars: 1, receipts: 1, succeeded_attempts: 1, complete_checkpoints: 1 });
  const recovered = await db.prepare(`SELECT attempt_id, finished_at, outcome, diagnostic_json
    FROM acquisition_attempt WHERE attempt_id IN ('stale-same', 'fresh-same') ORDER BY attempt_id`
  ).all<{ attempt_id: string; finished_at: string | null; outcome: string | null; diagnostic_json: string | null }>();
  assert.deepEqual(recovered.results, [{
    attempt_id: "fresh-same", finished_at: null, outcome: null, diagnostic_json: null,
  }, {
    attempt_id: "stale-same", finished_at: scheduledTime.toISOString(), outcome: "SUPERSEDED",
    diagnostic_json: JSON.stringify({
      reason: "STALE_ATTEMPT_REPLACED", replacementJobId: "market-bars:038e620d299135bb",
    }),
  }]);
});

test("holiday tick publishes an empty summary without acquisition state writes", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => ({
        market: "US_EQUITIES",
        dateRange: { startInclusive: "2026-12-24", endExclusive: "2026-12-28" },
        sessions: [], generatedAt: "2026-12-25T16:00:00.000Z",
        revision: "integration-holiday-calendar-v1",
      }) }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-12-25T16:00:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async () => { throw new Error("holiday acquisition must not run"); },
    });
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"], bindings: LIVE_BINDINGS,
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);

  assert.equal((await (await mf.getWorker()).scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-12-25T16:00:00.000Z"),
  })).outcome, "ok");
  const envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as { payload: Record<string, unknown> };
  assert.equal(envelope.payload.status, "ready");
  assert.equal(envelope.payload.plannedJobs, 0);
  assert.deepEqual(envelope.payload.summaries, []);
  const counts = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM coverage_checkpoint) AS checkpoints
  `).first();
  assert.deepEqual(counts, { bars: 0, receipts: 0, attempts: 0, checkpoints: 0 });
});

test("shortened session finalizes at the early close without post-close phantom work", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-11-26", endExclusive: "2026-11-30" },
      sessions: [{
        marketDate: "2026-11-27", sessionKind: "REGULAR",
        opensAt: "2026-11-27T14:30:00.000Z", closesAt: "2026-11-27T18:00:00.000Z",
        isShortened: true, calendarRevision: "integration-short-calendar-v1",
      }],
      generatedAt: "2026-11-27T18:01:00.000Z", revision: "integration-short-calendar-v1",
    };
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-11-27T18:01:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async (_credentials, request) => ({ bars: [{
        symbol: request.instrument.symbol, timestamp: "2026-11-27T17:59:00.000Z",
        open: 100, high: 102, low: 99, close: 101, volume: 500, tradeCount: 7, vwap: 100.5,
        provider: "alpaca", dataVariant: "stock:iex:raw",
      }] }),
    });
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"], bindings: LIVE_BINDINGS,
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const worker = await mf.getWorker();

  assert.equal((await worker.scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-11-27T18:01:00.000Z"),
  })).outcome, "ok");
  let envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as { payload: Record<string, unknown> };
  assert.equal(envelope.payload.plannedJobs, 1);
  assert.deepEqual(envelope.payload.summaries, [{
    jobId: "market-bars:edb1a94f83bc1d64", outcome: "SUCCEEDED",
    pages: 1, inserted: 1, matched: 0, conflicts: 0, rejected: 0, missing: 0,
  }]);
  const checkpoint = await db.prepare(
    "SELECT complete_through, state, missing_ranges_json FROM coverage_checkpoint WHERE coverage_key = ?",
  ).bind("SPY|1Min|REGULAR|stock:iex:raw").first();
  assert.deepEqual(checkpoint, {
    complete_through: "2026-11-27T18:00:00.000Z", state: "COMPLETE", missing_ranges_json: "[]",
  });

  assert.equal((await worker.scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-11-27T18:02:00.000Z"),
  })).outcome, "ok");
  envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as { payload: Record<string, unknown> };
  assert.equal(envelope.payload.plannedJobs, 0);
  assert.deepEqual(envelope.payload.summaries, []);
  const counts = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts
  `).first();
  assert.deepEqual(counts, { bars: 1, receipts: 1, attempts: 1 });
});

test("shortened-session daily work waits for the actual close plus finalization lag", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-11-26", endExclusive: "2026-11-30" },
      sessions: [{
        marketDate: "2026-11-27", sessionKind: "REGULAR",
        opensAt: "2026-11-27T14:30:00.000Z", closesAt: "2026-11-27T18:00:00.000Z",
        isShortened: true, calendarRevision: "integration-short-calendar-v1",
      }],
      generatedAt: "2026-11-27T18:30:00.000Z", revision: "integration-short-calendar-v1",
    };
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-11-27T18:30:00.000Z",
        instruments: [{ symbol: "EWJ", cadence: "1Day", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async (_credentials, request) => ({ bars: [{
        symbol: request.instrument.symbol, timestamp: "2026-11-27T05:00:00.000Z",
        open: 80, high: 82, low: 79, close: 81, volume: 1000, tradeCount: 20, vwap: 80.5,
        provider: "alpaca", dataVariant: "stock:iex:raw",
      }] }),
    });
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"],
    bindings: { ...LIVE_BINDINGS, ACQUISITION_RETENTION_MINUTES: "1440" },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const worker = await mf.getWorker();

  assert.equal((await worker.scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-11-27T18:29:59.000Z"),
  })).outcome, "ok");
  let envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as { payload: Record<string, unknown> };
  assert.equal(envelope.payload.plannedJobs, 0);
  assert.deepEqual(envelope.payload.summaries, []);
  assert.deepEqual(await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM coverage_checkpoint) AS checkpoints
  `).first(), { bars: 0, attempts: 0, checkpoints: 0 });

  assert.equal((await worker.scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-11-27T18:30:00.000Z"),
  })).outcome, "ok");
  envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as { payload: Record<string, unknown> };
  assert.equal(envelope.payload.plannedJobs, 1);
  const summary = (envelope.payload.summaries as Array<Record<string, unknown>>)[0];
  assert.deepEqual({ ...summary, jobId: "stable" }, {
    jobId: "stable", outcome: "SUCCEEDED", pages: 1, inserted: 1, matched: 0,
    conflicts: 0, rejected: 0, missing: 0,
  });
  assert.deepEqual(await db.prepare(
    "SELECT complete_through, state, missing_ranges_json FROM coverage_checkpoint WHERE coverage_key = ?",
  ).bind("EWJ|1Day|REGULAR|stock:iex:raw").first(), {
    complete_through: "2026-11-27T18:00:00.000Z", state: "COMPLETE", missing_ranges_json: "[]",
  });
});

test("repeated successful scheduled tick is idempotently replanned from durable coverage", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-08-27", endExclusive: "2026-08-31" },
      sessions: [{
        marketDate: "2026-08-28", sessionKind: "REGULAR",
        opensAt: "2026-08-28T13:30:00.000Z", closesAt: "2026-08-28T20:00:00.000Z",
        isShortened: false, calendarRevision: "integration-calendar-v1",
      }],
      generatedAt: "2026-08-28T14:32:00.000Z", revision: "integration-calendar-v1",
    };
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-28T14:32:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async (_credentials, request) => ({ bars: [{
        symbol: request.instrument.symbol, timestamp: "2026-08-28T14:30:00.000Z",
        open: 100, high: 102, low: 99, close: 101, volume: 500, tradeCount: 7, vwap: 100.5,
        provider: "alpaca", dataVariant: "stock:iex:raw",
      }] }),
    });
  `);
  const mf = new Miniflare({
    modules: true,
    script,
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: LIVE_BINDINGS,
  });
  t.after(() => mf.dispose());

  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const scheduledTime = new Date("2026-08-28T14:32:00.000Z");
  const worker = await mf.getWorker();
  assert.equal((await worker.scheduled({ cron: "* * * * *", scheduledTime })).outcome, "ok");

  const firstResponse = await mf.dispatchFetch("http://integration.test/digest/latest");
  const firstEnvelope = await firstResponse.json() as { payload: Record<string, unknown> };
  assert.deepEqual(firstEnvelope.payload.summaries, [{
    jobId: "market-bars:038e620d299135bb", outcome: "SUCCEEDED",
    pages: 1, inserted: 1, matched: 0, conflicts: 0, rejected: 0, missing: 0,
  }]);

  assert.equal((await worker.scheduled({ cron: "* * * * *", scheduledTime })).outcome, "ok");

  const secondResponse = await mf.dispatchFetch("http://integration.test/digest/latest");
  assert.equal(secondResponse.status, 200);
  const secondEnvelope = await secondResponse.json() as { payload: Record<string, unknown> };
  assert.equal(secondEnvelope.payload.plannedJobs, 0);
  assert.deepEqual(secondEnvelope.payload.summaries, []);

  const counts = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM coverage_checkpoint) AS checkpoints
  `).first();
  assert.deepEqual(counts, { bars: 1, receipts: 1, attempts: 1, checkpoints: 1 });

  const checkpoint = await db.prepare(`SELECT complete_through, state, missing_ranges_json, version
    FROM coverage_checkpoint WHERE coverage_key = ?`
  ).bind("SPY|1Min|REGULAR|stock:iex:raw").first();
  assert.deepEqual(checkpoint, {
    complete_through: "2026-08-28T14:31:00.000Z",
    state: "COMPLETE",
    missing_ranges_json: "[]",
    version: 0,
  });
});

test("CAS conflict is sanitized publicly and replanned successfully on the next cron", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    import { D1CoverageCheckpointPort } from "./checkpoint.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-08-27", endExclusive: "2026-08-31" },
      sessions: [{
        marketDate: "2026-08-28", sessionKind: "REGULAR",
        opensAt: "2026-08-28T14:30:00.000Z", closesAt: "2026-08-28T21:00:00.000Z",
        isShortened: false, calendarRevision: "integration-calendar-v1",
      }],
      generatedAt: "2026-08-28T14:33:00.000Z", revision: "integration-calendar-v1",
    };
    let induceConflict = true;
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-28T14:33:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      checkpointPort: (db) => {
        const durable = new D1CoverageCheckpointPort(db);
        return {
          get: (key) => durable.get(key),
          listDue: (query) => durable.listDue(query),
          recordAttempt: (attempt) => durable.recordAttempt(attempt),
          summarizeStaleAttempts: (staleBefore) => durable.summarizeStaleAttempts(staleBefore),
          supersedeStaleAttempts: (command) => durable.supersedeStaleAttempts(command),
          compareAndSet: async (expectedVersion, proposed) => {
            if (induceConflict) {
              induceConflict = false;
              await durable.compareAndSet(expectedVersion, {
                ...proposed,
                completeThrough: undefined,
                state: "PARTIAL",
                missingRanges: [{
                  startInclusive: "2026-08-28T14:30:00.000Z",
                  endExclusive: "2026-08-28T14:31:00.000Z",
                }],
                lastSuccessAt: undefined,
              });
            }
            return durable.compareAndSet(expectedVersion, proposed);
          },
        };
      },
      fetchPage: async (_credentials, request) => ({ bars: [
        {
          symbol: request.instrument.symbol, timestamp: "2026-08-28T14:30:00.000Z",
          open: 100, high: 102, low: 99, close: 101, volume: 500, tradeCount: 7, vwap: 100.5,
          provider: "alpaca", dataVariant: "stock:iex:raw",
        },
        ...request.endExclusive >= "2026-08-28T14:32:00.000Z" ? [{
          symbol: request.instrument.symbol, timestamp: "2026-08-28T14:31:00.000Z",
          open: 101, high: 103, low: 100, close: 102, volume: 600, tradeCount: 8, vwap: 101.5,
          provider: "alpaca", dataVariant: "stock:iex:raw",
        }] : [],
      ] }),
    });
  `);
  const mf = new Miniflare({
    modules: true,
    script,
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: { ...LIVE_BINDINGS, ACQUISITION_RETENTION_MINUTES: "3" },
  });
  t.after(() => mf.dispose());

  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const worker = await mf.getWorker();
  assert.equal((await worker.scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-08-28T14:32:00.000Z"),
  })).outcome, "ok");

  const failedResponse = await mf.dispatchFetch("http://integration.test/digest/latest");
  const failedEnvelope = await failedResponse.json() as { payload: Record<string, unknown> };
  assert.deepEqual(failedEnvelope.payload.summaries, [{
    jobId: "market-bars:038e620d299135bb", outcome: "FAILED",
  }]);
  assert.equal(JSON.stringify(failedEnvelope).includes("compare-and-set"), false);

  const failedAttempt = await db.prepare(
    "SELECT outcome, diagnostic_json FROM acquisition_attempt ORDER BY started_at LIMIT 1",
  ).first<{ outcome: string; diagnostic_json: string }>();
  assert.equal(failedAttempt?.outcome, "FAILED");
  assert.deepEqual(JSON.parse(failedAttempt?.diagnostic_json ?? "null"), {
    message: "checkpoint compare-and-set conflict",
  });

  assert.equal((await worker.scheduled({
    cron: "* * * * *", scheduledTime: new Date("2026-08-28T14:33:00.000Z"),
  })).outcome, "ok");
  const recoveredResponse = await mf.dispatchFetch("http://integration.test/digest/latest");
  const recoveredEnvelope = await recoveredResponse.json() as { payload: Record<string, unknown> };
  assert.equal(recoveredEnvelope.payload.plannedJobs, 1);
  assert.deepEqual(recoveredEnvelope.payload.summaries, [{
    jobId: "market-bars:c20b5e45b4cf2456", outcome: "SUCCEEDED",
    pages: 1, inserted: 0, matched: 1, conflicts: 0, rejected: 0, missing: 0,
  }]);

  const durableState = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM acquisition_attempt WHERE outcome = 'FAILED') AS failed_attempts,
    (SELECT COUNT(*) FROM acquisition_attempt WHERE outcome = 'SUCCEEDED') AS succeeded_attempts
  `).first();
  assert.deepEqual(durableState, { bars: 1, receipts: 2, failed_attempts: 1, succeeded_attempts: 1 });
  const canonicalBar = await db.prepare(
    "SELECT open, high, low, close, volume, trade_count, vwap FROM normalized_bar WHERE instrument_id = ?",
  ).bind("SPY").first();
  assert.deepEqual(canonicalBar, {
    open: 100, high: 102, low: 99, close: 101, volume: 500, trade_count: 7, vwap: 100.5,
  });
  const checkpoint = await db.prepare(
    "SELECT complete_through, state, missing_ranges_json, version FROM coverage_checkpoint WHERE coverage_key = ?",
  ).bind("SPY|1Min|REGULAR|stock:iex:raw").first();
  assert.deepEqual(checkpoint, {
    complete_through: "2026-08-28T14:31:00.000Z",
    state: "COMPLETE",
    missing_ranges_json: "[]",
    version: 1,
  });
});

test("scheduled live tick preserves a provider gap as partial durable coverage", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-08-27", endExclusive: "2026-08-31" },
      sessions: [{
        marketDate: "2026-08-28", sessionKind: "REGULAR",
        opensAt: "2026-08-28T14:30:00.000Z", closesAt: "2026-08-28T21:00:00.000Z",
        isShortened: false, calendarRevision: "integration-calendar-v1",
      }],
      generatedAt: "2026-08-28T14:33:00.000Z", revision: "integration-calendar-v1",
    };
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-28T14:33:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async (_credentials, request) => ({ bars: [{
        symbol: request.instrument.symbol, timestamp: "2026-08-28T14:31:00.000Z",
        open: 100, high: 102, low: 99, close: 101, volume: 500, tradeCount: 7, vwap: 100.5,
        provider: "alpaca", dataVariant: "stock:iex:raw",
      }] }),
    });
  `);
  const mf = new Miniflare({
    modules: true,
    script,
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: { ...LIVE_BINDINGS, ACQUISITION_RETENTION_MINUTES: "30" },
  });
  t.after(() => mf.dispose());

  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const scheduledTime = new Date("2026-08-28T14:33:00.000Z");
  const result = await (await mf.getWorker()).scheduled({ cron: "* * * * *", scheduledTime });
  assert.equal(result.outcome, "ok");

  const response = await mf.dispatchFetch("http://integration.test/digest/latest");
  assert.equal(response.status, 200);
  const envelope = await response.json() as { payload: Record<string, unknown> };
  assert.deepEqual(envelope.payload.summaries, [{
    jobId: "market-bars:544c3126bd098914", outcome: "PARTIAL",
    pages: 1, inserted: 1, matched: 0, conflicts: 0, rejected: 0, missing: 1,
  }]);

  const checkpoint = await db.prepare(`SELECT complete_through, state, missing_ranges_json,
    last_success_at, source_observed_through, version
    FROM coverage_checkpoint WHERE coverage_key = ?`
  ).bind("SPY|1Min|REGULAR|stock:iex:raw").first();
  assert.deepEqual(checkpoint, {
    complete_through: null,
    state: "PARTIAL",
    missing_ranges_json: JSON.stringify([{
      startInclusive: "2026-08-28T14:30:00.000Z",
      endExclusive: "2026-08-28T14:31:00.000Z",
    }]),
    last_success_at: null,
    source_observed_through: "2026-08-28T14:32:00.000Z",
    version: 0,
  });
  const attempt = await db.prepare(
    "SELECT outcome, diagnostic_json FROM acquisition_attempt WHERE coverage_key = ?",
  ).bind("SPY|1Min|REGULAR|stock:iex:raw").first();
  assert.equal(attempt?.outcome, "PARTIAL");
  assert.deepEqual(JSON.parse(String(attempt?.diagnostic_json)), {
    pages: 1, inserted: 1, matched: 0, conflicts: 0, rejected: 0, missing: 1,
  });

  const deferredTime = new Date("2026-08-28T14:34:00.000Z");
  const deferredResult = await (await mf.getWorker()).scheduled({ cron: "* * * * *", scheduledTime: deferredTime });
  assert.equal(deferredResult.outcome, "ok");
  const deferredResponse = await mf.dispatchFetch("http://integration.test/digest/latest");
  const deferredEnvelope = await deferredResponse.json() as { payload: Record<string, unknown> };
  assert.equal(deferredEnvelope.payload.plannedJobs, 0);
  assert.deepEqual(deferredEnvelope.payload.jobPlans, []);
  assert.equal(deferredEnvelope.payload.deferredGapRetries, 1);
  assert.equal(deferredEnvelope.payload.nextGapRetryEligibleAt, "2026-08-28T14:48:00.000Z");
  assert.equal(deferredEnvelope.payload.gapRetryMinutes, 15);
  assert.deepEqual(deferredEnvelope.payload.summaries, []);
  const deferredCounts = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT version FROM coverage_checkpoint WHERE coverage_key = ?) AS checkpoint_version
  `).bind("SPY|1Min|REGULAR|stock:iex:raw").first();
  assert.deepEqual(deferredCounts, { attempts: 1, receipts: 1, checkpoint_version: 0 });

  const eligibleTime = new Date("2026-08-28T14:48:00.000Z");
  const eligibleResult = await (await mf.getWorker()).scheduled({ cron: "* * * * *", scheduledTime: eligibleTime });
  assert.equal(eligibleResult.outcome, "ok");
  const eligibleCounts = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts
  `).first();
  assert.deepEqual(eligibleCounts, { attempts: 2, receipts: 2 });
});

test("retention-expired gap cannot suppress bounded forward coverage", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => ({
        market: "US_EQUITIES",
        dateRange: { startInclusive: "2026-08-28", endExclusive: "2026-08-31" },
        sessions: [], generatedAt: "2026-08-30T18:30:00.000Z",
        revision: "integration-calendar-v1",
      }) }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-30T18:30:00.000Z",
        instruments: [{ symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" }],
      }),
      fetchPage: async (_credentials, request) => {
        const bars = [];
        for (let time = Date.parse(request.startInclusive); time < Date.parse(request.endExclusive); time += 60000) {
          bars.push({
            symbol: request.instrument.symbol, timestamp: new Date(time).toISOString(),
            open: 100, high: 102, low: 99, close: 101, volume: 5, tradeCount: 7, vwap: 100.5,
            provider: "alpaca", dataVariant: "crypto:us",
          });
        }
        return { bars };
      },
    });
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"],
    bindings: { ...LIVE_BINDINGS, ACQUISITION_RETENTION_MINUTES: "60" },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  await db.prepare(`INSERT INTO coverage_checkpoint (
    coverage_key, symbol, interval, session_scope, logical_data_variant,
    complete_through, state, missing_ranges_json, retry_not_before, version
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)` ).bind(
    "BTCUSD|1Min|ALL_TRADING|crypto:us", "BTCUSD", "1Min", "ALL_TRADING", "crypto:us",
    "2026-08-30T16:00:00.000Z", "PARTIAL", JSON.stringify([{
      startInclusive: "2026-08-30T16:10:00.000Z", endExclusive: "2026-08-30T17:30:00.000Z",
    }]), "2026-08-30T19:00:00.000Z", 4,
  ).run();

  const scheduledTime = new Date("2026-08-30T18:30:00.000Z");
  assert.equal((await (await mf.getWorker()).scheduled({ cron: "* * * * *", scheduledTime })).outcome, "ok");
  const envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as {
    payload: Record<string, unknown>;
  };
  assert.equal(envelope.payload.plannedJobs, 1);
  assert.deepEqual(envelope.payload.jobPlans, [{
    jobId: "market-bars:fc698dd7338cc083",
    dueReason: "FORWARD_COVERAGE",
    requestedRange: {
      startInclusive: "2026-08-30T17:30:00.000Z",
      endExclusive: "2026-08-30T18:29:00.000Z",
    },
  }]);
  assert.equal(envelope.payload.deferredGapRetries, 0);
  assert.deepEqual(envelope.payload.summaries, [{
    jobId: "market-bars:fc698dd7338cc083", outcome: "SUCCEEDED",
    pages: 1, inserted: 59, matched: 0, conflicts: 0, rejected: 0, missing: 0,
  }]);
  assert.deepEqual(await db.prepare(`SELECT complete_through, state, missing_ranges_json,
    retry_not_before, version FROM coverage_checkpoint WHERE coverage_key = ?`
  ).bind("BTCUSD|1Min|ALL_TRADING|crypto:us").first(), {
    complete_through: "2026-08-30T18:29:00.000Z", state: "COMPLETE",
    missing_ranges_json: "[]", retry_not_before: null, version: 5,
  });
});

test("scheduled live tick keeps provider failure details out of the public digest", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const calendar = {
      market: "US_EQUITIES",
      dateRange: { startInclusive: "2026-08-27", endExclusive: "2026-08-31" },
      sessions: [{
        marketDate: "2026-08-28", sessionKind: "REGULAR",
        opensAt: "2026-08-28T13:30:00.000Z", closesAt: "2026-08-28T20:00:00.000Z",
        isShortened: false, calendarRevision: "integration-calendar-v1",
      }],
      generatedAt: "2026-08-28T14:32:00.000Z", revision: "integration-calendar-v1",
    };
    export default createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-28T14:32:00.000Z",
        instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
      }),
      fetchPage: async (credentials) => {
        throw new Error(
          "alpaca stock bars failed: 503 upstream-provider-body "
          + credentials.keyId + " " + credentials.secretKey,
        );
      },
    });
  `);
  const mf = new Miniflare({
    modules: true,
    script,
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
    bindings: LIVE_BINDINGS,
  });
  t.after(() => mf.dispose());

  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const scheduledTime = new Date("2026-08-28T14:32:00.000Z");
  const result = await (await mf.getWorker()).scheduled({ cron: "* * * * *", scheduledTime });
  assert.equal(result.outcome, "ok");

  const response = await mf.dispatchFetch("http://integration.test/digest/latest");
  assert.equal(response.status, 200);
  const envelope = await response.json() as { payload: Record<string, unknown> };
  assert.deepEqual(envelope.payload.summaries, [{
    jobId: "market-bars:038e620d299135bb", outcome: "FAILED",
  }]);
  const serializedEnvelope = JSON.stringify(envelope);
  for (const sensitive of [
    "integration-key", "integration-secret", "upstream-provider-body", "503",
  ]) assert.equal(serializedEnvelope.includes(sensitive), false);

  const counts = await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM coverage_checkpoint) AS checkpoints
  `).first();
  assert.deepEqual(counts, { bars: 0, receipts: 0, checkpoints: 0 });

  const attempt = await db.prepare(`SELECT outcome, diagnostic_json, finished_at
    FROM acquisition_attempt WHERE coverage_key = ?`
  ).bind("SPY|1Min|REGULAR|stock:iex:raw").first();
  assert.equal(attempt?.outcome, "FAILED");
  assert.equal(typeof attempt?.finished_at, "string");
  assert.deepEqual(JSON.parse(String(attempt?.diagnostic_json)), {
    message: "alpaca stock bars failed: 503 upstream-provider-body integration-key integration-secret",
  });
});

test("overlapping scheduled ticks report lease contention without duplicate acquisition state", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    let providerCalls = 0;
    const calendar = {
      market: "CRYPTO", dateRange: { startInclusive: "2026-08-29", endExclusive: "2026-08-31" },
      sessions: [], generatedAt: "2026-08-30T00:02:00.000Z", revision: "integration-crypto-v1",
    };
    const worker = createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-30T00:02:00.000Z",
        instruments: [{ symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" }],
      }),
      fetchPage: async (_credentials, request) => {
        providerCalls += 1;
        await new Promise((resolve) => setTimeout(resolve, 500));
        return { bars: [{
          symbol: request.instrument.symbol, timestamp: request.startInclusive,
          open: 100, high: 102, low: 99, close: 101, volume: 5, tradeCount: 7, vwap: 100.5,
          provider: "alpaca", dataVariant: "crypto:us",
        }] };
      },
    });
    export default {
      scheduled: worker.scheduled,
      async fetch(request, env, ctx) {
        const path = new URL(request.url).pathname;
        if (path === "/control/provider-calls") return new Response(String(providerCalls));
        return worker.fetch(request, env, ctx);
      },
    };
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"],
    bindings: { ...LIVE_BINDINGS, ACQUISITION_RETENTION_MINUTES: "2" },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const worker = await mf.getWorker();
  const event = { cron: "* * * * *", scheduledTime: new Date("2026-08-30T00:02:00.000Z") };

  const firstTick = worker.scheduled(event);
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (await (await mf.dispatchFetch("http://integration.test/control/provider-calls")).text() === "1") break;
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  assert.equal(await (await mf.dispatchFetch("http://integration.test/control/provider-calls")).text(), "1");

  assert.equal((await worker.scheduled(event)).outcome, "ok");
  const locked = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as {
    payload: Record<string, unknown>;
  };
  assert.deepEqual(locked.payload.summaries, [{
    jobId: "market-bars:4da3b1befb6065a3", outcome: "SKIPPED_LOCKED",
  }]);
  assert.deepEqual(await db.prepare(`SELECT
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts
  `).first(), { attempts: 1, receipts: 0 });

  assert.equal((await firstTick).outcome, "ok");
  assert.equal(await (await mf.dispatchFetch("http://integration.test/control/provider-calls")).text(), "1");
  assert.deepEqual(await db.prepare(`SELECT
    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM acquisition_lease) AS leases
  `).first(), { attempts: 1, receipts: 1, bars: 1, leases: 0 });
  assert.deepEqual(await db.prepare(
    "SELECT complete_through, state FROM coverage_checkpoint WHERE coverage_key = ?",
  ).bind("BTCUSD|1Min|ALL_TRADING|crypto:us").first(), {
    complete_through: "2026-08-30T00:01:00.000Z", state: "COMPLETE",
  });
});

test("late completion keeps both scheduled digests in history without replacing the newer latest digest", async (t) => {
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    let providerCalls = 0;
    const calendar = {
      market: "CRYPTO", dateRange: { startInclusive: "2026-08-29", endExclusive: "2026-08-31" },
      sessions: [], generatedAt: "2026-08-30T00:02:00.000Z", revision: "integration-crypto-v1",
    };
    const worker = createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-30T00:02:00.000Z",
        instruments: [{ symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" }],
      }),
      fetchPage: async (_credentials, request) => {
        providerCalls += 1;
        await new Promise((resolve) => setTimeout(resolve, 200));
        return { bars: [{
          symbol: request.instrument.symbol, timestamp: request.startInclusive,
          open: 100, high: 102, low: 99, close: 101, volume: 5, tradeCount: 7, vwap: 100.5,
          provider: "alpaca", dataVariant: "crypto:us",
        }] };
      },
    });
    export default {
      scheduled: worker.scheduled,
      async fetch(request, env, ctx) {
        if (new URL(request.url).pathname === "/control/provider-calls") return new Response(String(providerCalls));
        return worker.fetch(request, env, ctx);
      },
    };
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"],
    bindings: { ...LIVE_BINDINGS, ACQUISITION_RETENTION_MINUTES: "2" },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);
  const worker = await mf.getWorker();
  const firstTime = new Date("2026-08-30T00:02:00.000Z");
  const secondTime = new Date("2026-08-30T00:03:00.000Z");

  const firstTick = worker.scheduled({ cron: "* * * * *", scheduledTime: firstTime });
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (await (await mf.dispatchFetch("http://integration.test/control/provider-calls")).text() === "1") break;
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  assert.equal(await (await mf.dispatchFetch("http://integration.test/control/provider-calls")).text(), "1");

  assert.equal((await worker.scheduled({ cron: "* * * * *", scheduledTime: secondTime })).outcome, "ok");
  let latest = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as { generatedAt: string };
  assert.equal(latest.generatedAt, secondTime.toISOString());

  assert.equal((await firstTick).outcome, "ok");
  latest = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as { generatedAt: string };
  assert.equal(latest.generatedAt, secondTime.toISOString());
  const history = await (await mf.dispatchFetch("http://integration.test/digest/history?limit=2")).json() as {
    count: number; digests: Array<{ generatedAt: string }>;
  };
  assert.equal(history.count, 2);
  assert.deepEqual(history.digests.map((digest) => digest.generatedAt), [
    secondTime.toISOString(), firstTime.toISOString(),
  ]);
});

test("bounded crypto recovery reuses 331 canonical bars and reaches a 24-hour boundary across cron ticks", async (t) => {
  const startMs = Date.parse("2026-08-29T00:00:00.000Z");
  const script = await bundleWorker(`
    import { createWorker } from "./worker.ts";
    const canonicalStarts = new Set();
    for (let index = 0; index < 331; index += 1) {
      canonicalStarts.add(new Date(Date.parse("2026-08-29T00:00:00.000Z") + index * 60000).toISOString());
    }
    let accepted = 0;
    let matched = 0;
    let inserted = 0;
    const calendar = {
      market: "CRYPTO", dateRange: { startInclusive: "2026-08-29", endExclusive: "2026-08-31" },
      sessions: [], generatedAt: "2026-08-30T00:01:00.000Z", revision: "integration-crypto-v1",
    };
    const worker = createWorker({
      calendarProvider: () => ({ getCalendar: async () => calendar }),
      universe: () => ({
        revision: "integration-universe-v1", generatedAt: "2026-08-30T00:01:00.000Z",
        instruments: [{ symbol: "BTCUSD", cadence: "1Min", providerRoute: "alpaca_crypto_bars" }],
      }),
      barStore: () => ({
        accept: async (candidate, provenance) => {
          if (candidate.outcome !== "NORMALIZED") throw new Error("recovery fixture generated a rejected bar");
          accepted += 1;
          const existed = canonicalStarts.has(candidate.bar.barStartUtc);
          if (existed) matched += 1;
          else { inserted += 1; canonicalStarts.add(candidate.bar.barStartUtc); }
          return {
            identity: candidate.bar.barStartUtc, outcome: existed ? "MATCHED" : "INSERTED",
            storedVersion: 1, acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true,
          };
        },
      }),
      fetchPage: async (_credentials, request) => {
        const bars = [];
        for (let time = Date.parse(request.startInclusive); time < Date.parse(request.endExclusive); time += 60000) {
          bars.push({
            symbol: request.instrument.symbol, timestamp: new Date(time).toISOString(),
            open: 100, high: 102, low: 99, close: 101, volume: 5, tradeCount: 7, vwap: 100.5,
            provider: "alpaca", dataVariant: "crypto:us",
          });
        }
        return { bars };
      },
    });
    export default {
      scheduled: worker.scheduled,
      async fetch(request, env, ctx) {
        if (new URL(request.url).pathname === "/control/stats") return Response.json({
          accepted, matched, inserted, canonical: canonicalStarts.size,
        });
        return worker.fetch(request, env, ctx);
      },
    };
  `);
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"],
    bindings: { ...LIVE_BINDINGS, ACQUISITION_RETENTION_MINUTES: "1440" },
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  await migrateStateDb(db as unknown as D1Database);

  const seedStatements: D1PreparedStatement[] = [];
  for (let index = 0; index < 331; index += 1) {
    const barStartUtc = new Date(startMs + index * 60_000).toISOString();
    const barEndUtc = new Date(startMs + (index + 1) * 60_000).toISOString();
    const identity = JSON.stringify(["BTCUSD", "1Min", barStartUtc, "ALL_TRADING", "crypto:us"]);
    seedStatements.push(db.prepare(`INSERT INTO normalized_bar (
      identity_key, instrument_id, interval, bar_start_utc, bar_end_utc, market_date,
      session_kind, is_shortened_session, logical_data_variant, open, high, low, close,
      volume, trade_count, vwap, canonical_fingerprint, accepted_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)` ).bind(
      identity, "BTCUSD", "1Min", barStartUtc, barEndUtc, barStartUtc.slice(0, 10),
      "ALL_TRADING", 0, "crypto:us", 100, 102, 99, 101, 5, 7, 100.5,
      "seed-fixture", "2026-08-30T00:00:00.000Z",
    ));
  }
  for (let offset = 0; offset < seedStatements.length; offset += 100) {
    await db.batch(seedStatements.slice(offset, offset + 100));
  }
  assert.equal(await db.prepare("SELECT COUNT(*) AS count FROM normalized_bar").first("count"), 331);
  assert.equal(await db.prepare("SELECT COUNT(*) AS count FROM coverage_checkpoint").first("count"), 0);

  const worker = await mf.getWorker();
  const event = { cron: "* * * * *", scheduledTime: new Date("2026-08-30T00:01:00.000Z") };
  for (let tick = 0; tick < 15; tick += 1) {
    assert.equal((await worker.scheduled(event)).outcome, "ok", `tick ${tick + 1}`);
  }

  const envelope = await (await mf.dispatchFetch("http://integration.test/digest/latest")).json() as {
    payload: Record<string, unknown>;
  };
  const finalSummary = (envelope.payload.summaries as Array<Record<string, unknown>>)[0];
  assert.deepEqual({ ...finalSummary, jobId: "stable" }, {
    jobId: "stable", outcome: "SUCCEEDED", pages: 1, inserted: 52, matched: 1,
    conflicts: 0, rejected: 0, missing: 0,
  });
  assert.deepEqual(await db.prepare(`SELECT
    (SELECT COUNT(*) FROM normalized_bar) AS bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
    (SELECT COUNT(*) FROM acquisition_attempt WHERE outcome = 'SUCCEEDED') AS succeeded_attempts,
    (SELECT COUNT(*) FROM bar_conflict) AS conflicts
  `).first(), { bars: 331, receipts: 0, succeeded_attempts: 15, conflicts: 0 });
  assert.deepEqual(await (await mf.dispatchFetch("http://integration.test/control/stats")).json(), {
    accepted: 1453, matched: 344, inserted: 1109, canonical: 1440,
  });
  assert.deepEqual(await db.prepare(`SELECT complete_through, state, missing_ranges_json, version
    FROM coverage_checkpoint WHERE coverage_key = ?`
  ).bind("BTCUSD|1Min|ALL_TRADING|crypto:us").first(), {
    complete_through: "2026-08-30T00:00:00.000Z", state: "COMPLETE",
    missing_ranges_json: "[]", version: 14,
  });
});
