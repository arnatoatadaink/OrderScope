from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts import (
    AccountingBasis,
    ContentHash,
    ContractViolation,
    EarningsEvent,
    EarningsEventKind,
    EarningsEvidenceRef,
    EarningsEvidenceRole,
    EarningsResultMetric,
    Provenance,
    ScheduledReleaseWindow,
    SourceReference,
    SourceTimestamp,
)


AMD_IR = EarningsEvidenceRef(
    "evidence:amd:q2-2026:ir-result",
    EarningsEvidenceRole.ISSUER_RESULT_RELEASE,
)
AMD_SCHEDULE = EarningsEvidenceRef(
    "evidence:amd:q2-2026:ir-schedule",
    EarningsEvidenceRole.ISSUER_SCHEDULE_ANNOUNCEMENT,
)
AMD_SEC = EarningsEvidenceRef(
    "evidence:amd:q2-2026:8k",
    EarningsEvidenceRole.SEC_8K,
)
NVDA_EVENT = EarningsEvidenceRef(
    "evidence:nvda:q2-fy2027:event",
    EarningsEvidenceRole.ISSUER_EVENT_PAGE,
)


def test_amd_release_keeps_date_window_and_unknown_actual_time_distinct() -> None:
    event = EarningsEvent(
        instrument_id="AMD",
        event_kind=EarningsEventKind.RELEASE,
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=date(2026, 6, 27),
        scheduled_at=SourceTimestamp.date_only(date(2026, 8, 4)),
        scheduled_release_window=ScheduledReleaseWindow.AFTER_MARKET_CLOSE,
        actual_release_at=None,
        evidence=(AMD_SCHEDULE, AMD_IR, AMD_SEC),
    )

    assert event.scheduled_at.calendar_date == date(2026, 8, 4)
    assert event.scheduled_release_window is ScheduledReleaseWindow.AFTER_MARKET_CLOSE
    assert event.actual_release_at is None


def test_call_requires_an_established_instant_and_never_becomes_release_time() -> None:
    call = EarningsEvent(
        instrument_id="NVDA",
        event_kind=EarningsEventKind.CALL,
        fiscal_year_label="FY2027",
        fiscal_quarter="Q2",
        period_end=date(2026, 7, 26),
        scheduled_at=SourceTimestamp.at(
            datetime(2026, 8, 26, 21, 0, tzinfo=timezone.utc),
            source_timezone="PT",
        ),
        evidence=(NVDA_EVENT,),
    )

    assert call.scheduled_at.instant == datetime(2026, 8, 26, 21, 0, tzinfo=timezone.utc)
    assert call.actual_release_at is None

    with pytest.raises(ContractViolation, match="established instant"):
        EarningsEvent(
            instrument_id="AMD",
            event_kind=EarningsEventKind.CALL,
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            scheduled_at=SourceTimestamp.date_only(date(2026, 8, 4)),
            evidence=(AMD_SCHEDULE,),
        )


def test_sec_source_acceptance_does_not_fill_unknown_actual_release() -> None:
    sec_provenance = Provenance(
        source_ref=SourceReference(
            "https://www.sec.gov/Archives/edgar/data/2488/000000248826000121/amd-20260804.htm"
        ),
        content_hash=ContentHash("a" * 64),
        retrieved_at=datetime(2026, 8, 4, 20, 17, tzinfo=timezone.utc),
        available_at=datetime(2026, 8, 4, 20, 17, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 8, 4, 20, 18, tzinfo=timezone.utc),
        source_accepted_at=SourceTimestamp.at(
            datetime(2026, 8, 4, 20, 16, 24, tzinfo=timezone.utc)
        ),
    )
    event = EarningsEvent(
        instrument_id="AMD",
        event_kind=EarningsEventKind.RELEASE,
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=date(2026, 6, 27),
        evidence=(AMD_IR, AMD_SEC),
        actual_release_at=None,
    )

    assert sec_provenance.source_accepted_at.instant == datetime(
        2026, 8, 4, 20, 16, 24, tzinfo=timezone.utc
    )
    assert event.actual_release_at is None


def test_gaap_and_non_gaap_metrics_remain_distinct_records() -> None:
    common = dict(
        instrument_id="AMD",
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=date(2026, 6, 27),
        metric_type="diluted_eps",
        unit="currency_per_share",
        currency="USD",
        evidence=(AMD_IR, AMD_SEC),
    )
    gaap = EarningsResultMetric(
        value=Decimal("1.38"), accounting_basis=AccountingBasis.GAAP, **common
    )
    non_gaap = EarningsResultMetric(
        value=Decimal("1.66"), accounting_basis=AccountingBasis.NON_GAAP, **common
    )

    assert gaap.metric_type == non_gaap.metric_type
    assert gaap.accounting_basis is AccountingBasis.GAAP
    assert non_gaap.accounting_basis is AccountingBasis.NON_GAAP
    assert gaap != non_gaap


def test_issuer_fiscal_label_is_not_derived_from_calendar_year() -> None:
    metric = EarningsResultMetric(
        instrument_id="NVDA",
        fiscal_year_label="FY2027",
        fiscal_quarter="Q2",
        period_end=date(2026, 7, 26),
        metric_type="diluted_eps",
        value=Decimal("2.46"),
        unit="currency_per_share",
        currency="USD",
        accounting_basis=AccountingBasis.GAAP,
        evidence=(NVDA_EVENT,),
    )

    assert metric.fiscal_year_label == "FY2027"
    assert metric.period_end.year == 2026


def test_contract_rejects_invented_release_time_invalid_currency_and_duplicate_evidence() -> None:
    with pytest.raises(ContractViolation, match="established instant"):
        EarningsEvent(
            instrument_id="AMD",
            event_kind=EarningsEventKind.RELEASE,
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            actual_release_at=SourceTimestamp.date_only(date(2026, 8, 4)),
            evidence=(AMD_IR,),
        )

    with pytest.raises(ContractViolation, match="ISO-style"):
        EarningsResultMetric(
            instrument_id="AMD",
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            metric_type="revenue",
            value=Decimal("7685000000"),
            unit="currency",
            currency="usd",
            accounting_basis=AccountingBasis.GAAP,
            evidence=(AMD_IR,),
        )

    with pytest.raises(ContractViolation, match="duplicate"):
        EarningsEvent(
            instrument_id="AMD",
            event_kind=EarningsEventKind.RELEASE,
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            evidence=(AMD_IR, AMD_IR),
        )


def test_call_cannot_carry_release_window_or_actual_release() -> None:
    scheduled = SourceTimestamp.at(datetime(2026, 8, 4, 21, 0, tzinfo=timezone.utc))
    with pytest.raises(ContractViolation, match="release window"):
        EarningsEvent(
            instrument_id="AMD",
            event_kind=EarningsEventKind.CALL,
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            scheduled_at=scheduled,
            scheduled_release_window=ScheduledReleaseWindow.AFTER_MARKET_CLOSE,
            evidence=(AMD_SCHEDULE,),
        )

    with pytest.raises(ContractViolation, match="actual_release_at"):
        EarningsEvent(
            instrument_id="AMD",
            event_kind=EarningsEventKind.CALL,
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            scheduled_at=scheduled,
            actual_release_at=scheduled,
            evidence=(AMD_SCHEDULE,),
        )
