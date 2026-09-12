from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import sqlite3

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.storage.d1_bounded_export import export_sqlite_window


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE normalized_bar (
          identity_key TEXT PRIMARY KEY,
          instrument_id TEXT NOT NULL,
          bar_start_utc TEXT NOT NULL,
          close REAL NOT NULL,
          volume REAL NOT NULL
        )
        """
    )
    return connection


def _export(connection: sqlite3.Connection):
    return export_sqlite_window(
        connection,
        source_environment="fixture",
        source_database_id="fixture-state",
        source_revision="fixture-rev-1",
        table_name="normalized_bar",
        window_start=datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc),
        artifact_relpath="d1/fixture/normalized_bar/2026-09-10.ndjson",
    )


def test_exports_exact_half_open_window_in_deterministic_order() -> None:
    connection = _connection()
    rows = [
        ("z", "NVDA", "2026-09-10T12:00:00Z", 191.0, 20.0),
        ("outside-end", "AMD", "2026-09-11T00:00:00Z", 210.0, 1.0),
        ("b", "AMD", "2026-09-10T12:00:00Z", 205.0, 10.0),
        ("outside-start", "AMD", "2026-09-09T23:59:59Z", 199.0, 1.0),
        ("a", "AMD", "2026-09-10T00:00:00Z", 200.0, 5.0),
    ]
    connection.executemany("INSERT INTO normalized_bar VALUES (?, ?, ?, ?, ?)", rows)

    result = _export(connection)
    lines = [json.loads(line) for line in result.artifact_bytes.decode("utf-8").splitlines()]

    assert [line["identity_key"] for line in lines] == ["a", "b", "z"]
    assert result.export_manifest.row_count == 3
    assert result.export_manifest.byte_size == len(result.artifact_bytes)
    assert result.export_manifest.sha256 == hashlib.sha256(result.artifact_bytes).hexdigest()
    assert result.custody_manifest.export == result.export_manifest
    assert result.custody_manifest.export.window_end.isoformat() == "2026-09-11T00:00:00+00:00"


def test_same_rows_different_insert_order_produce_identical_artifact_and_generation() -> None:
    rows = [
        ("b", "AMD", "2026-09-10T12:00:00Z", 205.0, 10.0),
        ("a", "AMD", "2026-09-10T00:00:00Z", 200.0, 5.0),
    ]
    first = _connection()
    second = _connection()
    first.executemany("INSERT INTO normalized_bar VALUES (?, ?, ?, ?, ?)", rows)
    second.executemany("INSERT INTO normalized_bar VALUES (?, ?, ?, ?, ?)", reversed(rows))

    left = _export(first)
    right = _export(second)

    assert left.artifact_bytes == right.artifact_bytes
    assert left.export_manifest.manifest_id == right.export_manifest.manifest_id
    assert left.custody_manifest.generation_id == right.custody_manifest.generation_id


def test_empty_window_is_valid_and_hashes_exact_empty_artifact() -> None:
    connection = _connection()
    result = _export(connection)

    assert result.artifact_bytes == b""
    assert result.export_manifest.row_count == 0
    assert result.export_manifest.byte_size == 0
    assert result.export_manifest.sha256 == hashlib.sha256(b"").hexdigest()


def test_unregistered_table_fails_closed() -> None:
    connection = _connection()
    with pytest.raises(ContractViolation, match="not registered"):
        export_sqlite_window(
            connection,
            source_environment="fixture",
            source_database_id="fixture-state",
            source_revision="fixture-rev-1",
            table_name="coverage_checkpoint",
            window_start=datetime(2026, 9, 10, tzinfo=timezone.utc),
            window_end=datetime(2026, 9, 11, tzinfo=timezone.utc),
            artifact_relpath="d1/fixture/control.ndjson",
        )


def test_invalid_or_non_utc_window_fails_closed() -> None:
    connection = _connection()
    with pytest.raises(ContractViolation, match="normalized to UTC"):
        export_sqlite_window(
            connection,
            source_environment="fixture",
            source_database_id="fixture-state",
            source_revision="fixture-rev-1",
            table_name="normalized_bar",
            window_start=datetime(2026, 9, 10),
            window_end=datetime(2026, 9, 11, tzinfo=timezone.utc),
            artifact_relpath="d1/fixture/export.ndjson",
        )
    with pytest.raises(ContractViolation, match="non-empty"):
        export_sqlite_window(
            connection,
            source_environment="fixture",
            source_database_id="fixture-state",
            source_revision="fixture-rev-1",
            table_name="normalized_bar",
            window_start=datetime(2026, 9, 11, tzinfo=timezone.utc),
            window_end=datetime(2026, 9, 11, tzinfo=timezone.utc),
            artifact_relpath="d1/fixture/export.ndjson",
        )


def test_registered_plan_fails_if_fixture_schema_does_not_match() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE normalized_bar (identity_key TEXT PRIMARY KEY)")
    with pytest.raises(ContractViolation, match="does not match table schema"):
        _export(connection)
