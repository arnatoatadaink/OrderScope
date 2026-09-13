import type { NewsMetadata } from "./news";

export type NewsAcceptance = { outcome: "NEW" | "SAME" | "UPDATED" | "CONFLICT" };
export type NewsAcceptCommand = { article: NewsMetadata; querySymbol: "AMD" | "NVDA"; retrievedAt: string; acceptedAt: string };
export interface NewsStore { acceptBatch(commands: readonly NewsAcceptCommand[]): Promise<readonly NewsAcceptance[]>; }

function identity(article: NewsMetadata): string {
  return JSON.stringify([article.headline, article.publisher, article.url, article.providerPublishedAt,
    article.providerUpdatedAt ?? null, article.providerSymbols]);
}

export class D1NewsStore implements NewsStore {
  private readonly db: D1Database;
  constructor(db: D1Database) { this.db = db; }
  async acceptBatch(commands: readonly NewsAcceptCommand[]): Promise<readonly NewsAcceptance[]> {
    if (commands.length === 0) return [];
    const uniqueIds = [...new Set(commands.map((command) => command.article.providerArticleId))];
    const placeholders = uniqueIds.map(() => "?").join(",");
    const prior = await this.db.prepare(`SELECT provider_article_id, content_identity,
        provider_published_at, provider_updated_at FROM news_article
      WHERE provider = 'alpaca' AND provider_article_id IN (${placeholders})`).bind(...uniqueIds)
      .all<{ provider_article_id: string; content_identity: string; provider_published_at: string;
        provider_updated_at: string | null }>();
    const priorById = new Map(prior.results.map((row) => [row.provider_article_id, row]));
    const outcomes = commands.map((command): NewsAcceptance => {
      const previous = priorById.get(command.article.providerArticleId);
      if (!previous) return { outcome: "NEW" };
      if (previous.content_identity === identity(command.article)) return { outcome: "SAME" };
      const incomingRevision = command.article.providerUpdatedAt;
      const priorRevision = previous.provider_updated_at ?? previous.provider_published_at;
      return { outcome: incomingRevision && Date.parse(incomingRevision) > Date.parse(priorRevision)
        ? "UPDATED" : "CONFLICT" };
    });
    const writable = commands.filter((_command, index) => outcomes[index]!.outcome !== "CONFLICT");
    const articleValues = writable.map(() => "('alpaca', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)").join(",");
    const articleArgs = writable.flatMap((command) => [command.article.providerArticleId, command.article.headline,
      command.article.publisher, command.article.url, command.article.providerPublishedAt,
      command.article.providerUpdatedAt ?? null, JSON.stringify(command.article.providerSymbols), identity(command.article),
      command.retrievedAt, command.retrievedAt, command.acceptedAt]);
    if (writable.length > 0) await this.db.prepare(`INSERT INTO news_article
      (provider, provider_article_id, headline, publisher, url, provider_published_at, provider_updated_at,
       provider_symbols_json, content_identity, first_retrieved_at, last_retrieved_at, accepted_at)
      VALUES ${articleValues} ON CONFLICT(provider, provider_article_id) DO UPDATE SET
       headline=excluded.headline, publisher=excluded.publisher, url=excluded.url,
       provider_published_at=excluded.provider_published_at, provider_updated_at=excluded.provider_updated_at,
       provider_symbols_json=excluded.provider_symbols_json, content_identity=excluded.content_identity,
       last_retrieved_at=excluded.last_retrieved_at, accepted_at=excluded.accepted_at`).bind(...articleArgs).run();
    const membershipValues = commands.map(() => "('alpaca', ?, ?, ?, ?)").join(",");
    const membershipArgs = commands.flatMap((command) => [command.article.providerArticleId, command.querySymbol,
      command.retrievedAt, command.retrievedAt]);
    await this.db.prepare(`INSERT INTO news_query_membership
      (provider, provider_article_id, query_symbol, first_seen_at, last_seen_at) VALUES ${membershipValues}
      ON CONFLICT(provider, provider_article_id, query_symbol) DO UPDATE SET last_seen_at=excluded.last_seen_at`)
      .bind(...membershipArgs).run();
    return outcomes;
  }
}
