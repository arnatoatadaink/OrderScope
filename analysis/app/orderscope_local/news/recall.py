"""Deterministic News recall evaluation against labeled SEC/IR reference events (N1-006)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from orderscope_local.contracts import ContractViolation
from .event_taxonomy import NewsEventType


NEWS_RECALL_EVALUATOR_VERSION = "news-recall-evaluator-v0.1"
NEWS_RECALL_REPORT_SCHEMA_VERSION = "news-recall-report-v0.1"
_MIN_WINDOW = timedelta(days=30)
_MAX_WINDOW = timedelta(days=93)


@dataclass(frozen=True, slots=True)
class NewsRecallReferenceEvent:
    reference_id: str
    subject_ref: str
    event_type: NewsEventType
    available_at: datetime
    source_kind: str

    def __post_init__(self) -> None:
        _identifier(self.reference_id, "reference_id")
        _subject(self.subject_ref, "subject_ref")
        if not isinstance(self.event_type, NewsEventType):
            raise ContractViolation("reference event_type must be NewsEventType")
        _utc(self.available_at, "reference available_at")
        if self.source_kind not in {"sec", "ir"}:
            raise ContractViolation("reference source_kind must be sec or ir")


@dataclass(frozen=True, slots=True)
class NewsRecallDiscovery:
    discovery_id: str
    reference_id: str
    assigned_subject_ref: str
    observed_at: datetime

    def __post_init__(self) -> None:
        _identifier(self.discovery_id, "discovery_id")
        _identifier(self.reference_id, "reference_id")
        _subject(self.assigned_subject_ref, "assigned_subject_ref")
        _utc(self.observed_at, "discovery observed_at")


@dataclass(frozen=True, slots=True)
class NewsRecallReferenceResult:
    reference_id: str
    subject_ref: str
    event_type: NewsEventType
    discovered: bool
    first_discovery_id: str | None
    lag_seconds: int | None

    def __post_init__(self) -> None:
        _identifier(self.reference_id, "reference_id")
        _subject(self.subject_ref, "subject_ref")
        if not isinstance(self.event_type, NewsEventType):
            raise ContractViolation("reference result event_type must be NewsEventType")
        if not isinstance(self.discovered, bool):
            raise ContractViolation("discovered must be bool")
        if self.discovered:
            if self.first_discovery_id is None or self.lag_seconds is None:
                raise ContractViolation("discovered reference requires first discovery and lag")
            _identifier(self.first_discovery_id, "first_discovery_id")
            if not isinstance(self.lag_seconds, int) or isinstance(self.lag_seconds, bool):
                raise ContractViolation("lag_seconds must be integer when discovered")
        elif self.first_discovery_id is not None or self.lag_seconds is not None:
            raise ContractViolation("undiscovered reference cannot expose discovery metadata")


@dataclass(frozen=True, slots=True)
class NewsRecallReport:
    schema_version: str
    evaluator_version: str
    window_start: datetime
    window_end: datetime
    reference_count: int
    discovered_reference_count: int
    discovery_rate: float
    discovery_count: int
    ticker_misattribution_count: int
    ticker_misattribution_rate: float
    reference_results: tuple[NewsRecallReferenceResult, ...]

    def __post_init__(self) -> None:
        if self.schema_version != NEWS_RECALL_REPORT_SCHEMA_VERSION:
            raise ContractViolation("unsupported news recall report schema version")
        if self.evaluator_version != NEWS_RECALL_EVALUATOR_VERSION:
            raise ContractViolation("unsupported news recall evaluator version")
        _window(self.window_start, self.window_end)
        for value, field in (
            (self.reference_count, "reference_count"),
            (self.discovered_reference_count, "discovered_reference_count"),
            (self.discovery_count, "discovery_count"),
            (self.ticker_misattribution_count, "ticker_misattribution_count"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ContractViolation(f"{field} must be a non-negative integer")
        if self.discovered_reference_count > self.reference_count:
            raise ContractViolation("discovered_reference_count cannot exceed reference_count")
        if self.ticker_misattribution_count > self.discovery_count:
            raise ContractViolation("ticker_misattribution_count cannot exceed discovery_count")
        for value, field in (
            (self.discovery_rate, "discovery_rate"),
            (self.ticker_misattribution_rate, "ticker_misattribution_rate"),
        ):
            if not isinstance(value, float) or not 0.0 <= value <= 1.0:
                raise ContractViolation(f"{field} must be a float between 0 and 1")
        if not isinstance(self.reference_results, tuple) or any(
            not isinstance(item, NewsRecallReferenceResult) for item in self.reference_results
        ):
            raise ContractViolation("reference_results must be immutable NewsRecallReferenceResult tuple")
        if len(self.reference_results) != self.reference_count:
            raise ContractViolation("reference_results count must equal reference_count")


def evaluate_news_recall(
    *,
    references: tuple[NewsRecallReferenceEvent, ...],
    discoveries: tuple[NewsRecallDiscovery, ...],
    window_start: datetime,
    window_end: datetime,
) -> NewsRecallReport:
    """Measure labeled discovery recall, signed lag, and subject misattribution.

    Matching is deliberately benchmark-owned: every discovery points to an explicit
    SEC/IR ``reference_id``. This evaluator measures an already-labeled comparison
    dataset and never guesses event equivalence from headline similarity.
    """

    _window(window_start, window_end)
    if not isinstance(references, tuple) or any(not isinstance(item, NewsRecallReferenceEvent) for item in references):
        raise ContractViolation("references must be immutable NewsRecallReferenceEvent tuple")
    if not isinstance(discoveries, tuple) or any(not isinstance(item, NewsRecallDiscovery) for item in discoveries):
        raise ContractViolation("discoveries must be immutable NewsRecallDiscovery tuple")

    reference_ids = tuple(item.reference_id for item in references)
    if len(reference_ids) != len(set(reference_ids)):
        raise ContractViolation("reference_id values must be unique")
    discovery_ids = tuple(item.discovery_id for item in discoveries)
    if len(discovery_ids) != len(set(discovery_ids)):
        raise ContractViolation("discovery_id values must be unique")

    by_reference = {item.reference_id: item for item in references}
    for reference in references:
        if not window_start <= reference.available_at < window_end:
            raise ContractViolation("reference event falls outside evaluation window")
    for discovery in discoveries:
        if discovery.reference_id not in by_reference:
            raise ContractViolation("discovery references an unknown benchmark event")
        if not window_start <= discovery.observed_at < window_end:
            raise ContractViolation("discovery falls outside evaluation window")

    discoveries_by_reference: dict[str, list[NewsRecallDiscovery]] = {key: [] for key in reference_ids}
    misattributed = 0
    for discovery in discoveries:
        reference = by_reference[discovery.reference_id]
        discoveries_by_reference[discovery.reference_id].append(discovery)
        if discovery.assigned_subject_ref != reference.subject_ref:
            misattributed += 1

    results: list[NewsRecallReferenceResult] = []
    for reference in sorted(references, key=lambda item: (item.available_at, item.reference_id)):
        matched = sorted(
            discoveries_by_reference[reference.reference_id],
            key=lambda item: (item.observed_at, item.discovery_id),
        )
        if not matched:
            results.append(
                NewsRecallReferenceResult(
                    reference_id=reference.reference_id,
                    subject_ref=reference.subject_ref,
                    event_type=reference.event_type,
                    discovered=False,
                    first_discovery_id=None,
                    lag_seconds=None,
                )
            )
            continue
        first = matched[0]
        lag = int((first.observed_at - reference.available_at).total_seconds())
        results.append(
            NewsRecallReferenceResult(
                reference_id=reference.reference_id,
                subject_ref=reference.subject_ref,
                event_type=reference.event_type,
                discovered=True,
                first_discovery_id=first.discovery_id,
                lag_seconds=lag,
            )
        )

    reference_count = len(references)
    discovered_reference_count = sum(1 for item in results if item.discovered)
    discovery_count = len(discoveries)
    return NewsRecallReport(
        schema_version=NEWS_RECALL_REPORT_SCHEMA_VERSION,
        evaluator_version=NEWS_RECALL_EVALUATOR_VERSION,
        window_start=window_start,
        window_end=window_end,
        reference_count=reference_count,
        discovered_reference_count=discovered_reference_count,
        discovery_rate=0.0 if reference_count == 0 else discovered_reference_count / reference_count,
        discovery_count=discovery_count,
        ticker_misattribution_count=misattributed,
        ticker_misattribution_rate=0.0 if discovery_count == 0 else misattributed / discovery_count,
        reference_results=tuple(results),
    )


def _window(start: datetime, end: datetime) -> None:
    _utc(start, "window_start")
    _utc(end, "window_end")
    duration = end - start
    if duration < _MIN_WINDOW or duration > _MAX_WINDOW:
        raise ContractViolation("news recall evaluation window must span 30 through 93 days")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 128:
        raise ContractViolation(f"{field} must be bounded canonical text")


def _subject(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be bounded canonical subject text")
