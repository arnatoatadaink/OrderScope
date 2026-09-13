CREATE TABLE IF NOT EXISTS scheduler_run (
  run_id TEXT PRIMARY KEY,
  scheduled_at TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('RUNNING','SUCCEEDED','PARTIAL','FAILED','SUPERSEDED')),
  scheduler_revision TEXT NOT NULL,
  worker_mode TEXT NOT NULL,
  diagnostic_json TEXT
);

CREATE TABLE IF NOT EXISTS scheduler_run_job (
  run_id TEXT NOT NULL,
  job_id TEXT NOT NULL,
  job_kind TEXT NOT NULL,
  source TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('RUNNING','SUCCEEDED','PARTIAL','FAILED','SKIPPED_LOCKED','SUPERSEDED')),
  boundary_start TEXT,
  boundary_end TEXT,
  retry_of_job_id TEXT,
  failure_category TEXT,
  diagnostic_json TEXT,
  PRIMARY KEY(run_id, job_id),
  FOREIGN KEY(run_id) REFERENCES scheduler_run(run_id)
);

CREATE INDEX IF NOT EXISTS idx_scheduler_run_started_at ON scheduler_run(started_at);
CREATE INDEX IF NOT EXISTS idx_scheduler_run_job_status ON scheduler_run_job(status, started_at);
