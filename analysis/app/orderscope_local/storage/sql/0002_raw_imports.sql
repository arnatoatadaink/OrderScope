CREATE TABLE raw_imports (
    manifest_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    source_environment TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    table_name TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    sha256 TEXT NOT NULL UNIQUE CHECK (length(sha256) = 64),
    raw_relative_path TEXT NOT NULL UNIQUE,
    registered_at TEXT NOT NULL
) STRICT;
