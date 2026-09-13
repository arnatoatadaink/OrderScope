PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS normalized_bar (
  identity_key TEXT PRIMARY KEY,
  instrument_id TEXT NOT NULL,
  interval TEXT NOT NULL,
  bar_start_utc TEXT NOT NULL,
  bar_end_utc TEXT NOT NULL,
  market_date TEXT NOT NULL,
  session_kind TEXT NOT NULL,
  is_shortened_session INTEGER NOT NULL CHECK (is_shortened_session IN (0, 1)),
  logical_data_variant TEXT NOT NULL,
  open REAL NOT NULL,
  high REAL NOT NULL,
  low REAL NOT NULL,
  close REAL NOT NULL,
  volume REAL NOT NULL,
  trade_count INTEGER,
  vwap REAL,
  canonical_fingerprint TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  accepted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_normalized_bar_range
ON normalized_bar(instrument_id, interval, logical_data_variant, bar_start_utc);

CREATE TABLE IF NOT EXISTS bar_acceptance_receipt (
  idempotency_key TEXT PRIMARY KEY,
  request_fingerprint TEXT NOT NULL,
  identity_key TEXT,
  outcome TEXT CHECK (outcome IN ('INSERTED', 'MATCHED', 'CONFLICT', 'REJECTED')),
  reason TEXT,
  provider TEXT,
  job_id TEXT,
  source_timestamp TEXT,
  retrieved_at TEXT NOT NULL,
  stored_version INTEGER,
  completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_bar_receipt_identity
ON bar_acceptance_receipt(identity_key, retrieved_at);

CREATE TABLE IF NOT EXISTS bar_conflict (
  idempotency_key TEXT PRIMARY KEY,
  identity_key TEXT NOT NULL,
  stored_fingerprint TEXT NOT NULL,
  observed_fingerprint TEXT NOT NULL,
  observed_content_json TEXT NOT NULL,
  detected_at TEXT NOT NULL,
  FOREIGN KEY(idempotency_key) REFERENCES bar_acceptance_receipt(idempotency_key)
);
