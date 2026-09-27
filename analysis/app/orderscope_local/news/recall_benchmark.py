"""Validated benchmark manifest and report rendering for N1-006 real-window evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Mapping

from orderscope_local.contracts import ContractViolation
from .event_taxonomy import NewsEventType
from .recall import (
    NewsRecallDiscovery,
    NewsRecallReferenceEvent,
    NewsRecallReport,
    evaluate_news_recall,
)

NEWS_RECALL_BENCHMARK_SCHEMA_VERSION = "news-recall-benchmark-v0.1"


@dataclass(frozen=True, slots=True)
class NewsRecallUnresolvedLabel:
    case_id: str
    subject_ref: str
    observed_at: datetime
    reason: str

    def __post_init__(self) -> None:
        _bounded(self.case_id, "case_id", 128)
        _bounded(self.subject_ref, "subject_ref", 256)
        _utc(self.observed_at, "unresolved observed_at")
        _bounded(self.reason, "reason", 512)


@dataclass(frozen=True, slots=True)
class NewsRecallBenchmark:
    schema_version: str
    benchmark_id: str
    window_start: datetime
    window_end: datetime
    references: tuple[NewsRecallReferenceEvent, ...]
    discoveries: tuple[NewsRecallDiscovery, ...]
    unresolved_labels: tuple[NewsRecallUnresolvedLabel, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != NEWS_RECALL_BENCHMARK_SCHEMA_VERSION:
            raise ContractViolation("unsupported news recall benchmark schema version")
        _bounded(self.benchmark_id, "benchmark_id", 128)
        _window(self.window_start, self.window_end)
        if not isinstance(self.references, tuple) or any(not isinstance(item, NewsRecallReferenceEvent) for item in self.references):
            raise ContractViolation("benchmark references must be immutable NewsRecallReferenceEvent tuple")
        if not isinstance(self.discoveries, tuple) or any(not isinstance(item, NewsRecallDiscovery) for item in self.discoveries):
            raise ContractViolation("benchmark discoveries must be immutable NewsRecallDiscovery tuple")
        if not isinstance(self.unresolved_labels, tuple) or any(not isinstance(item, NewsRecallUnresolvedLabel) for item in self.unresolved_labels):
            raise ContractViolation("benchmark unresolved_labels must be immutable NewsRecallUnresolvedLabel tuple")
        unresolved_ids = tuple(item.case_id for item in self.unresolved_labels)
        if len(unresolved_ids) != len(set(unresolved_ids)):
            raise ContractViolation("unresolved case_id values must be unique")
        for unresolved in self.unresolved_labels:
            if not self.window_start <= unresolved.observed_at < self.window_end:
                raise ContractViolation("unresolved label falls outside evaluation window")

    def evaluate(self) -> NewsRecallReport:
        return evaluate_news_recall(
            references=self.references,
            discoveries=self.discoveries,
            window_start=self.window_start,
            window_end=self.window_end,
        )


def load_news_recall_benchmark(path: str | Path) -> NewsRecallBenchmark:
    benchmark_path = Path(path)
    try:
        payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractViolation("news recall benchmark must be readable UTF-8 JSON") from exc
    if not isinstance(payload, Mapping):
        raise ContractViolation("news recall benchmark root must be a JSON object")
    return decode_news_recall_benchmark(payload)


def decode_news_recall_benchmark(payload: Mapping[str, object]) -> NewsRecallBenchmark:
    _exact_keys(
        payload,
        required={"schema_version", "benchmark_id", "window_start", "window_end", "references", "discoveries"},
        optional={"unresolved_labels"},
        context="benchmark",
    )
    references_raw = payload["references"]
    discoveries_raw = payload["discoveries"]
    unresolved_raw = payload.get("unresolved_labels", [])
    if not isinstance(references_raw, list) or not isinstance(discoveries_raw, list) or not isinstance(unresolved_raw, list):
        raise ContractViolation("benchmark collections must be JSON arrays")

    references = tuple(_decode_reference(item) for item in references_raw)
    discoveries = tuple(_decode_discovery(item) for item in discoveries_raw)
    unresolved = tuple(_decode_unresolved(item) for item in unresolved_raw)
    return NewsRecallBenchmark(
        schema_version=_text(payload["schema_version"], "schema_version"),
        benchmark_id=_text(payload["benchmark_id"], "benchmark_id"),
        window_start=_timestamp(payload["window_start"], "window_start"),
        window_end=_timestamp(payload["window_end"], "window_end"),
        references=references,
        discoveries=discoveries,
        unresolved_labels=unresolved,
    )


def render_news_recall_markdown(*, benchmark: NewsRecallBenchmark, report: NewsRecallReport | None = None) -> str:
    if not isinstance(benchmark, NewsRecallBenchmark):
        raise ContractViolation("benchmark must be NewsRecallBenchmark")
    effective = report or benchmark.evaluate()
    if not isinstance(effective, NewsRecallReport):
        raise ContractViolation("report must be NewsRecallReport")
    if effective.window_start != benchmark.window_start or effective.window_end != benchmark.window_end:
        raise ContractViolation("report window must match benchmark window")

    lags = tuple(item.lag_seconds for item in effective.reference_results if item.lag_seconds is not None)
    lines = [
        f"# News Recall Benchmark — {benchmark.benchmark_id}",
        "",
        f"- Window: `{benchmark.window_start.isoformat()}` → `{benchmark.window_end.isoformat()}`",
        f"- Reference events: **{effective.reference_count}**",
        f"- Discovered references: **{effective.discovered_reference_count}**",
        f"- Discovery rate: **{effective.discovery_rate:.4f}**",
        f"- News discoveries: **{effective.discovery_count}**",
        f"- Subject/ticker misattributions: **{effective.ticker_misattribution_count}** ({effective.ticker_misattribution_rate:.4f})",
        f"- Unresolved benchmark labels: **{len(benchmark.unresolved_labels)}**",
        "",
        "## Per-reference results",
        "",
        "| Reference | Subject | Event type | Discovered | First discovery | Lag seconds |",
        "|---|---|---|---:|---|---:|",
    ]
    for item in effective.reference_results:
        lines.append(
            f"| {item.reference_id} | {item.subject_ref} | {item.event_type.value} | "
            f"{'yes' if item.discovered else 'no'} | {item.first_discovery_id or '—'} | "
            f"{item.lag_seconds if item.lag_seconds is not None else '—'} |"
        )

    lines.extend(["", "## Lag summary", ""])
    if lags:
        ordered = tuple(sorted(lags))
        lines.extend(
            [
                f"- Minimum signed lag: **{ordered[0]} s**",
                f"- Maximum signed lag: **{ordered[-1]} s**",
                f"- Median signed lag: **{_median(ordered)} s**",
            ]
        )
    else:
        lines.append("- No discovered reference has a measurable lag.")

    lines.extend(["", "## Unresolved benchmark labels", ""])
    if benchmark.unresolved_labels:
        for item in benchmark.unresolved_labels:
            lines.append(f"- `{item.case_id}` / `{item.subject_ref}` / `{item.observed_at.isoformat()}` — {item.reason}")
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def _decode_reference(value: object) -> NewsRecallReferenceEvent:
    if not isinstance(value, Mapping):
        raise ContractViolation("reference entry must be a JSON object")
    _exact_keys(value, required={"reference_id", "subject_ref", "event_type", "available_at", "source_kind"}, optional=set(), context="reference")
    try:
        event_type = NewsEventType(_text(value["event_type"], "event_type"))
    except ValueError as exc:
        raise ContractViolation("reference event_type is not in active News taxonomy") from exc
    return NewsRecallReferenceEvent(
        reference_id=_text(value["reference_id"], "reference_id"),
        subject_ref=_text(value["subject_ref"], "subject_ref"),
        event_type=event_type,
        available_at=_timestamp(value["available_at"], "available_at"),
        source_kind=_text(value["source_kind"], "source_kind"),
    )


def _decode_discovery(value: object) -> NewsRecallDiscovery:
    if not isinstance(value, Mapping):
        raise ContractViolation("discovery entry must be a JSON object")
    _exact_keys(value, required={"discovery_id", "reference_id", "assigned_subject_ref", "observed_at"}, optional=set(), context="discovery")
    return NewsRecallDiscovery(
        discovery_id=_text(value["discovery_id"], "discovery_id"),
        reference_id=_text(value["reference_id"], "reference_id"),
        assigned_subject_ref=_text(value["assigned_subject_ref"], "assigned_subject_ref"),
        observed_at=_timestamp(value["observed_at"], "observed_at"),
    )


def _decode_unresolved(value: object) -> NewsRecallUnresolvedLabel:
    if not isinstance(value, Mapping):
        raise ContractViolation("unresolved entry must be a JSON object")
    _exact_keys(value, required={"case_id", "subject_ref", "observed_at", "reason"}, optional=set(), context="unresolved")
    return NewsRecallUnresolvedLabel(
        case_id=_text(value["case_id"], "case_id"),
        subject_ref=_text(value["subject_ref"], "subject_ref"),
        observed_at=_timestamp(value["observed_at"], "observed_at"),
        reason=_text(value["reason"], "reason"),
    )


def _exact_keys(payload: Mapping[str, object], *, required: set[str], optional: set[str], context: str) -> None:
    keys = set(payload.keys())
    missing = required - keys
    extra = keys - required - optional
    if missing:
        raise ContractViolation(f"{context} is missing required fields: {', '.join(sorted(missing))}")
    if extra:
        raise ContractViolation(f"{context} contains unsupported fields: {', '.join(sorted(extra))}")


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be ISO-8601 UTC text")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation(f"{field} must be ISO-8601 UTC text") from exc
    _utc(parsed, field)
    return parsed


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} must be text")
    return value


def _window(start: datetime, end: datetime) -> None:
    _utc(start, "window_start")
    _utc(end, "window_end")
    duration = end - start
    if duration < timedelta(days=30) or duration > timedelta(days=93):
        raise ContractViolation("news recall benchmark window must span 30 through 93 days")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _bounded(value: str, field: str, maximum: int) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise ContractViolation(f"{field} must be bounded canonical text")


def _median(values: tuple[int, ...]) -> float:
    middle = len(values) // 2
    if len(values) % 2:
        return float(values[middle])
    return (values[middle - 1] + values[middle]) / 2
