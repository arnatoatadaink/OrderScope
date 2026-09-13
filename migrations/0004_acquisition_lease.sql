CREATE TABLE IF NOT EXISTS acquisition_lease (
  coverage_key TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  acquired_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_acquisition_lease_expiry
ON acquisition_lease(expires_at);
