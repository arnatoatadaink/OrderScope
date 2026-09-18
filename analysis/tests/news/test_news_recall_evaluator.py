from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.news import (
    NEWS_RECALL_EVALUATOR_VERSION,
    NEWS_RECALL_REPORT_SCHEMA_VERSION,
    NewsEventType,
    NewsRecallDiscovery,
    NewsRecallReferenceEvent,
    evaluate_news_recall,
)


UTC = timezone.utc
START = datetime(2026, 6, 1, tzinfo=UTC)
END = START + timedelta(days=61)


def _reference(
    reference_id: str,
    subject_ref: str,
    event_type: NewsEventType,
    offset_days: int,
    *,
    source_kind: str = "sec",
) -> NewsRecallReferenceEvent:
    return NewsRecallReferenceEvent(
        reference_id=reference_id,
        subject_ref=subject_ref,
        event_type=event_type,
        available_at=START + timedelta(days=offset_days),
        source_kind=source_kind,
    )


def _discovery(
    discovery_id: str,
    reference_id: str,
    subject_ref: str,
    offset_days: int,
    *,
    seconds: int = 0,
) -> NewsRecallDiscovery:
    return NewsRecallDiscovery(
        discovery_id=discovery_id,
        reference_id=reference_id,
        assigned_subject_ref=subject_ref,
        observed_at=START + timedelta(days=offset_days, seconds=seconds),
    )


def test_news_recall_measures_discovery_rate_and_signed_lag() -> None:
    references = (
        _reference("ref-a", "AMD", NewsEventType.EARNINGS, 10),
        _reference("ref-b", "NVDA", NewsEventType.CONTRACT, 20, source_kind="ir"),
        _reference("ref-c", "AMD", NewsEventType.M_AND_A, 30),
    )
    discoveries = (
        _discovery("disc-a", "ref-a", "AMD", 10, seconds=30),
        _discovery("disc-b", "ref-b", "NVDA", 19, seconds=86340),
    )

    report = evaluate_news_recall(
        references=references,
        discoveries=discoveries,
        window_start=START,
        window_end=END,
    )

    assert report.schema_version == NEWS_RECALL_REPORT_SCHEMA_VERSION
    assert report.evaluator_version == NEWS_RECALL_EVALUATOR_VERSION
    assert report.reference_count == 3
    assert report.discovered_reference_count == 2
    assert report.discovery_rate == pytest.approx(2 / 3)
    by_id = {item.reference_id: item for item in report.reference_results}
    assert by_id["ref-a"].lag_seconds == 30
    assert by_id["ref-b"].lag_seconds == -60
    assert by_id["ref-c"].discovered is False


def test_news_recall_uses_earliest_labeled_discovery_deterministically() -> None:
    references = (_reference("ref-a", "AMD", NewsEventType.CAPEX, 10),)
    discoveries = (
        _discovery("disc-late", "ref-a", "AMD", 10, seconds=120),
        _discovery("disc-first", "ref-a", "AMD", 10, seconds=60),
    )

    report = evaluate_news_recall(
        references=references,
        discoveries=discoveries,
        window_start=START,
        window_end=END,
    )

    result = report.reference_results[0]
    assert result.first_discovery_id == "disc-first"
    assert result.lag_seconds == 60


def test_news_recall_counts_ticker_misattribution_without_changing_reference_identity() -> None:
    references = (
        _reference("ref-amd", "AMD", NewsEventType.PRODUCT_SERVICE, 12),
        _reference("ref-nvda", "NVDA", NewsEventType.PARTNERSHIP, 13),
    )
    discoveries = (
        _discovery("disc-correct", "ref-amd", "AMD", 12, seconds=10),
        _discovery("disc-wrong", "ref-nvda", "AMD", 13, seconds=20),
    )

    report = evaluate_news_recall(
        references=references,
        discoveries=discoveries,
        window_start=START,
        window_end=END,
    )

    assert report.ticker_misattribution_count == 1
    assert report.ticker_misattribution_rate == 0.5
    assert {item.subject_ref for item in report.reference_results} == {"AMD", "NVDA"}


def test_news_recall_rejects_unlabeled_or_unknown_reference_matches() -> None:
    references = (_reference("ref-a", "AMD", NewsEventType.LEGAL, 5),)
    discoveries = (_discovery("disc-a", "missing", "AMD", 5, seconds=1),)

    with pytest.raises(ContractViolation, match="unknown benchmark event"):
        evaluate_news_recall(
            references=references,
            discoveries=discoveries,
            window_start=START,
            window_end=END,
        )


def test_news_recall_rejects_reference_or_discovery_outside_window() -> None:
    with pytest.raises(ContractViolation, match="reference event falls outside"):
        evaluate_news_recall(
            references=(_reference("ref-a", "AMD", NewsEventType.CONTRACT, 70),),
            discoveries=(),
            window_start=START,
            window_end=END,
        )

    references = (_reference("ref-a", "AMD", NewsEventType.CONTRACT, 10),)
    discoveries = (
        NewsRecallDiscovery(
            discovery_id="disc-a",
            reference_id="ref-a",
            assigned_subject_ref="AMD",
            observed_at=END,
        ),
    )
    with pytest.raises(ContractViolation, match="discovery falls outside"):
        evaluate_news_recall(
            references=references,
            discoveries=discoveries,
            window_start=START,
            window_end=END,
        )


def test_news_recall_enforces_one_to_three_month_evaluation_window() -> None:
    with pytest.raises(ContractViolation, match="30 through 93 days"):
        evaluate_news_recall(
            references=(),
            discoveries=(),
            window_start=START,
            window_end=START + timedelta(days=29),
        )

    with pytest.raises(ContractViolation, match="30 through 93 days"):
        evaluate_news_recall(
            references=(),
            discoveries=(),
            window_start=START,
            window_end=START + timedelta(days=94),
        )


def test_news_recall_empty_benchmark_is_explicit_zero_not_fabricated_success() -> None:
    report = evaluate_news_recall(
        references=(),
        discoveries=(),
        window_start=START,
        window_end=END,
    )

    assert report.reference_count == 0
    assert report.discovered_reference_count == 0
    assert report.discovery_rate == 0.0
    assert report.discovery_count == 0
    assert report.ticker_misattribution_rate == 0.0
    assert report.reference_results == ()
