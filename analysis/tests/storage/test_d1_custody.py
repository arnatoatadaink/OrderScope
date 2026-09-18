from __future__ import annotations

from datetime import datetime, timezone
import hashlib

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import.d1_manifest import D1ExportManifest
from orderscope_local.storage.d1_custody import (
    D1CustodyManifest,
    build_d1_custody_manifest,
    decode_d1_custody_manifest,
)


def _export(payload: bytes = b"row-1\nrow-2\n") -> tuple[D1ExportManifest, bytes]:
    manifest = D1ExportManifest(
        source_environment="live-canary",
        source_revision="worker-rev-1",
        window_start=datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc),
        table_name="normalized_bar",
        row_count=2,
        byte_size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    return manifest, payload


def test_builds_deterministic_bounded_custody_manifest() -> None:
    export, payload = _export()
    first = build_d1_custody_manifest(
        source_database_id="orderscope-state-live-canary",
        export=export,
        artifact_relpath="d1/live-canary/normalized_bar/2026-09-10.ndjson",
        artifact_bytes=payload,
    )
    second = build_d1_custody_manifest(
        source_database_id="orderscope-state-live-canary",
        export=export,
        artifact_relpath="d1/live-canary/normalized_bar/2026-09-10.ndjson",
        artifact_bytes=payload,
    )
    assert first.generation_id == second.generation_id
    assert first.export.window_start < first.export.window_end
    assert first.export.table_name == "normalized_bar"


def test_rejects_artifact_hash_or_size_mismatch() -> None:
    export, payload = _export()
    with pytest.raises(ContractViolation, match="byte size"):
        build_d1_custody_manifest(
            source_database_id="orderscope-state-live-canary",
            export=export,
            artifact_relpath="d1/export.ndjson",
            artifact_bytes=payload + b"x",
        )
    same_size_wrong = b"ROW-1\nROW-2\n"
    assert len(same_size_wrong) == len(payload)
    with pytest.raises(ContractViolation, match="sha256"):
        build_d1_custody_manifest(
            source_database_id="orderscope-state-live-canary",
            export=export,
            artifact_relpath="d1/export.ndjson",
            artifact_bytes=same_size_wrong,
        )


@pytest.mark.parametrize("path", ["/tmp/export", "../export", "d1/../export", r"d1\\export"])
def test_rejects_custody_path_escape(path: str) -> None:
    export, payload = _export()
    with pytest.raises(ContractViolation, match="artifact_relpath"):
        build_d1_custody_manifest(
            source_database_id="orderscope-state-live-canary",
            export=export,
            artifact_relpath=path,
            artifact_bytes=payload,
        )


def test_record_round_trip_and_generation_tamper_detection() -> None:
    export, payload = _export()
    manifest = build_d1_custody_manifest(
        source_database_id="orderscope-state-live-canary",
        export=export,
        artifact_relpath="d1/live-canary/export.ndjson",
        artifact_bytes=payload,
    )
    record = manifest.to_record()
    decoded = decode_d1_custody_manifest(record)
    assert decoded == manifest

    tampered = dict(record)
    tampered["generation_id"] = "d1-custody-" + "0" * 64
    with pytest.raises(ContractViolation, match="generation_id"):
        decode_d1_custody_manifest(tampered)


def test_unknown_fields_fail_closed() -> None:
    export, payload = _export()
    manifest = build_d1_custody_manifest(
        source_database_id="orderscope-state-live-canary",
        export=export,
        artifact_relpath="d1/live-canary/export.ndjson",
        artifact_bytes=payload,
    )
    record = manifest.to_record()
    record["sql"] = "select * from normalized_bar"
    with pytest.raises(ContractViolation, match="fields"):
        decode_d1_custody_manifest(record)
