CREATE TABLE catalog_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
) STRICT;

INSERT INTO catalog_metadata(key, value, updated_at)
VALUES ('schema_kind', 'orderscope-local-metadata', '2026-09-09T00:00:00+00:00');
