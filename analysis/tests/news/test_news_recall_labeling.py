from __future__ import annotations

import json
from pathlib import Path

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.news.recall_labeling import finalize_benchmark, write_label_template


START = "2026-08-11T00:00:00+00:00"
END = "2026-09-10T00:00:00+00:00"


def _reference(path: Path) -> Path:
    payload = {
        "schema_version": "news-recall-benchmark-v0.1",
        "benchmark_id": "fixture-v1",
        "window_start": START,
        "window_end": END,
        "references": [
            {
                "reference_id": "ref-amd",
                "subject_ref": "AMD",
                "event_type": "financing",
                "available_at": "2026-08-17T16:00:00+00:00",
                "source_kind": "sec",
            }
        ],
        "discoveries": [],
        "unresolved_labels": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _candidates(path: Path) -> Path:
    payload = {
        "schema_version": "news-recall-candidates-v0.1",
        "provider_key": "alpaca-news",
        "window_start": START,
        "window_end": END,
        "candidate_count": 2,
        "candidates": [
            {
                "provider_article_id": "10",
                "query_symbols": ["AMD"],
                "headline": "AMD financing event",
                "publisher": "wire",
                "article_url": "https://example.test/10",
                "provider_symbols": ["AMD"],
                "provider_published_at": "2026-08-17T15:30:00+00:00",
            },
            {
                "provider_article_id": "11",
                "query_symbols": ["AMD"],
                "headline": "Other AMD story",
                "publisher": "wire",
                "article_url": "https://example.test/11",
                "provider_symbols": ["AMD"],
                "provider_published_at": "2026-08-18T12:00:00+00:00",
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _labels(path: Path, first: str = "matched", second: str = "unrelated") -> Path:
    payload = {
        "schema_version": "news-recall-labels-v0.1",
        "window_start": START,
        "window_end": END,
        "labels": [
            {
                "provider_article_id": "10",
                "headline": "AMD financing event",
                "publisher": "wire",
                "provider_published_at": "2026-08-17T15:30:00+00:00",
                "query_symbols": ["AMD"],
                "provider_symbols": ["AMD"],
                "decision": first,
                "reference_id": "ref-amd" if first == "matched" else None,
                "assigned_subject_ref": "AMD" if first in {"matched", "unresolved"} else None,
                "reason": "ambiguous" if first == "unresolved" else None,
            },
            {
                "provider_article_id": "11",
                "headline": "Other AMD story",
                "publisher": "wire",
                "provider_published_at": "2026-08-18T12:00:00+00:00",
                "query_symbols": ["AMD"],
                "provider_symbols": ["AMD"],
                "decision": second,
                "reference_id": None,
                "assigned_subject_ref": None,
                "reason": None,
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_label_template_requires_explicit_review(tmp_path: Path) -> None:
    candidate = _candidates(tmp_path / "candidates.json")
    output = write_label_template(data_root=tmp_path, filename="labels.json", candidate_path=candidate)
    body = json.loads(output.read_text(encoding="utf-8"))
    assert [item["decision"] for item in body["labels"]] == ["unreviewed", "unreviewed"]


def test_finalize_emits_only_matched_discovery_and_preserves_provider_time(tmp_path: Path) -> None:
    benchmark = finalize_benchmark(
        reference_path=_reference(tmp_path / "reference.json"),
        candidate_path=_candidates(tmp_path / "candidates.json"),
        label_path=_labels(tmp_path / "labels.json"),
        output_path=tmp_path / "final.json",
    )
    assert len(benchmark.discoveries) == 1
    assert benchmark.discoveries[0].reference_id == "ref-amd"
    assert benchmark.discoveries[0].observed_at.isoformat() == "2026-08-17T15:30:00+00:00"
    assert benchmark.evaluate().reference_results[0].lag_seconds == -1800


def test_finalize_rejects_unreviewed_candidate(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation, match="explicitly reviewed"):
        finalize_benchmark(
            reference_path=_reference(tmp_path / "reference.json"),
            candidate_path=_candidates(tmp_path / "candidates.json"),
            label_path=_labels(tmp_path / "labels.json", first="matched", second="unreviewed"),
            output_path=tmp_path / "final.json",
        )


def test_finalize_requires_labels_for_every_candidate(tmp_path: Path) -> None:
    label_path = _labels(tmp_path / "labels.json")
    payload = json.loads(label_path.read_text(encoding="utf-8"))
    payload["labels"].pop()
    label_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ContractViolation, match="cover every candidate"):
        finalize_benchmark(
            reference_path=_reference(tmp_path / "reference.json"),
            candidate_path=_candidates(tmp_path / "candidates.json"),
            label_path=label_path,
            output_path=tmp_path / "final.json",
        )


def test_unresolved_candidate_is_not_counted_as_discovery(tmp_path: Path) -> None:
    benchmark = finalize_benchmark(
        reference_path=_reference(tmp_path / "reference.json"),
        candidate_path=_candidates(tmp_path / "candidates.json"),
        label_path=_labels(tmp_path / "labels.json", first="unresolved"),
        output_path=tmp_path / "final.json",
    )
    assert benchmark.discoveries == ()
    assert len(benchmark.unresolved_labels) == 1
    assert benchmark.unresolved_labels[0].reason == "ambiguous"


def test_unknown_reference_id_fails_closed(tmp_path: Path) -> None:
    labels = _labels(tmp_path / "labels.json")
    payload = json.loads(labels.read_text(encoding="utf-8"))
    payload["labels"][0]["reference_id"] = "missing-ref"
    labels.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ContractViolation, match="unknown benchmark reference"):
        finalize_benchmark(
            reference_path=_reference(tmp_path / "reference.json"),
            candidate_path=_candidates(tmp_path / "candidates.json"),
            label_path=labels,
            output_path=tmp_path / "final.json",
        )
