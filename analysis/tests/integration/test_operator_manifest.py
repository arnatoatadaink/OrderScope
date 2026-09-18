from __future__ import annotations

import json

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.integration.operator import OPERATOR_SNAPSHOT_SCHEMA_VERSION, WorkState, load_operator_snapshot


def _payload():
    return {
        "schema_version": OPERATOR_SNAPSHOT_SCHEMA_VERSION,
        "retention": [{
            "content_ref": "temp://news/due-1",
            "due_at": "2026-09-12T00:00:00+00:00",
            "state": "RETRYABLE",
            "failure_category": "DELETE_FAILED",
        }],
        "replay": [{
            "work_id": "news-retry-1",
            "source": "alpaca-news",
            "start": "2026-09-11T23:00:00+00:00",
            "end": "2026-09-12T00:00:00+00:00",
            "state": "FAILED",
            "failure_category": "TRANSPORT",
        }],
    }


def test_loader_accepts_metadata_only_allowlisted_snapshot(tmp_path):
    path = tmp_path / "operator.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")
    snapshot = load_operator_snapshot(path)
    assert snapshot.retention[0].content_ref == "temp://news/due-1"
    assert snapshot.retention[0].state is WorkState.RETRYABLE
    assert snapshot.replay[0].work_id == "news-retry-1"
    assert snapshot.replay[0].state is WorkState.FAILED


def test_loader_rejects_raw_body_or_credential_extension_fields(tmp_path):
    for key, value in (("body", "raw-news-body"), ("api_key", "secret-value")):
        payload = _payload()
        payload["replay"][0][key] = value
        path = tmp_path / f"operator-{key}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ContractViolation, match="unsupported fields"):
            load_operator_snapshot(path)


def test_loader_rejects_unknown_schema_and_non_utc_times(tmp_path):
    payload = _payload()
    payload["schema_version"] = "future-v9"
    path = tmp_path / "future.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ContractViolation, match="schema_version"):
        load_operator_snapshot(path)

    payload = _payload()
    payload["replay"][0]["start"] = "2026-09-11T23:00:00"
    path = tmp_path / "naive.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ContractViolation, match="normalized to UTC"):
        load_operator_snapshot(path)
