import type { AlpacaCredentials, ProviderRetryPolicy } from "./alpaca";
import { fetchNewsPage, NewsProviderError, type NewsPage, type NewsRequest } from "./news.ts";
import type { NewsAcquisitionJob, NewsCheckpoint } from "./news-schedule";
import type { NewsStore } from "./news-store";
import { InvocationBudget } from "./invocation-budget.ts";

export type StoredNewsCheckpoint = NewsCheckpoint & {
  state: "IN_PROGRESS" | "PARTIAL" | "RETRYABLE_FAILURE" | "COMPLETE";
  lastAttemptAt: string; lastSuccessAt?: string; retryNotBefore?: string;
  diagnostic?: Readonly<Record<string, unknown>>;
};
export interface NewsCheckpointPort {
  get(coverageKey: string): Promise<StoredNewsCheckpoint | undefined>;
  compareAndSet(expectedVersion: number | undefined, checkpoint: StoredNewsCheckpoint): Promise<"UPDATED" | "VERSION_CONFLICT">;
}
export class D1NewsCheckpointPort implements NewsCheckpointPort {
  private readonly db: D1Database;
  constructor(db: D1Database) { this.db = db; }
  async get(coverageKey: string): Promise<StoredNewsCheckpoint | undefined> {
    const row = await this.db.prepare("SELECT * FROM news_checkpoint WHERE coverage_key = ?").bind(coverageKey).first<Record<string, unknown>>();
    if (!row) return undefined;
    return { coverageKey, completeThrough: row.complete_through as string | undefined, state: row.state as StoredNewsCheckpoint["state"],
      lastAttemptAt: row.last_attempt_at as string, lastSuccessAt: row.last_success_at as string | undefined,
      retryNotBefore: row.retry_not_before as string | undefined, version: row.version as number,
      diagnostic: row.diagnostic_json ? JSON.parse(row.diagnostic_json as string) : undefined };
  }
  async compareAndSet(expectedVersion: number | undefined, value: StoredNewsCheckpoint): Promise<"UPDATED" | "VERSION_CONFLICT"> {
    const args = [value.coverageKey, value.completeThrough ?? null, value.state, value.lastAttemptAt,
      value.lastSuccessAt ?? null, value.retryNotBefore ?? null, value.diagnostic ? JSON.stringify(value.diagnostic) : null];
    const result = expectedVersion === undefined
      ? await this.db.prepare(`INSERT INTO news_checkpoint (coverage_key, complete_through, state, last_attempt_at,
          last_success_at, retry_not_before, diagnostic_json, version) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
          ON CONFLICT(coverage_key) DO NOTHING`).bind(...args).run()
      : await this.db.prepare(`UPDATE news_checkpoint SET complete_through = ?, state = ?, last_attempt_at = ?,
          last_success_at = ?, retry_not_before = ?, diagnostic_json = ?, version = version + 1
          WHERE coverage_key = ? AND version = ?`).bind(...args.slice(1), value.coverageKey, expectedVersion).run();
    return result.meta.changes === 1 ? "UPDATED" : "VERSION_CONFLICT";
  }
}

export type NewsExecutionSummary = { outcome: "SUCCEEDED" | "PARTIAL" | "FAILED"; pages: number; articlesObserved: number;
  newArticles: number; duplicates: number; updates: number; conflicts: number; externalSubrequests: number;
  d1Queries: number; nextCheckpoint?: string; errorCategory?: string };
export type NewsExecutionOptions = { credentials: AlpacaCredentials; store: NewsStore; checkpoints: NewsCheckpointPort;
  retry: ProviderRetryPolicy; retryDelayMs?: number; now?: () => Date; budget?: InvocationBudget;
  fetchPage?: (credentials: AlpacaCredentials, request: NewsRequest,
    options: { retry: ProviderRetryPolicy; onAttempt?: () => void }) => Promise<NewsPage> };

type ExecutionPhase = "CHECKPOINT_READ" | "PROVIDER_FETCH" | "STORE_ACCEPT" | "CHECKPOINT_WRITE";
type FailureClass = { category: string; retryable: boolean; skipCheckpointWrite: boolean };

function classifyFailure(error: unknown, phase: ExecutionPhase): FailureClass {
  if (error instanceof NewsProviderError) {
    return { category: error.category, retryable: error.retryable, skipCheckpointWrite: false };
  }
  const message = error instanceof Error ? error.message : "UNKNOWN";
  if (message === "D1_BUDGET") return { category: "D1_BUDGET", retryable: false, skipCheckpointWrite: true };
  if (message === "EXTERNAL_BUDGET") return { category: "EXTERNAL_BUDGET", retryable: false, skipCheckpointWrite: false };
  if (message === "PAGE_LIMIT" || message === "ARTICLE_LIMIT" || message === "PAGE_TOKEN_LOOP") {
    return { category: message, retryable: false, skipCheckpointWrite: false };
  }
  if (message === "CHECKPOINT_CONFLICT") {
    return { category: "CHECKPOINT_CONFLICT", retryable: false, skipCheckpointWrite: false };
  }
  if (phase === "CHECKPOINT_READ") {
    return { category: "D1_CONTROL_READ", retryable: true, skipCheckpointWrite: true };
  }
  if (phase === "CHECKPOINT_WRITE") {
    return { category: "D1_CONTROL_WRITE", retryable: true, skipCheckpointWrite: true };
  }
  if (phase === "STORE_ACCEPT") {
    return { category: "NEWS_STORE_FAILURE", retryable: true, skipCheckpointWrite: false };
  }
  return { category: "UNEXPECTED_EXECUTION", retryable: false, skipCheckpointWrite: false };
}

export async function executeNewsAcquisition(job: NewsAcquisitionJob, options: NewsExecutionOptions): Promise<NewsExecutionSummary> {
  const now = options.now ?? (() => new Date()); const fetchPage = options.fetchPage ?? fetchNewsPage;
  const budget = options.budget ?? new InvocationBudget(); const before = budget.snapshot();
  const counts = { pages: 0, articlesObserved: 0, newArticles: 0, duplicates: 0, updates: 0, conflicts: 0 };
  let existing: StoredNewsCheckpoint | undefined;
  let phase: ExecutionPhase = "CHECKPOINT_READ";
  try {
    existing = await options.checkpoints.get(job.checkpointExpectations[0]!.coverageKey);
    for (const symbol of job.symbols) {
      let token: string | undefined; const tokens = new Set<string>(); let pagesForSymbol = 0;
      do {
        if (pagesForSymbol >= job.maxPagesPerSymbol) throw new Error("PAGE_LIMIT");
        if (options.fetchPage) budget.consume("external");
        phase = "PROVIDER_FETCH";
        const page = await fetchPage(options.credentials, { symbol, ...job.requestedRange, pageToken: token, limit: 50 }, {
          retry: { ...options.retry, maxAttempts: Math.min(options.retry.maxAttempts, budget.remaining("external")) },
          ...(!options.fetchPage ? { onAttempt: () => budget.consume("external") } : {}),
        });
        pagesForSymbol += 1; counts.pages += 1;
        if (counts.articlesObserved + page.articles.length > job.maxArticlesPerRun) throw new Error("ARTICLE_LIMIT");
        const commands = page.articles.map((article) => { const observedAt = now().toISOString();
          return { article, querySymbol: symbol, retrievedAt: observedAt, acceptedAt: observedAt }; });
        phase = "STORE_ACCEPT";
        const acceptedBatch = await options.store.acceptBatch(commands);
        for (const accepted of acceptedBatch) {
          counts.articlesObserved += 1;
          counts[accepted.outcome === "NEW" ? "newArticles" : accepted.outcome === "SAME" ? "duplicates"
            : accepted.outcome === "UPDATED" ? "updates" : "conflicts"] += 1;
        }
        token = page.nextPageToken;
        if (token && tokens.has(token)) throw new Error("PAGE_TOKEN_LOOP");
        if (token) tokens.add(token);
      } while (token);
    }
    const finishedAt = now().toISOString();
    const proposed: StoredNewsCheckpoint = { coverageKey: job.checkpointExpectations[0]!.coverageKey,
      completeThrough: job.requestedRange.endExclusive, state: "COMPLETE", lastAttemptAt: finishedAt,
      lastSuccessAt: finishedAt, version: existing?.version ?? 0, diagnostic: counts };
    phase = "CHECKPOINT_WRITE";
    if (await options.checkpoints.compareAndSet(existing?.version, proposed) === "VERSION_CONFLICT") throw new Error("CHECKPOINT_CONFLICT");
    const used = budget.snapshot();
    return { outcome: "SUCCEEDED", ...counts, externalSubrequests: used.externalSubrequests - before.externalSubrequests,
      d1Queries: used.d1Queries - before.d1Queries, nextCheckpoint: proposed.completeThrough };
  } catch (error) {
    const finishedAt = now().toISOString();
    let failure = classifyFailure(error, phase);
    if (!failure.skipCheckpointWrite) {
      const proposed: StoredNewsCheckpoint = { coverageKey: job.checkpointExpectations[0]!.coverageKey,
        completeThrough: existing?.completeThrough, state: failure.retryable ? "RETRYABLE_FAILURE" : "PARTIAL",
        lastAttemptAt: finishedAt, lastSuccessAt: existing?.lastSuccessAt,
        retryNotBefore: failure.retryable ? new Date(Date.parse(finishedAt) + (options.retryDelayMs ?? 300_000)).toISOString() : undefined,
        version: existing?.version ?? 0, diagnostic: { category: failure.category, ...counts } };
      try {
        phase = "CHECKPOINT_WRITE";
        await options.checkpoints.compareAndSet(existing?.version, proposed);
      } catch (checkpointError) {
        failure = classifyFailure(checkpointError, "CHECKPOINT_WRITE");
      }
    }
    const used = budget.snapshot();
    return { outcome: failure.retryable ? "FAILED" : "PARTIAL", ...counts,
      externalSubrequests: used.externalSubrequests - before.externalSubrequests,
      d1Queries: used.d1Queries - before.d1Queries, errorCategory: failure.category,
      nextCheckpoint: existing?.completeThrough };
  }
}
