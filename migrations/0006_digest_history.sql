CREATE TABLE IF NOT EXISTS digest_history (
  digest_key TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (digest_key, generated_at)
);

CREATE INDEX IF NOT EXISTS idx_digest_history_recent
ON digest_history(digest_key, generated_at DESC);
