from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts import (
    AccountingBasis,
    ContentHash,
    ContractViolation,
    Evidence,
    Fact,
    FactAssertionKind,
    Provenance,
    SourceReference,
    SourceTimestamp,
    validate_fact_store,
)
from orderscope_local.earnings import (
    BasicEarningsMetricType,
    ObservedEarningsMetric,
    extract_basic_earnings_records,
)


def _provenance(url: str, digest: str, *, accepted_second: int = 2) -> Provenance:
    return Provenance(
        source_ref=SourceReference(url),
        content_hash=ContentHash(digest),
        published_at=SourceTimestamp.date_only(date(2026, 8, 4)),
        retrieved_at=datetime(2026, 8, 4, 20, 0, 1, tzinfo=timezone.utc),
        available_at=datetime(2026, 8, 4, 20, 0, 1, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 8, 4, 20, 0, accepted_second, tzinfo=timezone.utc),
    )


def _amd_revenue(*, provenance: Provenance | None = None) -> ObservedEarningsMetric:
    return ObservedEarningsMetric(
        instrument_id="AMD",
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_start=date(2026, 3, 29),
        period_end=date(2026, 6, 27),
        metric_type=BasicEarningsMetricType.REVENUE,
        value=Decimal("7685000000"),
        currency="USD",
        accounting_basis=AccountingBasis.GAAP,
        assertion_kind=FactAssertionKind.OBSERVATION,
        provenance=provenance
        or _provenance(
            "https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results",
            "a" * 64,
        ),
    )


def test_revenue_becomes_source_grounded_fact_and_evidence() -> None:
    records = extract_basic_earnings_records((_amd_revenue(),))

    assert len(records) == 2
    fact = next(record for record in records if isinstance(record, Fact))
    evidence = next(record for record in records if isinstance(record, Evidence))

    assert fact.fact_type == "earnings.revenue"
    assert fact.value["amount"] == "7685000000"
    assert fact.value["currency"] == "USD"
    assert fact.value["accounting_basis"] == "gaap"
    assert fact.value["fiscal_year_label"] == "FY2026"
    assert fact.value["fiscal_quarter"] == "Q2"
    assert fact.unit == "USD"
    assert fact.period_start.calendar_date == date(2026, 3, 29)
    assert fact.period_end.calendar_date == date(2026, 6, 27)
    assert fact.evidence_record_ids == (evidence.record_id,)
    assert evidence.target_record_ids == (fact.record_id,)
    assert evidence.locator == fact.provenance.source_ref.value
    validate_fact_store(records)


def test_eps_preserves_exact_decimal_text_and_per_share_unit() -> None:
    observation = ObservedEarningsMetric(
        instrument_id="AMD",
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=date(2026, 6, 27),
        metric_type=BasicEarningsMetricType.DILUTED_EPS,
        value=Decimal("1.38"),
        currency="USD",
        accounting_basis=AccountingBasis.GAAP,
        assertion_kind=FactAssertionKind.OBSERVATION,
        provenance=_provenance("https://www.sec.gov/example/amd-q2", "b" * 64),
    )

    fact = next(
        record
        for record in extract_basic_earnings_records((observation,))
        if isinstance(record, Fact)
    )
    assert fact.value["amount"] == "1.38"
    assert fact.unit == "USD_per_share"
    assert fact.period_start is None


def test_gaap_and_non_gaap_are_distinct_facts() -> None:
    common = dict(
        instrument_id="AMD",
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=date(2026, 6, 27),
        metric_type=BasicEarningsMetricType.DILUTED_EPS,
        currency="USD",
        assertion_kind=FactAssertionKind.OBSERVATION,
        provenance=_provenance("https://ir.amd.com/example/q2", "c" * 64),
    )
    gaap = ObservedEarningsMetric(
        value=Decimal("1.38"), accounting_basis=AccountingBasis.GAAP, **common
    )
    non_gaap = ObservedEarningsMetric(
        value=Decimal("1.66"), accounting_basis=AccountingBasis.NON_GAAP, **common
    )

    facts = [
        record
        for record in extract_basic_earnings_records((gaap, non_gaap))
        if isinstance(record, Fact)
    ]
    assert len(facts) == 2
    assert {fact.value["accounting_basis"] for fact in facts} == {"gaap", "non_gaap"}
    assert len({fact.record_id for fact in facts}) == 2


def test_same_semantic_value_from_sec_and_ir_remains_two_source_facts() -> None:
    ir = _amd_revenue()
    sec = _amd_revenue(
        provenance=_provenance(
            "https://www.sec.gov/Archives/edgar/data/2488/example/amd-q2.htm",
            "d" * 64,
        )
    )

    records = extract_basic_earnings_records((ir, sec))
    facts = [record for record in records if isinstance(record, Fact)]
    evidence = [record for record in records if isinstance(record, Evidence)]

    assert len(facts) == 2
    assert len(evidence) == 2
    assert {fact.provenance.source_ref.value for fact in facts} == {
        ir.provenance.source_ref.value,
        sec.provenance.source_ref.value,
    }


def test_exact_duplicate_observation_is_idempotent() -> None:
    observation = _amd_revenue()
    first = extract_basic_earnings_records((observation,))
    duplicate = extract_basic_earnings_records((observation, observation))

    assert duplicate == first


def test_nvda_fiscal_label_is_not_derived_from_calendar_year() -> None:
    observation = ObservedEarningsMetric(
        instrument_id="NVDA",
        fiscal_year_label="FY2027",
        fiscal_quarter="Q2",
        period_end=date(2026, 7, 26),
        metric_type=BasicEarningsMetricType.NET_INCOME,
        value=Decimal("26422000000"),
        currency="USD",
        accounting_basis=AccountingBasis.GAAP,
        assertion_kind=FactAssertionKind.OBSERVATION,
        provenance=_provenance(
            "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2027",
            "e" * 64,
        ),
    )

    fact = next(
        record
        for record in extract_basic_earnings_records((observation,))
        if isinstance(record, Fact)
    )
    assert fact.value["fiscal_year_label"] == "FY2027"
    assert fact.period_end.calendar_date.year == 2026


def test_extraction_requires_explicit_value_currency_and_supported_canary() -> None:
    with pytest.raises(ContractViolation, match="finite Decimal"):
        ObservedEarningsMetric(
            instrument_id="AMD",
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            metric_type=BasicEarningsMetricType.REVENUE,
            value=Decimal("NaN"),
            currency="USD",
            accounting_basis=AccountingBasis.GAAP,
            assertion_kind=FactAssertionKind.OBSERVATION,
            provenance=_provenance("https://ir.amd.com/example", "f" * 64),
        )

    with pytest.raises(ContractViolation, match="uppercase ISO-style"):
        ObservedEarningsMetric(
            instrument_id="AMD",
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            metric_type=BasicEarningsMetricType.REVENUE,
            value=Decimal("1"),
            currency="usd",
            accounting_basis=AccountingBasis.GAAP,
            assertion_kind=FactAssertionKind.OBSERVATION,
            provenance=_provenance("https://ir.amd.com/example", "1" * 64),
        )

    with pytest.raises(ContractViolation, match="outside the corporate canary"):
        ObservedEarningsMetric(
            instrument_id="INTC",
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=date(2026, 6, 27),
            metric_type=BasicEarningsMetricType.REVENUE,
            value=Decimal("1"),
            currency="USD",
            accounting_basis=AccountingBasis.GAAP,
            assertion_kind=FactAssertionKind.OBSERVATION,
            provenance=_provenance("https://example.com", "2" * 64),
        )


def test_extraction_does_not_infer_period_start_or_source_times() -> None:
    provenance = Provenance(
        source_ref=SourceReference("https://www.sec.gov/example/no-source-time"),
        content_hash=ContentHash("3" * 64),
        retrieved_at=datetime(2026, 8, 4, 20, 0, 1, tzinfo=timezone.utc),
        available_at=datetime(2026, 8, 4, 20, 0, 1, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 8, 4, 20, 0, 2, tzinfo=timezone.utc),
    )
    observation = ObservedEarningsMetric(
        instrument_id="AMD",
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=date(2026, 6, 27),
        metric_type=BasicEarningsMetricType.NET_INCOME,
        value=Decimal("872000000"),
        currency="USD",
        accounting_basis=AccountingBasis.GAAP,
        assertion_kind=FactAssertionKind.OBSERVATION,
        provenance=provenance,
    )

    fact = next(
        record
        for record in extract_basic_earnings_records((observation,))
        if isinstance(record, Fact)
    )
    assert fact.period_start is None
    assert fact.provenance.published_at is None
    assert fact.provenance.event_time is None
