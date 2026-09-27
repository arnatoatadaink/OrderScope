"""Market-data quality checks for canonical bar datasets (L1-005)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from orderscope_local.contracts import ContractViolation
from .canonical_bars import (
    CANONICAL_BAR_DATASET_SCHEMA_VERSION,
    CanonicalBarDataset,
)


MARKET_DATA_QUALITY_SCHEMA_VERSION = "market-data-quality-v0.1"


class MarketDataQualityIssueKind(StrEnum):
    SCHEMA = "schema"
    ROW_COUNT = "row_count"
    IDENTITY_DUPLICATE = "identity_duplicate"
    IDENTITY_CONFLICT = "identity_conflict"
    OHLCV = "ohlcv"
    RECEIPT_ORDER = "receipt_order"
    MISSING_GRID_POINT = "missing_grid_point"
    OFF_GRID_POINT = "off_grid_point"
    PROVENANCE = "provenance"
    DATASET_HASH = "dataset_hash"


@dataclass(frozen=True, slots=True)
class SessionWindow:
    name: str
    start: datetime
    end: datetime
    cadence: timedelta

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip() or self.name != self.name.strip() or len(self.name) > 64:
            raise ContractViolation("session window name must be bounded canonical text")
        _utc(self.start, "session start")
        _utc(self.end, "session end")
        if self.start >= self.end:
            raise ContractViolation("session window must be non-empty")
        if not isinstance(self.cadence, timedelta) or self.cadence <= timedelta(0):
            raise ContractViolation("session cadence must be positive")
        if (self.end - self.start) % self.cadence != timedelta(0):
            raise ContractViolation("session window length must align to cadence")

    def expected_points(self) -> tuple[datetime, ...]:
        points: list[datetime] = []
        current = self.start
        while current < self.end:
            points.append(current)
            current += self.cadence
        return tuple(points)


@dataclass(frozen=True, slots=True)
class MarketDataQualityIssue:
    kind: MarketDataQualityIssueKind
    symbol: str | None
    bar_time: datetime | None
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MarketDataQualityIssueKind):
            raise ContractViolation("quality issue kind is invalid")
        if self.symbol is not None and (not isinstance(self.symbol, str) or not self.symbol or len(self.symbol) > 32):
            raise ContractViolation("quality issue symbol is invalid")
        if self.bar_time is not None:
            _utc(self.bar_time, "quality issue bar_time")
        if not isinstance(self.detail, str) or not self.detail.strip() or self.detail != self.detail.strip() or len(self.detail) > 512:
            raise ContractViolation("quality issue detail must be bounded canonical text")


@dataclass(frozen=True, slots=True)
class MarketDataQualityReport:
    schema_version: str
    dataset_manifest_id: str
    dataset_parquet_sha256: str
    row_count: int
    symbols: tuple[str, ...]
    expected_grid_points: int
    issues: tuple[MarketDataQualityIssue, ...]

    def __post_init__(self) -> None:
        if self.schema_version != MARKET_DATA_QUALITY_SCHEMA_VERSION:
            raise ContractViolation("unsupported market-data quality schema version")
        if not self.dataset_manifest_id.startswith("d1-export-"):
            raise ContractViolation("quality report requires D1 manifest identity")
        if not _sha256(self.dataset_parquet_sha256):
            raise ContractViolation("quality report parquet hash must be SHA-256")
        if not isinstance(self.row_count, int) or isinstance(self.row_count, bool) or self.row_count < 0:
            raise ContractViolation("quality report row_count must be non-negative integer")
        if not isinstance(self.symbols, tuple) or tuple(sorted(set(self.symbols))) != self.symbols:
            raise ContractViolation("quality report symbols must be unique canonical sorted tuple")
        if not isinstance(self.expected_grid_points, int) or self.expected_grid_points < 0:
            raise ContractViolation("expected_grid_points must be non-negative integer")
        if not isinstance(self.issues, tuple) or any(not isinstance(item, MarketDataQualityIssue) for item in self.issues):
            raise ContractViolation("quality report issues must be immutable issue tuple")

    @property
    def passed(self) -> bool:
        return not self.issues


def evaluate_market_data_quality(
    *,
    dataset: CanonicalBarDataset,
    dataset_root: Path,
    expected_symbols: tuple[str, ...],
    session_windows: tuple[SessionWindow, ...],
) -> MarketDataQualityReport:
    """Evaluate canonical Parquet integrity and explicit session-grid coverage."""

    if not isinstance(dataset, CanonicalBarDataset):
        raise ContractViolation("dataset must be CanonicalBarDataset")
    if not isinstance(expected_symbols, tuple) or not expected_symbols:
        raise ContractViolation("expected_symbols must be a non-empty tuple")
    symbols = tuple(sorted(expected_symbols))
    if len(symbols) != len(set(symbols)) or any(not isinstance(symbol, str) or not symbol or symbol != symbol.strip() or len(symbol) > 32 for symbol in symbols):
        raise ContractViolation("expected_symbols must contain unique canonical symbols")
    if not isinstance(session_windows, tuple) or not session_windows or any(not isinstance(window, SessionWindow) for window in session_windows):
        raise ContractViolation("session_windows must be a non-empty immutable tuple")
    _validate_session_windows(session_windows)

    path = dataset_root / dataset.relative_path
    if not path.is_file():
        raise ContractViolation("canonical dataset file is missing")
    parquet_bytes = path.read_bytes()
    actual_hash = sha256(parquet_bytes).hexdigest()
    issues: list[MarketDataQualityIssue] = []
    if actual_hash != dataset.parquet_sha256:
        issues.append(_issue(MarketDataQualityIssueKind.DATASET_HASH, None, None, "Parquet SHA-256 differs from dataset descriptor."))

    try:
        table = pq.read_table(path)
    except Exception as exc:
        raise ContractViolation("canonical dataset cannot be read as Parquet") from exc

    if not _schema_matches(table.schema):
        issues.append(_issue(MarketDataQualityIssueKind.SCHEMA, None, None, "Canonical Parquet schema or schema version is invalid."))

    rows = table.to_pylist()
    if len(rows) != dataset.row_count:
        issues.append(_issue(MarketDataQualityIssueKind.ROW_COUNT, None, None, "Parquet row count differs from dataset descriptor."))

    expected_points = _expected_points(session_windows)
    expected_set = set(expected_points)
    seen: dict[tuple[str, datetime], dict[str, object]] = {}
    actual_by_symbol: dict[str, set[datetime]] = {symbol: set() for symbol in symbols}

    for row in rows:
        symbol = row.get("symbol")
        bar_time = row.get("bar_time")
        receipt_time = row.get("receipt_time")
        if not isinstance(symbol, str) or symbol not in actual_by_symbol or not isinstance(bar_time, datetime):
            issues.append(_issue(MarketDataQualityIssueKind.SCHEMA, symbol if isinstance(symbol, str) else None, bar_time if isinstance(bar_time, datetime) else None, "Row identity fields do not match expected canonical types/symbols."))
            continue
        try:
            _utc(bar_time, "bar_time")
            if not isinstance(receipt_time, datetime):
                raise ContractViolation("receipt_time must be datetime")
            _utc(receipt_time, "receipt_time")
        except ContractViolation:
            issues.append(_issue(MarketDataQualityIssueKind.SCHEMA, symbol, bar_time if bar_time.tzinfo else None, "Row timestamps are not normalized UTC instants."))
            continue

        key = (symbol, bar_time)
        previous = seen.get(key)
        if previous is not None:
            kind = MarketDataQualityIssueKind.IDENTITY_DUPLICATE if previous == row else MarketDataQualityIssueKind.IDENTITY_CONFLICT
            detail = "Duplicate canonical bar identity." if kind is MarketDataQualityIssueKind.IDENTITY_DUPLICATE else "Conflicting rows share one canonical bar identity."
            issues.append(_issue(kind, symbol, bar_time, detail))
        else:
            seen[key] = row

        if receipt_time < bar_time:
            issues.append(_issue(MarketDataQualityIssueKind.RECEIPT_ORDER, symbol, bar_time, "receipt_time precedes bar_time."))

        if not _valid_ohlcv(row):
            issues.append(_issue(MarketDataQualityIssueKind.OHLCV, symbol, bar_time, "OHLCV values violate canonical numeric/envelope constraints."))

        if not _valid_provenance(row, dataset):
            issues.append(_issue(MarketDataQualityIssueKind.PROVENANCE, symbol, bar_time, "Row provenance does not match the canonical dataset descriptor."))

        actual_by_symbol[symbol].add(bar_time)
        if bar_time not in expected_set:
            issues.append(_issue(MarketDataQualityIssueKind.OFF_GRID_POINT, symbol, bar_time, "bar_time is outside the supplied session grid."))

    for symbol in symbols:
        for point in sorted(expected_set - actual_by_symbol[symbol]):
            issues.append(_issue(MarketDataQualityIssueKind.MISSING_GRID_POINT, symbol, point, "Expected session-grid bar is missing."))

    ordered_issues = tuple(sorted(issues, key=_issue_sort_key))
    return MarketDataQualityReport(
        schema_version=MARKET_DATA_QUALITY_SCHEMA_VERSION,
        dataset_manifest_id=dataset.manifest_id,
        dataset_parquet_sha256=actual_hash,
        row_count=len(rows),
        symbols=symbols,
        expected_grid_points=len(expected_set) * len(symbols),
        issues=ordered_issues,
    )


def _schema_matches(schema: pa.Schema) -> bool:
    expected_names = (
        "symbol", "bar_time", "open", "high", "low", "close", "volume", "receipt_time",
        "source_manifest_id", "source_artifact_sha256", "source_environment", "source_revision",
    )
    if tuple(schema.names) != expected_names:
        return False
    metadata = schema.metadata or {}
    if metadata.get(b"orderscope_schema_version") != CANONICAL_BAR_DATASET_SCHEMA_VERSION.encode("ascii"):
        return False
    fields = schema
    return (
        pa.types.is_string(fields.field("symbol").type)
        and pa.types.is_timestamp(fields.field("bar_time").type)
        and fields.field("bar_time").type.tz == "UTC"
        and all(pa.types.is_decimal(fields.field(name).type) for name in ("open", "high", "low", "close"))
        and pa.types.is_int64(fields.field("volume").type)
        and pa.types.is_timestamp(fields.field("receipt_time").type)
        and fields.field("receipt_time").type.tz == "UTC"
        and all(pa.types.is_string(fields.field(name).type) for name in ("source_manifest_id", "source_artifact_sha256", "source_environment", "source_revision"))
    )


def _valid_ohlcv(row: dict[str, object]) -> bool:
    values = [row.get(name) for name in ("open", "high", "low", "close")]
    if any(not isinstance(value, Decimal) or not value.is_finite() or value < 0 for value in values):
        return False
    open_, high, low, close = values
    volume = row.get("volume")
    if not isinstance(volume, int) or isinstance(volume, bool) or volume < 0:
        return False
    return high >= max(open_, close, low) and low <= min(open_, close, high)


def _valid_provenance(row: dict[str, object], dataset: CanonicalBarDataset) -> bool:
    manifest_id = row.get("source_manifest_id")
    artifact_hash = row.get("source_artifact_sha256")
    environment = row.get("source_environment")
    revision = row.get("source_revision")
    return (
        manifest_id == dataset.manifest_id
        and artifact_hash == dataset.artifact_sha256
        and isinstance(environment, str) and bool(environment)
        and isinstance(revision, str) and bool(revision)
    )


def _expected_points(windows: tuple[SessionWindow, ...]) -> tuple[datetime, ...]:
    points: list[datetime] = []
    for window in windows:
        points.extend(window.expected_points())
    return tuple(sorted(points))


def _validate_session_windows(windows: tuple[SessionWindow, ...]) -> None:
    ordered = tuple(sorted(windows, key=lambda item: item.start))
    for previous, current in zip(ordered, ordered[1:]):
        if current.start < previous.end:
            raise ContractViolation("session windows cannot overlap")


def _issue(kind: MarketDataQualityIssueKind, symbol: str | None, bar_time: datetime | None, detail: str) -> MarketDataQualityIssue:
    return MarketDataQualityIssue(kind=kind, symbol=symbol, bar_time=bar_time, detail=detail)


def _issue_sort_key(issue: MarketDataQualityIssue) -> tuple[str, str, str, str]:
    return (
        issue.kind.value,
        issue.symbol or "",
        issue.bar_time.isoformat() if issue.bar_time is not None else "",
        issue.detail,
    )


def _sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
