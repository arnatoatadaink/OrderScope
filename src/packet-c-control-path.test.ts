import assert from "node:assert/strict";
import test from "node:test";
import { executeNewsAcquisition, type NewsCheckpointPort, type StoredNewsCheckpoint } from "./news-execution.ts";
import { NewsProviderError, type NewsMetadata } from "./news.ts";
import { NEWS_COVERAGE_KEY, type NewsAcquisitionJob } from "./news-schedule.ts";
import type { NewsStore } from "./news-store.ts";

const job: NewsAcquisitionJob = {
  jobId: "packet-c-news-job",
  jobKind: "NEWS_METADATA",
  createdAt: "2026-09-12T00:00:00Z",
  symbols: ["AMD", "NVDA"],
  requestedRange: { startInclusive: "2026-09-11T23:45:00Z", endExclusive: "2026-09-12T00:00:00Z" },
  mode: "CATCH_UP",
  checkpointExpectations: [{ coverageKey: NEWS_COVERAGE_KEY }],
  maxPagesPerSymbol: 1,
  maxArticlesPerRun: 10,
  dueReason: "CADENCE",
};

const article: NewsMetadata = {
  provider: "alpaca",
  providerArticleId: "packet-c-1",
  headline: "fixture",
  publisher: "fixture",
  url: "https://example.test/packet-c-1",
  providerPublishedAt: "2026-09-11T23:59:00Z",
  providerSymbols: ["AMD", "NVDA"],
};

const retry = { maxAttempts: 1, baseBackoffMs: 0, maxBackoffMs: 0, maxRetryAfterMs: 0 };

class ExistingCheckpoint implements NewsCheckpointPort {
  value: StoredNewsCheckpoint = {
    coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-11T23:40:00Z",
    state: "COMPLETE",
    lastAttemptAt: "2026-09-11T23:40:00Z",
    lastSuccessAt: "2026-09-11T23:40:00Z",
    version: 4,
  };
  writes: StoredNewsCheckpoint[] = [];
  async get() { return this.value; }
  async compareAndSet(_expected: number | undefined, next: StoredNewsCheckpoint) {
    this.writes.push(next);
    this.value = next;
    return "UPDATED" as const;
  }
}

class EmptyStore implements NewsStore {
  async acceptBatch() { return []; }
}

test("checkpoint read failure is classified, sanitized, and prevents provider execution", async () => {
  let providerCalls = 0;
  const checkpoints: NewsCheckpointPort = {
    async get() { throw new Error("socket failure with secret-token and raw body"); },
    async compareAndSet() { throw new Error("must not write after failed checkpoint read"); },
  };
  const result = await executeNewsAcquisition(job, {
    credentials: { keyId: "credential-key", secretKey: "credential-secret" },
    checkpoints,
    store: new EmptyStore(),
    retry,
    fetchPage: async () => { providerCalls += 1; return { articles: [] }; },
  });
  assert.equal(result.outcome, "FAILED");
  assert.equal(result.errorCategory, "D1_CONTROL_READ");
  assert.equal(result.nextCheckpoint, undefined);
  assert.equal(providerCalls, 0);
  assert.equal(JSON.stringify(result).includes("secret-token"), false);
  assert.equal(JSON.stringify(result).includes("credential-secret"), false);
});

test("News store failure keeps prior coverage and records only a sanitized category", async () => {
  const checkpoints = new ExistingCheckpoint();
  const store: NewsStore = {
    async acceptBatch() { throw new Error("sqlite provider response secret body"); },
  };
  const result = await executeNewsAcquisition(job, {
    credentials: { keyId: "k", secretKey: "s" },
    checkpoints,
    store,
    retry,
    now: () => new Date("2026-09-12T00:00:01Z"),
    fetchPage: async () => ({ articles: [article] }),
  });
  assert.equal(result.outcome, "FAILED");
  assert.equal(result.errorCategory, "NEWS_STORE_FAILURE");
  assert.equal(result.nextCheckpoint, "2026-09-11T23:40:00Z");
  assert.equal(checkpoints.value.completeThrough, "2026-09-11T23:40:00Z");
  assert.equal(checkpoints.value.state, "RETRYABLE_FAILURE");
  assert.equal(checkpoints.value.diagnostic?.category, "NEWS_STORE_FAILURE");
  assert.equal(JSON.stringify(checkpoints.value).includes("secret body"), false);
});

test("checkpoint write failure never reports newly completed coverage", async () => {
  const current: StoredNewsCheckpoint = {
    coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-11T23:40:00Z",
    state: "COMPLETE",
    lastAttemptAt: "2026-09-11T23:40:00Z",
    lastSuccessAt: "2026-09-11T23:40:00Z",
    version: 2,
  };
  let writes = 0;
  const checkpoints: NewsCheckpointPort = {
    async get() { return current; },
    async compareAndSet() { writes += 1; throw new Error("D1 socket unavailable secret-detail"); },
  };
  const result = await executeNewsAcquisition(job, {
    credentials: { keyId: "k", secretKey: "s" },
    checkpoints,
    store: new EmptyStore(),
    retry,
    fetchPage: async () => ({ articles: [] }),
  });
  assert.equal(result.outcome, "FAILED");
  assert.equal(result.errorCategory, "D1_CONTROL_WRITE");
  assert.equal(result.nextCheckpoint, current.completeThrough);
  assert.equal(writes, 1);
  assert.equal(JSON.stringify(result).includes("secret-detail"), false);
});

test("authentication failure remains provider-classified and does not advance coverage", async () => {
  const checkpoints = new ExistingCheckpoint();
  const result = await executeNewsAcquisition(job, {
    credentials: { keyId: "credential-key", secretKey: "credential-secret" },
    checkpoints,
    store: new EmptyStore(),
    retry,
    fetchPage: async () => { throw new NewsProviderError("AUTHENTICATION", false); },
  });
  assert.equal(result.outcome, "PARTIAL");
  assert.equal(result.errorCategory, "AUTHENTICATION");
  assert.equal(result.nextCheckpoint, "2026-09-11T23:40:00Z");
  assert.equal(checkpoints.value.completeThrough, "2026-09-11T23:40:00Z");
  assert.equal(JSON.stringify(checkpoints.value).includes("credential-secret"), false);
});
