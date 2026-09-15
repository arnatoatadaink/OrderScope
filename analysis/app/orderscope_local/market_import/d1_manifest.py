"""Provider-neutral D1 export manifest contract for L1-001."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import re
from typing import Mapping

from orderscope_local.contracts import ContractViolation


D1_EXPORT_MANIFEST_SCHEMA_VERSION = "d1-export-manifest-v0.1"

_ENVIRONMENT = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}")
_REVISION = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:/+-]{0,255}")
_TABLE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class D1ExportManifest:
    """Immutable manifest for one exported raw table window.

    The manifest describes the exported artifact without embedding SQL rows,
    provider payloads, credentials, or local filesystem paths.
    """

    source_environment: str
    source_revision: str
    window_start: datetime
    window_end: datetime
    table_name: str
    row_count: int
    byte_size: int
    sha256: str
    schema_version: str = D1_EXPORT_MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != D1_EXPORT_MANIFEST_SCHEMA_VERSION:
            raise ContractViolation("unsupported D1 export manifest schema version")
        if not isinstance(self.source_environment, str) or _ENVIRONMENT.fullmatch(self.source_environment) is None:
            raise ContractViolation("source_environment must be a bounded canonical identifier")
        if not isinstance(self.source_revision, str) or _REVISION.fullmatch(self.source_revision) is None:
            raise ContractViolation("source_revision must be a bounded canonical revision")
        _utc(self.window_start, "window_start")
        _utc(self.window_end, "window_end")
        if self.window_start >= self.window_end:
            raise ContractViolation("D1 export window must be non-empty and half-open")
        if not isinstance(self.table_name, str) or _TABLE.fullmatch(self.table_name) is None:
            raise ContractViolation("table_name must be a bounded SQL identifier")
        if not isinstance(self.row_count, int) or isinstance(self.row_count, bool) or self.row_count < 0:
            raise ContractViolation("row_count must be a non-negative integer")
        if not isinstance(self.byte_size, int) or isinstance(self.byte_size, bool) or self.byte_size < 0:
            raise ContractViolation("byte_size must be a non-negative integer")
        if not isinstance(self.sha256, str) or _SHA256.fullmatch(self.sha256) is None:
            raise ContractViolation("sha256 must be lowercase 64-character hex")

    @property
    def manifest_id(self) -> str:
        """Return a deterministic identity for idempotent manifest registration."""

        payload = "\n".join(
            (
                self.schema_version,
                self.source_environment,
                self.source_revision,
                self.window_start.isoformat(),
                self.window_end.isoformat(),
                self.table_name,
                str(self.row_count),
                str(self.byte_size),
                self.sha256,
            )
        )
        return "d1-export-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_record(self) -> dict[str, str | int]:
        """Serialize to a storage-neutral scalar-only record."""

        return {
            "schema_version": self.schema_version,
            "source_environment": self.source_environment,
            "source_revision": self.source_revision,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "table_name": self.table_name,
            "row_count": self.row_count,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "manifest_id": self.manifest_id,
        }


def decode_d1_export_manifest(record: Mapping[str, object]) -> D1ExportManifest:
    """Decode a persisted manifest record and verify deterministic identity."""

    if not isinstance(record, Mapping):
        raise ContractViolation("manifest record must be a mapping")
    required = {
        "schema_version",
        "source_environment",
        "source_revision",
        "window_start",
        "window_end",
        "table_name",
        "row_count",
        "byte_size",
        "sha256",
        "manifest_id",
    }
    if set(record) != required:
        raise ContractViolation("manifest record fields do not match v0.1 schema")

    manifest = D1ExportManifest(
        schema_version=_text(record["schema_version"], "schema_version"),
        source_environment=_text(record["source_environment"], "source_environment"),
        source_revision=_text(record["source_revision"], "source_revision"),
        window_start=_timestamp(record["window_start"], "window_start"),
        window_end=_timestamp(record["window_end"], "window_end"),
        table_name=_text(record["table_name"], "table_name"),
        row_count=_integer(record["row_count"], "row_count"),
        byte_size=_integer(record["byte_size"], "byte_size"),
        sha256=_text(record["sha256"], "sha256"),
    )
    if _text(record["manifest_id"], "manifest_id") != manifest.manifest_id:
        raise ContractViolation("manifest_id does not match manifest content")
    return manifest


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation(f"{field} must be an ISO-8601 UTC timestamp") from exc
    _utc(parsed, field)
    return parsed


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be text")
    return value


def _integer(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ContractViolation(f"{field} must be an integer")
    return value


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
