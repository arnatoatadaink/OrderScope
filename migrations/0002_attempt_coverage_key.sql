ALTER TABLE acquisition_attempt ADD COLUMN coverage_key TEXT;

CREATE INDEX IF NOT EXISTS idx_attempt_coverage_started
ON acquisition_attempt(coverage_key, started_at);
