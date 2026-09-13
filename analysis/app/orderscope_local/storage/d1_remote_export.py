"""Pure adapter for bounded remote-D1 query results used by R0-007.

This module does not invoke Wrangler or contact Cloudflare. It builds an allow-listed
read-only SQL statement and canonicalizes Wrangler ``d1 execute --json`` output into
the same manifest/custody contract used by local fixture export.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from typing import Final, Mapping, Sequence

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import.d1_manifest import D1ExportManifest
from orderscope_local.storage.d1_custody import D1CustodyManifest, build_d1_custody_manifest
from orderscope_local.storage.d1_bounded_export import EXPORT_PLANS

REMOTE_EXPORT_MAX_ROWS: Final[int] = 5000


@dataclass(frozen=True, slots=True)
class RemoteExportResult:
    artifact_bytes: bytes
    export_manifest: D1ExportManifest
    custody_manifest: D1CustodyManifest


def build_remote_export_sql(*, table_name: str, window_start: datetime, window_end: datetime, max_rows: int = REMOTE_EXPORT_MAX_ROWS) -> str:
    plan = EXPORT_PLANS.get(table_name)
    if plan is None:
        raise ContractViolation("table is not registered for bounded D1 export")
    _utc(window_start, "window_start")
    _utc(window_end, "window_end")
    if window_start >= window_end:
        raise ContractViolation("export window must be non-empty and half-open")
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or max_rows < 1 or max_rows > REMOTE_EXPORT_MAX_ROWS:
        raise ContractViolation("max_rows exceeds remote export safety ceiling")
    start = window_start.isoformat().replace("+00:00", "Z").replace("'", "''")
    end = window_end.isoformat().replace("+00:00", "Z").replace("'", "''")
    order_by = ", ".join(_quote_identifier(c) for c in plan.order_columns)
    return (
        f"SELECT * FROM {_quote_identifier(plan.table_name)} "
        f"WHERE {_quote_identifier(plan.time_column)} >= '{start}' "
        f"AND {_quote_identifier(plan.time_column)} < '{end}' "
        f"ORDER BY {order_by} LIMIT {max_rows + 1};"
    )


def canonicalize_wrangler_json(
    payload: object,
    *,
    source_environment: str,
    source_database_id: str,
    source_revision: str,
    table_name: str,
    window_start: datetime,
    window_end: datetime,
    artifact_relpath: str,
    max_rows: int = REMOTE_EXPORT_MAX_ROWS,
) -> RemoteExportResult:
    if table_name not in EXPORT_PLANS:
        raise ContractViolation("table is not registered for bounded D1 export")
    _utc(window_start, "window_start")
    _utc(window_end, "window_end")
    if window_start >= window_end:
        raise ContractViolation("export window must be non-empty and half-open")
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or max_rows < 1 or max_rows > REMOTE_EXPORT_MAX_ROWS:
        raise ContractViolation("max_rows exceeds remote export safety ceiling")

    rows = _extract_rows(payload)
    if len(rows) > max_rows:
        raise ContractViolation("remote export row count exceeds safety ceiling")
    plan = EXPORT_PLANS[table_name]
    for row in rows:
        if plan.time_column not in row or any(c not in row for c in plan.order_columns):
            raise ContractViolation("remote export row does not match registered plan")

    ordered = sorted(rows, key=lambda row: tuple(_sortable(row[c]) for c in plan.order_columns))
    artifact = b"".join(_canonical_row(row) for row in ordered)
    digest = hashlib.sha256(artifact).hexdigest()
    export = D1ExportManifest(
        source_environment=source_environment,
        source_revision=source_revision,
        window_start=window_start,
        window_end=window_end,
        table_name=table_name,
        row_count=len(ordered),
        byte_size=len(artifact),
        sha256=digest,
    )
    custody = build_d1_custody_manifest(
        source_database_id=source_database_id,
        export=export,
        artifact_relpath=artifact_relpath,
        artifact_bytes=artifact,
    )
    return RemoteExportResult(artifact, export, custody)


def _extract_rows(payload: object) -> list[dict[str, object]]:
    envelopes: Sequence[object]
    if isinstance(payload, list):
        envelopes = payload
    elif isinstance(payload, Mapping):
        envelopes = [payload]
    else:
        raise ContractViolation("Wrangler JSON payload must be object or array")
    rows: list[dict[str, object]] = []
    for envelope in envelopes:
        if not isinstance(envelope, Mapping):
            raise ContractViolation("Wrangler JSON envelope must be an object")
        result_rows = envelope.get("results")
        if result_rows is None and isinstance(envelope.get("result"), Mapping):
            result_rows = envelope["result"].get("results")
        if not isinstance(result_rows, list):
            raise ContractViolation("Wrangler JSON envelope is missing results")
        for row in result_rows:
            if not isinstance(row, Mapping) or not all(isinstance(k, str) for k in row):
                raise ContractViolation("Wrangler result row must be a string-keyed object")
            rows.append(dict(row))
    return rows


def _canonical_row(row: Mapping[str, object]) -> bytes:
    try:
        text = json.dumps(dict(row), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ContractViolation("remote export row contains unsupported value") from exc
    return (text + "\n").encode("utf-8")


def _sortable(value: object) -> str:
    if value is None or isinstance(value, (str, int, float, bool)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    raise ContractViolation("remote export order column contains unsupported value")


def _quote_identifier(value: str) -> str:
    if not value or not value.replace("_", "a").isalnum() or value[0].isdigit():
        raise ContractViolation("invalid registered SQL identifier")
    return '"' + value + '"'


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
