import type { Cadence } from "./universe";

export type AcquisitionRuntimeConfig = {
  retentionLookbackMs: number;
  overlapMs: Readonly<Record<Cadence, number>>;
  finalizationLagMs: Readonly<Record<Cadence, number>>;
  maxJobsPerTick: number;
  maxPagesPerJob: number;
  maxBarsPerJob: number;
  staleAttemptMinutes: number;
  gapRetryMinutes: number;
  providerRetry: {
    maxAttempts: number;
    baseBackoffMs: number;
    maxBackoffMs: number;
    maxRetryAfterMs: number;
  };
  retryPolicy: "NEXT_CRON";
};

export type AcquisitionConfigEnv = {
  ACQUISITION_RETENTION_MINUTES: string;
  ACQUISITION_OVERLAP_1MIN_MINUTES: string;
  ACQUISITION_OVERLAP_15MIN_MINUTES: string;
  ACQUISITION_OVERLAP_1DAY_MINUTES: string;
  ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES: string;
  ACQUISITION_FINALIZATION_LAG_15MIN_MINUTES: string;
  ACQUISITION_FINALIZATION_LAG_1DAY_MINUTES: string;
  ACQUISITION_MAX_JOBS_PER_TICK: string;
  ACQUISITION_MAX_PAGES_PER_JOB: string;
  ACQUISITION_MAX_BARS_PER_JOB: string;
  ACQUISITION_STALE_ATTEMPT_MINUTES: string;
  ACQUISITION_GAP_RETRY_MINUTES: string;
  ACQUISITION_PROVIDER_MAX_ATTEMPTS: string;
  ACQUISITION_PROVIDER_BASE_BACKOFF_MS: string;
  ACQUISITION_PROVIDER_MAX_BACKOFF_MS: string;
  ACQUISITION_PROVIDER_MAX_RETRY_AFTER_MS: string;
  ACQUISITION_RETRY_POLICY: string;
};

const MINUTE_MS = 60_000;
const MAX_MINUTES = 365 * 24 * 60;
// D1NormalizedBarStore currently uses at most six D1 operations per observed bar
// (including the conflict path). Keep enough headroom below Workers' 1,000
// subrequest limit for leases, attempts, checkpoints, digests, and retries.
export const MAX_BARS_WITHIN_D1_OPERATION_BUDGET = 150;

function integer(value: string, name: string, minimum: number, maximum: number): number {
  if (!/^(0|[1-9]\d*)$/.test(value)) throw new Error(`${name} must be a base-10 integer`);
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new Error(`${name} must be between ${minimum} and ${maximum}`);
  }
  return parsed;
}

function minutes(value: string, name: string, minimum: number): number {
  return integer(value, name, minimum, MAX_MINUTES) * MINUTE_MS;
}

export function loadAcquisitionRuntimeConfig(env: AcquisitionConfigEnv): AcquisitionRuntimeConfig {
  if (env.ACQUISITION_RETRY_POLICY !== "NEXT_CRON") {
    throw new Error("ACQUISITION_RETRY_POLICY must be NEXT_CRON");
  }
  const baseBackoffMs = integer(env.ACQUISITION_PROVIDER_BASE_BACKOFF_MS, "ACQUISITION_PROVIDER_BASE_BACKOFF_MS", 0, 5_000);
  const maxBackoffMs = integer(env.ACQUISITION_PROVIDER_MAX_BACKOFF_MS, "ACQUISITION_PROVIDER_MAX_BACKOFF_MS", 0, 10_000);
  if (maxBackoffMs < baseBackoffMs) throw new Error("ACQUISITION_PROVIDER_MAX_BACKOFF_MS must be at least ACQUISITION_PROVIDER_BASE_BACKOFF_MS");
  return {
    retentionLookbackMs: minutes(env.ACQUISITION_RETENTION_MINUTES, "ACQUISITION_RETENTION_MINUTES", 1),
    overlapMs: {
      "1Min": minutes(env.ACQUISITION_OVERLAP_1MIN_MINUTES, "ACQUISITION_OVERLAP_1MIN_MINUTES", 1),
      "15Min": minutes(env.ACQUISITION_OVERLAP_15MIN_MINUTES, "ACQUISITION_OVERLAP_15MIN_MINUTES", 15),
      "1Day": minutes(env.ACQUISITION_OVERLAP_1DAY_MINUTES, "ACQUISITION_OVERLAP_1DAY_MINUTES", 1_440),
    },
    finalizationLagMs: {
      "1Min": minutes(env.ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES, "ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES", 0),
      "15Min": minutes(env.ACQUISITION_FINALIZATION_LAG_15MIN_MINUTES, "ACQUISITION_FINALIZATION_LAG_15MIN_MINUTES", 0),
      "1Day": minutes(env.ACQUISITION_FINALIZATION_LAG_1DAY_MINUTES, "ACQUISITION_FINALIZATION_LAG_1DAY_MINUTES", 0),
    },
    maxJobsPerTick: integer(env.ACQUISITION_MAX_JOBS_PER_TICK, "ACQUISITION_MAX_JOBS_PER_TICK", 1, 100),
    maxPagesPerJob: integer(env.ACQUISITION_MAX_PAGES_PER_JOB, "ACQUISITION_MAX_PAGES_PER_JOB", 1, 100),
    maxBarsPerJob: integer(env.ACQUISITION_MAX_BARS_PER_JOB, "ACQUISITION_MAX_BARS_PER_JOB", 1,
      MAX_BARS_WITHIN_D1_OPERATION_BUDGET),
    staleAttemptMinutes: integer(env.ACQUISITION_STALE_ATTEMPT_MINUTES, "ACQUISITION_STALE_ATTEMPT_MINUTES", 5, 10_080),
    gapRetryMinutes: integer(env.ACQUISITION_GAP_RETRY_MINUTES, "ACQUISITION_GAP_RETRY_MINUTES", 2, 10_080),
    providerRetry: {
      maxAttempts: integer(env.ACQUISITION_PROVIDER_MAX_ATTEMPTS, "ACQUISITION_PROVIDER_MAX_ATTEMPTS", 1, 5),
      baseBackoffMs,
      maxBackoffMs,
      maxRetryAfterMs: integer(env.ACQUISITION_PROVIDER_MAX_RETRY_AFTER_MS, "ACQUISITION_PROVIDER_MAX_RETRY_AFTER_MS", 0, 10_000),
    },
    retryPolicy: "NEXT_CRON",
  };
}
