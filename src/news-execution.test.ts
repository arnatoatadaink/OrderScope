import assert from "node:assert/strict";
import test from "node:test";
import { executeNewsAcquisition, type NewsCheckpointPort, type StoredNewsCheckpoint } from "./news-execution.ts";
import { NewsProviderError, type NewsMetadata } from "./news.ts";
import { NEWS_COVERAGE_KEY, type NewsAcquisitionJob } from "./news-schedule.ts";
import type { NewsAcceptCommand, NewsStore } from "./news-store.ts";
import { InvocationBudget } from "./invocation-budget.ts";

const job: NewsAcquisitionJob = { jobId: "news:test", jobKind: "NEWS_METADATA", createdAt: "2026-09-10T14:00:00Z",
  symbols: ["AMD", "NVDA"], requestedRange: { startInclusive: "2026-09-10T13:45:00Z", endExclusive: "2026-09-10T14:00:00Z" },
  mode: "CATCH_UP", checkpointExpectations: [{ coverageKey: NEWS_COVERAGE_KEY }], maxPagesPerSymbol: 2,
  maxArticlesPerRun: 10, dueReason: "NO_CHECKPOINT" };
const article: NewsMetadata = { provider: "alpaca", providerArticleId: "123", headline: "h", publisher: "p",
  url: "https://example.test", providerPublishedAt: "2026-09-10T13:50:00Z", providerSymbols: ["AMD", "NVDA"] };
class Checkpoints implements NewsCheckpointPort {
  value?: StoredNewsCheckpoint;
  async get() { return this.value; }
  async compareAndSet(_expected: number | undefined, value: StoredNewsCheckpoint) { this.value = value; return "UPDATED" as const; }
}
class MemoryStore implements NewsStore {
  identities = new Map<string, { identity: string; members: Set<string> }>();
  commands: NewsAcceptCommand[] = [];
  async acceptBatch(commands: readonly NewsAcceptCommand[]) {
    return commands.map((command) => {
      this.commands.push(command); const key = command.article.providerArticleId;
      const identity = JSON.stringify(command.article); const found = this.identities.get(key);
      if (!found) { this.identities.set(key, { identity, members: new Set([command.querySymbol]) }); return { outcome: "NEW" as const }; }
      found.members.add(command.querySymbol);
      if (found.identity === identity) return { outcome: "SAME" as const };
      found.identity = identity; return { outcome: "UPDATED" as const };
    });
  }
}
const retry = { maxAttempts: 1, baseBackoffMs: 0, maxBackoffMs: 0, maxRetryAfterMs: 0 };

test("multi-page execution deduplicates one provider identity across AMD and NVDA", async () => {
  const store = new MemoryStore(); const checkpoints = new Checkpoints();
  const calls = new Map<string, number>();
  const result = await executeNewsAcquisition(job, { credentials: { keyId: "k", secretKey: "s" }, store, checkpoints, retry,
    now: () => new Date("2026-09-10T14:00:01Z"), fetchPage: async (_credentials, request) => {
      const count = (calls.get(request.symbol) ?? 0) + 1; calls.set(request.symbol, count);
      if (request.symbol === "NVDA" && count === 1) return { articles: [article], nextPageToken: "page-2" };
      return { articles: [article] };
    } });
  assert.equal(result.outcome, "SUCCEEDED"); assert.equal(result.pages, 3);
  assert.equal(store.identities.size, 1); assert.deepEqual([...store.identities.get("123")!.members].sort(), ["AMD", "NVDA"]);
  assert.equal(checkpoints.value?.completeThrough, job.requestedRange.endExclusive);
});
test("page budget produces partial state without advancing completeThrough", async () => {
  const checkpoints = new Checkpoints(); checkpoints.value = { coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:40:00Z", state: "COMPLETE", lastAttemptAt: "2026-09-10T13:40:00Z", version: 2 };
  const result = await executeNewsAcquisition({ ...job, maxPagesPerSymbol: 1 }, { credentials: { keyId: "k", secretKey: "s" },
    store: new MemoryStore(), checkpoints, retry, fetchPage: async () => ({ articles: [], nextPageToken: "more" }) });
  assert.equal(result.outcome, "PARTIAL"); assert.equal(result.errorCategory, "PAGE_LIMIT");
  assert.equal(checkpoints.value.completeThrough, "2026-09-10T13:40:00Z");
});
test("page-token loops terminate fail closed", async () => {
  const checkpoints = new Checkpoints();
  const result = await executeNewsAcquisition(job, { credentials: { keyId: "k", secretKey: "s" }, store: new MemoryStore(),
    checkpoints, retry, fetchPage: async () => ({ articles: [], nextPageToken: "same" }) });
  assert.equal(result.outcome, "PARTIAL"); assert.equal(result.errorCategory, "PAGE_TOKEN_LOOP");
  assert.equal(checkpoints.value?.completeThrough, undefined);
});
test("retryable provider failure is sanitized and preserves checkpoint", async () => {
  const checkpoints = new Checkpoints(); checkpoints.value = { coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:40:00Z", state: "COMPLETE", lastAttemptAt: "2026-09-10T13:40:00Z", version: 1 };
  const result = await executeNewsAcquisition(job, { credentials: { keyId: "credential-key", secretKey: "credential-secret" },
    store: new MemoryStore(), checkpoints, retry, now: () => new Date("2026-09-10T14:00:00Z"),
    fetchPage: async () => { throw new NewsProviderError("RATE_LIMIT", true); } });
  assert.equal(result.outcome, "FAILED"); assert.equal(result.errorCategory, "RATE_LIMIT");
  assert.equal(checkpoints.value.completeThrough, "2026-09-10T13:40:00Z");
  const stored = JSON.stringify(checkpoints.value); assert.equal(stored.includes("credential-key"), false); assert.equal(stored.includes("credential-secret"), false);
});
test("external budget exhaustion is partial and never advances the checkpoint", async () => {
  const checkpoints = new Checkpoints(); checkpoints.value = { coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:40:00Z", state: "COMPLETE", lastAttemptAt: "2026-09-10T13:40:00Z", version: 1 };
  const budget = new InvocationBudget(); budget.consume("external", 39);
  const result = await executeNewsAcquisition(job, { credentials: { keyId: "k", secretKey: "s" },
    store: new MemoryStore(), checkpoints, retry, budget, fetchPage: async () => ({ articles: [] }) });
  assert.equal(result.outcome, "PARTIAL"); assert.equal(result.errorCategory, "EXTERNAL_BUDGET");
  assert.equal(result.externalSubrequests, 1); assert.equal(checkpoints.value.completeThrough, "2026-09-10T13:40:00Z");
});
test("D1 budget prevention fails closed without a false checkpoint advance", async () => {
  const checkpoints = new Checkpoints(); checkpoints.value = { coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:40:00Z", state: "COMPLETE", lastAttemptAt: "2026-09-10T13:40:00Z", version: 1 };
  const budget = new InvocationBudget(); budget.consume("d1", 36);
  const result = await executeNewsAcquisition(job, { credentials: { keyId: "k", secretKey: "s" },
    store: new MemoryStore(), checkpoints, retry, budget, fetchPage: async () => ({ articles: [article] }) });
  assert.equal(result.outcome, "PARTIAL"); assert.equal(result.errorCategory, "D1_BUDGET");
  assert.equal(checkpoints.value.completeThrough, "2026-09-10T13:40:00Z");
});
test("500-class provider failure is retryable and preserves checkpoint", async () => {
  const checkpoints = new Checkpoints();
  const result = await executeNewsAcquisition(job, { credentials: { keyId: "k", secretKey: "s" },
    store: new MemoryStore(), checkpoints, retry,
    fetchPage: async () => { throw new NewsProviderError("PROVIDER_UNAVAILABLE", true); } });
  assert.equal(result.outcome, "FAILED"); assert.equal(result.errorCategory, "PROVIDER_UNAVAILABLE");
  assert.equal(checkpoints.value?.completeThrough, undefined);
});
