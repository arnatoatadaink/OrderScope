import assert from "node:assert/strict";
import test from "node:test";
import { loadAcquisitionRuntimeConfig, type AcquisitionConfigEnv } from "./acquisition-config.ts";

const valid: AcquisitionConfigEnv = {
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
};

test("loads the reviewed acquisition policy from Worker variables", () => {
  assert.deepEqual(loadAcquisitionRuntimeConfig(valid), {
    retentionLookbackMs: 86_400_000,
    overlapMs: { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 },
    finalizationLagMs: { "1Min": 60_000, "15Min": 120_000, "1Day": 1_800_000 },
    maxJobsPerTick: 1,
    maxPagesPerJob: 10,
    maxBarsPerJob: 100,
    staleAttemptMinutes: 15,
    gapRetryMinutes: 15,
    providerRetry: { maxAttempts: 3, baseBackoffMs: 250, maxBackoffMs: 2000, maxRetryAfterMs: 5000 },
    retryPolicy: "NEXT_CRON",
  });
});

test("rejects malformed, unsafe, or sub-interval policy values", () => {
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_RETENTION_MINUTES: "24h" }), /base-10 integer/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_OVERLAP_15MIN_MINUTES: "14" }), /between 15/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_MAX_JOBS_PER_TICK: "0" }), /between 1/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_MAX_PAGES_PER_JOB: "101" }), /between 1 and 100/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_MAX_BARS_PER_JOB: "151" }), /between 1 and 150/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_STALE_ATTEMPT_MINUTES: "4" }), /between 5/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_GAP_RETRY_MINUTES: "1" }), /between 2/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_PROVIDER_MAX_ATTEMPTS: "6" }), /between 1 and 5/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_PROVIDER_BASE_BACKOFF_MS: "3000", ACQUISITION_PROVIDER_MAX_BACKOFF_MS: "2000" }), /must be at least/);
  assert.throws(() => loadAcquisitionRuntimeConfig({ ...valid, ACQUISITION_RETRY_POLICY: "IMMEDIATE" }), /NEXT_CRON/);
});
