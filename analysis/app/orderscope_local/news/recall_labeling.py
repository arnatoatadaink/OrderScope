"""Explicit candidate labeling and final benchmark construction for N1-006."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
import json
from pathlib import Path
from typing import Mapping

from orderscope_local.contracts import ContractViolation
from .recall_benchmark import (
    NEWS_RECALL_BENCHMARK_SCHEMA_VERSION,
    NewsRecallBenchmark,
    NewsRecallUnresolvedLabel,
    decode_news_recall_benchmark,
)
from .recall import NewsRecallDiscovery
from .recall_population import NEWS_RECALL_CANDIDATE_SCHEMA_VERSION

NEWS_RECALL_LABEL_SCHEMA_VERSION = "news-recall-labels-v0.1"


class NewsRecallLabelDecision(StrEnum):
    MATCHED = "matched"
    UNRELATED = "unrelated"
    UNRESOLVED = "unresolved"
    UNREVIEWED = "unreviewed"


@dataclass(frozen=True, slots=True)
class CandidateMetadata:
    provider_article_id: str
    query_symbols: tuple[str, ...]
    headline: str
    publisher: str
    article_url: str | None
    provider_symbols: tuple[str, ...]
    provider_published_at: datetime


@dataclass(frozen=True, slots=True)
class NewsRecallLabel:
    provider_article_id: str
    decision: NewsRecallLabelDecision
    reference_id: str | None = None
    assigned_subject_ref: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        _bounded(self.provider_article_id, "provider_article_id", 512)
        if not isinstance(self.decision, NewsRecallLabelDecision):
            raise ContractViolation("label decision is invalid")
        if self.decision is NewsRecallLabelDecision.MATCHED:
            if self.reference_id is None or self.assigned_subject_ref is None:
                raise ContractViolation("matched label requires reference_id and assigned_subject_ref")
            _bounded(self.reference_id, "reference_id", 128)
            _bounded(self.assigned_subject_ref, "assigned_subject_ref", 256)
            if self.reason is not None:
                raise ContractViolation("matched label cannot include unresolved reason")
        elif self.decision is NewsRecallLabelDecision.UNRESOLVED:
            if self.reason is None or self.assigned_subject_ref is None:
                raise ContractViolation("unresolved label requires assigned_subject_ref and reason")
            _bounded(self.assigned_subject_ref, "assigned_subject_ref", 256)
            _bounded(self.reason, "reason", 512)
            if self.reference_id is not None:
                raise ContractViolation("unresolved label cannot assert reference_id")
        else:
            if self.reference_id is not None or self.assigned_subject_ref is not None or self.reason is not None:
                raise ContractViolation("unrelated/unreviewed labels cannot include match metadata")


def load_candidate_metadata(path: str | Path) -> tuple[datetime, datetime, tuple[CandidateMetadata, ...]]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractViolation("candidate file must be readable UTF-8 JSON") from exc
    if not isinstance(payload, Mapping):
        raise ContractViolation("candidate file root must be a JSON object")
    expected = {"schema_version", "provider_key", "window_start", "window_end", "candidate_count", "candidates"}
    if set(payload) != expected:
        raise ContractViolation("candidate file contains missing or unsupported fields")
    if payload["schema_version"] != NEWS_RECALL_CANDIDATE_SCHEMA_VERSION:
        raise ContractViolation("unsupported candidate schema version")
    start = _timestamp(payload["window_start"], "window_start")
    end = _timestamp(payload["window_end"], "window_end")
    raw = payload["candidates"]
    if not isinstance(raw, list):
        raise ContractViolation("candidate file candidates must be an array")
    candidates = tuple(_decode_candidate(item) for item in raw)
    if payload["candidate_count"] != len(candidates):
        raise ContractViolation("candidate_count does not match candidates length")
    ids = tuple(item.provider_article_id for item in candidates)
    if len(ids) != len(set(ids)):
        raise ContractViolation("candidate provider_article_id values must be unique")
    return start, end, candidates


def write_label_template(*, data_root: Path, filename: str, candidate_path: str | Path) -> Path:
    start, end, candidates = load_candidate_metadata(candidate_path)
    destination = _destination(data_root, filename)
    payload = {
        "schema_version": NEWS_RECALL_LABEL_SCHEMA_VERSION,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "labels": [
            {
                "provider_article_id": item.provider_article_id,
                "headline": item.headline,
                "publisher": item.publisher,
                "provider_published_at": item.provider_published_at.isoformat(),
                "query_symbols": list(item.query_symbols),
                "provider_symbols": list(item.provider_symbols),
                "decision": "unreviewed",
                "reference_id": None,
                "assigned_subject_ref": None,
                "reason": None,
            }
            for item in candidates
        ],
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def finalize_benchmark(
    *,
    reference_path: str | Path,
    candidate_path: str | Path,
    label_path: str | Path,
    output_path: str | Path,
) -> NewsRecallBenchmark:
    reference = _load_reference(reference_path)
    start, end, candidates = load_candidate_metadata(candidate_path)
    if start != reference.window_start or end != reference.window_end:
        raise ContractViolation("candidate and reference windows must match")
    labels = _load_labels(label_path, start=start, end=end)
    candidate_by_id = {item.provider_article_id: item for item in candidates}
    if set(labels) != set(candidate_by_id):
        raise ContractViolation("labels must cover every candidate exactly once")
    if any(label.decision is NewsRecallLabelDecision.UNREVIEWED for label in labels.values()):
        raise ContractViolation("all candidates must be explicitly reviewed before finalization")
    reference_ids = {item.reference_id for item in reference.references}

    discoveries: list[NewsRecallDiscovery] = []
    unresolved: list[NewsRecallUnresolvedLabel] = []
    for article_id, label in labels.items():
        candidate = candidate_by_id[article_id]
        if label.decision is NewsRecallLabelDecision.MATCHED:
            if label.reference_id not in reference_ids:
                raise ContractViolation("matched label references unknown benchmark reference")
            discoveries.append(
                NewsRecallDiscovery(
                    discovery_id=f"alpaca-news-{article_id}",
                    reference_id=label.reference_id,
                    assigned_subject_ref=label.assigned_subject_ref,
                    observed_at=candidate.provider_published_at,
                )
            )
        elif label.decision is NewsRecallLabelDecision.UNRESOLVED:
            unresolved.append(
                NewsRecallUnresolvedLabel(
                    case_id=f"alpaca-news-{article_id}",
                    subject_ref=label.assigned_subject_ref,
                    observed_at=candidate.provider_published_at,
                    reason=label.reason,
                )
            )

    benchmark = NewsRecallBenchmark(
        schema_version=NEWS_RECALL_BENCHMARK_SCHEMA_VERSION,
        benchmark_id=reference.benchmark_id,
        window_start=reference.window_start,
        window_end=reference.window_end,
        references=reference.references,
        discoveries=tuple(sorted(discoveries, key=lambda item: (item.observed_at, item.discovery_id))),
        unresolved_labels=tuple(sorted(unresolved, key=lambda item: (item.observed_at, item.case_id))),
    )
    Path(output_path).write_text(_benchmark_json(benchmark), encoding="utf-8")
    return benchmark


def _load_reference(path: str | Path) -> NewsRecallBenchmark:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractViolation("reference benchmark must be readable UTF-8 JSON") from exc
    if not isinstance(payload, Mapping):
        raise ContractViolation("reference benchmark root must be a JSON object")
    benchmark = decode_news_recall_benchmark(payload)
    if benchmark.discoveries or benchmark.unresolved_labels:
        raise ContractViolation("reference seed must not contain discovery labels")
    return benchmark


def _load_labels(path: str | Path, *, start: datetime, end: datetime) -> dict[str, NewsRecallLabel]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractViolation("label file must be readable UTF-8 JSON") from exc
    if not isinstance(payload, Mapping) or set(payload) != {"schema_version", "window_start", "window_end", "labels"}:
        raise ContractViolation("label file contains missing or unsupported fields")
    if payload["schema_version"] != NEWS_RECALL_LABEL_SCHEMA_VERSION:
        raise ContractViolation("unsupported label schema version")
    if _timestamp(payload["window_start"], "window_start") != start or _timestamp(payload["window_end"], "window_end") != end:
        raise ContractViolation("label window must match candidate/reference window")
    raw = payload["labels"]
    if not isinstance(raw, list):
        raise ContractViolation("labels must be a JSON array")
    result: dict[str, NewsRecallLabel] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ContractViolation("label entry must be a JSON object")
        required = {
            "provider_article_id", "headline", "publisher", "provider_published_at",
            "query_symbols", "provider_symbols", "decision", "reference_id",
            "assigned_subject_ref", "reason",
        }
        if set(item) != required:
            raise ContractViolation("label entry contains missing or unsupported fields")
        try:
            decision = NewsRecallLabelDecision(item["decision"])
        except (ValueError, TypeError) as exc:
            raise ContractViolation("label decision is invalid") from exc
        label = NewsRecallLabel(
            provider_article_id=_text(item["provider_article_id"], "provider_article_id"),
            decision=decision,
            reference_id=_optional_text(item["reference_id"], "reference_id"),
            assigned_subject_ref=_optional_text(item["assigned_subject_ref"], "assigned_subject_ref"),
            reason=_optional_text(item["reason"], "reason"),
        )
        if label.provider_article_id in result:
            raise ContractViolation("duplicate provider_article_id in labels")
        result[label.provider_article_id] = label
    return result


def _decode_candidate(value: object) -> CandidateMetadata:
    if not isinstance(value, Mapping):
        raise ContractViolation("candidate entry must be a JSON object")
    required = {
        "provider_article_id", "query_symbols", "headline", "publisher", "article_url",
        "provider_symbols", "provider_published_at",
    }
    if set(value) != required:
        raise ContractViolation("candidate entry contains missing or unsupported fields")
    query_symbols = _string_tuple(value["query_symbols"], "query_symbols")
    provider_symbols = _string_tuple(value["provider_symbols"], "provider_symbols", allow_empty=True)
    return CandidateMetadata(
        provider_article_id=_text(value["provider_article_id"], "provider_article_id"),
        query_symbols=query_symbols,
        headline=_text(value["headline"], "headline"),
        publisher=_text(value["publisher"], "publisher"),
        article_url=_optional_text(value["article_url"], "article_url"),
        provider_symbols=provider_symbols,
        provider_published_at=_timestamp(value["provider_published_at"], "provider_published_at"),
    )


def _benchmark_json(benchmark: NewsRecallBenchmark) -> str:
    payload = {
        "schema_version": benchmark.schema_version,
        "benchmark_id": benchmark.benchmark_id,
        "window_start": benchmark.window_start.isoformat(),
        "window_end": benchmark.window_end.isoformat(),
        "references": [
            {
                "reference_id": item.reference_id,
                "subject_ref": item.subject_ref,
                "event_type": item.event_type.value,
                "available_at": item.available_at.isoformat(),
                "source_kind": item.source_kind,
            }
            for item in benchmark.references
        ],
        "discoveries": [
            {
                "discovery_id": item.discovery_id,
                "reference_id": item.reference_id,
                "assigned_subject_ref": item.assigned_subject_ref,
                "observed_at": item.observed_at.isoformat(),
            }
            for item in benchmark.discoveries
        ],
        "unresolved_labels": [
            {
                "case_id": item.case_id,
                "subject_ref": item.subject_ref,
                "observed_at": item.observed_at.isoformat(),
                "reason": item.reason,
            }
            for item in benchmark.unresolved_labels
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _destination(data_root: Path, filename: str) -> Path:
    if not isinstance(data_root, Path):
        raise ContractViolation("data_root must be pathlib.Path")
    if not isinstance(filename, str) or not filename.endswith(".json") or Path(filename).name != filename:
        raise ContractViolation("filename must be a simple .json filename")
    destination = data_root / "benchmarks" / "n1-006" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be ISO-8601 UTC text")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation(f"{field} must be ISO-8601 UTC text") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
    return parsed


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractViolation(f"{field} must be non-blank canonical text")
    return value


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _string_tuple(value: object, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ContractViolation(f"{field} must be a JSON array")
    result = tuple(_text(item, field) for item in value)
    if not allow_empty and not result:
        raise ContractViolation(f"{field} must not be empty")
    if len(result) != len(set(result)):
        raise ContractViolation(f"{field} values must be unique")
    return tuple(sorted(result))


def _bounded(value: str, field: str, maximum: int) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise ContractViolation(f"{field} must be bounded canonical text")
