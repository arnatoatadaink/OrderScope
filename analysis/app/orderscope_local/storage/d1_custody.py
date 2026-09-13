"""Bounded local custody contract for R0-007 D1 incremental exports.

This module does not contact D1. It validates an already-produced bounded export
artifact and records enough source identity to make local custody idempotent and
reviewable. Remote export remains separately gated.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import hashlib
import re
from typing import Mapping

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import.d1_manifest import D1ExportManifest, decode_d1_export_manifest


D1_CUSTODY_MANIFEST_SCHEMA_VERSION = "d1-custody-manifest-v0.1"
_DATABASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class D1CustodyManifest:
    source_database_id: str
    export: D1ExportManifest
    artifact_relpath: str
    schema_version: str = D1_CUSTODY_MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != D1_CUSTODY_MANIFEST_SCHEMA_VERSION:
            raise ContractViolation("unsupported D1 custody manifest schema version")
        if not isinstance(self.source_database_id, str) or _DATABASE_ID.fullmatch(self.source_database_id) is None:
            raise ContractViolation("source_database_id must be a bounded canonical identifier")
        _validate_relpath(self.artifact_relpath)

    @property
    def generation_id(self) -> str:
        payload = "\n".join(
            (
                self.schema_version,
                self.source_database_id,
                self.export.manifest_id,
                self.artifact_relpath,
            )
        )
        return "d1-custody-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "generation_id": self.generation_id,
            "source_database_id": self.source_database_id,
            "artifact_relpath": self.artifact_relpath,
            "export": self.export.to_record(),
        }


def build_d1_custody_manifest(
    *,
    source_database_id: str,
    export: D1ExportManifest,
    artifact_relpath: str,
    artifact_bytes: bytes,
) -> D1CustodyManifest:
    """Verify artifact size/hash against the L1-001 export manifest and wrap it.

    The export manifest already enforces a non-empty half-open UTC window. A
    retry with identical source identity, export manifest, and relative path
    yields the same generation_id.
    """

    if not isinstance(artifact_bytes, bytes):
        raise ContractViolation("artifact_bytes must be bytes")
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    if len(artifact_bytes) != export.byte_size:
        raise ContractViolation("artifact byte size does not match export manifest")
    if digest != export.sha256:
        raise ContractViolation("artifact sha256 does not match export manifest")
    return D1CustodyManifest(
        source_database_id=source_database_id,
        export=export,
        artifact_relpath=artifact_relpath,
    )


def decode_d1_custody_manifest(record: Mapping[str, object]) -> D1CustodyManifest:
    if not isinstance(record, Mapping):
        raise ContractViolation("custody manifest record must be a mapping")
    required = {
        "schema_version",
        "generation_id",
        "source_database_id",
        "artifact_relpath",
        "export",
    }
    if set(record) != required:
        raise ContractViolation("custody manifest fields do not match v0.1 schema")
    export_record = record["export"]
    if not isinstance(export_record, Mapping):
        raise ContractViolation("export must be a D1 export manifest mapping")
    manifest = D1CustodyManifest(
        schema_version=_text(record["schema_version"], "schema_version"),
        source_database_id=_text(record["source_database_id"], "source_database_id"),
        artifact_relpath=_text(record["artifact_relpath"], "artifact_relpath"),
        export=decode_d1_export_manifest(export_record),
    )
    if _text(record["generation_id"], "generation_id") != manifest.generation_id:
        raise ContractViolation("generation_id does not match custody manifest content")
    return manifest


def _validate_relpath(value: object) -> None:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractViolation("artifact_relpath must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractViolation("artifact_relpath must remain inside local custody root")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be text")
    return value
