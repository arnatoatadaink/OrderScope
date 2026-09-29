from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.storage.d1_bounded_export import export_sqlite_window
from orderscope_local.storage.d1_custody import build_d1_custody_manifest


START = datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc)


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE normalized_bar (
          identity_key TEXT PRIMARY KEY,
          instrument_id TEXT NOT NULL,
          interval TEXT NOT NULL,
          bar_start_utc TEXT NOT NULL,
          bar_end_utc TEXT NOT NULL,
          market_date TEXT NOT NULL,
          session_kind TEXT NOT NULL,
          is_shortened_session INTEGER NOT NULL,
          logical_data_variant TEXT NOT NULL,
          open REAL NOT NULL,
          high REAL NOT NULL,
          low REAL NOT NULL,
          close REAL NOT NULL,
          volume REAL NOT NULL,
          trade_count INTEGER,
          vwap REAL,
          canonical_fingerprint TEXT NOT NULL,
          version INTEGER NOT NULL,
          accepted_at TEXT NOT NULL
        )
        """
    )
    rows = [
        (
            "bar-b", "NVDA", "1Min", "2026-09-10T00:02:00Z", "2026-09-10T00:03:00Z",
            "2026-09-10", "PRE", 0, "raw", 2.0, 3.0, 1.5, 2.5, 200.0, 20, 2.4,
            "fp-b", 1, "2026-09-10T00:03:05Z",
        ),
        (
            "bar-a", "AMD", "1Min", "2026-09-10T00:01:00Z", "2026-09-10T00:02:00Z",
            "2026-09-10", "PRE", 0, "raw", 1.0, 2.0, 0.5, 1.5, 100.0, 10, 1.4,
            "fp-a", 1, "2026-09-10T00:02:05Z",
        ),
    ]
    connection.executemany(
        "INSERT INTO normalized_bar VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    return connection


def _export(connection: sqlite3.Connection):
    return export_sqlite_window(
        connection,
        source_environment="fixture",
        source_database_id="fixture-db",
        source_revision="r0-009-fixture",
        table_name="normalized_bar",
        window_start=START,
        window_end=END,
        artifact_relpath="d1/fixture/normalized_bar/2026-09-10.ndjson",
    )


def test_duplicate_export_retry_is_byte_and_generation_id_idempotent() -> None:
    connection = _connection()
    first = _export(connection)
    second = _export(connection)
    assert first.artifact_bytes == second.artifact_bytes
    assert first.export_manifest.manifest_id == second.export_manifest.manifest_id
    assert first.custody_manifest.generation_id == second.custody_manifest.generation_id


def test_hash_mismatch_blocks_custody_acknowledgement() -> None:
    connection = _connection()
    result = _export(connection)
    tampered = result.artifact_bytes + b"tamper\n"
    with pytest.raises(ContractViolation, match="byte size"):
        build_d1_custody_manifest(
            source_database_id="fixture-db",
            export=result.export_manifest,
            artifact_relpath="d1/fixture/normalized_bar/2026-09-10.ndjson",
            artifact_bytes=tampered,
        )


def test_local_custody_remains_readable_after_source_rows_are_purged() -> None:
    connection = _connection()
    result = _export(connection)
    connection.execute("DELETE FROM normalized_bar")
    connection.commit()
    assert connection.execute("SELECT count(*) FROM normalized_bar").fetchone()[0] == 0

    records = [json.loads(line) for line in result.artifact_bytes.decode("utf-8").splitlines()]
    assert [record["identity_key"] for record in records] == ["bar-a", "bar-b"]
    assert len(records) == result.export_manifest.row_count == 2


def test_export_failure_does_not_fabricate_manifest() -> None:
    connection = sqlite3.connect(":memory:")
    with pytest.raises(ContractViolation, match="registered export table is missing"):
        _export(connection)
