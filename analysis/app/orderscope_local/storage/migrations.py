"""Versioned SQLite migration runner for the local metadata catalog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
import re
import sqlite3
from typing import Iterable


_MIGRATION_NAME = re.compile(r"^(?P<version>[0-9]{4})_(?P<name>[a-z0-9][a-z0-9_]*)\.sql$")


class MigrationError(RuntimeError):
    """Raised when migrations cannot be safely discovered or applied."""


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    sql: str
    checksum: str


@dataclass(frozen=True, slots=True)
class AppliedMigration:
    version: int
    name: str
    checksum: str
    applied_at: str


def _default_migration_directory() -> Path:
    return Path(str(files("orderscope_local.storage").joinpath("sql")))


def discover_migrations(directory: Path | None = None) -> tuple[Migration, ...]:
    """Load a gap-free sequence of UTF-8 ``NNNN_name.sql`` migrations."""
    root = directory or _default_migration_directory()
    if not root.is_dir():
        raise MigrationError(f"migration directory does not exist: {root}")

    migrations: list[Migration] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.suffix == ".sql":
            match = _MIGRATION_NAME.fullmatch(path.name)
            if match is None:
                raise MigrationError(f"invalid migration filename: {path.name}")
            raw = path.read_bytes()
            try:
                sql = raw.decode("utf-8")
            except UnicodeDecodeError as error:
                raise MigrationError(f"migration is not UTF-8: {path.name}") from error
            if not sql.strip():
                raise MigrationError(f"migration is empty: {path.name}")
            migrations.append(
                Migration(
                    version=int(match.group("version")),
                    name=match.group("name"),
                    sql=sql,
                    checksum=sha256(raw).hexdigest(),
                )
            )

    versions = [migration.version for migration in migrations]
    expected = list(range(1, len(migrations) + 1))
    if versions != expected:
        raise MigrationError(f"migration versions must be unique and contiguous from 0001: {versions}")
    if not migrations:
        raise MigrationError("at least one migration is required")
    return tuple(migrations)


def _statements(sql: str) -> Iterable[str]:
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            if buffer.strip():
                yield buffer
            buffer = ""
    if buffer.strip():
        raise MigrationError("migration ends with an incomplete SQL statement")


def _ensure_history(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY CHECK (version > 0),
            name TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL CHECK (length(checksum) = 64),
            applied_at TEXT NOT NULL
        ) STRICT
        """
    )


def _applied(connection: sqlite3.Connection) -> tuple[AppliedMigration, ...]:
    rows = connection.execute(
        "SELECT version, name, checksum, applied_at FROM schema_migrations ORDER BY version"
    ).fetchall()
    return tuple(AppliedMigration(*row) for row in rows)


def apply_migrations(
    database: str | Path,
    *,
    migration_directory: Path | None = None,
) -> tuple[AppliedMigration, ...]:
    """Apply pending migrations and verify already-applied files have not drifted."""
    migrations = discover_migrations(migration_directory)
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_history(connection)
        applied_by_version = {item.version: item for item in _applied(connection)}
        known_versions = {item.version for item in migrations}
        unknown = sorted(set(applied_by_version) - known_versions)
        if unknown:
            raise MigrationError(f"database contains unknown migration versions: {unknown}")

        for migration in migrations:
            previous = applied_by_version.get(migration.version)
            if previous is not None:
                if previous.name != migration.name or previous.checksum != migration.checksum:
                    raise MigrationError(f"applied migration has changed: {migration.version:04d}_{migration.name}")
                continue

            try:
                connection.execute("BEGIN IMMEDIATE")
                for statement in _statements(migration.sql):
                    connection.execute(statement)
                applied_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
                connection.execute(
                    "INSERT INTO schema_migrations(version, name, checksum, applied_at) VALUES (?, ?, ?, ?)",
                    (migration.version, migration.name, migration.checksum, applied_at),
                )
                connection.execute(f"PRAGMA user_version = {migration.version}")
                connection.commit()
            except (sqlite3.Error, MigrationError) as error:
                connection.rollback()
                if isinstance(error, MigrationError):
                    raise
                raise MigrationError(
                    f"failed to apply migration {migration.version:04d}_{migration.name}"
                ) from error

        return _applied(connection)
    finally:
        connection.close()
