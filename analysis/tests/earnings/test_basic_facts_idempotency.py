from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts import (
    AccountingBasis,
    ContentHash,
    ContractViolation,
    Fact,
    FactAssertionKind,
    Provenance,
    SourceReference,
    SourceTimestamp,
)
from orderscope_local.earnings import (
    BasicEarningsMetricType,
    ObservedEarningsMetric,
    extract_basic_earnings_records,
)


SOURCE = "https://www.sec.gov/Archives/edgar/data/2488/example/amd-q2.htm"


def _provenance(*, minute: int, published_day: int = 4) -> Provenance:
    return Provenance(
        source_ref=SourceReference(SOURCE),
        content_hash=ContentHash("9" * 64),
        published_at=SourceTimestamp.date_only(date(2026, 8, published_day)),
        available_at=datetime(2026, 8, 4, 20, minute, 0, tzinfo=timezone.utc),
        retrieved_at=datetime(2026, 8, 4, 20, minute, 0, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 8, 4, 20, minute, 1, tzinfo=timezone.utc),
    )


def _metric(provenance: Provenance) -> ObservedEarningsMetric:
    return ObservedEarningsMetric(
        instrument_id="AMD",
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=date(2026, 6, 27),
        metric_type=BasicEarningsMetricType.REVENUE,
        value=Decimal("7685000000"),
        currency="USD",
        accounting_basis=AccountingBasis.GAAP,
        assertion_kind=FactAssertionKind.OBSERVATION,
        provenance=provenance,
    )


def test_repeat_retrieval_same_source_hash_keeps_first_operational_observation() -> None:
    first = _metric(_provenance(minute=1))
    later = _metric(_provenance(minute=5))

    records = extract_basic_earnings_records((later, first))
    fact = next(record for record in records if isinstance(record, Fact))

    assert len(records) == 2
    assert fact.provenance == first.provenance
    assert fact.record_id == next(
        record.record_id
        for record in extract_basic_earnings_records((first,))
        if isinstance(record, Fact)
    )


def test_same_source_hash_with_conflicting_source_timestamp_is_not_silent_duplicate() -> None:
    first = _metric(_provenance(minute=1, published_day=4))
    conflicting = _metric(_provenance(minute=5, published_day=5))

    with pytest.raises(ContractViolation, match="conflicting source semantics"):
        extract_basic_earnings_records((first, conflicting))
