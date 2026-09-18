from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import import D1ExportManifest, generate_fixture_canonical_bars
from orderscope_local.storage.migrations import apply_migrations
from orderscope_local.storage.restore_drill import (
    RESTORE_DRILL_SCHEMA_VERSION,
    RestoredDatasetReference,
    validate_restore_drill,
)


UTC = timezone.utc


def _fixture_sql() -> bytes:
    return b'''\nCREATE TABLE market_bars (\n    symbol TEXT NOT NULL,\n    bar_time TEXT NOT NULL,\n    open TEXT NOT NULL,\n    high TEXT NOT NULL,\n    low TEXT NOT NULL,\n    close TEXT NOT NULL,\n    volume INTEGER NOT NULL,\n    receipt_time TEXT NOT NULL\n);\nINSERT INTO market_bars VALUES\n('AMD','2026-09-11T14:30:00+00:00','100','102','99','101','1000','2026-09-11T14:30:02+00:00');\n'''


def _build_restored_root(tmp_path: Path):
    root = tmp_path / "restored"
    root.mkdir()
    database = root / "catalog.sqlite3"
    migrations = apply_migrations(database)

    artifact = _fixture_sql()
    manifest = D1ExportManifest(
        source_environment="fixture",
        source_revision="packet-f",
        window_start=datetime(2026, 9, 11, 14, 30, tzinfo=UTC),
        window_end=datetime(2026, 9, 11, 14, 31, tzinfo=UTC),
        table_name="market_bars",
        row_count=1,
        byte_size=len(artifact),
        sha256=sha256(artifact).hexdigest(),
    )
    dataset = generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=root)
    reference = RestoredDatasetReference(
        relative_path=dataset.relative_path,
        parquet_sha256=dataset.parquet_sha256,
        row_count=dataset.row_count,
        manifest_record=manifest.to_record(),
    )
    return root, database, migrations, reference


def test_restore_drill_validates_catalog_migrations_and_parquet_provenance(tmp_path):
    root, _database, migrations, reference = _build_restored_root(tmp_path)

    result = validate_restore_drill(
        restored_root=root,
        catalog_relative_path="catalog.sqlite3",
        datasets=(reference,),
    )

    assert result.schema_version == RESTORE_DRILL_SCHEMA_VERSION
    assert result.migration_count == len(migrations)
    assert result.dataset_count == 1
    assert result.row_count == 1


def test_restore_drill_rejects_catalog_migration_history_drift(tmp_path):
    root, database, _migrations, reference = _build_restored_root(tmp_path)
    connection = sqlite3.connect(database)
    try:
        connection.execute("UPDATE schema_migrations SET checksum = ? WHERE version = 1", ("0" * 64,))
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(ContractViolation, match="migration history"):
        validate_restore_drill(
            restored_root=root,
            catalog_relative_path="catalog.sqlite3",
            datasets=(reference,),
        )


def test_restore_drill_rejects_parquet_tamper_before_provenance_read(tmp_path):
    root, _database, _migrations, reference = _build_restored_root(tmp_path)
    dataset_path = root / reference.relative_path
    dataset_path.write_bytes(dataset_path.read_bytes() + b"tamper")

    with pytest.raises(ContractViolation, match="hash mismatch"):
        validate_restore_drill(
            restored_root=root,
            catalog_relative_path="catalog.sqlite3",
            datasets=(reference,),
        )


def test_restore_drill_rejects_wrong_source_manifest_reference(tmp_path):
    root, _database, _migrations, reference = _build_restored_root(tmp_path)
    record = dict(reference.manifest_record)
    record["source_revision"] = "different"
    # Recompute through the contract so the manifest itself is internally valid,
    # but no longer matches the provenance stored in the restored Parquet.
    altered = D1ExportManifest(
        source_environment=record["source_environment"],
        source_revision=record["source_revision"],
        window_start=datetime.fromisoformat(record["window_start"]),
        window_end=datetime.fromisoformat(record["window_end"]),
        table_name=record["table_name"],
        row_count=record["row_count"],
        byte_size=record["byte_size"],
        sha256=record["sha256"],
    )
    wrong = RestoredDatasetReference(
        relative_path=reference.relative_path,
        parquet_sha256=reference.parquet_sha256,
        row_count=reference.row_count,
        manifest_record=altered.to_record(),
    )

    with pytest.raises(ContractViolation, match="manifest reference mismatch"):
        validate_restore_drill(
            restored_root=root,
            catalog_relative_path="catalog.sqlite3",
            datasets=(wrong,),
        )


def test_restore_drill_rejects_root_escape_and_duplicate_dataset_paths(tmp_path):
    root, _database, _migrations, reference = _build_restored_root(tmp_path)
    with pytest.raises(ContractViolation, match="canonical relative"):
        validate_restore_drill(
            restored_root=root,
            catalog_relative_path="../catalog.sqlite3",
            datasets=(reference,),
        )
    with pytest.raises(ContractViolation, match="paths must be unique"):
        validate_restore_drill(
            restored_root=root,
            catalog_relative_path="catalog.sqlite3",
            datasets=(reference, reference),
        )
