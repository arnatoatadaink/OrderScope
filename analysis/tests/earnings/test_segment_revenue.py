from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, Provenance, SourceReference
from orderscope_local.earnings import (
    SegmentRevenueFailureReason,
    SegmentRevenueMethod,
    SegmentRevenueObservation,
    SegmentRevenueStatus,
    resolve_segment_revenue,
)
from orderscope_local.sec import XbrlDimension, XbrlFact, XbrlPeriod


ACC = "0001045810-26-000199"
START = date(2026, 4, 27)
END = date(2026, 7, 26)


def _prov(ref: str, digest: str = "a" * 64) -> Provenance:
    ts = datetime(2026, 8, 20, 20, 0, tzinfo=timezone.utc)
    return Provenance(
        source_ref=SourceReference(ref),
        content_hash=ContentHash(digest),
        retrieved_at=ts,
        available_at=ts,
        accepted_at=ts,
    )


def _fact(*, dimensions=(), value="88299000000", ref="https://www.sec.gov/xbrl/nvda") -> XbrlFact:
    return XbrlFact(
        concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        value=Decimal(value),
        unit="USD",
        period=XbrlPeriod(START, END),
        dimensions=dimensions,
        filing_source_ref="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000199",
        source_accession=ACC,
        source_form="10-Q",
        filed_on=date(2026, 8, 20),
        source_ref=ref,
    )


def test_company_facts_success_stops_chain() -> None:
    fact = _fact(ref="https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json")
    result = resolve_segment_revenue(
        instrument_id="NVDA",
        raw_label="Compute & Networking",
        classification_role="reportable_segment",
        period_start=START,
        period_end=END,
        source_accession=ACC,
        company_facts=(fact,),
        company_facts_provenance=_prov(fact.source_ref),
    )
    assert [a.method for a in result.attempts] == [SegmentRevenueMethod.COMPANY_FACTS]
    assert result.attempts[0].status is SegmentRevenueStatus.SUCCESS
    assert result.observation.value == Decimal("88299000000")


def test_dimension_fallback_records_company_facts_failure() -> None:
    dims = (XbrlDimension("us-gaap:OperatingSegmentsAxis", "nvda:ComputeNetworkingMember"),)
    fact = _fact(dimensions=dims)
    result = resolve_segment_revenue(
        instrument_id="NVDA",
        raw_label="Compute & Networking",
        classification_role="reportable_segment",
        period_start=START,
        period_end=END,
        source_accession=ACC,
        dimension_facts=(fact,),
        dimension_provenance=_prov(fact.source_ref),
    )
    assert [a.method for a in result.attempts] == [
        SegmentRevenueMethod.COMPANY_FACTS,
        SegmentRevenueMethod.XBRL_DIMENSION,
    ]
    assert result.attempts[0].failure_reason is SegmentRevenueFailureReason.DIMENSION_FACT_NOT_IN_COMPANYFACTS_SCOPE
    assert result.attempts[1].status is SegmentRevenueStatus.SUCCESS
    assert result.observation.axis_member == (("us-gaap:OperatingSegmentsAxis", "nvda:ComputeNetworkingMember"),)


def test_filing_table_is_third_fallback_and_preserves_role() -> None:
    filing = SegmentRevenueObservation(
        instrument_id="AMD",
        raw_label="Data Center",
        classification_role="reportable_segment",
        period_start=date(2026, 3, 29),
        period_end=date(2026, 6, 27),
        value=Decimal("6718000000"),
        currency="USD",
        display_scale=1000000,
        provenance=_prov("https://www.sec.gov/Archives/edgar/data/2488/example"),
        source_accession="0000002488-26-000099",
        method=SegmentRevenueMethod.FILING_TABLE,
        table_role="Segment Reporting",
    )
    result = resolve_segment_revenue(
        instrument_id="AMD",
        raw_label="Data Center",
        classification_role="reportable_segment",
        period_start=filing.period_start,
        period_end=filing.period_end,
        source_accession=filing.source_accession,
        filing_observation=filing,
    )
    assert [a.method for a in result.attempts] == list(SegmentRevenueMethod)
    assert result.attempts[-1].table_role == "Segment Reporting"
    assert result.observation is filing


def test_all_failures_preserve_reason_without_inventing_zero() -> None:
    result = resolve_segment_revenue(
        instrument_id="AMD",
        raw_label="Client & Gaming",
        classification_role="reportable_segment",
        period_start=date(2026, 3, 29),
        period_end=date(2026, 6, 27),
        source_accession="0000002488-26-000099",
        company_facts_failure=SegmentRevenueFailureReason.ENTITY_WIDE_ONLY,
        dimension_failure=SegmentRevenueFailureReason.CONTEXT_MEMBER_UNRESOLVED,
        filing_failure=SegmentRevenueFailureReason.TABLE_LAYOUT_UNRESOLVED,
    )
    assert result.observation is None
    assert [a.failure_reason for a in result.attempts] == [
        SegmentRevenueFailureReason.ENTITY_WIDE_ONLY,
        SegmentRevenueFailureReason.CONTEXT_MEMBER_UNRESOLVED,
        SegmentRevenueFailureReason.TABLE_LAYOUT_UNRESOLVED,
    ]


def test_quarter_and_ytd_are_not_interchangeable() -> None:
    ytd = XbrlFact(
        concept="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        value=Decimal("162850000000"),
        unit="USD",
        period=XbrlPeriod(date(2026, 1, 26), END),
        dimensions=(XbrlDimension("us-gaap:OperatingSegmentsAxis", "nvda:ComputeNetworkingMember"),),
        filing_source_ref="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000199",
        source_accession=ACC,
        source_form="10-Q",
        filed_on=date(2026, 8, 20),
        source_ref="https://www.sec.gov/xbrl/nvda",
    )
    result = resolve_segment_revenue(
        instrument_id="NVDA",
        raw_label="Compute & Networking",
        classification_role="reportable_segment",
        period_start=START,
        period_end=END,
        source_accession=ACC,
        dimension_facts=(ytd,),
        dimension_provenance=_prov(ytd.source_ref),
    )
    assert result.observation is None
    assert result.attempts[1].failure_reason is SegmentRevenueFailureReason.CONTEXT_MEMBER_UNRESOLVED


def test_successful_xbrl_requires_real_matching_provenance() -> None:
    fact = _fact()
    with pytest.raises(ContractViolation, match="explicit provenance"):
        resolve_segment_revenue(
            instrument_id="NVDA",
            raw_label="Compute & Networking",
            classification_role="reportable_segment",
            period_start=START,
            period_end=END,
            source_accession=ACC,
            company_facts=(fact,),
        )

    with pytest.raises(ContractViolation, match="source_ref must match"):
        resolve_segment_revenue(
            instrument_id="NVDA",
            raw_label="Compute & Networking",
            classification_role="reportable_segment",
            period_start=START,
            period_end=END,
            source_accession=ACC,
            company_facts=(fact,),
            company_facts_provenance=_prov("https://example.com/wrong"),
        )


def test_ambiguous_matching_dimension_facts_are_rejected() -> None:
    dims = (XbrlDimension("us-gaap:OperatingSegmentsAxis", "nvda:ComputeNetworkingMember"),)
    one = _fact(dimensions=dims, value="1")
    two = _fact(dimensions=dims, value="2")
    with pytest.raises(ContractViolation, match="ambiguous"):
        resolve_segment_revenue(
            instrument_id="NVDA",
            raw_label="Compute & Networking",
            classification_role="reportable_segment",
            period_start=START,
            period_end=END,
            source_accession=ACC,
            dimension_facts=(one, two),
            dimension_provenance=_prov(one.source_ref),
        )
