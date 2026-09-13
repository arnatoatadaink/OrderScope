"""Local quality validation for bounded D1 custody artifacts used by R0-008.

This validator is intentionally D1-native. It validates canonical NDJSON produced
by the reviewed R0-007 remote adapter without pretending that the artifact is an
L1 fixture-SQL canonical dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Mapping

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import.d1_manifest import D1ExportManifest


_REQUIRED_NORMALIZED_BAR_FIELDS = {
    "identity_key",
    "instrument_id",
    "interval",
    "bar_start_utc",
    "bar_end_utc",
    "market_date",
    "session_kind",
    "is_shortened_session",
    "logical_data_variant",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "trade_count",
    "vwap",
    "canonical_fingerprint",
    "version",
    "accepted_at",
}


@dataclass(frozen=True, slots=True)
class D1CustodyQualityResult:
    table_name: str
    manifest_id: str
    row_count: int
    artifact_sha256: str
    quality_accepted: bool


def validate_d1_custody_artifact(*, manifest: D1ExportManifest, artifact: bytes) -> D1CustodyQualityResult:
    if not isinstance(manifest, D1ExportManifest):
        raise ContractViolation("manifest must be D1ExportManifest")
    if not isinstance(artifact, bytes):
        raise ContractViolation("artifact must be bytes")
    if len(artifact) != manifest.byte_size:
        raise ContractViolation("custody artifact byte size does not match manifest")
    digest = sha256(artifact).hexdigest()
    if digest != manifest.sha256:
        raise ContractViolation("custody artifact sha256 does not match manifest")
    if manifest.table_name != "normalized_bar":
        raise ContractViolation("R0-008 custody quality currently supports normalized_bar only")

    rows = _decode_ndjson(artifact)
    if len(rows) != manifest.row_count:
        raise ContractViolation("custody artifact row count does not match manifest")

    seen_identity: set[str] = set()
    for row in rows:
        _validate_normalized_bar_row(row, manifest=manifest)
        identity = _bounded_text(row["identity_key"], "identity_key")
        if identity in seen_identity:
            raise ContractViolation("duplicate normalized_bar identity_key in custody artifact")
        seen_identity.add(identity)

    return D1CustodyQualityResult(
        table_name=manifest.table_name,
        manifest_id=manifest.manifest_id,
        row_count=len(rows),
        artifact_sha256=digest,
        quality_accepted=True,
    )


def _decode_ndjson(artifact: bytes) -> list[dict[str, object]]:
    try:
        text = artifact.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractViolation("custody artifact must be UTF-8 NDJSON") from exc
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ContractViolation(f"custody artifact contains blank NDJSON line {line_number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractViolation(f"custody artifact contains invalid NDJSON line {line_number}") from exc
        if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
            raise ContractViolation("custody NDJSON row must be a string-keyed object")
        rows.append(value)
    return rows


def _validate_normalized_bar_row(row: Mapping[str, object], *, manifest: D1ExportManifest) -> None:
    if set(row) != _REQUIRED_NORMALIZED_BAR_FIELDS:
        raise ContractViolation("normalized_bar custody row fields do not match reviewed D1 schema")

    for field in ("identity_key", "instrument_id", "interval", "market_date", "session_kind", "logical_data_variant", "canonical_fingerprint"):
        _bounded_text(row[field], field)

    bar_start = _timestamp(row["bar_start_utc"], "bar_start_utc")
    bar_end = _timestamp(row["bar_end_utc"], "bar_end_utc")
    accepted_at = _timestamp(row["accepted_at"], "accepted_at")
    if not (manifest.window_start <= bar_start < manifest.window_end):
        raise ContractViolation("normalized_bar bar_start_utc falls outside manifest window")
    if bar_end <= bar_start:
        raise ContractViolation("normalized_bar bar_end_utc must be after bar_start_utc")
    if accepted_at < bar_start:
        raise ContractViolation("normalized_bar accepted_at cannot precede bar_start_utc")

    shortened = row["is_shortened_session"]
    if shortened not in (0, 1):
        raise ContractViolation("is_shortened_session must be 0 or 1")

    open_ = _decimal(row["open"], "open")
    high = _decimal(row["high"], "high")
    low = _decimal(row["low"], "low")
    close = _decimal(row["close"], "close")
    if min(open_, high, low, close) < 0:
        raise ContractViolation("OHLC values cannot be negative")
    if high < max(open_, close, low) or low > min(open_, close, high):
        raise ContractViolation("OHLC envelope is invalid")

    volume = _decimal(row["volume"], "volume")
    if volume < 0:
        raise ContractViolation("volume cannot be negative")

    trade_count = row["trade_count"]
    if trade_count is not None and (not isinstance(trade_count, int) or isinstance(trade_count, bool) or trade_count < 0):
        raise ContractViolation("trade_count must be null or a non-negative integer")
    if row["vwap"] is not None and _decimal(row["vwap"], "vwap") < 0:
        raise ContractViolation("vwap cannot be negative")
    version = row["version"]
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ContractViolation("version must be a positive integer")


def _bounded_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 512:
        raise ContractViolation(f"{field} must be bounded non-empty canonical text")
    return value


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be ISO-8601 UTC text")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ContractViolation(f"{field} must be ISO-8601 UTC text") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
    return parsed


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ContractViolation(f"{field} must be a finite numeric value")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ContractViolation(f"{field} must be a finite numeric value") from exc
    if not result.is_finite():
        raise ContractViolation(f"{field} must be finite")
    return result
