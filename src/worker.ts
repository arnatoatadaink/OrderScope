import { loadAcquisitionRuntimeConfig } from "./acquisition-config";
import { D1NormalizedBarStore, type NormalizedBarStore } from "./bar-store";
import { AlpacaMarketCalendarProvider, type MarketCalendarProvider } from "./calendar";
import { D1CoverageCheckpointPort, type CoverageCheckpointPort } from "./checkpoint";
import { DIGEST_HISTORY_DEFAULT_LIMIT, DIGEST_HISTORY_MAX_LIMIT, D1LatestDigestStore, LATEST_DIGEST_KEY } from "./digest";
import { executeAcquisitionJob, type AcquisitionExecutionSummary, type AcquisitionExecutorOptions } from "./execution";
import { prioritizeAcquisitionJobs } from "./job-priority";
import { D1AcquisitionLeaseStore, type AcquisitionLeaseStore } from "./lease";
import { gapRetryEligibility, type DeferredGapRetry } from "./gap-retry";
import { loadPredictionRegistries, type PredictionRegistryBundle } from "./prediction-registry";
import { buildPredictionPremarketUniverse, planPredictionPremarketAcquisition } from "./prediction";
import { batchAcquisitionJobs, coverageKeyFor, SchedulePolicy } from "./schedule";
import { loadUniverseSnapshot, type UniverseInstrument, type UniverseSnapshot } from "./universe";
import { loadNewsAcquisitionRuntimeConfig, type NewsAcquisitionConfigEnv } from "./news-acquisition-config";
import { NEWS_COVERAGE_KEY, planNewsAcquisition } from "./news-schedule";
import { D1NewsCheckpointPort, executeNewsAcquisition, type NewsCheckpointPort, type NewsExecutionSummary } from "./news-execution";
import { D1NewsStore, type NewsStore } from "./news-store";
import type { NewsExecutionOptions } from "./news-execution";
import { D1_QUERY_CEILING, EXTERNAL_SUBREQUEST_CEILING, InvocationBudget } from "./invocation-budget";
import { loadMarketCheckpoints } from "./market-checkpoint-load";
import { budgetedD1 } from "./budgeted-d1";
import { D1SchedulerRunEvidenceStore, type SchedulerRunEvidenceStore } from "./run-evidence";
import { SchedulerRunEvidenceSession } from "./run-evidence-session";
import { runHistoricalRecoveryChunk } from "./historical-recovery-runner";
import { planNextHistoricalRecoveryChunk, type HistoricalRecoveryRequest } from "./historical-recovery";

type PredictionMode = "off" | "shadow";

const SCHEDULER_EVIDENCE_REVISION = "packet-d-v1";
const DISABLED_RUN_EVIDENCE_STORE: SchedulerRunEvidenceStore = {
  async startRun() {},
  async finishRun() {},
  async startJob() {},
  async finishJob() {},
  async supersedeStaleJobs() { return 0; },
};

type Digest = {
  generatedAt: string;
  mode: string;
  status: "shadow" | "ready" | "blocked";
  marketTimezone: string;
  feed: string;
  predictionMode?: PredictionMode;
  predictionTargetProfile?: string;
  notes: string[];
  news?: Readonly<Record<string, unknown>>;
};

// `Env` is generated from wrangler.jsonc. Dashboard secrets and bindings that
// are intentionally provisioned after the first shadow deploy are supplemental.
type ProvisionedBindings = {
  ALPACA_API_KEY?: string;
  ALPACA_API_SECRET?: string;
  STATE_DB?: D1Database;
  BAR_ARCHIVE?: R2Bucket;
  SCHEDULER_RUN_EVIDENCE_ENABLED?: string;
  HISTORICAL_RECOVERY_CONTROL_TOKEN?: string;
  HISTORICAL_RECOVERY_ENABLED?: string;
};

type RuntimeEnv = Omit<Env,
  "WORKER_MODE" | "PREDICTION_MODE" | "PREDICTION_TARGET_PROFILE" | "HISTORICAL_RECOVERY_ENABLED"
  | keyof NewsAcquisitionConfigEnv> & ProvisionedBindings & {
  WORKER_MODE: "shadow" | "live";
  PREDICTION_MODE?: PredictionMode;
  PREDICTION_TARGET_PROFILE?: string;
} & NewsAcquisitionConfigEnv;

type PredictionRuntimeConfig = {
  mode: PredictionMode;
  targetProfile?: string;
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function predictionRuntimeConfig(env: RuntimeEnv): PredictionRuntimeConfig {
  const mode = env.PREDICTION_MODE ?? "off";
  if (mode !== "off" && mode !== "shadow") throw new Error(`unsupported PREDICTION_MODE: ${mode}`);
  const targetProfile = env.PREDICTION_TARGET_PROFILE?.trim();
  if (mode === "shadow" && !targetProfile) {
    throw new Error("PREDICTION_TARGET_PROFILE is required in prediction shadow mode");
  }
  return { mode, ...(targetProfile ? { targetProfile } : {}) };
}

function schedulerRunEvidenceEnabled(env: RuntimeEnv): boolean {
  const value = env.SCHEDULER_RUN_EVIDENCE_ENABLED ?? "false";
  if (value !== "true" && value !== "false") {
    throw new Error("SCHEDULER_RUN_EVIDENCE_ENABLED must be true or false");
  }
  return value === "true";
}

const NVDA_RECOVERY = {
  recoveryId: "L1-003-NVDA-20260916-01",
  expectedJobId: "historical-market-recovery:ef94f87d37bf2746",
  providerRevision: "alpaca-stock-bars-v1",
  universeRevision: "stock-monitoring-canary-v0.1",
  calendarRevision: "alpaca-calendar-v2:da7d32f3",
  calendarStart: "2026-09-02",
  calendarEnd: "2026-09-17",
  coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
  recoveryStart: "2026-09-02T20:00:00.000Z",
  recoveryEnd: "2026-09-15T20:00:00.000Z",
  checkpointBefore: "2026-09-02T20:00:00.000Z",
  checkpointVersion: 6,
  maxBars: 100,
} as const;

async function constantTimeEqual(provided: string, expected: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [providedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(provided)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  return crypto.subtle.timingSafeEqual(providedHash, expectedHash);
}

function historicalRecoveryEnabled(env: RuntimeEnv): boolean {
  const value = env.HISTORICAL_RECOVERY_ENABLED ?? "false";
  if (value !== "true" && value !== "false") {
    throw new Error("HISTORICAL_RECOVERY_ENABLED must be true or false");
  }
  return value === "true";
}

async function authorizeHistoricalRecovery(request: Request, env: RuntimeEnv): Promise<boolean> {
  const expected = env.HISTORICAL_RECOVERY_CONTROL_TOKEN;
  const authorization = request.headers.get("authorization");
  if (!expected || !authorization?.startsWith("Bearer ")) return false;
  return constantTimeEqual(authorization.slice("Bearer ".length), expected);
}

function parseCheckpointVersion(value: string | null): number | undefined {
  if (value === null || !/^(0|[1-9]\d*)$/.test(value)) return undefined;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : undefined;
}

function currentDigest(
  env: RuntimeEnv,
  now: Date,
  predictionConfig = predictionRuntimeConfig(env),
): Digest {
  const hasCredentials = Boolean(env.ALPACA_API_KEY && env.ALPACA_API_SECRET);
  const hasState = "STATE_DB" in env && Boolean(env.STATE_DB);
  const hasArchive = "BAR_ARCHIVE" in env && Boolean(env.BAR_ARCHIVE);
  const liveRequested = env.WORKER_MODE === "live";
  const newsConfig = loadNewsAcquisitionRuntimeConfig(env);

  return {
    generatedAt: now.toISOString(),
    mode: env.WORKER_MODE ?? "shadow",
    status: liveRequested && hasCredentials && hasState ? "ready" : liveRequested ? "blocked" : "shadow",
    marketTimezone: env.MARKET_TIMEZONE ?? "America/New_York",
    feed: env.ALPACA_FEED ?? "iex",
    ...(env.PREDICTION_MODE !== undefined ? { predictionMode: predictionConfig.mode } : {}),
    ...(predictionConfig.targetProfile ? { predictionTargetProfile: predictionConfig.targetProfile } : {}),
    news: { mode: newsConfig.enabled && liveRequested ? "active" : newsConfig.enabled ? "shadow-plan" : "disabled",
      cadenceMinutes: newsConfig.cadenceMinutes, plannedJobs: 0, selectedJobs: 0, completedJobs: 0,
      partialJobs: 0, failedJobs: 0, articlesObserved: 0, duplicates: 0, updates: 0, pages: 0 },
    notes: [
      hasCredentials ? "alpaca credentials configured" : "alpaca credentials not configured",
      hasState ? "D1 state binding configured" : "D1 state binding not configured",
      hasArchive ? "R2 archive binding configured" : "R2 archive binding not configured",
      "calendar-aware acquisition is intentionally not simulated from weekday/UTC rules",
    ],
  };
}

export type ScheduledOrchestrationDependencies = {
  calendarProvider: (
    credentials: { keyId: string; secretKey: string },
    options: { includePremarket: boolean; includeAfterHours: boolean },
  ) => MarketCalendarProvider;
  universe: (profile: string) => UniverseSnapshot;
  predictionRegistries?: (profile: string) => PredictionRegistryBundle;
  predictionUniverse?: () => UniverseSnapshot;
  fetchPage?: AcquisitionExecutorOptions["fetchPage"];
  checkpointPort?: (db: D1Database) => CoverageCheckpointPort;
  leaseStore?: (db: D1Database) => AcquisitionLeaseStore;
  barStore?: (db: D1Database) => NormalizedBarStore;
  newsCheckpointPort?: (db: D1Database) => NewsCheckpointPort;
  newsStore?: (db: D1Database) => NewsStore;
  fetchNewsPage?: NewsExecutionOptions["fetchPage"];
  runEvidenceStore?: (db: D1Database) => SchedulerRunEvidenceStore;
};

const productionDependencies: ScheduledOrchestrationDependencies = {
  calendarProvider: (credentials, options) => new AlpacaMarketCalendarProvider({ credentials, ...options }),
  universe: (profile) => loadUniverseSnapshot(profile),
  predictionRegistries: (profile) => loadPredictionRegistries(profile),
  predictionUniverse: () => loadUniverseSnapshot("full-v0.1"),
};

function schedulerEvidenceRunStatus(
  marketSummaries: readonly (AcquisitionExecutionSummary | { jobId: string; outcome: "FAILED" | "SKIPPED_LOCKED" })[],
  newsSummaries: readonly NewsExecutionSummary[],
): "SUCCEEDED" | "PARTIAL" {
  return marketSummaries.some((summary) => summary.outcome !== "SUCCEEDED")
    || newsSummaries.some((summary) => summary.outcome !== "SUCCEEDED")
    ? "PARTIAL"
    : "SUCCEEDED";
}

async function runScheduledTick(
  controller: ScheduledController,
  env: RuntimeEnv,
  dependencies: ScheduledOrchestrationDependencies,
): Promise<void> {
  const now = new Date(controller.scheduledTime);
  const predictionConfig = predictionRuntimeConfig(env);
  const digest = currentDigest(env, now, predictionConfig);

  // Shadow mode is deployable before credentials/storage exist and deliberately
  // performs no market-data writes. This prevents a calendar/session guess from
  // becoming production behavior.
  if (env.WORKER_MODE !== "live") {
    if ("STATE_DB" in env && env.STATE_DB) {
      await new D1LatestDigestStore(env.STATE_DB).put(LATEST_DIGEST_KEY, digest.generatedAt, digest);
    }
    console.log(JSON.stringify({ event: "scheduler_tick", ...digest }));
    return;
  }

  if (!env.ALPACA_API_KEY || !env.ALPACA_API_SECRET) {
    throw new Error("live mode requires Alpaca secrets");
  }
  if (!("STATE_DB" in env) || !env.STATE_DB) {
    throw new Error("live mode requires STATE_DB D1 binding");
  }

  const credentials = { keyId: env.ALPACA_API_KEY, secretKey: env.ALPACA_API_SECRET };
  const invocationBudget = new InvocationBudget();
  const stateDb = budgetedD1(env.STATE_DB, invocationBudget);
  const acquisitionConfig = loadAcquisitionRuntimeConfig(env);
  const newsConfig = loadNewsAcquisitionRuntimeConfig(env);
  const evidenceEnabled = schedulerRunEvidenceEnabled(env);
  const universe = dependencies.universe(env.UNIVERSE_PROFILE);
  const predictionRegistries = predictionConfig.mode === "shadow"
    ? (dependencies.predictionRegistries ?? productionDependencies.predictionRegistries!)(predictionConfig.targetProfile!)
    : undefined;
  const predictionUniverse = predictionRegistries
    ? buildPredictionPremarketUniverse(
      predictionRegistries.target,
      (dependencies.predictionUniverse ?? productionDependencies.predictionUniverse!)(),
      now.toISOString(),
    )
    : undefined;
  const retentionFloor = new Date(now.getTime() - acquisitionConfig.retentionLookbackMs).toISOString();
  const calendarStart = new Date(Date.parse(retentionFloor) - 24 * 60 * 60_000).toISOString().slice(0, 10);
  const calendarEnd = new Date(now.getTime() + 2 * 24 * 60 * 60_000).toISOString().slice(0, 10);
  const calendar = await dependencies.calendarProvider(credentials, {
    includePremarket: predictionConfig.mode === "shadow",
    includeAfterHours: newsConfig.enabled,
  }).getCalendar(calendarStart, calendarEnd);
  const checkpoints = dependencies.checkpointPort?.(stateDb) ?? new D1CoverageCheckpointPort(stateDb);
  const stored = await loadMarketCheckpoints(universe, checkpoints, env.ALPACA_FEED);
  const marketBootstrapD1Queries = invocationBudget.snapshot().d1Queries;
  const policy = new SchedulePolicy({
    retentionFloor,
    overlapMs: acquisitionConfig.overlapMs,
    finalizationLagMs: acquisitionConfig.finalizationLagMs,
    maxBarsPerJob: acquisitionConfig.maxBarsPerJob,
    logicalDataVariant: (instrument) => logicalVariant(instrument, env.ALPACA_FEED),
  });
  const planned = policy.plan(universe, calendar, stored, now)
    .filter((job) => stored.find((checkpoint) => checkpoint.coverageKey === job.checkpointExpectations[0]?.coverageKey)?.state !== "BLOCKED");
  const deferredGapRetries = stored
    .map((checkpoint) => gapRetryEligibility(checkpoint, now, acquisitionConfig.gapRetryMinutes, retentionFloor))
    .filter((retry): retry is DeferredGapRetry => retry !== undefined);
  const deferredCoverageKeys = new Set(deferredGapRetries.map((retry) => retry.coverageKey));
  const jobs = planned.filter((job) => job.dueReason !== "MISSING_RANGE"
    || !deferredCoverageKeys.has(job.checkpointExpectations[0]?.coverageKey ?? ""));
  let predictionShadow: Record<string, unknown> | undefined;
  if (predictionRegistries && predictionUniverse) {
    const predictionKeys = predictionUniverse.instruments.map((instrument) =>
      coverageKeyFor(instrument, "PREMARKET", logicalVariant(instrument, env.ALPACA_FEED)));
    const predictionBefore = invocationBudget.snapshot().d1Queries;
    const predictionStored = await checkpoints.getMany(predictionKeys);
    const predictionPlanned = planPredictionPremarketAcquisition({
      acquisitionUniverse: predictionUniverse,
      calendar,
      checkpoints: predictionStored,
      now,
      scheduleConfig: {
        retentionFloor,
        overlapMs: acquisitionConfig.overlapMs,
        finalizationLagMs: acquisitionConfig.finalizationLagMs,
        maxBarsPerJob: acquisitionConfig.maxBarsPerJob,
        logicalDataVariant: (instrument) => logicalVariant(instrument, env.ALPACA_FEED),
      },
    }).filter((job) => predictionStored.find((checkpoint) =>
      checkpoint.coverageKey === job.checkpointExpectations[0]?.coverageKey)?.state !== "BLOCKED");
    const predictionDeferredGapRetries = predictionStored
      .map((checkpoint) => gapRetryEligibility(
        checkpoint, now, acquisitionConfig.gapRetryMinutes, retentionFloor,
      ))
      .filter((retry): retry is DeferredGapRetry => retry !== undefined);
    const predictionDeferredCoverageKeys = new Set(
      predictionDeferredGapRetries.map((retry) => retry.coverageKey),
    );
    const predictionJobs = predictionPlanned.filter((job) => job.dueReason !== "MISSING_RANGE"
      || !predictionDeferredCoverageKeys.has(job.checkpointExpectations[0]?.coverageKey ?? ""));
    predictionShadow = {
      mode: "shadow",
      targetProfile: predictionConfig.targetProfile,
      inputRegistryRevision: predictionRegistries.input.revision,
      targetRegistryRevision: predictionRegistries.target.revision,
      inputInstrumentCount: predictionRegistries.input.instruments.filter((instrument) => instrument.enabled).length,
      targetCount: predictionRegistries.target.targets.length,
      acquisitionInstrumentCount: predictionUniverse.instruments.length,
      plannedPremarketJobs: predictionJobs.length,
      checkpointKeys: new Set(predictionKeys).size,
      checkpointBootstrapD1Queries: invocationBudget.snapshot().d1Queries - predictionBefore,
      deferredGapRetries: predictionDeferredGapRetries.length,
      jobPlans: predictionJobs.slice(0, acquisitionConfig.maxJobsPerTick).map((job) => ({
        jobId: job.jobId,
        dueReason: job.dueReason,
        sessionScope: job.sessionScope,
        requestedRange: job.requestedRange,
      })),
    };
  }
  const runnableJobs = batchAcquisitionJobs(
    prioritizeAcquisitionJobs(jobs, stored),
  ).slice(0, acquisitionConfig.maxJobsPerTick);
  const jobPlans = runnableJobs.map((job) => ({
    jobId: job.jobId,
    dueReason: job.dueReason,
    requestedRange: job.requestedRange,
  }));
  const summaries: Array<AcquisitionExecutionSummary
    | { jobId: string; outcome: "FAILED" | "SKIPPED_LOCKED" }> = [];
  const staleBefore = new Date(now.getTime() - acquisitionConfig.staleAttemptMinutes * 60_000).toISOString();
  const runId = `scheduler:${now.toISOString()}:${crypto.randomUUID()}`;
  const runEvidence = await SchedulerRunEvidenceSession.start({
    store: evidenceEnabled
      ? (dependencies.runEvidenceStore?.(stateDb) ?? new D1SchedulerRunEvidenceStore(stateDb))
      : DISABLED_RUN_EVIDENCE_STORE,
    runId,
    scheduledAt: now.toISOString(),
    schedulerRevision: SCHEDULER_EVIDENCE_REVISION,
    workerMode: env.WORKER_MODE,
  });
  const supersededStaleRunJobs = await runEvidence.supersedeStaleJobs(staleBefore);
  let supersededStaleAttempts = 0;
  const leases = dependencies.leaseStore?.(stateDb) ?? new D1AcquisitionLeaseStore(stateDb);
  for (const job of runnableJobs) {
    const evidenceDescriptor = {
      jobId: job.jobId,
      jobKind: "MARKET_BARS",
      source: "alpaca-market-data",
      boundaryStart: job.requestedRange.startInclusive,
      boundaryEnd: job.requestedRange.endExclusive,
    };
    const coverageKey = job.instruments.length === 1
      ? job.checkpointExpectations[0]!.coverageKey
      : `batch:${job.jobId}`;
    const ownerId = `${job.jobId}:${now.toISOString()}`;
    const acquired = await leases.acquire(coverageKey, ownerId, now.toISOString(), 5 * 60_000);
    if (!acquired) {
      await runEvidence.recordLocked(evidenceDescriptor);
      summaries.push({ jobId: job.jobId, outcome: "SKIPPED_LOCKED" });
      continue;
    }
    try {
      supersededStaleAttempts += await checkpoints.supersedeStaleAttempts({
        coverageKey, staleBefore, finishedAt: now.toISOString(), replacementJobId: job.jobId,
      });
      const summary = await runEvidence.runJob(evidenceDescriptor, async () => {
        const value = await executeAcquisitionJob(job, {
          credentials, calendar, checkpoints,
          bars: dependencies.barStore?.(stateDb) ?? new D1NormalizedBarStore(stateDb),
          feed: env.ALPACA_FEED, maxPages: acquisitionConfig.maxPagesPerJob,
          maxBars: acquisitionConfig.maxBarsPerJob,
          gapRetryDelayMs: acquisitionConfig.gapRetryMinutes * 60_000,
          providerFetchOptions: { retry: acquisitionConfig.providerRetry },
          now: () => now,
          fetchPage: dependencies.fetchPage,
          budget: invocationBudget,
        });
        return {
          value,
          completion: {
            status: value.outcome,
            diagnostic: {
              pages: value.pages, inserted: value.inserted, matched: value.matched,
              conflicts: value.conflicts, rejected: value.rejected, missing: value.missing,
            },
          },
        };
      });
      summaries.push(summary);
    } catch {
      // Detailed diagnostics are already recorded on the attempt/evidence rows.
      // Keep the public operational digest compact and free of provider details.
      summaries.push({ jobId: job.jobId, outcome: "FAILED" });
    } finally {
      await leases.release(coverageKey, ownerId);
    }
  }
  const staleAttempts = await checkpoints.summarizeStaleAttempts(staleBefore);
  const marketExternalSubrequests = invocationBudget.snapshot().externalSubrequests;
  const marketD1Queries = invocationBudget.snapshot().d1Queries;
  const newsCheckpoints = dependencies.newsCheckpointPort?.(stateDb) ?? new D1NewsCheckpointPort(stateDb);
  const newsBefore = invocationBudget.snapshot().d1Queries;
  const newsStored = newsConfig.enabled ? await newsCheckpoints.get(NEWS_COVERAGE_KEY) : undefined;
  const newsPlanned = planNewsAcquisition(newsConfig, calendar, newsStored, now);
  const newsSummaries: NewsExecutionSummary[] = [];
  for (const newsJob of newsPlanned) {
    const summary = await runEvidence.runJob({
      jobId: newsJob.jobId,
      jobKind: "NEWS_METADATA",
      source: "alpaca-news",
      boundaryStart: newsJob.requestedRange.startInclusive,
      boundaryEnd: newsJob.requestedRange.endExclusive,
    }, async () => {
      const value = await executeNewsAcquisition(newsJob, {
        credentials, checkpoints: newsCheckpoints,
        store: dependencies.newsStore?.(stateDb) ?? new D1NewsStore(stateDb),
        retry: acquisitionConfig.providerRetry,
        retryDelayMs: acquisitionConfig.gapRetryMinutes * 60_000,
        now: () => now, fetchPage: dependencies.fetchNewsPage, budget: invocationBudget,
      });
      return {
        value,
        completion: {
          status: value.outcome,
          ...(value.errorCategory ? { failureCategory: value.errorCategory } : {}),
          diagnostic: {
            pages: value.pages, articlesObserved: value.articlesObserved,
            newArticles: value.newArticles, duplicates: value.duplicates,
            updates: value.updates, conflicts: value.conflicts,
          },
        },
      };
    });
    newsSummaries.push(summary);
  }
  const news = {
    mode: newsConfig.enabled ? "active" : "disabled",
    cadenceMinutes: newsConfig.cadenceMinutes,
    plannedJobs: newsPlanned.length,
    selectedJobs: newsPlanned.length,
    completedJobs: newsSummaries.filter((summary) => summary.outcome === "SUCCEEDED").length,
    partialJobs: newsSummaries.filter((summary) => summary.outcome === "PARTIAL").length,
    failedJobs: newsSummaries.filter((summary) => summary.outcome === "FAILED").length,
    articlesObserved: newsSummaries.reduce((sum, summary) => sum + summary.articlesObserved, 0),
    duplicates: newsSummaries.reduce((sum, summary) => sum + summary.duplicates, 0),
    updates: newsSummaries.reduce((sum, summary) => sum + summary.updates, 0),
    pages: newsSummaries.reduce((sum, summary) => sum + summary.pages, 0),
    externalSubrequests: newsSummaries.reduce((sum, summary) => sum + summary.externalSubrequests, 0),
    d1Queries: invocationBudget.snapshot().d1Queries - newsBefore,
    nextCheckpoint: newsSummaries.at(-1)?.nextCheckpoint ?? newsStored?.completeThrough,
  };
  await runEvidence.finish(schedulerEvidenceRunStatus(summaries, newsSummaries), {
    marketJobs: summaries.length,
    newsJobs: newsSummaries.length,
  });
  // Digest persistence is a three-statement batch. Reserve it so the persisted
  // payload's total includes its own writes without double charging the raw DB.
  invocationBudget.consume("d1", 3);
  const totalD1Queries = invocationBudget.snapshot().d1Queries;
  const budget = {
    marketExternalSubrequests,
    newsExternalSubrequests: news.externalSubrequests,
    totalExternalSubrequests: invocationBudget.snapshot().externalSubrequests,
    marketD1Queries,
    newsD1Queries: news.d1Queries,
    totalD1Queries,
    externalBudgetCeiling: EXTERNAL_SUBREQUEST_CEILING,
    d1BudgetCeiling: D1_QUERY_CEILING,
    withinBudget: totalD1Queries <= D1_QUERY_CEILING,
    marketCheckpointBootstrapD1Queries: marketBootstrapD1Queries,
  };
  const persistedDigest = { ...digest, plannedJobs: jobs.length, jobPlans,
    maxJobsPerTick: acquisitionConfig.maxJobsPerTick, retryPolicy: acquisitionConfig.retryPolicy,
    gapRetryMinutes: acquisitionConfig.gapRetryMinutes,
    deferredGapRetries: deferredGapRetries.length,
    ...(deferredGapRetries.length > 0 ? {
      nextGapRetryEligibleAt: deferredGapRetries
        .map((retry) => retry.retryEligibleAt).sort()[0],
    } : {}),
    staleAttemptThresholdMinutes: acquisitionConfig.staleAttemptMinutes,
    staleAttempts, supersededStaleAttempts,
    runEvidence: {
      mode: evidenceEnabled ? "active" : "disabled",
      runId, schedulerRevision: SCHEDULER_EVIDENCE_REVISION, supersededStaleRunJobs,
    },
    summaries, news, budget, ...(predictionShadow ? { predictionShadow } : {}) };
  await new D1LatestDigestStore(env.STATE_DB).put(LATEST_DIGEST_KEY, digest.generatedAt, persistedDigest);
  console.log(JSON.stringify({ event: "scheduler_tick_live", ...persistedDigest }));
}

function logicalVariant(instrument: UniverseInstrument, feed: string): string {
  return instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : `stock:${feed}:raw`;
}

export function createWorker(dependencies: ScheduledOrchestrationDependencies = productionDependencies) {
  return {
    async scheduled(controller: ScheduledController, env: RuntimeEnv, ctx: ExecutionContext): Promise<void> {
      ctx.waitUntil(runScheduledTick(controller, env, dependencies));
    },

    async fetch(request: Request, env: RuntimeEnv): Promise<Response> {
      const url = new URL(request.url);

      const firstRecoveryPath = url.pathname === "/control/historical-recovery/nvda/first-chunk";
      const continuationRecoveryPath = url.pathname === "/control/historical-recovery/nvda/next-chunk";
      if (firstRecoveryPath || continuationRecoveryPath) {
        if (!historicalRecoveryEnabled(env)) return json({ error: "not_found" }, 404);
        if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
        if (!await authorizeHistoricalRecovery(request, env)) return json({ error: "unauthorized" }, 401);
        const expectedJobId = request.headers.get("x-orderscope-job-id");
        const suppliedVersion = request.headers.get("x-orderscope-checkpoint-version");
        const suppliedCompleteThrough = request.headers.get("x-orderscope-complete-through");
        const continuationVersion = parseCheckpointVersion(suppliedVersion);
        const expectedVersion = firstRecoveryPath ? NVDA_RECOVERY.checkpointVersion : continuationVersion;
        const expectedCompleteThrough = firstRecoveryPath ? NVDA_RECOVERY.checkpointBefore : suppliedCompleteThrough;
        const continuationHeadersValid = expectedVersion !== undefined
          && expectedVersion >= NVDA_RECOVERY.checkpointVersion + 1
          && expectedCompleteThrough !== null
          && Number.isFinite(Date.parse(expectedCompleteThrough))
          && new Date(Date.parse(expectedCompleteThrough)).toISOString() === expectedCompleteThrough;
        if (request.headers.get("x-orderscope-recovery-id") !== NVDA_RECOVERY.recoveryId
          || !expectedJobId
          || (firstRecoveryPath && expectedJobId !== NVDA_RECOVERY.expectedJobId)
          || (continuationRecoveryPath && !continuationHeadersValid)) {
          return json({ error: "frozen_identity_mismatch" }, 409);
        }
        if (!env.ALPACA_API_KEY || !env.ALPACA_API_SECRET || !("STATE_DB" in env) || !env.STATE_DB) {
          return json({ error: "runtime_binding_unavailable" }, 503);
        }
        if (env.ALPACA_FEED !== "iex" || env.UNIVERSE_PROFILE !== "canary-v0.1"
          || env.WORKER_MODE !== "shadow" || loadNewsAcquisitionRuntimeConfig(env).enabled) {
          return json({ error: "runtime_precondition_mismatch" }, 409);
        }

        const credentials = { keyId: env.ALPACA_API_KEY, secretKey: env.ALPACA_API_SECRET };
        const acquisitionConfig = loadAcquisitionRuntimeConfig(env);
        if (acquisitionConfig.maxBarsPerJob !== NVDA_RECOVERY.maxBars
          || acquisitionConfig.maxPagesPerJob !== 10) {
          return json({ error: "execution_bound_mismatch" }, 409);
        }
        const budget = new InvocationBudget();
        const stateDb = budgetedD1(env.STATE_DB, budget);
        const checkpoints = dependencies.checkpointPort?.(stateDb) ?? new D1CoverageCheckpointPort(stateDb);
        const checkpointBefore = await checkpoints.get(NVDA_RECOVERY.coverageKey);
        if (expectedVersion === undefined || !checkpointBefore
          || checkpointBefore.symbol !== "NVDA"
          || checkpointBefore.interval !== "1Min"
          || checkpointBefore.sessionScope !== "REGULAR"
          || checkpointBefore.logicalDataVariant !== "stock:iex:raw"
          || checkpointBefore.state !== "COMPLETE"
          || checkpointBefore.completeThrough !== expectedCompleteThrough
          || checkpointBefore.version !== expectedVersion
          || checkpointBefore.universeRevision !== NVDA_RECOVERY.universeRevision
          || checkpointBefore.missingRanges.length !== 0) {
          return json({ error: "checkpoint_preflight_mismatch" }, 409);
        }
        const calendar = await dependencies.calendarProvider(credentials, {
          includePremarket: false,
          includeAfterHours: false,
        }).getCalendar(NVDA_RECOVERY.calendarStart, NVDA_RECOVERY.calendarEnd);
        if (calendar.revision !== NVDA_RECOVERY.calendarRevision) {
          return json({ error: "calendar_preflight_mismatch" }, 409);
        }

        const recoveryRequest: HistoricalRecoveryRequest = {
          recoveryId: NVDA_RECOVERY.recoveryId,
          providerRevision: NVDA_RECOVERY.providerRevision,
          universeRevision: NVDA_RECOVERY.universeRevision,
          calendarRevision: NVDA_RECOVERY.calendarRevision,
          instrument: { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
          coverageKey: NVDA_RECOVERY.coverageKey,
          sessionScope: "REGULAR",
          logicalDataVariant: "stock:iex:raw",
          mode: "CATCH_UP",
          recoveryRange: { startInclusive: NVDA_RECOVERY.recoveryStart, endExclusive: NVDA_RECOVERY.recoveryEnd },
          checkpointBefore,
          maxBarsPerJob: NVDA_RECOVERY.maxBars,
          createdAt: new Date().toISOString(),
        };
        const plannedJob = planNextHistoricalRecoveryChunk(recoveryRequest, calendar);
        if (!plannedJob) return json({ error: "recovery_complete" }, 409);
        if (plannedJob.jobId !== expectedJobId) return json({ error: "planned_job_mismatch" }, 409);
        const expectedBarCount = (Date.parse(plannedJob.requestedRange.endExclusive)
          - Date.parse(plannedJob.requestedRange.startInclusive)) / 60_000;
        const leases = dependencies.leaseStore?.(stateDb) ?? new D1AcquisitionLeaseStore(stateDb);
        const ownerId = `${expectedJobId}:${crypto.randomUUID()}`;
        const acquired = await leases.acquire(
          NVDA_RECOVERY.coverageKey,
          ownerId,
          new Date().toISOString(),
          5 * 60_000,
        );
        if (!acquired) return json({ error: "recovery_locked" }, 409);
        try {
          const result = await runHistoricalRecoveryChunk(recoveryRequest, calendar, {
            credentials,
            checkpoints,
            bars: dependencies.barStore?.(stateDb) ?? new D1NormalizedBarStore(stateDb),
            feed: "iex",
            maxPages: acquisitionConfig.maxPagesPerJob,
            maxBars: NVDA_RECOVERY.maxBars,
            gapRetryDelayMs: acquisitionConfig.gapRetryMinutes * 60_000,
            providerFetchOptions: { retry: acquisitionConfig.providerRetry },
            now: () => new Date(),
            fetchPage: dependencies.fetchPage,
            budget,
          });
          const checkpointAfter = await checkpoints.get(NVDA_RECOVERY.coverageKey);
          const accepted = result.outcome === "SUCCEEDED"
            && result.summary.jobId === expectedJobId
            && result.summary.inserted + result.summary.matched === expectedBarCount
            && result.summary.conflicts === 0
            && result.summary.rejected === 0
            && result.summary.missing === 0
            && checkpointAfter?.completeThrough === plannedJob.requestedRange.endExclusive
            && checkpointAfter.state === "COMPLETE"
            && checkpointAfter.missingRanges.length === 0
            && checkpointAfter.version === expectedVersion + 1;
          const evidence = {
            recoveryId: NVDA_RECOVERY.recoveryId,
            expectedJobId,
            checkpointBefore: { completeThrough: expectedCompleteThrough, version: expectedVersion },
            requestedRange: plannedJob.requestedRange,
            expectedBarCount,
            result,
            checkpointAfter: checkpointAfter ? {
              completeThrough: checkpointAfter.completeThrough,
              state: checkpointAfter.state,
              missingRanges: checkpointAfter.missingRanges,
              version: checkpointAfter.version,
            } : null,
            budget: budget.snapshot(),
            stoppedAfterOneChunk: true,
          };
          console.log(JSON.stringify({
            event: firstRecoveryPath ? "historical_recovery_first_chunk" : "historical_recovery_next_chunk",
            accepted,
            ...evidence,
          }));
          return json({ accepted, ...evidence }, accepted ? 200 : 409);
        } catch (error) {
          console.error(JSON.stringify({
            event: firstRecoveryPath
              ? "historical_recovery_first_chunk_failed"
              : "historical_recovery_next_chunk_failed",
            recoveryId: NVDA_RECOVERY.recoveryId,
            errorCategory: error instanceof Error ? "execution_error" : "unknown_error",
          }));
          return json({ error: "historical_recovery_failed", recoveryId: NVDA_RECOVERY.recoveryId }, 409);
        } finally {
          await leases.release(NVDA_RECOVERY.coverageKey, ownerId);
        }
      }

      if (url.pathname === "/health") {
        return json({ ok: true, ...currentDigest(env, new Date()) });
      }

      if (url.pathname === "/digest/latest") {
        if ("STATE_DB" in env && env.STATE_DB) {
          const stored = await new D1LatestDigestStore(env.STATE_DB).get(LATEST_DIGEST_KEY);
          if (stored) return json(stored);
        }
        return json({ ...currentDigest(env, new Date()), persisted: false });
      }

      if (url.pathname === "/digest/history") {
        if (!("STATE_DB" in env) || !env.STATE_DB) return json({ error: "state_unavailable" }, 503);
        const rawLimit = url.searchParams.get("limit");
        const limit = rawLimit === null ? DIGEST_HISTORY_DEFAULT_LIMIT : Number(rawLimit);
        if (!Number.isInteger(limit) || limit < 1 || limit > DIGEST_HISTORY_MAX_LIMIT) {
          return json({ error: "invalid_limit", min: 1, max: DIGEST_HISTORY_MAX_LIMIT }, 400);
        }
        const digests = await new D1LatestDigestStore(env.STATE_DB).list(LATEST_DIGEST_KEY, limit);
        return json({ digestKey: LATEST_DIGEST_KEY, count: digests.length, digests });
      }

      return json({ error: "not_found" }, 404);
    },
  } satisfies ExportedHandler<RuntimeEnv>;
}

export default createWorker();
