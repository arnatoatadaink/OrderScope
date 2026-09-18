from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.storage.d1_remote_export import (
    REMOTE_EXPORT_MAX_ROWS,
    build_remote_export_sql,
    canonicalize_wrangler_json,
)

START = datetime(2026, 9, 11, 13, 30, tzinfo=timezone.utc)
END = datetime(2026, 9, 11, 13, 35, tzinfo=timezone.utc)


def _row(ts: str, identity: str, close: float) -> dict[str, object]:
    return {
        "bar_start_utc": ts,
        "identity_key": identity,
        "close": close,
    }


def test_sql_is_half_open_allowlisted_and_overfetches_one() -> None:
    sql = build_remote_export_sql(table_name="normalized_bar", window_start=START, window_end=END, max_rows=10)
    assert 'FROM "normalized_bar"' in sql
    assert '"bar_start_utc" >= \'2026-09-11T13:30:00Z\'' in sql
    assert '"bar_start_utc" < \'2026-09-11T13:35:00Z\'' in sql
    assert 'ORDER BY "bar_start_utc", "identity_key"' in sql
    assert "LIMIT 11" in sql


def test_unknown_table_and_oversized_limit_fail_closed() -> None:
    with pytest.raises(ContractViolation):
        build_remote_export_sql(table_name="coverage_checkpoint", window_start=START, window_end=END)
    with pytest.raises(ContractViolation):
        build_remote_export_sql(table_name="normalized_bar", window_start=START, window_end=END, max_rows=REMOTE_EXPORT_MAX_ROWS + 1)


def test_canonicalizes_wrangler_array_deterministically() -> None:
    payload = [{"results": [
        _row("2026-09-11T13:31:00Z", "b", 2.0),
        _row("2026-09-11T13:30:00Z", "a", 1.0),
    ]}]
    result = canonicalize_wrangler_json(
        payload,
        source_environment="live-canary",
        source_database_id="03c85865-1aa3-4b0c-b219-18987cd260a6",
        source_revision="r0-007-remote-v1",
        table_name="normalized_bar",
        window_start=START,
        window_end=END,
        artifact_relpath="d1/live-canary/normalized_bar.ndjson",
        max_rows=10,
    )
    lines = result.artifact_bytes.decode().splitlines()
    assert '"identity_key":"a"' in lines[0]
    assert '"identity_key":"b"' in lines[1]
    assert result.export_manifest.row_count == 2
    assert result.export_manifest.byte_size == len(result.artifact_bytes)
    assert result.custody_manifest.export.manifest_id == result.export_manifest.manifest_id


def test_nested_result_shape_is_supported() -> None:
    payload = {"result": {"results": [_row("2026-09-11T13:30:00Z", "a", 1.0)]}}
    result = canonicalize_wrangler_json(
        payload,
        source_environment="live-canary",
        source_database_id="03c85865-1aa3-4b0c-b219-18987cd260a6",
        source_revision="r0-007-remote-v1",
        table_name="normalized_bar",
        window_start=START,
        window_end=END,
        artifact_relpath="d1/live-canary/normalized_bar.ndjson",
        max_rows=10,
    )
    assert result.export_manifest.row_count == 1


def test_overfetch_detects_row_ceiling() -> None:
    payload = [{"results": [_row("2026-09-11T13:30:00Z", str(i), 1.0) for i in range(3)]}]
    with pytest.raises(ContractViolation, match="row count exceeds"):
        canonicalize_wrangler_json(
            payload,
            source_environment="live-canary",
            source_database_id="03c85865-1aa3-4b0c-b219-18987cd260a6",
            source_revision="r0-007-remote-v1",
            table_name="normalized_bar",
            window_start=START,
            window_end=END,
            artifact_relpath="d1/live-canary/normalized_bar.ndjson",
            max_rows=2,
        )
