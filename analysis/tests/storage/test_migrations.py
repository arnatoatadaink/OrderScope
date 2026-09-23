from contextlib import closing
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from orderscope_local.storage import MigrationError, apply_migrations, discover_migrations


def schema(database: Path) -> tuple[tuple[str, str, str], ...]:
    with closing(sqlite3.connect(database)) as connection:
        return tuple(
            connection.execute(
                "SELECT type, name, sql FROM sqlite_schema "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            )
        )


def test_empty_databases_rebuild_to_identical_catalog_schema(tmp_path: Path) -> None:
    first = tmp_path / "first.sqlite3"
    second = tmp_path / "second.sqlite3"

    first_applied = apply_migrations(first)
    second_applied = apply_migrations(second)

    assert schema(first) == schema(second)
    assert [(item.version, item.name, item.checksum) for item in first_applied] == [
        (item.version, item.name, item.checksum) for item in second_applied
    ]
    assert first_applied
    with closing(sqlite3.connect(first)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (first_applied[-1].version,)
        assert connection.execute(
            "SELECT value FROM catalog_metadata WHERE key = 'schema_kind'"
        ).fetchone() == ("orderscope-local-metadata",)


def test_current_migrations_install_filing_records_schema(tmp_path: Path) -> None:
    database = tmp_path / "catalog.sqlite3"
    apply_migrations(database)

    with closing(sqlite3.connect(database)) as connection:
        columns = {
            row[1]: (row[2], row[3], row[5])
            for row in connection.execute("PRAGMA table_info(filing_records)")
        }
        assert columns == {
            "accession": ("TEXT", 1, 1),
            "content_hash": ("TEXT", 1, 0),
            "cik": ("TEXT", 1, 0),
            "ticker": ("TEXT", 1, 0),
            "form": ("TEXT", 1, 0),
            "filed_at": ("TEXT", 1, 0),
            "period_end": ("TEXT", 0, 0),
            "primary_document_ref": ("TEXT", 0, 0),
            "source_ref": ("TEXT", 1, 0),
            "retrieved_at": ("TEXT", 1, 0),
        }
        indexes = {
            row[1] for row in connection.execute("PRAGMA index_list(filing_records)")
        }
        assert "filing_records_cik_filed_at_idx" in indexes


def test_reapplying_current_migrations_is_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "catalog.sqlite3"
    first = apply_migrations(database)
    second = apply_migrations(database)

    assert second == first
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone() == (len(first),)


def test_applied_migration_checksum_drift_is_rejected(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    migration = migrations / "0001_base.sql"
    migration.write_text("CREATE TABLE example(id INTEGER PRIMARY KEY) STRICT;\n", encoding="utf-8")
    database = tmp_path / "catalog.sqlite3"
    apply_migrations(database, migration_directory=migrations)

    migration.write_text("CREATE TABLE changed(id INTEGER PRIMARY KEY) STRICT;\n", encoding="utf-8")

    with pytest.raises(MigrationError, match="has changed"):
        apply_migrations(database, migration_directory=migrations)


@pytest.mark.parametrize("names", [("0002_gap.sql",), ("0001_ok.sql", "0003_gap.sql")])
def test_discovery_rejects_non_contiguous_versions(tmp_path: Path, names: tuple[str, ...]) -> None:
    for name in names:
        (tmp_path / name).write_text("SELECT 1;\n", encoding="utf-8")

    with pytest.raises(MigrationError, match="contiguous"):
        discover_migrations(tmp_path)


def test_failed_migration_rolls_back_schema_and_history(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0001_broken.sql").write_text(
        "CREATE TABLE should_rollback(id INTEGER);\nINSERT INTO missing_table VALUES (1);\n",
        encoding="utf-8",
    )
    database = tmp_path / "catalog.sqlite3"

    with pytest.raises(MigrationError, match="failed to apply"):
        apply_migrations(database, migration_directory=migrations)

    with closing(sqlite3.connect(database)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_schema")}
        assert "should_rollback" not in names
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone() == (0,)


def test_discovery_checksum_is_sha256_of_exact_file_bytes(tmp_path: Path) -> None:
    raw = b"SELECT 1;\n"
    (tmp_path / "0001_base.sql").write_bytes(raw)

    assert discover_migrations(tmp_path)[0].checksum == sha256(raw).hexdigest()
