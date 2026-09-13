from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import.d1_manifest import D1ExportManifest
from orderscope_local.storage.d1_custody_quality import validate_d1_custody_artifact


def _artifact(**overrides: object) -> bytes:
    row: dict[str, object] = {
        "identity_key": "instrument-1:1Min:2026-09-01T16:03:00.000Z",
        "instrument_id": "instrument-1",
        "interval": "1Min",
        "bar_start_utc": "2026-09-01T16:03:00.000Z",
        "bar_end_utc": "2026-09-01T16:04:00.000Z",
        "market_date": "2026-09-01",
        "session_kind": "REGULAR",
        "is_shortened_session": 0,
        "logical_data_variant": "raw",
        "open": 100.0,
        "high": 102.0,
        "low": 99.0,
        "close": 101.0,
        "volume": 1234.0,
        "trade_count": 42,
        "vwap": 100.5,
        "canonical_fingerprint": "abc123",
        "version": 1,
        "accepted_at": "2026-09-01T16:04:05.000Z",
    }
    row.update(overrides)
    return (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _manifest(artifact: bytes) -> D1ExportManifest:
    return D1ExportManifest(
        source_environment="live-canary",
        source_revision="abc123",
        window_start=datetime(2026, 9, 1, 16, 3, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 1, 16, 4, tzinfo=timezone.utc),
        table_name="normalized_bar",
        row_count=1,
        byte_size=len(artifact),
        sha256=hashlib.sha256(artifact).hexdigest(),
    )


def test_accepts_reviewed_normalized_bar_ndjson() -> None:
    artifact = _artifact()
    result = validate_d1_custody_artifact(manifest=_manifest(artifact), artifact=artifact)
    assert result.quality_accepted is True
    assert result.row_count == 1
    assert result.artifact_sha256 == hashlib.sha256(artifact).hexdigest()


def test_rejects_hash_mismatch() -> None:
    artifact = _artifact()
    manifest = _manifest(artifact)
    tampered = bytearray(artifact)
    tampered[-2] = ord(" ") if tampered[-2] != ord(" ") else ord("x")
    with pytest.raises(ContractViolation, match="sha256"):
        validate_d1_custody_artifact(manifest=manifest, artifact=bytes(tampered))


def test_rejects_bar_outside_half_open_window() -> None:
    artifact = _artifact(bar_start_utc="2026-09-01T16:04:00.000Z", bar_end_utc="2026-09-01T16:05:00.000Z")
    with pytest.raises(ContractViolation, match="outside manifest window"):
        validate_d1_custody_artifact(manifest=_manifest(artifact), artifact=artifact)


def test_rejects_invalid_ohlc_envelope() -> None:
    artifact = _artifact(high=98.0)
    with pytest.raises(ContractViolation, match="OHLC envelope"):
        validate_d1_custody_artifact(manifest=_manifest(artifact), artifact=artifact)


def test_rejects_unknown_or_missing_schema_fields() -> None:
    artifact = _artifact(extra_field="unexpected")
    with pytest.raises(ContractViolation, match="fields do not match"):
        validate_d1_custody_artifact(manifest=_manifest(artifact), artifact=artifact)
