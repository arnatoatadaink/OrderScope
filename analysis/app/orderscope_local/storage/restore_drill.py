"""Restore drill validation for Packet F.

This module validates a clean local restore without mutating remote D1 or the
Worker.  It verifies SQLite integrity/current migration history and explicit
canonical Parquet references against their source D1 export manifests.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence

import pyarrow.parquet as pq

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import.canonical_bars import CANONICAL_BAR_DATASET_SCHEMA_VERSION
from orderscope_local.market_import.d1_manifest import decode_d1_export_manifest
from .migrations import discover_migrations


RESTORE_DRILL_SCHEMA_VERSION = "local-restore-drill-v0.1"
MAX_RESTORE_DATASETS = 10_000


@dataclass(frozen=True, slots=True)
class RestoredDatasetReference:
    relative_path: str
    parquet_sha256: str
    row_count: int
    manifest_record: Mapping[str, object]

    def __post_init__(self) -> None:
        _relative_path(self.relative_path, prefix="canonical/")
        _sha256(self.parquet_sha256, "parquet_sha256")
        if not isinstance(self.row_count, int) or isinstance(self.row_count, bool) or self.row_count < 0:
            raise ContractViolation("restore dataset row_count must be a non-negative integer")
        decode_d1_export_manifest(self.manifest_record)


@dataclass(frozen=True, slots=True)
class RestoreDrillResult:
    schema_version: str
    migration_count: int
    dataset_count: int
    row_count: int


def validate_restore_drill(
    *,
    restored_root: Path,
    catalog_relative_path: str,
    datasets: Sequence[RestoredDatasetReference],
) -> RestoreDrillResult:
    """Validate one explicit restored root in read-only/fail-closed fashion."""

    root = _root(restored_root)
    catalog_rel = _relative_path(catalog_relative_path)
    refs = tuple(datasets)
    if len(refs) > MAX_RESTORE_DATASETS:
        raise ContractViolation("restore dataset count exceeds 10000")
    if len({item.relative_path for item in refs}) != len(refs):
        raise ContractViolation("restore dataset paths must be unique")

    migration_count = _validate_catalog(root=root, relative_path=catalog_rel)
    rows = 0
    for reference in refs:
        _validate_dataset(root=root, reference=reference)
        rows += reference.row_count
    return RestoreDrillResult(
        schema_version=RESTORE_DRILL_SCHEMA_VERSION,
        migration_count=migration_count,
        dataset_count=len(refs),
        row_count=rows,
    )


def _validate_catalog(*, root: Path, relative_path: str) -> int:
    database = _resolve_under(root, relative_path)
    if not database.is_file():
        raise ContractViolation("restored catalog is missing")
    expected = discover_migrations()
    try:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise ContractViolation("restored catalog cannot be opened read-only") from exc
    try:
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchall()
            if integrity != [("ok",)]:
                raise ContractViolation("restored catalog integrity_check failed")
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_keys:
                raise ContractViolation("restored catalog foreign_key_check failed")
            rows = connection.execute(
                "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
            ).fetchall()
        except sqlite3.Error as exc:
            raise ContractViolation("restored catalog migration history is unreadable") from exc
    finally:
        connection.close()

    expected_rows = [(item.version, item.name, item.checksum) for item in expected]
    if rows != expected_rows:
        raise ContractViolation("restored catalog migration history does not match current migrations")
    return len(expected_rows)


def _validate_dataset(*, root: Path, reference: RestoredDatasetReference) -> None:
    path = _resolve_under(root, reference.relative_path)
    if not path.is_file():
        raise ContractViolation("restored canonical dataset is missing")
    if _hash(path) != reference.parquet_sha256:
        raise ContractViolation("restored canonical dataset hash mismatch")

    manifest = decode_d1_export_manifest(reference.manifest_record)
    try:
        parquet = pq.ParquetFile(path)
    except Exception as exc:
        raise ContractViolation("restored canonical dataset is not readable Parquet") from exc
    metadata = parquet.schema_arrow.metadata or {}
    if metadata.get(b"orderscope_schema_version") != CANONICAL_BAR_DATASET_SCHEMA_VERSION.encode("ascii"):
        raise ContractViolation("restored canonical dataset schema version mismatch")
    if parquet.metadata.num_rows != reference.row_count:
        raise ContractViolation("restored canonical dataset row count mismatch")

    columns = set(parquet.schema_arrow.names)
    required = {"source_manifest_id", "source_artifact_sha256"}
    if not required.issubset(columns):
        raise ContractViolation("restored canonical dataset provenance columns are missing")
    try:
        table = pq.read_table(path, columns=["source_manifest_id", "source_artifact_sha256"])
    except Exception as exc:
        raise ContractViolation("restored canonical dataset provenance is unreadable") from exc
    manifest_ids = set(table.column("source_manifest_id").to_pylist())
    artifact_hashes = set(table.column("source_artifact_sha256").to_pylist())
    if reference.row_count == 0:
        if manifest_ids or artifact_hashes:
            raise ContractViolation("empty restored dataset contains provenance values")
    else:
        if manifest_ids != {manifest.manifest_id}:
            raise ContractViolation("restored canonical dataset manifest reference mismatch")
        if artifact_hashes != {manifest.sha256}:
            raise ContractViolation("restored canonical dataset artifact reference mismatch")


def _root(value: Path) -> Path:
    if not isinstance(value, Path):
        raise ContractViolation("restored_root must be pathlib.Path")
    return value.resolve()


def _relative_path(value: str, *, prefix: str | None = None) -> str:
    path = Path(value)
    if not isinstance(value, str) or not value or path.is_absolute() or ".." in path.parts or value != path.as_posix():
        raise ContractViolation("restore path must be canonical relative POSIX path")
    if prefix is not None and not value.startswith(prefix):
        raise ContractViolation(f"restore dataset path must remain beneath {prefix}")
    return value


def _resolve_under(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ContractViolation("restore path escapes root") from exc
    return candidate


def _sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ContractViolation(f"{field} must be lowercase SHA-256 hex")


def _hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
