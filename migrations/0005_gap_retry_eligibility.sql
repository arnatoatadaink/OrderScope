ALTER TABLE coverage_checkpoint ADD COLUMN retry_not_before TEXT;

CREATE INDEX IF NOT EXISTS idx_checkpoint_retry_not_before
ON coverage_checkpoint(retry_not_before);
