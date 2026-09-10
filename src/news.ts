import type { AlpacaCredentials, ProviderRetryPolicy } from "./alpaca";

export type NewsMetadata = {
  provider: "alpaca"; providerArticleId: string; headline: string; publisher: string; url: string;
  providerPublishedAt: string; providerUpdatedAt?: string; providerSymbols: readonly string[];
};
export type NewsPage = { articles: readonly NewsMetadata[]; nextPageToken?: string };
export type NewsRequest = { symbol: "AMD" | "NVDA"; startInclusive: string; endExclusive: string; pageToken?: string; limit?: number };
export type NewsFetchOptions = { retry?: ProviderRetryPolicy; sleep?: (ms: number) => Promise<void>;
  onAttempt?: () => void; now?: () => number };

export class NewsProviderError extends Error {
  readonly category: "RATE_LIMIT" | "PROVIDER_UNAVAILABLE" | "INVALID_RESPONSE";
  readonly retryable: boolean;
  constructor(category: NewsProviderError["category"], retryable: boolean) {
    super(`news provider ${category.toLowerCase()}`);
    this.name = "NewsProviderError"; this.category = category; this.retryable = retryable;
  }
}

function instant(value: unknown): value is string {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}
function text(value: unknown): value is string { return typeof value === "string" && value.trim().length > 0; }
function symbols(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
    throw new NewsProviderError("INVALID_RESPONSE", false);
  }
  return [...new Set(value.map((item) => item.trim().toUpperCase()).filter(Boolean))].sort();
}

export function normalizeNewsPayload(value: unknown): NewsPage {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new NewsProviderError("INVALID_RESPONSE", false);
  const payload = value as Record<string, unknown>;
  const articles = payload.news;
  const token = payload.next_page_token;
  if (!Array.isArray(articles) || (token != null && typeof token !== "string")) throw new NewsProviderError("INVALID_RESPONSE", false);
  return {
    articles: articles.map((item) => {
      if (typeof item !== "object" || item === null || Array.isArray(item)) throw new NewsProviderError("INVALID_RESPONSE", false);
      const article = item as Record<string, unknown>;
      const id = typeof article.id === "number" && Number.isSafeInteger(article.id) ? String(article.id) : article.id;
      if (!text(id) || !text(article.headline) || !text(article.author) || !text(article.url)
        || !instant(article.created_at) || (article.updated_at != null && !instant(article.updated_at))) {
        throw new NewsProviderError("INVALID_RESPONSE", false);
      }
      return {
        provider: "alpaca" as const, providerArticleId: id, headline: article.headline.trim(),
        publisher: article.author.trim(), url: article.url.trim(), providerPublishedAt: article.created_at,
        ...(instant(article.updated_at) ? { providerUpdatedAt: article.updated_at } : {}), providerSymbols: symbols(article.symbols),
      };
    }),
    ...(typeof token === "string" && token ? { nextPageToken: token } : {}),
  };
}

export async function fetchNewsPage(credentials: AlpacaCredentials, request: NewsRequest, options: NewsFetchOptions = {}): Promise<NewsPage> {
  const url = new URL("https://data.alpaca.markets/v1beta1/news");
  url.searchParams.set("symbols", request.symbol); url.searchParams.set("start", request.startInclusive);
  url.searchParams.set("end", request.endExclusive); url.searchParams.set("limit", String(Math.min(request.limit ?? 50, 50)));
  url.searchParams.set("sort", "asc"); url.searchParams.set("include_content", "false");
  if (request.pageToken) url.searchParams.set("page_token", request.pageToken);
  const retry = options.retry; const attempts = retry?.maxAttempts ?? 1;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    options.onAttempt?.();
    const response = await fetch(url, { headers: { "APCA-API-KEY-ID": credentials.keyId, "APCA-API-SECRET-KEY": credentials.secretKey } });
    if (response.ok) return normalizeNewsPayload(await response.json());
    const retryable = response.status === 429 || response.status >= 500;
    if (!retryable || attempt === attempts) throw new NewsProviderError(response.status === 429 ? "RATE_LIMIT" : "PROVIDER_UNAVAILABLE", retryable);
    const header = response.headers.get("retry-after");
    const seconds = header === null ? NaN : Number(header);
    const dateDelay = header === null ? NaN : Date.parse(header) - (options.now ?? Date.now)();
    const requested = Number.isFinite(seconds) && seconds >= 0 ? seconds * 1_000
      : Number.isFinite(dateDelay) ? Math.max(0, dateDelay) : undefined;
    const exponential = Math.min(retry!.baseBackoffMs * 2 ** (attempt - 1), retry!.maxBackoffMs);
    const delay = Math.min(requested ?? exponential, retry!.maxRetryAfterMs);
    await (options.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms))))(delay);
  }
  throw new NewsProviderError("PROVIDER_UNAVAILABLE", true);
}
