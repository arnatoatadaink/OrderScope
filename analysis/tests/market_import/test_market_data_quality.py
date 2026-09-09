from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.market_import import (
    D1ExportManifest,
    MarketDataQualityIssueKind,
    SessionWindow,
    evaluate_market_data_quality,
    generate_fixture_canonical_bars,
)


UTC = timezone.utc
BASE = datetime(2026, 9, 9, 13, 30, tzinfo=UTC)


def _artifact(rows: tuple[tuple[object, ...], ...]) -> bytes:
    values = ",\n".join(
        "(" + ", ".join(_sql(value) for value in row) + ")" for row in rows
    )
    return (
        "CREATE TABLE bars (\n"
        "symbol TEXT NOT NULL,\n"
        "bar_time TEXT NOT NULL,\n"
        "open TEXT NOT NULL,\n"
        "high TEXT NOT NULL,\n"
        "low TEXT NOT NULL,\n"
        "close TEXT NOT NULL,\n"
        "volume INTEGER NOT NULL,\n"
        "receipt_time TEXT NOT NULL\n"
        ");\n"
        "INSERT INTO bars VALUES\n"
        f"{values};\n"
    ).encode("utf-8")


def _sql(value: object) -> str:
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _rows() -> tuple[tuple[object, ...], ...]:
    return (
        ("AMD", BASE.isoformat(), "10", "11", "9", "10.5", 100, (BASE + timedelta(seconds=2)).isoformat()),
        ("AMD", (BASE + timedelta(minutes=1)).isoformat(), "10.5", "11.5", "10", "11", 120, (BASE + timedelta(minutes=1, seconds=2)).isoformat()),
        ("AMD", (BASE + timedelta(minutes=2)).isoformat(), "11", "12", "10.5", "11.5", 140, (BASE + timedelta(minutes=2, seconds=2)).isoformat()),
    )


def _dataset(tmp_path: Path, rows: tuple[tuple[object, ...], ...] | None = None):
    rows = rows or _rows()
    artifact = _artifact(rows)
    manifest = D1ExportManifest(
        source_environment="fixture",
        source_revision="fixture-v1",
        window_start=BASE,
        window_end=BASE + timedelta(minutes=10),
        table_name="bars",
        row_count=len(rows),
        byte_size=len(artifact),
        sha256=sha256(artifact).hexdigest(),
    )
    dataset = generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=tmp_path)
    return dataset


def _window(*, minutes: int = 3, cadence: int = 1) -> SessionWindow:
    return SessionWindow(
        name="regular-fixture",
        start=BASE,
        end=BASE + timedelta(minutes=minutes),
        cadence=timedelta(minutes=cadence),
    )


def _rewrite(path: Path, transform) -> None:
    table = pq.read_table(path)
    replacement = transform(table)
    pq.write_table(replacement, path, compression="zstd", use_dictionary=False, write_statistics=True)


def _kinds(report) -> set[MarketDataQualityIssueKind]:
    return {issue.kind for issue in report.issues}


def test_complete_fixture_dataset_passes_schema_identity_ohlcv_and_session_grid(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )

    assert report.passed
    assert report.row_count == 3
    assert report.expected_grid_points == 3
    assert report.symbols == ("AMD",)
    assert report.issues == ()


def test_missing_grid_point_is_reported_without_inventing_bar(tmp_path: Path) -> None:
    rows = (_rows()[0], _rows()[2])
    dataset = _dataset(tmp_path, rows)
    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )

    missing = [issue for issue in report.issues if issue.kind is MarketDataQualityIssueKind.MISSING_GRID_POINT]
    assert [issue.bar_time for issue in missing] == [BASE + timedelta(minutes=1)]


def test_off_grid_bar_is_reported(tmp_path: Path) -> None:
    rows = _rows() + (("AMD", (BASE + timedelta(minutes=4)).isoformat(), "11", "12", "10", "11", 1, (BASE + timedelta(minutes=4, seconds=1)).isoformat()),)
    dataset = _dataset(tmp_path, rows)
    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )

    assert MarketDataQualityIssueKind.OFF_GRID_POINT in _kinds(report)


def test_dataset_hash_tamper_is_observable(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    path = tmp_path / dataset.relative_path
    _rewrite(path, lambda table: table.replace_schema_metadata({**(table.schema.metadata or {}), b"extra": b"tamper"}))

    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )
    assert MarketDataQualityIssueKind.DATASET_HASH in _kinds(report)


def test_schema_drift_is_reported(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    path = tmp_path / dataset.relative_path
    _rewrite(path, lambda table: table.drop(["source_revision"]))

    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )
    assert MarketDataQualityIssueKind.SCHEMA in _kinds(report)


def test_duplicate_and_conflicting_identities_are_distinguished(tmp_path: Path) -> None:
    duplicate_dataset = _dataset(tmp_path / "duplicate")
    duplicate_path = (tmp_path / "duplicate") / duplicate_dataset.relative_path
    _rewrite(duplicate_path, lambda table: pa.concat_tables([table, table.slice(0, 1)]))
    duplicate_report = evaluate_market_data_quality(
        dataset=duplicate_dataset,
        dataset_root=tmp_path / "duplicate",
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )
    assert MarketDataQualityIssueKind.IDENTITY_DUPLICATE in _kinds(duplicate_report)

    conflict_dataset = _dataset(tmp_path / "conflict")
    conflict_path = (tmp_path / "conflict") / conflict_dataset.relative_path

    def conflict(table: pa.Table) -> pa.Table:
        records = table.to_pylist()
        changed = dict(records[0])
        changed["close"] = changed["close"] + 1
        return pa.Table.from_pylist(records + [changed], schema=table.schema)

    _rewrite(conflict_path, conflict)
    conflict_report = evaluate_market_data_quality(
        dataset=conflict_dataset,
        dataset_root=tmp_path / "conflict",
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )
    assert MarketDataQualityIssueKind.IDENTITY_CONFLICT in _kinds(conflict_report)


def test_ohlcv_and_receipt_order_are_revalidated_on_parquet(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    path = tmp_path / dataset.relative_path

    def mutate(table: pa.Table) -> pa.Table:
        records = table.to_pylist()
        records[0]["high"] = records[0]["low"]
        records[1]["receipt_time"] = records[1]["bar_time"] - timedelta(seconds=1)
        return pa.Table.from_pylist(records, schema=table.schema)

    _rewrite(path, mutate)
    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )
    assert MarketDataQualityIssueKind.OHLCV in _kinds(report)
    assert MarketDataQualityIssueKind.RECEIPT_ORDER in _kinds(report)


def test_row_provenance_must_match_dataset_descriptor(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    path = tmp_path / dataset.relative_path

    def mutate(table: pa.Table) -> pa.Table:
        records = table.to_pylist()
        records[0]["source_manifest_id"] = "d1-export-" + "0" * 64
        return pa.Table.from_pylist(records, schema=table.schema)

    _rewrite(path, mutate)
    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD",),
        session_windows=(_window(),),
    )
    assert MarketDataQualityIssueKind.PROVENANCE in _kinds(report)


def test_expected_symbol_without_rows_produces_full_grid_gap(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    report = evaluate_market_data_quality(
        dataset=dataset,
        dataset_root=tmp_path,
        expected_symbols=("AMD", "NVDA"),
        session_windows=(_window(),),
    )
    missing_nvda = [
        issue for issue in report.issues
        if issue.kind is MarketDataQualityIssueKind.MISSING_GRID_POINT and issue.symbol == "NVDA"
    ]
    assert len(missing_nvda) == 3


def test_session_windows_must_be_utc_aligned_nonoverlapping_and_positive() -> None:
    with pytest.raises(ContractViolation, match="normalized to UTC"):
        SessionWindow(name="bad", start=BASE.replace(tzinfo=None), end=(BASE + timedelta(minutes=1)).replace(tzinfo=None), cadence=timedelta(minutes=1))
    with pytest.raises(ContractViolation, match="positive"):
        SessionWindow(name="bad", start=BASE, end=BASE + timedelta(minutes=1), cadence=timedelta(0))
    with pytest.raises(ContractViolation, match="align"):
        SessionWindow(name="bad", start=BASE, end=BASE + timedelta(seconds=90), cadence=timedelta(minutes=1))

    dataset_root = Path("unused")
    # Overlap is validated by the evaluator before any dataset path is touched.
    window_a = SessionWindow(name="a", start=BASE, end=BASE + timedelta(minutes=2), cadence=timedelta(minutes=1))
    window_b = SessionWindow(name="b", start=BASE + timedelta(minutes=1), end=BASE + timedelta(minutes=3), cadence=timedelta(minutes=1))
    fake = object()
    with pytest.raises(ContractViolation, match="dataset must"):
        evaluate_market_data_quality(dataset=fake, dataset_root=dataset_root, expected_symbols=("AMD",), session_windows=(window_a, window_b))


def test_quality_report_is_deterministic_for_same_dataset_and_grid(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    kwargs = dict(dataset=dataset, dataset_root=tmp_path, expected_symbols=("AMD",), session_windows=(_window(),))
    assert evaluate_market_data_quality(**kwargs) == evaluate_market_data_quality(**kwargs)
