from datetime import datetime, timezone

from fastapi.testclient import TestClient
import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.local_api import LocalReadSnapshot, create_read_app
from orderscope_local.market_import import (
    CANONICAL_BAR_DATASET_SCHEMA_VERSION,
    MARKET_DATA_QUALITY_SCHEMA_VERSION,
    CanonicalBarDataset,
    MarketDataQualityReport,
    RawImportResult,
)


UTC = timezone.utc
REGISTERED = datetime(2026, 9, 10, 1, 0, tzinfo=UTC)
ARTIFACT_HASH = "a" * 64
PARQUET_HASH = "b" * 64
MANIFEST_ID = "d1-export-fixture-l1-006"


def _import() -> RawImportResult:
    return RawImportResult(
        status="new",
        manifest_id=MANIFEST_ID,
        sha256=ARTIFACT_HASH,
        raw_relative_path=f"d1/{ARTIFACT_HASH}.sql",
        registered_at=REGISTERED,
    )


def _dataset() -> CanonicalBarDataset:
    return CanonicalBarDataset(
        schema_version=CANONICAL_BAR_DATASET_SCHEMA_VERSION,
        manifest_id=MANIFEST_ID,
        artifact_sha256=ARTIFACT_HASH,
        row_count=4,
        relative_path=f"canonical/{MANIFEST_ID}.parquet",
        parquet_sha256=PARQUET_HASH,
    )


def _quality() -> MarketDataQualityReport:
    return MarketDataQualityReport(
        schema_version=MARKET_DATA_QUALITY_SCHEMA_VERSION,
        dataset_manifest_id=MANIFEST_ID,
        dataset_parquet_sha256=PARQUET_HASH,
        row_count=4,
        symbols=("AMD", "NVDA"),
        expected_grid_points=4,
        issues=(),
    )


def _client() -> TestClient:
    return TestClient(
        create_read_app(
            snapshot=LocalReadSnapshot(
                imports=(_import(),),
                datasets=(_dataset(),),
                quality_reports=(_quality(),),
            )
        )
    )


def test_imports_exposes_sanitized_immutable_catalog_view() -> None:
    response = _client().get("/imports")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0] == {
        "status": "new",
        "manifest_id": MANIFEST_ID,
        "sha256": ARTIFACT_HASH,
        "raw_relative_path": f"d1/{ARTIFACT_HASH}.sql",
        "registered_at": REGISTERED.isoformat(),
    }


def test_datasets_exposes_descriptor_not_parquet_body() -> None:
    response = _client().get("/datasets")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["manifest_id"] == MANIFEST_ID
    assert item["row_count"] == 4
    assert item["relative_path"].startswith("canonical/")
    assert "rows" not in item
    assert "body" not in item


def test_quality_latest_exposes_latest_accepted_quality_descriptor() -> None:
    response = _client().get("/quality/latest")
    assert response.status_code == 200
    quality = response.json()["quality"]
    assert quality["dataset_manifest_id"] == MANIFEST_ID
    assert quality["symbols"] == ["AMD", "NVDA"]
    assert quality["passed"] is True
    assert quality["issues"] == []


def test_coverage_latest_is_derived_from_latest_quality_and_dataset() -> None:
    response = _client().get("/coverage/latest")
    assert response.status_code == 200
    coverage = response.json()["coverage"]
    assert coverage["dataset_manifest_id"] == MANIFEST_ID
    assert coverage["row_count"] == 4
    assert coverage["expected_grid_points"] == 4
    assert coverage["issue_count"] == 0
    assert coverage["passed"] is True
    assert coverage["dataset_relative_path"] == f"canonical/{MANIFEST_ID}.parquet"


def test_latest_routes_do_not_fabricate_absent_market_state() -> None:
    client = TestClient(create_read_app(snapshot=LocalReadSnapshot()))
    assert client.get("/quality/latest").json()["quality"] is None
    assert client.get("/coverage/latest").json()["coverage"] is None
    assert client.get("/imports").json()["items"] == []
    assert client.get("/datasets").json()["items"] == []


def test_l1_006_http_surface_remains_read_only() -> None:
    client = _client()
    for path in ("/imports", "/datasets", "/quality/latest", "/coverage/latest"):
        assert client.post(path).status_code == 405
        assert client.delete(path).status_code == 405


def test_snapshot_rejects_mutable_market_collections() -> None:
    with pytest.raises(ContractViolation, match="imports must be an immutable tuple"):
        LocalReadSnapshot(imports=[_import()])
    with pytest.raises(ContractViolation, match="datasets must be an immutable tuple"):
        LocalReadSnapshot(datasets=[_dataset()])
    with pytest.raises(ContractViolation, match="quality_reports must be an immutable tuple"):
        LocalReadSnapshot(quality_reports=[_quality()])
