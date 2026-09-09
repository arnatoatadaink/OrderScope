from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import import D1ExportManifest, import_fixture_dump

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


def test_import_registers_hash_addressed_raw_fixture_and_catalog(tmp_path: Path) -> None:
    artifact = _artifact()
    manifest = _manifest(artifact)
    database = tmp_path / "catalog.sqlite3"
    raw_root = tmp_path / "var" / "raw"

    result = import_fixture_dump(
        manifest=manifest,
        artifact=artifact,
        catalog_database=database,
        raw_root=raw_root,
        registered_at=REGISTERED,
    )

    assert result.status == "new"
    target = raw_root / result.raw_relative_path
    assert target.read_bytes() == artifact
    assert target.name == f"{manifest.sha256}.sql"
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT manifest_id, sha256, raw_relative_path FROM raw_imports"
        ).fetchone()
    assert row == (manifest.manifest_id, manifest.sha256, result.raw_relative_path)


def test_reimport_same_manifest_and_hash_is_idempotent(tmp_path: Path) -> None:
    artifact = _artifact()
    manifest = _manifest(artifact)
    kwargs = dict(
        manifest=manifest,
        artifact=artifact,
        catalog_database=tmp_path / "catalog.sqlite3",
        raw_root=tmp_path / "raw",
        registered_at=REGISTERED,
    )
    first = import_fixture_dump(**kwargs)
    second = import_fixture_dump(**{**kwargs, "registered_at": REGISTERED + timedelta(hours=1)})

    assert first.status == "new"
    assert second.status == "duplicate"
    assert second.registered_at == first.registered_at
    with sqlite3.connect(kwargs["catalog_database"]) as connection:
        assert connection.execute("SELECT count(*) FROM raw_imports").fetchone() == (1,)


def test_manifest_size_or_hash_mismatch_is_rejected_before_storage(tmp_path: Path) -> None:
    artifact = _artifact()
    with pytest.raises(ContractViolation, match="byte_size"):
        import_fixture_dump(
            manifest=_manifest(artifact, byte_size=len(artifact) + 1),
            artifact=artifact,
            catalog_database=tmp_path / "size.sqlite3",
            raw_root=tmp_path / "raw-size",
            registered_at=REGISTERED,
        )
    with pytest.raises(ContractViolation, match="sha256"):
        import_fixture_dump(
            manifest=_manifest(artifact, sha256="0" * 64),
            artifact=artifact,
            catalog_database=tmp_path / "hash.sqlite3",
            raw_root=tmp_path / "raw-hash",
            registered_at=REGISTERED,
        )


def test_same_hash_under_different_manifest_metadata_is_conflict(tmp_path: Path) -> None:
    artifact = _artifact()
    database = tmp_path / "catalog.sqlite3"
    raw_root = tmp_path / "raw"
    first = _manifest(artifact)
    second = _manifest(artifact, source_revision="fixture-rev-002")
    import_fixture_dump(
        manifest=first,
        artifact=artifact,
        catalog_database=database,
        raw_root=raw_root,
        registered_at=REGISTERED,
    )
    with pytest.raises(ContractViolation, match="different manifest metadata"):
        import_fixture_dump(
            manifest=second,
            artifact=artifact,
            catalog_database=database,
            raw_root=raw_root,
            registered_at=REGISTERED + timedelta(minutes=1),
        )


def test_existing_hash_path_with_different_bytes_is_rejected(tmp_path: Path) -> None:
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


def test_catalog_migration_registers_version_two(tmp_path: Path) -> None:
    artifact = _artifact()
    database = tmp_path / "catalog.sqlite3"
    import_fixture_dump(
        manifest=_manifest(artifact),
        artifact=artifact,
        catalog_database=database,
        raw_root=tmp_path / "raw",
        registered_at=REGISTERED,
    )
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (2,)
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone() == (2,)


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
    assert not hasattr(result, "rows")
    assert result.raw_relative_path.startswith("d1/")
