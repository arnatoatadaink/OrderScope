"""Explicit local backup/restore boundary for Packet F.

Backups are not D1 exports and are not retention archives. Only caller-selected
files beneath one data root are copied. Restore targets must be empty/clean and
every file is verified by SHA-256 before completion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Sequence

from orderscope_local.contracts import ContractViolation


BACKUP_MANIFEST_SCHEMA_VERSION = "local-backup-manifest-v0.1"
MAX_BACKUP_FILES = 10_000


@dataclass(frozen=True, slots=True)
class BackupEntry:
    relative_path: str
    size_bytes: int
    sha256_hex: str


@dataclass(frozen=True, slots=True)
class BackupManifest:
    backup_id: str
    created_at: datetime
    entries: tuple[BackupEntry, ...]


def create_backup(*, data_root: Path, destination: Path, relative_paths: Sequence[str], created_at: datetime | None = None) -> BackupManifest:
    root = _root(data_root)
    dest = destination.resolve()
    when = created_at or datetime.now(timezone.utc)
    _utc(when, "created_at")
    paths = _paths(relative_paths)
    if dest.exists() and any(dest.iterdir()):
        raise ContractViolation("backup destination must be empty")
    dest.mkdir(parents=True, exist_ok=True)
    entries: list[BackupEntry] = []
    for rel in paths:
        source = _resolve_under(root, rel)
        if not source.is_file():
            raise ContractViolation("backup source must be an existing file")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        digest = _hash(target)
        entries.append(BackupEntry(rel, target.stat().st_size, digest))
    backup_id = sha256((when.isoformat() + "|" + "|".join(paths)).encode("utf-8")).hexdigest()[:24]
    manifest = BackupManifest(backup_id=backup_id, created_at=when, entries=tuple(entries))
    payload = {
        "schema_version": BACKUP_MANIFEST_SCHEMA_VERSION,
        "backup_id": backup_id,
        "created_at": when.isoformat(),
        "entries": [entry.__dict__ for entry in entries],
    }
    (dest / "backup-manifest.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def restore_backup(*, backup_dir: Path, destination_root: Path) -> BackupManifest:
    source_root = backup_dir.resolve()
    manifest_path = source_root / "backup-manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractViolation("backup manifest is unreadable") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != BACKUP_MANIFEST_SCHEMA_VERSION:
        raise ContractViolation("unsupported backup manifest")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list) or len(raw_entries) > MAX_BACKUP_FILES:
        raise ContractViolation("backup manifest entries are invalid")
    destination = destination_root.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ContractViolation("restore destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    entries: list[BackupEntry] = []
    for raw in raw_entries:
        if not isinstance(raw, dict) or set(raw) != {"relative_path", "size_bytes", "sha256_hex"}:
            raise ContractViolation("backup manifest entry is invalid")
        rel = _path(str(raw["relative_path"]))
        expected_size = raw["size_bytes"]
        expected_hash = raw["sha256_hex"]
        if not isinstance(expected_size, int) or expected_size < 0:
            raise ContractViolation("backup entry size is invalid")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise ContractViolation("backup entry hash is invalid")
        source = _resolve_under(source_root, rel)
        if not source.is_file() or source.stat().st_size != expected_size or _hash(source) != expected_hash:
            raise ContractViolation("backup entry verification failed")
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if _hash(target) != expected_hash:
            raise ContractViolation("restored entry verification failed")
        entries.append(BackupEntry(rel, expected_size, expected_hash))
    created = _parse_utc(payload.get("created_at"))
    backup_id = payload.get("backup_id")
    if not isinstance(backup_id, str) or not backup_id.strip() or len(backup_id) > 128:
        raise ContractViolation("backup_id is invalid")
    return BackupManifest(backup_id=backup_id, created_at=created, entries=tuple(entries))


def _paths(values: Sequence[str]) -> tuple[str, ...]:
    result = tuple(_path(value) for value in values)
    if not result or len(result) > MAX_BACKUP_FILES:
        raise ContractViolation("backup requires 1 through 10000 explicit files")
    if len(set(result)) != len(result):
        raise ContractViolation("backup paths must be unique")
    return result


def _path(value: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or value != path.as_posix():
        raise ContractViolation("backup path must be canonical relative POSIX path")
    return value


def _root(value: Path) -> Path:
    if not isinstance(value, Path):
        raise ContractViolation("data_root must be pathlib.Path")
    return value.resolve()


def _resolve_under(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ContractViolation("backup path escapes root") from exc
    return candidate


def _hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ContractViolation("backup created_at is invalid")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation("backup created_at is invalid") from exc
    _utc(parsed, "created_at")
    return parsed


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
