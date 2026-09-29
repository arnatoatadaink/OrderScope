import assert from "node:assert/strict";
import test from "node:test";
import { executeAcquisitionJob } from "./execution.ts";
import { executeNewsAcquisition, type NewsCheckpointPort, type StoredNewsCheckpoint } from "./news-execution.ts";
import { InvocationBudget } from "./invocation-budget.ts";
import type { AcquisitionJob } from "./schedule.ts";
import { NEWS_COVERAGE_KEY, type NewsAcquisitionJob } from "./news-schedule.ts";
import type { NewsAcceptCommand, NewsStore } from "./news-store.ts";
import type { NewsMetadata } from "./news.ts";

const calendar = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-09-10", endExclusive: "2026-09-11" },
  generatedAt: "2026-09-10T14:00:00Z",
  revision: "packet-b-calendar-v1",
  sessions: [{
    marketDate: "2026-09-10",
    sessionKind: "REGULAR" as const,
    opensAt: "2026-09-10T13:30:00.000Z",
    closesAt: "2026-09-10T20:00:00.000Z",
    isShortened: false,
    calendarRevision: "packet-b-calendar-v1",
  }],
};

const marketJob: AcquisitionJob = {
  jobId: "packet-b-market-job",
  jobKind: "MARKET_BARS",
  createdAt: "2026-09-10T14:00:00Z",
  universeRevision: "packet-b-universe-v1",
  calendarRevision: "packet-b-calendar-v1",
  instruments: [{ symbol: "SPY", cadence: "1Min", providerRoute: "alpaca_stock_bars" }],
  interval: "1Min",
  requestedRange: { startInclusive: "2026-09-10T13:58:00.000Z", endExclusive: "2026-09-10T13:59:00.000Z" },
  sessionScope: "REGULAR",
  mode: "CATCH_UP",
  providerRoute: "alpaca_stock_bars",
  checkpointExpectations: [{ coverageKey: "SPY|1Min|REGULAR|stock:iex:raw" }],
  attempt: 0,
  dueReason: "NO_CHECKPOINT",
};

const newsJob: NewsAcquisitionJob = {
  jobId: "packet-b-news-job",
  jobKind: "NEWS_METADATA",
  createdAt: "2026-09-10T14:00:00Z",
  symbols: ["AMD", "NVDA"],
  requestedRange: { startInclusive: "2026-09-10T13:45:00Z", endExclusive: "2026-09-10T14:00:00Z" },
  mode: "CATCH_UP",
  checkpointExpectations: [{ coverageKey: NEWS_COVERAGE_KEY }],
  maxPagesPerSymbol: 1,
  maxArticlesPerRun: 10,
  dueReason: "NO_CHECKPOINT",
};

const article: NewsMetadata = {
  provider: "alpaca",
  providerArticleId: "packet-b-article-1",
  headline: "AMD and NVDA fixture update",
  publisher: "fixture",
  url: "https://example.test/packet-b-article-1",
  providerPublishedAt: "2026-09-10T13:59:00Z",
  providerSymbols: ["AMD", "NVDA"],
};

const retry = { maxAttempts: 1, baseBackoffMs: 0, maxBackoffMs: 0, maxRetryAfterMs: 0 };

class MarketCheckpoints {
  proposed?: Record<string, unknown>;
  attempts: Array<Record<string, unknown>> = [];
  async recordAttempt(value: Record<string, unknown>) { this.attempts.push(value); }
  async get() { return undefined; }
  async compareAndSet(_expectedVersion: number | undefined, proposed: Record<string, unknown>) {
    this.proposed = proposed;
    return { outcome: "UPDATED" as const, checkpoint: proposed };
  }
}

class NewsCheckpoints implements NewsCheckpointPort {
  value?: StoredNewsCheckpoint;
  calls = 0;
  async get() { return this.value; }
  async compareAndSet(_expectedVersion: number | undefined, value: StoredNewsCheckpoint) {
    this.calls += 1;
    this.value = value;
    return "UPDATED" as const;
  }
}

class ConflictingNewsCheckpoints implements NewsCheckpointPort {
  readonly value: StoredNewsCheckpoint;
  calls = 0;
  constructor(value: StoredNewsCheckpoint) { this.value = value; }
  async get() { return this.value; }
  async compareAndSet() {
    this.calls += 1;
    return "VERSION_CONFLICT" as const;
  }
}

class MemoryNewsStore implements NewsStore {
  identities = new Map<string, { identity: string; members: Set<string> }>();
  commands: NewsAcceptCommand[] = [];
  async acceptBatch(commands: readonly NewsAcceptCommand[]) {
    return commands.map((command) => {
      this.commands.push(command);
      const key = command.article.providerArticleId;
      const identity = JSON.stringify(command.article);
      const found = this.identities.get(key);
      if (!found) {
        this.identities.set(key, { identity, members: new Set([command.querySymbol]) });
        return { outcome: "NEW" as const };
      }
      found.members.add(command.querySymbol);
      if (found.identity === identity) return { outcome: "SAME" as const };
      found.identity = identity;
      return { outcome: "UPDATED" as const };
    });
  }
}

function marketSource() {
  return {
    symbol: "SPY",
    timestamp: "2026-09-10T13:58:00Z",
    open: 100,
    high: 101,
    low: 99,
    close: 100,
    volume: 10,
    provider: "alpaca" as const,
    dataVariant: "stock:iex:raw",
  };
}

test("Market and News share one external-call budget and News fails closed at the remaining limit", async () => {
  const budget = new InvocationBudget(2, 100);
  const marketCheckpoints = new MarketCheckpoints();
  const market = await executeAcquisitionJob(marketJob, {
    credentials: { keyId: "k", secretKey: "s" },
    calendar,
    checkpoints: marketCheckpoints as never,
    bars: {
      accept: async (candidate, provenance) => ({
        identity: candidate.outcome === "NORMALIZED" ? candidate.bar.barStartUtc : undefined,
        outcome: "INSERTED" as const,
        acceptanceReceipt: provenance.idempotencyKey,
        provenanceAppended: true,
      }),
    },
    feed: "iex",
    maxPages: 1,
    maxBars: 10,
    budget,
    now: () => new Date("2026-09-10T14:00:00Z"),
    fetchPage: async () => ({ bars: [marketSource()] }),
  });
  assert.equal(market.outcome, "SUCCEEDED");
  assert.equal(budget.snapshot().externalSubrequests, 1);

  const newsCheckpoints = new NewsCheckpoints();
  newsCheckpoints.value = {
    coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:40:00Z",
    state: "COMPLETE",
    lastAttemptAt: "2026-09-10T13:40:00Z",
    version: 7,
  };
  let newsProviderCalls = 0;
  const news = await executeNewsAcquisition(newsJob, {
    credentials: { keyId: "k", secretKey: "s" },
    store: new MemoryNewsStore(),
    checkpoints: newsCheckpoints,
    retry,
    budget,
    fetchPage: async () => {
      newsProviderCalls += 1;
      return { articles: [] };
    },
  });

  assert.equal(news.outcome, "PARTIAL");
  assert.equal(news.errorCategory, "EXTERNAL_BUDGET");
  assert.equal(newsProviderCalls, 1);
  assert.equal(budget.snapshot().externalSubrequests, 2);
  assert.equal(newsCheckpoints.value.completeThrough, "2026-09-10T13:40:00Z");
});

test("News checkpoint CAS conflict stays partial and never overwrites current checkpoint truth", async () => {
  const current: StoredNewsCheckpoint = {
    coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:55:00Z",
    state: "COMPLETE",
    lastAttemptAt: "2026-09-10T13:55:00Z",
    lastSuccessAt: "2026-09-10T13:55:00Z",
    version: 3,
  };
  const checkpoints = new ConflictingNewsCheckpoints(current);
  const result = await executeNewsAcquisition(newsJob, {
    credentials: { keyId: "k", secretKey: "s" },
    store: new MemoryNewsStore(),
    checkpoints,
    retry,
    fetchPage: async () => ({ articles: [] }),
  });

  assert.equal(result.outcome, "PARTIAL");
  assert.equal(result.errorCategory, "CHECKPOINT_CONFLICT");
  assert.equal(result.nextCheckpoint, current.completeThrough);
  assert.equal(checkpoints.value, current);
  assert.equal(checkpoints.calls, 2);
});

test("retrying overlapping News metadata preserves one canonical article and separate symbol membership", async () => {
  const store = new MemoryNewsStore();
  const checkpoints = new NewsCheckpoints();
  const first = await executeNewsAcquisition(newsJob, {
    credentials: { keyId: "k", secretKey: "s" },
    store,
    checkpoints,
    retry,
    fetchPage: async () => ({ articles: [article] }),
  });
  assert.equal(first.outcome, "SUCCEEDED");
  assert.equal(first.newArticles, 1);
  assert.equal(first.duplicates, 1);
  assert.equal(store.identities.size, 1);
  assert.deepEqual([...store.identities.get(article.providerArticleId)!.members].sort(), ["AMD", "NVDA"]);

  const retryJob: NewsAcquisitionJob = {
    ...newsJob,
    jobId: "packet-b-news-job-retry",
    createdAt: "2026-09-10T14:05:00Z",
    requestedRange: { startInclusive: "2026-09-10T13:50:00Z", endExclusive: "2026-09-10T14:05:00Z" },
    dueReason: "CADENCE",
  };
  const second = await executeNewsAcquisition(retryJob, {
    credentials: { keyId: "k", secretKey: "s" },
    store,
    checkpoints,
    retry,
    fetchPage: async () => ({ articles: [article] }),
  });

  assert.equal(second.outcome, "SUCCEEDED");
  assert.equal(second.newArticles, 0);
  assert.equal(second.duplicates, 2);
  assert.equal(store.identities.size, 1);
  assert.deepEqual([...store.identities.get(article.providerArticleId)!.members].sort(), ["AMD", "NVDA"]);
  assert.equal(checkpoints.value?.completeThrough, "2026-09-10T14:05:00Z");
});

test("budget preflight never increments D1 usage past the configured ceiling", () => {
  const budget = new InvocationBudget(40, 40);
  budget.consume("d1", 38);
  assert.throws(() => budget.consume("d1", 3), /D1_BUDGET/);
  assert.deepEqual(budget.snapshot(), { externalSubrequests: 0, d1Queries: 38 });
  budget.consume("d1", 2);
  assert.deepEqual(budget.snapshot(), { externalSubrequests: 0, d1Queries: 40 });
  assert.throws(() => budget.consume("d1"), /D1_BUDGET/);
  assert.equal(budget.snapshot().d1Queries, 40);
});
