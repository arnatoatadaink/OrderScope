from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import import D1ExportManifest, decode_d1_export_manifest

UTC = timezone.utc
START = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
END = datetime(2026, 9, 2, 0, 0, tzinfo=UTC)
HASH = "a" * 64


def _manifest(**kwargs):
    values = {
        "source_environment": "cloudflare-d1-prod",
        "source_revision": "worker-schema-v0.1:abc123",
        "window_start": START,
        "window_end": END,
        "table_name": "market_bars",
        "row_count": 1440,
        "byte_size": 987654,
        "sha256": HASH,
    }
    values.update(kwargs)
    return D1ExportManifest(**values)


def test_manifest_preserves_required_export_fields_and_half_open_window():
    manifest = _manifest()

    assert manifest.source_environment == "cloudflare-d1-prod"
    assert manifest.source_revision == "worker-schema-v0.1:abc123"
    assert manifest.window_start == START
    assert manifest.window_end == END
    assert manifest.table_name == "market_bars"
    assert manifest.row_count == 1440
    assert manifest.byte_size == 987654
    assert manifest.sha256 == HASH


def test_manifest_identity_is_deterministic_and_changes_with_artifact_hash():
    first = _manifest()
    second = _manifest()
    changed = _manifest(sha256="b" * 64)

    assert first.manifest_id == second.manifest_id
    assert first.manifest_id != changed.manifest_id
    assert first.manifest_id.startswith("d1-export-")


def test_storage_record_round_trip_is_scalar_only_and_identity_checked():
    manifest = _manifest()
    record = manifest.to_record()

    assert all(isinstance(value, (str, int)) and not isinstance(value, bool) for value in record.values())
    assert decode_d1_export_manifest(record) == manifest

    tampered = dict(record)
    tampered["manifest_id"] = "d1-export-" + "0" * 64
    with pytest.raises(ContractViolation, match="manifest_id"):
        decode_d1_export_manifest(tampered)


def test_empty_or_reversed_windows_and_non_utc_times_are_rejected():
    with pytest.raises(ContractViolation, match="half-open"):
        _manifest(window_end=START)
    with pytest.raises(ContractViolation, match="half-open"):
        _manifest(window_start=END)
    with pytest.raises(ContractViolation, match="UTC"):
        _manifest(window_start=START.replace(tzinfo=None))


def test_table_environment_revision_and_hash_are_strictly_bounded():
    with pytest.raises(ContractViolation, match="table_name"):
        _manifest(table_name="market-bars")
    with pytest.raises(ContractViolation, match="source_environment"):
        _manifest(source_environment="prod key=secret")
    with pytest.raises(ContractViolation, match="source_revision"):
        _manifest(source_revision="")
    with pytest.raises(ContractViolation, match="sha256"):
        _manifest(sha256="A" * 64)


def test_counts_are_non_negative_integers_not_booleans():
    with pytest.raises(ContractViolation, match="row_count"):
        _manifest(row_count=-1)
    with pytest.raises(ContractViolation, match="byte_size"):
        _manifest(byte_size=-1)
    with pytest.raises(ContractViolation, match="row_count"):
        _manifest(row_count=True)


def test_decoder_rejects_missing_extra_or_wrong_typed_fields():
    record = _manifest().to_record()

    missing = dict(record)
    missing.pop("byte_size")
    with pytest.raises(ContractViolation, match="fields"):
        decode_d1_export_manifest(missing)

    extra = dict(record)
    extra["path"] = "/tmp/raw.sql"
    with pytest.raises(ContractViolation, match="fields"):
        decode_d1_export_manifest(extra)

    wrong = dict(record)
    wrong["row_count"] = "1440"
    with pytest.raises(ContractViolation, match="row_count"):
        decode_d1_export_manifest(wrong)


def test_manifest_contract_does_not_store_rows_credentials_or_local_paths():
    record = _manifest().to_record()

    assert "rows" not in record
    assert "sql" not in record
    assert "path" not in record
    assert "credentials" not in record
    assert "api_key" not in record
