from datetime import datetime, timezone
import json

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.storage.backup import (
    BACKUP_MANIFEST_SCHEMA_VERSION,
    create_backup,
    restore_backup,
)

UTC = timezone.utc


def test_explicit_backup_and_clean_restore_round_trip(tmp_path):
    data_root = tmp_path / "data"
    (data_root / "catalog").mkdir(parents=True)
    (data_root / "datasets").mkdir(parents=True)
    (data_root / "catalog" / "metadata.sqlite3").write_bytes(b"sqlite-fixture")
    (data_root / "datasets" / "bars.parquet").write_bytes(b"parquet-fixture")
    (data_root / "temporary").mkdir()
    (data_root / "temporary" / "body.txt").write_text("must not be auto included", encoding="utf-8")

    backup_dir = tmp_path / "backup"
    manifest = create_backup(
        data_root=data_root,
        destination=backup_dir,
        relative_paths=("catalog/metadata.sqlite3", "datasets/bars.parquet"),
        created_at=datetime(2026, 9, 12, 0, 0, tzinfo=UTC),
    )

    assert len(manifest.entries) == 2
    assert not (backup_dir / "temporary" / "body.txt").exists()
    payload = json.loads((backup_dir / "backup-manifest.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == BACKUP_MANIFEST_SCHEMA_VERSION
    assert {entry["relative_path"] for entry in payload["entries"]} == {
        "catalog/metadata.sqlite3", "datasets/bars.parquet"
    }

    restored = tmp_path / "restored"
    result = restore_backup(backup_dir=backup_dir, destination_root=restored)
    assert result.backup_id == manifest.backup_id
    assert (restored / "catalog" / "metadata.sqlite3").read_bytes() == b"sqlite-fixture"
    assert (restored / "datasets" / "bars.parquet").read_bytes() == b"parquet-fixture"
    assert not (restored / "temporary" / "body.txt").exists()


def test_backup_rejects_escape_duplicate_and_missing_sources(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "ok.txt").write_text("ok", encoding="utf-8")

    with pytest.raises(ContractViolation, match="canonical relative POSIX"):
        create_backup(data_root=root, destination=tmp_path / "b1", relative_paths=("../secret",))
    with pytest.raises(ContractViolation, match="unique"):
        create_backup(data_root=root, destination=tmp_path / "b2", relative_paths=("ok.txt", "ok.txt"))
    with pytest.raises(ContractViolation, match="existing file"):
        create_backup(data_root=root, destination=tmp_path / "b3", relative_paths=("missing.txt",))


def test_restore_detects_tampering_before_copy(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "state.db").write_bytes(b"original")
    backup_dir = tmp_path / "backup"
    create_backup(data_root=root, destination=backup_dir, relative_paths=("state.db",))
    (backup_dir / "state.db").write_bytes(b"tampered")

    destination = tmp_path / "restore"
    with pytest.raises(ContractViolation, match="verification failed"):
        restore_backup(backup_dir=backup_dir, destination_root=destination)
    assert not (destination / "state.db").exists()


def test_restore_requires_clean_destination(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "state.db").write_bytes(b"original")
    backup_dir = tmp_path / "backup"
    create_backup(data_root=root, destination=backup_dir, relative_paths=("state.db",))

    destination = tmp_path / "restore"
    destination.mkdir()
    (destination / "existing.txt").write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(ContractViolation, match="must be empty"):
        restore_backup(backup_dir=backup_dir, destination_root=destination)


def test_backup_destination_must_be_empty(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "state.db").write_bytes(b"original")
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "existing.txt").write_text("occupied", encoding="utf-8")
    with pytest.raises(ContractViolation, match="must be empty"):
        create_backup(data_root=root, destination=backup_dir, relative_paths=("state.db",))
