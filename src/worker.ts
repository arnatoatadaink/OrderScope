import { loadAcquisitionRuntimeConfig } from "./acquisition-config";
import { D1NormalizedBarStore, type NormalizedBarStore } from "./bar-store";
import { AlpacaMarketCalendarProvider, type MarketCalendarProvider } from "./calendar";
import { D1CoverageCheckpointPort, type CoverageCheckpointPort } from "./checkpoint";
import { DIGEST_HISTORY_DEFAULT_LIMIT, DIGEST_HISTORY_MAX_LIMIT, D1LatestDigestStore, LATEST_DIGEST_KEY } from "./digest";
import { executeAcquisitionJob, type AcquisitionExecutionSummary, type AcquisitionExecutorOptions } from "./execution";
import { D1AcquisitionLeaseStore, type AcquisitionLeaseStore } from "./lease";
import { gapRetryEligibility, type DeferredGapRetry } from "./gap-retry";
import { loadPredictionRegistries, type PredictionRegistryBundle } from "./prediction-registry";
import { buildPredictionPremarketUniverse, planPredictionPremarketAcquisition } from "./prediction";
import { coverageKeyFor, SchedulePolicy } from "./schedule";
import { loadUniverseSnapshot, type UniverseInstrument, type UniverseSnapshot } from "./universe";

type PredictionMode = "off" | "shadow";

type Digest = {
  generatedAt: string;
  mode: string;
  status: "shadow" | "ready" | "blocked";
  marketTimezone: string;
  feed: string;
  predictionMode?: PredictionMode;
  predictionTargetProfile?: string;
  notes: string[];
};

// `Env` is generated from wrangler.jsonc. Dashboard secrets and bindings that
// are intentionally provisioned after the first shadow deploy are supplemental.
type ProvisionedBindings = {
  ALPACA_API_KEY?: string;
  ALPACA_API_SECRET?: string;
  STATE_DB?: D1Database;
  BAR_ARCHIVE?: R2Bucket;
};

type RuntimeEnv = Omit<Env, "WORKER_MODE" | "PREDICTION_MODE" | "PREDICTION_TARGET_PROFILE"> & ProvisionedBindings & {
  WORKER_MODE: "shadow" | "live";
  PREDICTION_MODE?: PredictionMode;
  PREDICTION_TARGET_PROFILE?: string;
};

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

function currentDigest(
  env: RuntimeEnv,
  now: Date,
  predictionConfig = predictionRuntimeConfig(env),
): Digest {
  const hasCredentials = Boolean(env.ALPACA_API_KEY && env.ALPACA_API_SECRET);
  const hasState = "STATE_DB" in env && Boolean(env.STATE_DB);
  const hasArchive = "BAR_ARCHIVE" in env && Boolean(env.BAR_ARCHIVE);
  const liveRequested = env.WORKER_MODE === "live";

  return {
    generatedAt: now.toISOString(),
    mode: env.WORKER_MODE ?? "shadow",
    status: liveRequested && hasCredentials && hasState ? "ready" : liveRequested ? "blocked" : "shadow",
    marketTimezone: env.MARKET_TIMEZONE ?? "America/New_York",
    feed: env.ALPACA_FEED ?? "iex",
    ...(env.PREDICTION_MODE !== undefined ? { predictionMode: predictionConfig.mode } : {}),
    ...(predictionConfig.targetProfile ? { predictionTargetProfile: predictionConfig.targetProfile } : {}),
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
    options: { includePremarket: boolean },
  ) => MarketCalendarProvider;
  universe: (profile: string) => UniverseSnapshot;
  predictionRegistries?: (profile: string) => PredictionRegistryBundle;
  predictionUniverse?: () => UniverseSnapshot;
  fetchPage?: AcquisitionExecutorOptions["fetchPage"];
  checkpointPort?: (db: D1Database) => CoverageCheckpointPort;
  leaseStore?: (db: D1Database) => AcquisitionLeaseStore;
  barStore?: (db: D1Database) => NormalizedBarStore;
};

const productionDependencies: ScheduledOrchestrationDependencies = {
  calendarProvider: (credentials, options) => new AlpacaMarketCalendarProvider({ credentials, ...options }),
  universe: (profile) => loadUniverseSnapshot(profile),
  predictionRegistries: (profile) => loadPredictionRegistries(profile),
  predictionUniverse: () => loadUniverseSnapshot("full-v0.1"),
};

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
  const acquisitionConfig = loadAcquisitionRuntimeConfig(env);
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
  }).getCalendar(calendarStart, calendarEnd);
  const checkpoints = dependencies.checkpointPort?.(env.STATE_DB) ?? new D1CoverageCheckpointPort(env.STATE_DB);
  const stored = (await Promise.all(universe.instruments.map((instrument) => {
    const scope = instrument.providerRoute === "alpaca_crypto_bars" ? "ALL_TRADING" : "REGULAR";
    return checkpoints.get(coverageKeyFor(instrument, scope, logicalVariant(instrument, env.ALPACA_FEED)));
  }))).filter((checkpoint) => checkpoint !== undefined);
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
    const predictionStored = (await Promise.all(predictionUniverse.instruments.map((instrument) =>
      checkpoints.get(coverageKeyFor(instrument, "PREMARKET", logicalVariant(instrument, env.ALPACA_FEED))),
    ))).filter((checkpoint) => checkpoint !== undefined);
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
      deferredGapRetries: predictionDeferredGapRetries.length,
      jobPlans: predictionJobs.slice(0, acquisitionConfig.maxJobsPerTick).map((job) => ({
        jobId: job.jobId,
        dueReason: job.dueReason,
        sessionScope: job.sessionScope,
        requestedRange: job.requestedRange,
      })),
    };
  }
  const runnableJobs = jobs.slice(0, acquisitionConfig.maxJobsPerTick);
  const jobPlans = runnableJobs.map((job) => ({
    jobId: job.jobId,
    dueReason: job.dueReason,
    requestedRange: job.requestedRange,
  }));
  // Keep the first live boundary deliberately bounded by reviewed configuration.
  // Failed work is retried by deterministic replanning on the next cron tick.
  const summaries: Array<AcquisitionExecutionSummary
    | { jobId: string; outcome: "FAILED" | "SKIPPED_LOCKED" }> = [];
  const staleBefore = new Date(now.getTime() - acquisitionConfig.staleAttemptMinutes * 60_000).toISOString();
  let supersededStaleAttempts = 0;
  const leases = dependencies.leaseStore?.(env.STATE_DB) ?? new D1AcquisitionLeaseStore(env.STATE_DB);
  for (const job of runnableJobs) {
    const coverageKey = job.checkpointExpectations[0]!.coverageKey;
    const ownerId = `${job.jobId}:${now.toISOString()}`;
    const acquired = await leases.acquire(coverageKey, ownerId, now.toISOString(), 5 * 60_000);
    if (!acquired) {
      summaries.push({ jobId: job.jobId, outcome: "SKIPPED_LOCKED" });
      continue;
    }
    try {
      supersededStaleAttempts += await checkpoints.supersedeStaleAttempts({
        coverageKey, staleBefore, finishedAt: now.toISOString(), replacementJobId: job.jobId,
      });
      summaries.push(await executeAcquisitionJob(job, {
        credentials, calendar, checkpoints,
        bars: dependencies.barStore?.(env.STATE_DB) ?? new D1NormalizedBarStore(env.STATE_DB),
        feed: env.ALPACA_FEED, maxPages: acquisitionConfig.maxPagesPerJob,
        maxBars: acquisitionConfig.maxBarsPerJob,
        gapRetryDelayMs: acquisitionConfig.gapRetryMinutes * 60_000,
        providerFetchOptions: { retry: acquisitionConfig.providerRetry },
        now: () => now,
        fetchPage: dependencies.fetchPage,
      }));
    } catch {
      // Detailed diagnostics are already recorded on the attempt row. Keep the
      // public operational digest compact and free of provider response details.
      summaries.push({ jobId: job.jobId, outcome: "FAILED" });
    } finally {
      await leases.release(coverageKey, ownerId);
    }
  }
  const staleAttempts = await checkpoints.summarizeStaleAttempts(staleBefore);
  const persistedDigest = { ...digest, plannedJobs: jobs.length, jobPlans,
    maxJobsPerTick: acquisitionConfig.maxJobsPerTick, retryPolicy: acquisitionConfig.retryPolicy,
    gapRetryMinutes: acquisitionConfig.gapRetryMinutes,
    deferredGapRetries: deferredGapRetries.length,
    ...(deferredGapRetries.length > 0 ? {
      nextGapRetryEligibleAt: deferredGapRetries
        .map((retry) => retry.retryEligibleAt).sort()[0],
    } : {}),
    staleAttemptThresholdMinutes: acquisitionConfig.staleAttemptMinutes,
    staleAttempts, supersededStaleAttempts, summaries,
    ...(predictionShadow ? { predictionShadow } : {}) };
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
