from contextlib import closing
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import import D1ExportManifest, import_fixture_dump
from orderscope_local.storage.migrations import discover_migrations

UTC = timezone.utc
START = datetime(2026, 9, 1, tzinfo=UTC)
END = START + timedelta(days=1)
REGISTERED = END + timedelta(minutes=5)


def _artifact() -> bytes:
    return (
        b"CREATE TABLE bars(symbol TEXT, ts TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER);\n"
        b"INSERT INTO bars VALUES ('AMD','2026-09-01T13:30:00Z',100,101,99,100.5,12345);\n"
    )


def _manifest(artifact: bytes, **overrides) -> D1ExportManifest:
    values = dict(
        source_environment="worker-shadow",
        source_revision="fixture-rev-001",
        window_start=START,
        window_end=END,
        table_name="bars",
        row_count=1,
        byte_size=len(artifact),
        sha256=sha256(artifact).hexdigest(),
    )
    values.update(overrides)
    return D1ExportManifest(**values)


def test_import_fixture_dump_persists_immutable_artifact_and_catalog(tmp_path: Path) -> None:
    artifact = _artifact()
    manifest = _manifest(artifact)
    raw_root = tmp_path / "raw"
    database = tmp_path / "catalog.sqlite3"

    result = import_fixture_dump(
        manifest=manifest,
        artifact=artifact,
        catalog_database=database,
        raw_root=raw_root,
        registered_at=REGISTERED,
    )

    assert result.row_count == 1
    assert result.byte_size == len(artifact)
    assert result.sha256 == manifest.sha256
    assert result.raw_path.read_bytes() == artifact

    with closing(sqlite3.connect(database)) as connection:
        row = connection.execute(
            "SELECT dataset_id, source_environment, source_revision, table_name, row_count, byte_size, sha256 FROM import_datasets"
        ).fetchone()
        assert row == (
            result.dataset_id,
            "worker-shadow",
            "fixture-rev-001",
            "bars",
            1,
            len(artifact),
            manifest.sha256,
        )
        raw = connection.execute(
            "SELECT sha256, relative_path, byte_size FROM raw_imports"
        ).fetchone()
        assert raw == (
            manifest.sha256,
            str(result.raw_path.relative_to(raw_root)),
            len(artifact),
        )


def test_import_fixture_dump_is_idempotent_for_same_manifest_and_artifact(tmp_path: Path) -> None:
    artifact = _artifact()
    manifest = _manifest(artifact)
    raw_root = tmp_path / "raw"
    database = tmp_path / "catalog.sqlite3"

    first = import_fixture_dump(
        manifest=manifest,
        artifact=artifact,
        catalog_database=database,
        raw_root=raw_root,
        registered_at=REGISTERED,
    )
    second = import_fixture_dump(
        manifest=manifest,
        artifact=artifact,
        catalog_database=database,
        raw_root=raw_root,
        registered_at=REGISTERED,
    )

    assert second == first
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT count(*) FROM import_datasets").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM raw_imports").fetchone() == (1,)


def test_import_rejects_manifest_hash_mismatch(tmp_path: Path) -> None:
    artifact = _artifact()
    with pytest.raises(ContractViolation, match="sha256"):
        import_fixture_dump(
            manifest=_manifest(artifact, sha256="0" * 64),
            artifact=artifact,
            catalog_database=tmp_path / "catalog.sqlite3",
            raw_root=tmp_path / "raw",
            registered_at=REGISTERED,
        )


def test_import_rejects_manifest_byte_size_mismatch(tmp_path: Path) -> None:
    artifact = _artifact()
    with pytest.raises(ContractViolation, match="byte_size"):
        import_fixture_dump(
            manifest=_manifest(artifact, byte_size=len(artifact) + 1),
            artifact=artifact,
            catalog_database=tmp_path / "catalog.sqlite3",
            raw_root=tmp_path / "raw",
            registered_at=REGISTERED,
        )


def test_import_rejects_existing_artifact_with_different_content(tmp_path: Path) -> None:
    artifact = _artifact()
    manifest = _manifest(artifact)
    raw_root = tmp_path / "raw"
    target = raw_root / "d1" / f"{manifest.sha256}.sql"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"tampered")

    with pytest.raises(ContractViolation, match="different immutable content"):
        import_fixture_dump(
            manifest=manifest,
            artifact=artifact,
            catalog_database=tmp_path / "catalog.sqlite3",
            raw_root=raw_root,
            registered_at=REGISTERED,
        )


def test_catalog_migration_registers_current_schema_version(tmp_path: Path) -> None:
    artifact = _artifact()
    database = tmp_path / "catalog.sqlite3"
    import_fixture_dump(
        manifest=_manifest(artifact),
        artifact=artifact,
        catalog_database=database,
        raw_root=tmp_path / "raw",
        registered_at=REGISTERED,
    )
    migrations = discover_migrations()
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (migrations[-1].version,)
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone() == (len(migrations),)


def test_registered_at_requires_utc(tmp_path: Path) -> None:
    artifact = _artifact()
    with pytest.raises(ContractViolation, match="registered_at must be normalized to UTC"):
        import_fixture_dump(
            manifest=_manifest(artifact),
            artifact=artifact,
            catalog_database=tmp_path / "catalog.sqlite3",
            raw_root=tmp_path / "raw",
            registered_at=datetime(2026, 9, 2),
        )


def test_import_result_exposes_metadata_not_raw_body(tmp_path: Path) -> None:
    artifact = _artifact()
    result = import_fixture_dump(
        manifest=_manifest(artifact),
        artifact=artifact,
        catalog_database=tmp_path / "catalog.sqlite3",
        raw_root=tmp_path / "raw",
        registered_at=REGISTERED,
    )

    assert not hasattr(result, "artifact")
    assert not hasattr(result, "raw_body")
