from __future__ import annotations

import json

from typer.testing import CliRunner

from orderscope_local import cli
from orderscope_local.news import NEWS_RECALL_BENCHMARK_SCHEMA_VERSION


runner = CliRunner()


def test_root_help_lists_required_commands() -> None:
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "serve" in result.stdout
    assert "import" in result.stdout
    assert "quality" in result.stdout
    assert "schedule" in result.stdout


def test_import_group_is_cli_only_boundary() -> None:
    result = runner.invoke(cli.app, ["import", "status"])
    assert result.exit_code == 0
    assert "CLI-only" in result.stdout


def test_quality_group_is_cli_only_boundary() -> None:
    result = runner.invoke(cli.app, ["quality", "status"])
    assert result.exit_code == 0
    assert "CLI-only" in result.stdout


def test_quality_news_recall_evaluates_explicit_benchmark(tmp_path) -> None:
    path = tmp_path / "benchmark.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": NEWS_RECALL_BENCHMARK_SCHEMA_VERSION,
                "benchmark_id": "cli-fixture",
                "window_start": "2026-06-01T00:00:00+00:00",
                "window_end": "2026-08-31T00:00:00+00:00",
                "references": [
                    {
                        "reference_id": "ref-1",
                        "subject_ref": "AMD",
                        "event_type": "earnings",
                        "available_at": "2026-08-04T20:00:00+00:00",
                        "source_kind": "ir",
                    }
                ],
                "discoveries": [
                    {
                        "discovery_id": "news-1",
                        "reference_id": "ref-1",
                        "assigned_subject_ref": "AMD",
                        "observed_at": "2026-08-04T20:01:00+00:00",
                    }
                ],
                "unresolved_labels": [],
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(cli.app, ["quality", "news-recall", "--benchmark", str(path)])
    assert result.exit_code == 0
    assert "News Recall Benchmark — cli-fixture" in result.stdout
    assert "Discovery rate: **1.0000**" in result.stdout


def test_serve_uses_literal_loopback_and_read_only_app(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)
    result = runner.invoke(cli.app, ["serve", "--port", "8123"])

    assert result.exit_code == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8123
    app = captured["app"]
    methods = {method for route in app.routes for method in getattr(route, "methods", set())}
    assert not ({"POST", "PUT", "PATCH", "DELETE"} & methods)


def test_serve_has_no_host_override() -> None:
    result = runner.invoke(cli.app, ["serve", "--host", "0.0.0.0"])
    assert result.exit_code != 0


def test_serve_rejects_invalid_port() -> None:
    result = runner.invoke(cli.app, ["serve", "--port", "0"])
    assert result.exit_code != 0


def test_schedule_run_is_manual_cli_boundary(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ORDERSCOPE_DATA_ROOT", str(tmp_path))
    result = runner.invoke(cli.app, ["schedule", "run", "--max-jobs", "1"])
    assert result.exit_code == 0
    assert "selected=0 completed=0 dry_run=false" in result.stdout


def test_schedule_run_supports_dry_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ORDERSCOPE_DATA_ROOT", str(tmp_path))
    result = runner.invoke(cli.app, ["schedule", "run", "--max-jobs", "1", "--dry-run"])
    assert result.exit_code == 0
    assert "selected=0 completed=0 dry_run=true" in result.stdout
