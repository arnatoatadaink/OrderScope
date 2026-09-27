"""Deterministic canonical bar dataset generation for the L1-004 fixture path."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
import sqlite3

import pyarrow as pa
import pyarrow.parquet as pq

from orderscope_local.contracts import ContractViolation
from .d1_manifest import D1ExportManifest


CANONICAL_BAR_DATASET_SCHEMA_VERSION = "canonical-bar-dataset-v0.1"
_REQUIRED_COLUMNS = (
    "symbol",
    "bar_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "receipt_time",
)


@dataclass(frozen=True, slots=True)
class CanonicalBarDataset:
    schema_version: str
    manifest_id: str
    artifact_sha256: str
    row_count: int
    relative_path: str
    parquet_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != CANONICAL_BAR_DATASET_SCHEMA_VERSION:
            raise ContractViolation("unsupported canonical bar dataset schema version")
        if not self.manifest_id.startswith("d1-export-"):
            raise ContractViolation("canonical dataset requires D1 export manifest identity")
        for value, field in ((self.artifact_sha256, "artifact_sha256"), (self.parquet_sha256, "parquet_sha256")):
            if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ContractViolation(f"{field} must be lowercase SHA-256 hex")
        if not isinstance(self.row_count, int) or isinstance(self.row_count, bool) or self.row_count < 0:
            raise ContractViolation("row_count must be a non-negative integer")
        if not isinstance(self.relative_path, str) or not self.relative_path.startswith("canonical/"):
            raise ContractViolation("canonical dataset path must remain beneath canonical/")


def generate_fixture_canonical_bars(
    *,
    manifest: D1ExportManifest,
    artifact: bytes,
    dataset_root: Path,
) -> CanonicalBarDataset:
    """Generate deterministic Parquet from one hash-verified SQL fixture artifact."""

    if not isinstance(manifest, D1ExportManifest):
        raise ContractViolation("manifest must be D1ExportManifest")
    if not isinstance(artifact, bytes):
        raise ContractViolation("artifact must be bytes")
    if len(artifact) != manifest.byte_size or sha256(artifact).hexdigest() != manifest.sha256:
        raise ContractViolation("fixture artifact does not match manifest size/hash")
    try:
        sql = artifact.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractViolation("fixture SQL must be UTF-8") from exc

    rows = _read_fixture_rows(sql=sql, table_name=manifest.table_name)
    if len(rows) != manifest.row_count:
        raise ContractViolation("fixture row count does not match manifest")
    normalized = tuple(sorted((_normalize_row(row, manifest) for row in rows), key=lambda item: (item["symbol"], item["bar_time"], item["receipt_time"])))
    _reject_duplicate_or_conflicting_bars(normalized)

    table = _arrow_table(normalized, manifest)
    relative_path = f"canonical/{manifest.manifest_id}.parquet"
    destination = dataset_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".parquet.tmp")
    pq.write_table(table, temporary, compression="zstd", use_dictionary=False, write_statistics=True)
    parquet_bytes = temporary.read_bytes()
    parquet_hash = sha256(parquet_bytes).hexdigest()
    if destination.exists():
        if destination.read_bytes() != parquet_bytes:
            temporary.unlink(missing_ok=True)
            raise ContractViolation("canonical dataset identity already exists with different bytes")
        temporary.unlink(missing_ok=True)
    else:
        temporary.replace(destination)

    return CanonicalBarDataset(
        schema_version=CANONICAL_BAR_DATASET_SCHEMA_VERSION,
        manifest_id=manifest.manifest_id,
        artifact_sha256=manifest.sha256,
        row_count=len(normalized),
        relative_path=relative_path,
        parquet_sha256=parquet_hash,
    )


def _read_fixture_rows(*, sql: str, table_name: str) -> tuple[sqlite3.Row, ...]:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        try:
            connection.executescript(sql)
        except sqlite3.Error as exc:
            raise ContractViolation("fixture SQL cannot be loaded into isolated SQLite") from exc
        info = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        if not info:
            raise ContractViolation("manifest table is absent from fixture SQL")
        columns = tuple(row[1] for row in info)
        if columns != _REQUIRED_COLUMNS:
            raise ContractViolation("fixture bar table columns do not match canonical fixture contract")
        return tuple(connection.execute(f'SELECT * FROM "{table_name}"').fetchall())
    finally:
        connection.close()


def _normalize_row(row: sqlite3.Row, manifest: D1ExportManifest) -> dict[str, object]:
    symbol = row["symbol"]
    if not isinstance(symbol, str) or not symbol or symbol != symbol.strip() or len(symbol) > 32:
        raise ContractViolation("bar symbol must be bounded canonical text")
    bar_time = _timestamp(row["bar_time"], "bar_time")
    receipt_time = _timestamp(row["receipt_time"], "receipt_time")
    if not (manifest.window_start <= bar_time < manifest.window_end):
        raise ContractViolation("bar_time falls outside manifest half-open window")
    if receipt_time < bar_time:
        raise ContractViolation("receipt_time cannot precede bar_time")

    open_ = _decimal(row["open"], "open")
    high = _decimal(row["high"], "high")
    low = _decimal(row["low"], "low")
    close = _decimal(row["close"], "close")
    if min(open_, high, low, close) < 0:
        raise ContractViolation("OHLC values cannot be negative")
    if high < max(open_, close, low) or low > min(open_, close, high):
        raise ContractViolation("OHLC envelope is invalid")
    volume = row["volume"]
    if not isinstance(volume, int) or isinstance(volume, bool) or volume < 0:
        raise ContractViolation("volume must be a non-negative integer")

    return {
        "symbol": symbol,
        "bar_time": bar_time,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "receipt_time": receipt_time,
    }


def _reject_duplicate_or_conflicting_bars(rows: tuple[dict[str, object], ...]) -> None:
    seen: dict[tuple[str, datetime], dict[str, object]] = {}
    for row in rows:
        key = (row["symbol"], row["bar_time"])
        previous = seen.get(key)
        if previous is None:
            seen[key] = row
            continue
        if previous == row:
            raise ContractViolation("duplicate canonical bar key is not allowed")
        raise ContractViolation("conflicting canonical bar key is not allowed")


def _arrow_table(rows: tuple[dict[str, object], ...], manifest: D1ExportManifest) -> pa.Table:
    schema = pa.schema(
        [
            pa.field("symbol", pa.string(), nullable=False),
            pa.field("bar_time", pa.timestamp("us", tz="UTC"), nullable=False),
            pa.field("open", pa.decimal128(24, 8), nullable=False),
            pa.field("high", pa.decimal128(24, 8), nullable=False),
            pa.field("low", pa.decimal128(24, 8), nullable=False),
            pa.field("close", pa.decimal128(24, 8), nullable=False),
            pa.field("volume", pa.int64(), nullable=False),
            pa.field("receipt_time", pa.timestamp("us", tz="UTC"), nullable=False),
            pa.field("source_manifest_id", pa.string(), nullable=False),
            pa.field("source_artifact_sha256", pa.string(), nullable=False),
            pa.field("source_environment", pa.string(), nullable=False),
            pa.field("source_revision", pa.string(), nullable=False),
        ],
        metadata={b"orderscope_schema_version": CANONICAL_BAR_DATASET_SCHEMA_VERSION.encode("ascii")},
    )
    records = [
        {
            **row,
            "source_manifest_id": manifest.manifest_id,
            "source_artifact_sha256": manifest.sha256,
            "source_environment": manifest.source_environment,
            "source_revision": manifest.source_revision,
        }
        for row in rows
    ]
    return pa.Table.from_pylist(records, schema=schema)


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be ISO-8601 UTC text")
    try:
        parsed = datetime.fromisoformat(value)
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
    return result.quantize(Decimal("0.00000001"))
