CREATE TABLE IF NOT EXISTS news_article (
  provider TEXT NOT NULL,
  provider_article_id TEXT NOT NULL,
  headline TEXT NOT NULL,
  publisher TEXT NOT NULL,
  url TEXT NOT NULL,
  provider_published_at TEXT NOT NULL,
  provider_updated_at TEXT,
  provider_symbols_json TEXT NOT NULL,
  content_identity TEXT NOT NULL,
  first_retrieved_at TEXT NOT NULL,
  last_retrieved_at TEXT NOT NULL,
  accepted_at TEXT NOT NULL,
  PRIMARY KEY(provider, provider_article_id)
);
CREATE TABLE IF NOT EXISTS news_query_membership (
  provider TEXT NOT NULL,
  provider_article_id TEXT NOT NULL,
  query_symbol TEXT NOT NULL CHECK (query_symbol IN ('AMD','NVDA')),
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  PRIMARY KEY(provider, provider_article_id, query_symbol),
  FOREIGN KEY(provider, provider_article_id) REFERENCES news_article(provider, provider_article_id)
);
CREATE TABLE IF NOT EXISTS news_checkpoint (
  coverage_key TEXT PRIMARY KEY,
  complete_through TEXT,
  state TEXT NOT NULL CHECK (state IN ('IN_PROGRESS','PARTIAL','RETRYABLE_FAILURE','COMPLETE')),
  last_attempt_at TEXT NOT NULL,
  last_success_at TEXT,
  retry_not_before TEXT,
  diagnostic_json TEXT,
  version INTEGER NOT NULL DEFAULT 0
);
