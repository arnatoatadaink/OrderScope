PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS coverage_checkpoint (
  coverage_key TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  interval TEXT NOT NULL,
  session_scope TEXT NOT NULL,
  logical_data_variant TEXT NOT NULL,
  complete_through TEXT,
  state TEXT NOT NULL CHECK (state IN ('COMPLETE','PARTIAL','UNKNOWN','BLOCKED')),
  missing_ranges_json TEXT NOT NULL DEFAULT '[]',
  last_success_at TEXT,
  last_attempt_at TEXT,
  source_observed_through TEXT,
  universe_revision TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  blocker_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_checkpoint_due
ON coverage_checkpoint(state, complete_through);

CREATE TABLE IF NOT EXISTS latest_digest (
  digest_key TEXT PRIMARY KEY,
  generated_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS feature_state (
  symbol TEXT NOT NULL,
  interval TEXT NOT NULL,
  session_kind TEXT NOT NULL,
  bucket_key TEXT NOT NULL,
  feature_name TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  value REAL,
  quality TEXT NOT NULL DEFAULT 'OK',
  observed_at TEXT NOT NULL,
  PRIMARY KEY(symbol, interval, session_kind, bucket_key, feature_name, feature_version)
);

CREATE TABLE IF NOT EXISTS acquisition_attempt (
  attempt_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  outcome TEXT,
  diagnostic_json TEXT
);
