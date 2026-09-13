"""Immutable raw fixture importer for L1-002."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
import sqlite3

from orderscope_local.contracts import ContractViolation
from orderscope_local.storage import apply_migrations

from .d1_manifest import D1ExportManifest


RAW_IMPORT_SCHEMA_VERSION = "raw-import-v0.1"


@dataclass(frozen=True, slots=True)
class RawImportResult:
    status: str
    manifest_id: str
    sha256: str
    raw_relative_path: str
    registered_at: datetime

    def __post_init__(self) -> None:
        if self.status not in {"new", "duplicate"}:
            raise ContractViolation("raw import status must be new or duplicate")
        _utc(self.registered_at, "registered_at")


def import_fixture_dump(
    *,
    manifest: D1ExportManifest,
    artifact: bytes,
    catalog_database: str | Path,
    raw_root: str | Path,
    registered_at: datetime,
) -> RawImportResult:
    """Verify, store, and register one immutable fixture dump.

    The raw artifact is content-addressed beneath ``raw_root`` and cataloged in
    the L0-005 SQLite metadata store. Reimporting the same manifest/hash is
    idempotent. A previously registered hash with different manifest metadata is
    rejected as a conflict rather than silently reinterpreted.
    """

    if not isinstance(manifest, D1ExportManifest):
        raise ContractViolation("manifest must be D1ExportManifest")
    if not isinstance(artifact, bytes):
        raise ContractViolation("artifact must be bytes")
    _utc(registered_at, "registered_at")

    actual_size = len(artifact)
    actual_hash = sha256(artifact).hexdigest()
    if actual_size != manifest.byte_size:
        raise ContractViolation("fixture byte_size does not match manifest")
    if actual_hash != manifest.sha256:
        raise ContractViolation("fixture sha256 does not match manifest")

    raw_root_path = Path(raw_root)
    raw_root_path.mkdir(parents=True, exist_ok=True)
    relative_path = Path("d1") / f"{manifest.sha256}.sql"
    target = raw_root_path / relative_path

    apply_migrations(catalog_database)
    with sqlite3.connect(catalog_database) as connection:
        connection.row_factory = sqlite3.Row
        existing_manifest = connection.execute(
            "SELECT * FROM raw_imports WHERE manifest_id = ?",
            (manifest.manifest_id,),
        ).fetchone()
        existing_hash = connection.execute(
            "SELECT * FROM raw_imports WHERE sha256 = ?",
            (manifest.sha256,),
        ).fetchone()

        if existing_manifest is not None:
            _assert_catalog_match(existing_manifest, manifest, relative_path)
            _assert_raw_file(target, artifact)
            return RawImportResult(
                status="duplicate",
                manifest_id=manifest.manifest_id,
                sha256=manifest.sha256,
                raw_relative_path=relative_path.as_posix(),
                registered_at=datetime.fromisoformat(existing_manifest["registered_at"]),
            )

        if existing_hash is not None:
            raise ContractViolation("fixture hash is already registered under different manifest metadata")

        if target.exists():
            _assert_raw_file(target, artifact)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with target.open("xb") as handle:
                    handle.write(artifact)
            except FileExistsError:
                _assert_raw_file(target, artifact)

        connection.execute(
            """
            INSERT INTO raw_imports(
                manifest_id, schema_version, source_environment, source_revision,
                window_start, window_end, table_name, row_count, byte_size,
                sha256, raw_relative_path, registered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manifest.manifest_id,
                manifest.schema_version,
                manifest.source_environment,
                manifest.source_revision,
                manifest.window_start.isoformat(),
                manifest.window_end.isoformat(),
                manifest.table_name,
                manifest.row_count,
                manifest.byte_size,
                manifest.sha256,
                relative_path.as_posix(),
                registered_at.isoformat(),
            ),
        )
        connection.commit()

    return RawImportResult(
        status="new",
        manifest_id=manifest.manifest_id,
        sha256=manifest.sha256,
        raw_relative_path=relative_path.as_posix(),
        registered_at=registered_at,
    )


def _assert_catalog_match(row: sqlite3.Row, manifest: D1ExportManifest, relative_path: Path) -> None:
    expected = {
        "schema_version": manifest.schema_version,
        "source_environment": manifest.source_environment,
        "source_revision": manifest.source_revision,
        "window_start": manifest.window_start.isoformat(),
        "window_end": manifest.window_end.isoformat(),
        "table_name": manifest.table_name,
        "row_count": manifest.row_count,
        "byte_size": manifest.byte_size,
        "sha256": manifest.sha256,
        "raw_relative_path": relative_path.as_posix(),
    }
    for key, value in expected.items():
        if row[key] != value:
            raise ContractViolation("registered fixture manifest conflicts with immutable catalog metadata")


def _assert_raw_file(path: Path, artifact: bytes) -> None:
    try:
        existing = path.read_bytes()
    except OSError as exc:
        raise ContractViolation("registered raw fixture cannot be read") from exc
    if sha256(existing).hexdigest() != sha256(artifact).hexdigest() or existing != artifact:
        raise ContractViolation("raw fixture path contains different immutable content")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
