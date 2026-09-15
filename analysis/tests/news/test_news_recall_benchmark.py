from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.news import (
    NEWS_RECALL_BENCHMARK_SCHEMA_VERSION,
    decode_news_recall_benchmark,
    load_news_recall_benchmark,
    render_news_recall_markdown,
)

UTC = timezone.utc
START = datetime(2026, 6, 1, tzinfo=UTC)
END = datetime(2026, 8, 31, tzinfo=UTC)


def _payload() -> dict[str, object]:
    return {
        "schema_version": NEWS_RECALL_BENCHMARK_SCHEMA_VERSION,
        "benchmark_id": "amd-nvda-2026q3",
        "window_start": START.isoformat(),
        "window_end": END.isoformat(),
        "references": [
            {
                "reference_id": "ref-amd-earnings",
                "subject_ref": "AMD",
                "event_type": "earnings",
                "available_at": "2026-08-04T20:00:00+00:00",
                "source_kind": "ir",
            },
            {
                "reference_id": "ref-nvda-earnings",
                "subject_ref": "NVDA",
                "event_type": "earnings",
                "available_at": "2026-08-26T20:00:00+00:00",
                "source_kind": "sec",
            },
        ],
        "discoveries": [
            {
                "discovery_id": "news-amd-1",
                "reference_id": "ref-amd-earnings",
                "assigned_subject_ref": "AMD",
                "observed_at": "2026-08-04T20:00:30+00:00",
            },
            {
                "discovery_id": "news-nvda-1",
                "reference_id": "ref-nvda-earnings",
                "assigned_subject_ref": "AMD",
                "observed_at": "2026-08-26T19:59:00+00:00",
            },
        ],
        "unresolved_labels": [
            {
                "case_id": "unresolved-1",
                "subject_ref": "AMD",
                "observed_at": "2026-07-15T12:00:00+00:00",
                "reason": "Headline could refer to either partnership expansion or a new contract.",
            }
        ],
    }


def test_decode_benchmark_and_evaluate_measured_fields() -> None:
    benchmark = decode_news_recall_benchmark(_payload())
    report = benchmark.evaluate()
    assert benchmark.benchmark_id == "amd-nvda-2026q3"
    assert report.reference_count == 2
    assert report.discovered_reference_count == 2
    assert report.discovery_rate == 1.0
    assert report.ticker_misattribution_count == 1
    assert report.reference_results[0].lag_seconds == 30
    assert report.reference_results[1].lag_seconds == -60


def test_load_benchmark_reads_utf8_json(tmp_path) -> None:
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")
    benchmark = load_news_recall_benchmark(path)
    assert benchmark.schema_version == NEWS_RECALL_BENCHMARK_SCHEMA_VERSION
    assert len(benchmark.unresolved_labels) == 1


def test_benchmark_rejects_unknown_fields() -> None:
    payload = _payload()
    payload["unexpected"] = "value"
    with pytest.raises(ContractViolation, match="unsupported fields"):
        decode_news_recall_benchmark(payload)


def test_benchmark_rejects_unresolved_label_outside_window() -> None:
    payload = _payload()
    payload["unresolved_labels"][0]["observed_at"] = "2026-09-01T00:00:00+00:00"
    with pytest.raises(ContractViolation, match="outside evaluation window"):
        decode_news_recall_benchmark(payload)


def test_benchmark_rejects_non_taxonomy_reference_type() -> None:
    payload = _payload()
    payload["references"][0]["event_type"] = "rumor"
    with pytest.raises(ContractViolation, match="active News taxonomy"):
        decode_news_recall_benchmark(payload)


def test_markdown_report_surfaces_signed_lag_misattribution_and_unresolved_labels() -> None:
    benchmark = decode_news_recall_benchmark(_payload())
    markdown = render_news_recall_markdown(benchmark=benchmark)
    assert "Discovery rate: **1.0000**" in markdown
    assert "Subject/ticker misattributions: **1** (0.5000)" in markdown
    assert "Median signed lag: **-15.0 s**" in markdown
    assert "Unresolved benchmark labels: **1**" in markdown
    assert "unresolved-1" in markdown
