from __future__ import annotations

import json

from typer.testing import CliRunner

from orderscope_local import cli
from orderscope_local.integration.operator import OPERATOR_SNAPSHOT_SCHEMA_VERSION


runner = CliRunner()


def _write_snapshot(tmp_path):
    path = tmp_path / "operator.json"
    path.write_text(json.dumps({
        "schema_version": OPERATOR_SNAPSHOT_SCHEMA_VERSION,
        "retention": [
            {"content_ref": "temp://due", "due_at": "2026-09-12T00:00:00+00:00", "state": "PENDING"},
            {"content_ref": "temp://future", "due_at": "2026-09-12T02:00:00+00:00", "state": "PENDING"},
        ],
        "replay": [
            {"work_id": "r1", "source": "alpaca-news", "start": "2026-09-11T22:00:00+00:00", "end": "2026-09-11T23:00:00+00:00", "state": "FAILED", "failure_category": "TRANSPORT"},
            {"work_id": "done", "source": "alpaca-news", "start": "2026-09-11T23:00:00+00:00", "end": "2026-09-12T00:00:00+00:00", "state": "COMPLETE"},
        ],
    }), encoding="utf-8")
    return path


def test_operator_inspect_reports_metadata_counts_only(tmp_path):
    path = _write_snapshot(tmp_path)
    result = runner.invoke(cli.app, [
        "operator", "inspect", "--snapshot", str(path), "--now", "2026-09-12T01:00:00Z",
    ])
    assert result.exit_code == 0
    assert "retention_pending=2" in result.stdout
    assert "due=1" in result.stdout
    assert "replay_retryable=1" in result.stdout
    assert "TRANSPORT" not in result.stdout


def test_operator_replay_plan_is_dry_run_and_bounded(tmp_path):
    path = _write_snapshot(tmp_path)
    result = runner.invoke(cli.app, [
        "operator", "replay-plan", "--snapshot", str(path), "--source", "alpaca-news",
        "--start", "2026-09-11T21:00:00Z", "--end", "2026-09-12T00:00:00Z", "--max-items", "1",
    ])
    assert result.exit_code == 0
    assert "selected=1" in result.stdout
    assert "dry_run=true" in result.stdout
    assert "work_ids=r1" in result.stdout
    assert "done" not in result.stdout


def test_operator_delete_plan_requires_explicit_due_reference(tmp_path):
    path = _write_snapshot(tmp_path)
    result = runner.invoke(cli.app, [
        "operator", "delete-plan", "--snapshot", str(path), "--content-ref", "temp://due",
        "--now", "2026-09-12T01:00:00Z", "--max-items", "1",
    ])
    assert result.exit_code == 0
    assert "selected=1" in result.stdout
    assert "dry_run=true" in result.stdout
    assert "temp://due" in result.stdout

    rejected = runner.invoke(cli.app, [
        "operator", "delete-plan", "--snapshot", str(path), "--content-ref", "temp://future",
        "--now", "2026-09-12T01:00:00Z", "--max-items", "1",
    ])
    assert rejected.exit_code != 0
