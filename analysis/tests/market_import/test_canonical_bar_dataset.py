from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import import (
    CANONICAL_BAR_DATASET_SCHEMA_VERSION,
    D1ExportManifest,
    generate_fixture_canonical_bars,
)

UTC = timezone.utc
START = datetime(2026, 9, 8, 13, 30, tzinfo=UTC)
END = datetime(2026, 9, 8, 13, 35, tzinfo=UTC)


def _sql(rows: tuple[str, ...]) -> bytes:
    statements = [
        "CREATE TABLE bars(symbol TEXT, bar_time TEXT, open TEXT, high TEXT, low TEXT, close TEXT, volume INTEGER, receipt_time TEXT);"
    ]
    statements.extend(rows)
    return ("\n".join(statements) + "\n").encode()


def _row(symbol: str, minute: int, *, close: str = "100.5", receipt_offset: int = 1) -> str:
    return (
        "INSERT INTO bars VALUES "
        f"('{symbol}','2026-09-08T13:{minute:02d}:00+00:00','100.0','101.0','99.0','{close}',1000,"
        f"'2026-09-08T13:{minute:02d}:0{receipt_offset}+00:00');"
    )


def _manifest(artifact: bytes, *, row_count: int) -> D1ExportManifest:
    return D1ExportManifest(
        source_environment="fixture",
        source_revision="fixture-v1",
        window_start=START,
        window_end=END,
        table_name="bars",
        row_count=row_count,
        byte_size=len(artifact),
        sha256=sha256(artifact).hexdigest(),
    )


def test_generates_deterministically_ordered_parquet_with_source_provenance(tmp_path: Path) -> None:
    artifact = _sql((_row("NVDA", 31), _row("AMD", 32), _row("AMD", 30)))
    manifest = _manifest(artifact, row_count=3)

    result = generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=tmp_path)
    table = pq.read_table(tmp_path / result.relative_path)

    assert result.schema_version == CANONICAL_BAR_DATASET_SCHEMA_VERSION
    assert result.row_count == 3
    assert result.artifact_sha256 == manifest.sha256
    assert table.column("symbol").to_pylist() == ["AMD", "AMD", "NVDA"]
    assert table.column("source_manifest_id").to_pylist() == [manifest.manifest_id] * 3
    assert table.column("source_artifact_sha256").to_pylist() == [manifest.sha256] * 3
    assert table.column("source_environment").to_pylist() == ["fixture"] * 3
    assert table.column("source_revision").to_pylist() == ["fixture-v1"] * 3


def test_same_input_reproduces_same_dataset_identity_and_bytes(tmp_path: Path) -> None:
    artifact = _sql((_row("AMD", 30), _row("NVDA", 31)))
    manifest = _manifest(artifact, row_count=2)

    first = generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=tmp_path)
    first_bytes = (tmp_path / first.relative_path).read_bytes()
    second = generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=tmp_path)

    assert second == first
    assert (tmp_path / second.relative_path).read_bytes() == first_bytes


def test_manifest_size_hash_and_row_count_are_enforced(tmp_path: Path) -> None:
    artifact = _sql((_row("AMD", 30),))
    manifest = _manifest(artifact, row_count=1)

    with pytest.raises(ContractViolation, match="size/hash"):
        generate_fixture_canonical_bars(manifest=manifest, artifact=artifact + b" ", dataset_root=tmp_path)

    wrong_count = D1ExportManifest(
        source_environment=manifest.source_environment,
        source_revision=manifest.source_revision,
        window_start=manifest.window_start,
        window_end=manifest.window_end,
        table_name=manifest.table_name,
        row_count=2,
        byte_size=manifest.byte_size,
        sha256=manifest.sha256,
    )
    with pytest.raises(ContractViolation, match="row count"):
        generate_fixture_canonical_bars(manifest=wrong_count, artifact=artifact, dataset_root=tmp_path)


def test_fixture_table_contract_is_exact_and_manifest_table_must_exist(tmp_path: Path) -> None:
    wrong_schema = (
        "CREATE TABLE bars(symbol TEXT, bar_time TEXT, open TEXT, high TEXT, low TEXT, close TEXT, volume INTEGER);\n"
    ).encode()
    with pytest.raises(ContractViolation, match="columns"):
        generate_fixture_canonical_bars(manifest=_manifest(wrong_schema, row_count=0), artifact=wrong_schema, dataset_root=tmp_path)

    other = _sql((_row("AMD", 30),)).replace(b"CREATE TABLE bars", b"CREATE TABLE other").replace(b"INSERT INTO bars", b"INSERT INTO other")
    with pytest.raises(ContractViolation, match="absent"):
        generate_fixture_canonical_bars(manifest=_manifest(other, row_count=1), artifact=other, dataset_root=tmp_path)


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (_row("AMD", 29), "outside manifest"),
        ("INSERT INTO bars VALUES ('AMD','2026-09-08T13:30:00+00:00','100','99','98','100',1,'2026-09-08T13:30:01+00:00');", "OHLC envelope"),
        ("INSERT INTO bars VALUES ('AMD','2026-09-08T13:30:00+00:00','100','101','99','100',-1,'2026-09-08T13:30:01+00:00');", "volume"),
        ("INSERT INTO bars VALUES ('AMD','2026-09-08T13:30:00+00:00','100','101','99','100',1,'2026-09-08T13:29:59+00:00');", "receipt_time"),
    ],
)
def test_invalid_bar_values_and_times_fail_closed(tmp_path: Path, row: str, message: str) -> None:
    artifact = _sql((row,))
    with pytest.raises(ContractViolation, match=message):
        generate_fixture_canonical_bars(manifest=_manifest(artifact, row_count=1), artifact=artifact, dataset_root=tmp_path)


def test_duplicate_and_conflicting_bar_keys_are_rejected(tmp_path: Path) -> None:
    duplicate = _sql((_row("AMD", 30), _row("AMD", 30)))
    with pytest.raises(ContractViolation, match="duplicate"):
        generate_fixture_canonical_bars(manifest=_manifest(duplicate, row_count=2), artifact=duplicate, dataset_root=tmp_path)

    conflict = _sql((_row("AMD", 30), _row("AMD", 30, close="100.7", receipt_offset=2)))
    with pytest.raises(ContractViolation, match="conflicting"):
        generate_fixture_canonical_bars(manifest=_manifest(conflict, row_count=2), artifact=conflict, dataset_root=tmp_path)


def test_existing_dataset_path_with_different_bytes_is_rejected(tmp_path: Path) -> None:
    artifact = _sql((_row("AMD", 30),))
    manifest = _manifest(artifact, row_count=1)
    relative = f"canonical/{manifest.manifest_id}.parquet"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(b"tampered")

    with pytest.raises(ContractViolation, match="different bytes"):
        generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=tmp_path)


def test_result_and_parquet_metadata_do_not_embed_raw_sql_or_credentials(tmp_path: Path) -> None:
    artifact = _sql((_row("AMD", 30),))
    manifest = _manifest(artifact, row_count=1)
    result = generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=tmp_path)
    table = pq.read_table(tmp_path / result.relative_path)

    assert not hasattr(result, "artifact")
    assert not hasattr(result, "rows")
    assert table.schema.metadata == {b"orderscope_schema_version": CANONICAL_BAR_DATASET_SCHEMA_VERSION.encode("ascii")}
    assert all("key" not in name.casefold() and "secret" not in name.casefold() for name in table.column_names)
