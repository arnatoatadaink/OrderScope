from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import pytest

from orderscope_local.contracts import (
    AcquisitionCheckpoint,
    BoundedWindow,
    CheckpointScope,
    CheckpointState,
    ContentHash,
    ContractViolation,
    Fact,
    FactAssertionKind,
    Provenance,
    SourceReference,
)
from orderscope_local.integration import (
    SourceCoverageInput,
    summarize_corporate_coverage,
)
from orderscope_local.local_api import (
    LOCAL_READ_API_SCHEMA_VERSION,
    LocalReadSnapshot,
    LocalServerBinding,
    create_read_app,
)


UTC = timezone.utc
BASE = datetime(2026, 9, 9, 13, 30, tzinfo=UTC)


def _fact(record_id: str, fact_type: str, *, subject_ref: str = "AMD", available_offset: int = 0) -> Fact:
    accepted = BASE + timedelta(seconds=available_offset)
    provenance = Provenance(
        source_ref=SourceReference(f"https://example.test/{record_id}"),
        content_hash=ContentHash("1" * 64),
        available_at=accepted,
        retrieved_at=accepted,
        accepted_at=accepted,
    )
    return Fact(
        record_id=record_id,
        schema_version="fixture-v1",
        subject_ref=subject_ref,
        accepted_at=accepted,
        created_at=accepted,
        provenance=provenance,
        fact_type=fact_type,
        value={"status": "fixture"},
        assertion_kind=FactAssertionKind.PENDING_REVIEW,
        evidence_record_ids=(),
    )


def _coverage():
    checkpoint = AcquisitionCheckpoint(
        scope=CheckpointScope("sec", "filings"),
        window=BoundedWindow(BASE - timedelta(hours=1), BASE),
        state=CheckpointState.COMPLETE,
        observed_at=BASE,
    )
    return summarize_corporate_coverage(
        as_of=BASE + timedelta(minutes=5),
        sources=(SourceCoverageInput(provider_key="sec", source_key="filings", checkpoints=(checkpoint,)),),
    )


def _client() -> TestClient:
    snapshot = LocalReadSnapshot(
        facts=(
            _fact("fact-filing", "filing.detected"),
            _fact("fact-earnings", "earnings.revenue", available_offset=1),
            _fact("fact-news", "news.event.contract", available_offset=2),
            _fact("fact-official", "official.statement", available_offset=3),
        ),
        coverage=_coverage(),
    )
    return TestClient(create_read_app(snapshot=snapshot))


def test_read_app_keeps_exact_localhost_binding_and_health_contract() -> None:
    app = create_read_app(snapshot=LocalReadSnapshot())
    assert app.state.local_binding == LocalServerBinding()
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["bind_host"] == "127.0.0.1"


def test_facts_returns_as_of_safe_sorted_metadata_and_value() -> None:
    response = _client().get("/facts", params={"as_of": (BASE + timedelta(seconds=1)).isoformat()})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == LOCAL_READ_API_SCHEMA_VERSION
    assert [item["record_id"] for item in body["items"]] == ["fact-filing", "fact-earnings"]
    assert body["items"][0]["value"] == {"status": "fixture"}
    assert "provenance" not in body["items"][0]


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/filings", "fact-filing"),
        ("/earnings", "fact-earnings"),
        ("/news", "fact-news"),
    ],
)
def test_domain_routes_expose_only_their_fact_classification(path: str, expected: str) -> None:
    response = _client().get(path, params={"as_of": (BASE + timedelta(minutes=1)).isoformat()})
    assert response.status_code == 200
    assert [item["record_id"] for item in response.json()["items"]] == [expected]


def test_subject_filter_is_exact_and_does_not_guess_ticker_aliases() -> None:
    response = _client().get("/facts", params={"subject_ref": "NVDA"})
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_sources_health_exposes_accepted_coverage_summary_only() -> None:
    response = _client().get("/sources/health")
    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert source["provider_key"] == "sec"
    assert source["source_key"] == "filings"
    assert source["latest_state"] == "complete"
    assert source["resume_cursor"] is None


def test_sources_health_handles_absent_coverage_without_fabrication() -> None:
    response = TestClient(create_read_app(snapshot=LocalReadSnapshot())).get("/sources/health")
    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert response.json()["as_of"] is None


def test_http_surface_is_read_only() -> None:
    client = _client()
    assert client.post("/facts").status_code == 405
    assert client.post("/news").status_code == 405
    assert client.delete("/sources/health").status_code == 405


@pytest.mark.parametrize("host", ["0.0.0.0", "localhost", "::1", "192.168.1.5"])
def test_read_app_reuses_strict_localhost_binding(host: str) -> None:
    with pytest.raises(ContractViolation, match="127.0.0.1"):
        create_read_app(snapshot=LocalReadSnapshot(), binding=LocalServerBinding(host=host))


def test_snapshot_requires_immutable_fact_tuple() -> None:
    with pytest.raises(ContractViolation, match="immutable tuple"):
        LocalReadSnapshot(facts=[_fact("fact-a", "news.event.contract")])
