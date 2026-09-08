from datetime import date, datetime, timezone
from decimal import Decimal

from orderscope_local.contracts import (
    AccountingBasis,
    ContentHash,
    Fact,
    FactAssertionKind,
    Provenance,
    SourceReference,
)
from orderscope_local.earnings import (
    BasicEarningsMetricType,
    EarningsFactEvidence,
    EarningsQualitySource,
    ObservedEarningsMetric,
    SegmentQualityCheck,
    SegmentRevenueAttempt,
    SegmentRevenueFailureReason,
    SegmentRevenueMethod,
    SegmentRevenueObservation,
    SegmentRevenueResolution,
    SegmentRevenueStatus,
    build_earnings_canary_quality_report,
    extract_basic_earnings_records,
    render_earnings_canary_quality_markdown,
)


def _prov(url: str, digest: str) -> Provenance:
    stamp = datetime(2026, 8, 30, 20, 0, tzinfo=timezone.utc)
    return Provenance(
        source_ref=SourceReference(url),
        content_hash=ContentHash(digest),
        retrieved_at=stamp,
        available_at=stamp,
        accepted_at=stamp,
    )


def _fact(*, instrument: str, fy: str, fq: str, end: date, amount: str, source: EarningsQualitySource, digest: str = "a") -> EarningsFactEvidence:
    if source is EarningsQualitySource.SEC:
        url = f"https://www.sec.gov/Archives/edgar/data/1/{instrument.lower()}-{end}.htm"
    elif instrument == "AMD":
        url = f"https://ir.amd.com/example/{end}"
    else:
        url = f"https://nvidianews.nvidia.com/news/example-{end}"
    observation = ObservedEarningsMetric(
        instrument_id=instrument,
        fiscal_year_label=fy,
        fiscal_quarter=fq,
        period_end=end,
        metric_type=BasicEarningsMetricType.REVENUE,
        value=Decimal(amount),
        currency="USD",
        accounting_basis=AccountingBasis.GAAP,
        assertion_kind=FactAssertionKind.OBSERVATION,
        provenance=_prov(url, digest * 64),
    )
    fact = next(record for record in extract_basic_earnings_records((observation,)) if isinstance(record, Fact))
    return EarningsFactEvidence(source, fact)


def _unresolved_segment(instrument: str, end: date) -> SegmentRevenueResolution:
    accession = "0000000000-26-000001"
    attempts = (
        SegmentRevenueAttempt(SegmentRevenueMethod.COMPANY_FACTS, SegmentRevenueStatus.FAILED, SegmentRevenueFailureReason.ENTITY_WIDE_ONLY, accession, "sec:companyfacts"),
        SegmentRevenueAttempt(SegmentRevenueMethod.XBRL_DIMENSION, SegmentRevenueStatus.FAILED, SegmentRevenueFailureReason.CONTEXT_MEMBER_UNRESOLVED, accession, "sec:xbrl-instance"),
        SegmentRevenueAttempt(SegmentRevenueMethod.FILING_TABLE, SegmentRevenueStatus.FAILED, SegmentRevenueFailureReason.TABLE_LAYOUT_UNRESOLVED, accession, "sec:filing-table"),
    )
    return SegmentRevenueResolution(attempts, None)


def _filing_segment(instrument: str, end: date) -> SegmentRevenueResolution:
    accession = "0000000000-26-000002"
    observation = SegmentRevenueObservation(
        instrument_id=instrument,
        raw_label="Data Center" if instrument == "AMD" else "Compute & Networking",
        classification_role="reportable_segment",
        period_start=date(end.year, max(1, end.month - 2), 1),
        period_end=end,
        value=Decimal("100"),
        currency="USD",
        display_scale=6,
        provenance=_prov("https://www.sec.gov/Archives/edgar/data/1/segment.htm", "f" * 64),
        source_accession=accession,
        method=SegmentRevenueMethod.FILING_TABLE,
        table_role="Segment Information",
    )
    attempts = (
        SegmentRevenueAttempt(SegmentRevenueMethod.COMPANY_FACTS, SegmentRevenueStatus.FAILED, SegmentRevenueFailureReason.DIMENSION_FACT_NOT_IN_COMPANYFACTS_SCOPE, accession, "sec:companyfacts"),
        SegmentRevenueAttempt(SegmentRevenueMethod.XBRL_DIMENSION, SegmentRevenueStatus.FAILED, SegmentRevenueFailureReason.CONTEXT_MEMBER_UNRESOLVED, accession, "sec:xbrl-instance"),
        SegmentRevenueAttempt(SegmentRevenueMethod.FILING_TABLE, SegmentRevenueStatus.SUCCESS, None, accession, observation.provenance.source_ref.value, raw_label=observation.raw_label, table_role=observation.table_role),
    )
    return SegmentRevenueResolution(attempts, observation)


def test_report_reconciles_multiple_amd_nvda_periods_without_choosing_conflict() -> None:
    facts = (
        _fact(instrument="AMD", fy="FY2026", fq="Q1", end=date(2026, 3, 28), amount="7438", source=EarningsQualitySource.SEC, digest="a"),
        _fact(instrument="AMD", fy="FY2026", fq="Q1", end=date(2026, 3, 28), amount="7438", source=EarningsQualitySource.ISSUER_IR, digest="b"),
        _fact(instrument="AMD", fy="FY2026", fq="Q2", end=date(2026, 6, 27), amount="11536", source=EarningsQualitySource.SEC, digest="c"),
        _fact(instrument="AMD", fy="FY2026", fq="Q2", end=date(2026, 6, 27), amount="11535", source=EarningsQualitySource.ISSUER_IR, digest="d"),
        _fact(instrument="NVDA", fy="FY2027", fq="Q1", end=date(2026, 4, 26), amount="44062", source=EarningsQualitySource.SEC, digest="e"),
        _fact(instrument="NVDA", fy="FY2027", fq="Q2", end=date(2026, 7, 26), amount="96221", source=EarningsQualitySource.ISSUER_IR, digest="f"),
    )
    report = build_earnings_canary_quality_report(earnings_facts=facts, segment_checks=())

    assert report.metric_checks == 4
    assert report.metric_agreements == 1
    assert report.metric_conflicts == 1
    assert report.metric_single_source == 2
    conflict = next(row for row in report.metric_rows if row.status.value == "conflict")
    assert dict(conflict.values_by_source) == {"issuer_ir": "11535", "sec": "11536"}


def test_segment_quality_reports_success_method_and_complete_failure_path() -> None:
    checks = (
        SegmentQualityCheck("AMD", "FY2026", "Q2", date(2026, 6, 27), "amd.data-center", "Data Center", _filing_segment("AMD", date(2026, 6, 27))),
        SegmentQualityCheck("NVDA", "FY2027", "Q2", date(2026, 7, 26), "nvda.graphics", "Graphics", _unresolved_segment("NVDA", date(2026, 7, 26))),
    )
    report = build_earnings_canary_quality_report(earnings_facts=(), segment_checks=checks)

    assert report.segment_checks == 2
    assert report.segment_extracted == 1
    assert report.segment_unresolved == 1
    assert report.segment_rows[0].successful_method == "filing_table"
    assert report.segment_rows[1].failure_path == (
        "company_facts:entity_wide_only",
        "xbrl_dimension:context_member_unresolved",
        "filing_table:table_layout_unresolved",
    )


def test_markdown_is_deterministic_and_surfaces_conflicts() -> None:
    facts = (
        _fact(instrument="AMD", fy="FY2026", fq="Q2", end=date(2026, 6, 27), amount="2", source=EarningsQualitySource.SEC, digest="a"),
        _fact(instrument="AMD", fy="FY2026", fq="Q2", end=date(2026, 6, 27), amount="1", source=EarningsQualitySource.ISSUER_IR, digest="b"),
    )
    report = build_earnings_canary_quality_report(earnings_facts=facts, segment_checks=())
    rendered = render_earnings_canary_quality_markdown(report)

    assert rendered == render_earnings_canary_quality_markdown(report)
    assert "Conflicts: 1" in rendered
    assert "issuer_ir=1; sec=2" in rendered
    assert "conflict" in rendered


def test_metric_agreement_rate_excludes_single_source_rows() -> None:
    facts = (
        _fact(instrument="AMD", fy="FY2026", fq="Q1", end=date(2026, 3, 28), amount="7", source=EarningsQualitySource.SEC, digest="a"),
        _fact(instrument="AMD", fy="FY2026", fq="Q1", end=date(2026, 3, 28), amount="7", source=EarningsQualitySource.ISSUER_IR, digest="b"),
        _fact(instrument="NVDA", fy="FY2027", fq="Q1", end=date(2026, 4, 26), amount="8", source=EarningsQualitySource.SEC, digest="c"),
    )
    report = build_earnings_canary_quality_report(earnings_facts=facts, segment_checks=())
    assert report.metric_agreement_rate == 1.0


def test_segment_extraction_rate_is_explicit() -> None:
    checks = (
        SegmentQualityCheck("AMD", "FY2026", "Q2", date(2026, 6, 27), "amd.data-center", "Data Center", _filing_segment("AMD", date(2026, 6, 27))),
        SegmentQualityCheck("NVDA", "FY2027", "Q2", date(2026, 7, 26), "nvda.graphics", "Graphics", _unresolved_segment("NVDA", date(2026, 7, 26))),
    )
    report = build_earnings_canary_quality_report(earnings_facts=(), segment_checks=checks)
    assert report.segment_extraction_rate == 0.5
