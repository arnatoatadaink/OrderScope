CREATE TABLE filing_records (
    accession TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL CHECK (length(content_hash) = 64),
    cik TEXT NOT NULL CHECK (length(cik) = 10),
    ticker TEXT NOT NULL,
    form TEXT NOT NULL,
    filed_at TEXT NOT NULL,
    period_end TEXT,
    primary_document_ref TEXT,
    source_ref TEXT NOT NULL,
    retrieved_at TEXT NOT NULL
) STRICT;

CREATE INDEX filing_records_cik_filed_at_idx
    ON filing_records(cik, filed_at, accession);
