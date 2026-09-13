"""Deterministic bounded export primitive for R0-007 local/fixture acceptance.

This module deliberately operates on a local SQLite fixture only. It does not
contact Cloudflare D1 and must not be treated as authorization for a remote
export. Only explicitly registered table plans may be exported.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import sqlite3
from typing import Final

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import.d1_manifest import D1ExportManifest
from orderscope_local.storage.d1_custody import D1CustodyManifest, build_d1_custody_manifest


@dataclass(frozen=True, slots=True)
class BoundedExportPlan:
    table_name: str
    time_column: str
    order_columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BoundedExportResult:
    artifact_bytes: bytes
    export_manifest: D1ExportManifest
    custody_manifest: D1CustodyManifest


EXPORT_PLANS: Final[dict[str, BoundedExportPlan]] = {
    "normalized_bar": BoundedExportPlan(
        table_name="normalized_bar",
        time_column="bar_start_utc",
        order_columns=("bar_start_utc", "identity_key"),
    ),
}


def export_sqlite_window(
    connection: sqlite3.Connection,
    *,
    source_environment: str,
    source_database_id: str,
    source_revision: str,
    table_name: str,
    window_start: datetime,
    window_end: datetime,
    artifact_relpath: str,
) -> BoundedExportResult:
    """Export one registered table over an explicit half-open UTC window.

    Rows are serialized as canonical UTF-8 NDJSON in a deterministic order.
    The returned export and custody manifests are derived from the exact bytes.
    No local or remote mutation is performed.
    """

    plan = EXPORT_PLANS.get(table_name)
    if plan is None:
        raise ContractViolation("table is not registered for bounded D1 export")
    _utc(window_start, "window_start")
    _utc(window_end, "window_end")
    if window_start >= window_end:
        raise ContractViolation("export window must be non-empty and half-open")
    if not isinstance(connection, sqlite3.Connection):
        raise ContractViolation("connection must be sqlite3.Connection")

    columns = _table_columns(connection, plan.table_name)
    if plan.time_column not in columns or any(column not in columns for column in plan.order_columns):
        raise ContractViolation("registered export plan does not match table schema")

    quoted_table = _quote_identifier(plan.table_name)
    quoted_time = _quote_identifier(plan.time_column)
    order_by = ", ".join(_quote_identifier(column) for column in plan.order_columns)
    sql = (
        f"SELECT * FROM {quoted_table} "
        f"WHERE {quoted_time} >= ? AND {quoted_time} < ? "
        f"ORDER BY {order_by}"
    )
    start_text = window_start.isoformat().replace("+00:00", "Z")
    end_text = window_end.isoformat().replace("+00:00", "Z")
    cursor = connection.execute(sql, (start_text, end_text))
    names = tuple(description[0] for description in cursor.description or ())
    rows = cursor.fetchall()

    artifact = b"".join(_canonical_ndjson_row(names, row) for row in rows)
    digest = hashlib.sha256(artifact).hexdigest()
    export = D1ExportManifest(
        source_environment=source_environment,
        source_revision=source_revision,
        window_start=window_start,
        window_end=window_end,
        table_name=table_name,
        row_count=len(rows),
        byte_size=len(artifact),
        sha256=digest,
    )
    custody = build_d1_custody_manifest(
        source_database_id=source_database_id,
        export=export,
        artifact_relpath=artifact_relpath,
        artifact_bytes=artifact,
    )
    return BoundedExportResult(
        artifact_bytes=artifact,
        export_manifest=export,
        custody_manifest=custody,
    )


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    if not rows:
        raise ContractViolation("registered export table is missing")
    return {str(row[1]) for row in rows}


def _canonical_ndjson_row(names: tuple[str, ...], row: tuple[object, ...]) -> bytes:
    record = {name: value for name, value in zip(names, row, strict=True)}
    try:
        text = json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContractViolation("export row contains unsupported non-canonical value") from exc
    return (text + "\n").encode("utf-8")


def _quote_identifier(value: str) -> str:
    if not value or not value.replace("_", "a").isalnum() or value[0].isdigit():
        raise ContractViolation("invalid registered SQL identifier")
    return '"' + value + '"'


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
