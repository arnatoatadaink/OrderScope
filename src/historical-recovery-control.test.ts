import assert from "node:assert/strict";
import test from "node:test";
import { build } from "esbuild";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";

const endpoint = "https://example.test/control/historical-recovery/nvda/first-chunk";
const recoveryId = "L1-003-NVDA-20260916-01";
const jobId = "historical-market-recovery:ef94f87d37bf2746";

// Node's Web Crypto test runtime does not yet expose the Workers-only method.
const testSubtle = crypto.subtle as SubtleCrypto & {
  timingSafeEqual?: (left: ArrayBuffer, right: ArrayBuffer) => boolean;
};
if (!testSubtle.timingSafeEqual) {
  testSubtle.timingSafeEqual = (left, right) => {
    const leftBytes = new Uint8Array(left);
    const rightBytes = new Uint8Array(right);
    if (leftBytes.length !== rightBytes.length) return false;
    let difference = 0;
    for (let index = 0; index < leftBytes.length; index += 1) difference |= leftBytes[index]! ^ rightBytes[index]!;
    return difference === 0;
  };
}

const workerModule = build({
  entryPoints: [new URL("./worker.ts", import.meta.url).pathname],
  bundle: true,
  format: "esm",
  platform: "neutral",
  write: false,
}).then(async (result) => import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0]!.text).toString("base64")}`));

async function createTestWorker(dependencies?: unknown) {
  const module = await workerModule;
  return module.createWorker(dependencies);
}

function runtimeEnv(overrides: Record<string, unknown> = {}) {
  return {
    WORKER_MODE: "shadow", PREDICTION_MODE: "shadow", PREDICTION_TARGET_PROFILE: "semiconductor-canary-v0.1",
    MARKET_TIMEZONE: "America/New_York", DISPLAY_TIMEZONE: "Asia/Tokyo", ALPACA_FEED: "iex",
    UNIVERSE_PROFILE: "canary-v0.1", ACQUISITION_RETENTION_MINUTES: "1440",
    ACQUISITION_OVERLAP_1MIN_MINUTES: "1", ACQUISITION_OVERLAP_15MIN_MINUTES: "15",
    ACQUISITION_OVERLAP_1DAY_MINUTES: "1440", ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES: "1",
    ACQUISITION_FINALIZATION_LAG_15MIN_MINUTES: "2", ACQUISITION_FINALIZATION_LAG_1DAY_MINUTES: "30",
    ACQUISITION_MAX_JOBS_PER_TICK: "2", ACQUISITION_MAX_PAGES_PER_JOB: "10",
    ACQUISITION_MAX_BARS_PER_JOB: "100", ACQUISITION_STALE_ATTEMPT_MINUTES: "15",
    ACQUISITION_GAP_RETRY_MINUTES: "15", ACQUISITION_PROVIDER_MAX_ATTEMPTS: "3",
    ACQUISITION_PROVIDER_BASE_BACKOFF_MS: "0", ACQUISITION_PROVIDER_MAX_BACKOFF_MS: "0",
    ACQUISITION_PROVIDER_MAX_RETRY_AFTER_MS: "0", ACQUISITION_RETRY_POLICY: "NEXT_CRON",
    NEWS_ACQUISITION_ENABLED: "false", NEWS_ACQUISITION_CADENCE_MINUTES: "5",
    NEWS_ACQUISITION_OVERLAP_MINUTES: "15", NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL: "2",
    NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN: "200", NEWS_ACQUISITION_CANARY_SYMBOLS: "AMD,NVDA",
    HISTORICAL_RECOVERY_ENABLED: "true", HISTORICAL_RECOVERY_CONTROL_TOKEN: "control-secret",
    ALPACA_API_KEY: "provider-key", ALPACA_API_SECRET: "provider-secret", STATE_DB: {},
    ...overrides,
  };
}

function invocation(token = "control-secret", expectedRecoveryId = recoveryId, expectedJobId = jobId): Request {
  return new Request(endpoint, { method: "POST", headers: {
    authorization: `Bearer ${token}`,
    "x-orderscope-recovery-id": expectedRecoveryId,
    "x-orderscope-job-id": expectedJobId,
  } });
}

function checkpoint(): StoredCoverageCheckpoint {
  return {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw", symbol: "NVDA", interval: "1Min",
    sessionScope: "REGULAR", logicalDataVariant: "stock:iex:raw", state: "COMPLETE",
    completeThrough: "2026-09-02T20:00:00.000Z", missingRanges: [], version: 6,
    universeRevision: "stock-monitoring-canary-v0.1",
  };
}

function dependencies() {
  let current = checkpoint();
  let providerCalls = 0;
  const sessions = ["02", "03", "04", "08", "09", "10", "11", "14", "15"].map((day) => ({
    marketDate: `2026-09-${day}`, sessionKind: "REGULAR" as const,
    opensAt: `2026-09-${day}T13:30:00.000Z`, closesAt: `2026-09-${day}T20:00:00.000Z`,
    isShortened: false, calendarRevision: "alpaca-calendar-v2:da7d32f3",
  }));
  return {
    state: { get providerCalls() { return providerCalls; }, get checkpoint() { return current; } },
    value: {
      calendarProvider: () => ({ getCalendar: async () => ({
        market: "US_EQUITIES", dateRange: { startInclusive: "2026-09-02", endExclusive: "2026-09-17" },
        generatedAt: "2026-09-16T00:00:00.000Z", revision: "alpaca-calendar-v2:da7d32f3", sessions,
      }) }),
      universe: () => ({ revision: "unused", instruments: [] }),
      checkpointPort: () => ({
        get: async () => current, getMany: async () => [current], listDue: async () => [],
        compareAndSet: async (expectedVersion: number | undefined, proposed: StoredCoverageCheckpoint) => {
          if (expectedVersion !== current.version) return { outcome: "VERSION_CONFLICT" as const };
          current = { ...proposed, version: current.version + 1 };
          return { outcome: "UPDATED" as const, checkpoint: current };
        },
        recordAttempt: async () => {}, summarizeStaleAttempts: async () => ({ count: 0 }),
        supersedeStaleAttempts: async () => 0,
      }),
      leaseStore: () => ({ acquire: async () => true, release: async () => {} }),
      barStore: () => ({ accept: async (_candidate: unknown, provenance: { idempotencyKey: string }) => ({
        outcome: "INSERTED" as const, acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true,
      }) }),
      fetchPage: async (_credentials: unknown, request: { startInclusive: string }) => {
        providerCalls += 1;
        const start = Date.parse(request.startInclusive);
        return { bars: Array.from({ length: 100 }, (_, index) => ({
          symbol: "NVDA", timestamp: new Date(start + index * 60_000).toISOString(),
          open: 100, high: 101, low: 99, close: 100, volume: 10,
          provider: "alpaca" as const, dataVariant: "stock:iex:raw",
        })) };
      },
    },
  };
}

test("one-shot recovery route is hidden while its feature gate is disabled", async () => {
  const worker = await createTestWorker();
  const response = await worker.fetch(invocation(), runtimeEnv({ HISTORICAL_RECOVERY_ENABLED: "false" }) as never, {} as never);
  assert.equal(response.status, 404);
});

test("one-shot recovery route rejects bad authentication and frozen identity before provider work", async () => {
  const fixture = dependencies();
  const worker = await createTestWorker(fixture.value);
  assert.equal((await worker.fetch(invocation("wrong"), runtimeEnv() as never, {} as never)).status, 401);
  assert.equal((await worker.fetch(invocation("control-secret", "wrong"), runtimeEnv() as never, {} as never)).status, 409);
  assert.equal(fixture.state.providerCalls, 0);
});

test("one-shot recovery executes only the frozen first chunk and closes on replay", async () => {
  const fixture = dependencies();
  const worker = await createTestWorker(fixture.value);
  const first = await worker.fetch(invocation(), runtimeEnv() as never, {} as never);
  assert.equal(first.status, 200);
  const evidence = await first.json() as { accepted: boolean; stoppedAfterOneChunk: boolean };
  assert.equal(evidence.accepted, true);
  assert.equal(evidence.stoppedAfterOneChunk, true);
  assert.equal(fixture.state.providerCalls, 1);
  assert.equal(fixture.state.checkpoint.completeThrough, "2026-09-03T15:10:00.000Z");
  assert.equal(fixture.state.checkpoint.version, 7);

  const replay = await worker.fetch(invocation(), runtimeEnv() as never, {} as never);
  assert.equal(replay.status, 409);
  assert.equal(fixture.state.providerCalls, 1);
});
