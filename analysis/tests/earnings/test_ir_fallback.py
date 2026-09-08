from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, SourceTimestamp
from orderscope_local.earnings import (
    EarningsSourcePriority,
    IrReleaseRecord,
    IrReleaseSource,
    reconcile_sec_ir_evidence,
)
from orderscope_local.sec import (
    FilingRecord,
    SecEarningsCandidate,
    SecEarningsDetectionReason,
)


AMD_PERIOD = date(2026, 6, 27)
NVDA_PERIOD = date(2026, 7, 26)


def filing(*, ticker="AMD", accession="0000002488-26-000121", period_end=AMD_PERIOD):
    cik = "0000002488" if ticker == "AMD" else "0001045810"
    return FilingRecord(
        accession=accession,
        content_hash="a" * 64,
        cik=cik,
        ticker=ticker,
        form="8-K",
        filed_at=date(2026, 8, 4),
        period_end=period_end,
        primary_document_ref=f"https://www.sec.gov/Archives/edgar/data/{int(accession[:10])}/{accession.replace('-', '')}/primary.htm",
        source_ref=f"https://www.sec.gov/Archives/edgar/data/{int(accession[:10])}/{accession.replace('-', '')}",
        retrieved_at=datetime(2026, 8, 4, 21, tzinfo=timezone.utc),
    )


def sec_candidate(**kwargs):
    return SecEarningsCandidate(
        filing(**kwargs),
        (SecEarningsDetectionReason.CURRENT_REPORT_ITEM_202,),
    )


def amd_release(*, discovery=None, digest="b" * 64):
    return IrReleaseRecord(
        instrument_id="AMD",
        source=IrReleaseSource.AMD_IR,
        discovery_url=discovery or "https://ir.amd.com/financial-information/financial-results",
        canonical_release_url="https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results",
        content_hash=ContentHash(digest),
        fiscal_year_label="FY2026",
        fiscal_quarter="Q2",
        period_end=AMD_PERIOD,
        published_at=SourceTimestamp.date_only(date(2026, 8, 4)),
    )


def nvda_release():
    return IrReleaseRecord(
        instrument_id="NVDA",
        source=IrReleaseSource.NVIDIA_IR,
        discovery_url="https://investor.nvidia.com/financial-info/quarterly-results/default.aspx",
        canonical_release_url="https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2027",
        content_hash=ContentHash("c" * 64),
        fiscal_year_label="FY2027",
        fiscal_quarter="Q2",
        period_end=NVDA_PERIOD,
        published_at=SourceTimestamp.date_only(date(2026, 8, 26)),
    )


def test_reconcile_retains_sec_and_ir_with_sec_discovery_priority() -> None:
    bundle = reconcile_sec_ir_evidence(
        sec_candidates=(sec_candidate(),),
        ir_releases=(amd_release(),),
    )

    assert bundle.instrument_id == "AMD"
    assert bundle.period_end == AMD_PERIOD
    assert len(bundle.sec_candidates) == 1
    assert len(bundle.ir_releases) == 1
    assert bundle.source_priority == (
        EarningsSourcePriority.SEC,
        EarningsSourcePriority.ISSUER_IR,
    )


def test_duplicate_ir_discovery_paths_collapse_without_discarding_release_evidence() -> None:
    from_financial_results = amd_release()
    from_press_archive = amd_release(
        discovery="https://ir.amd.com/news-events/press-releases"
    )

    bundle = reconcile_sec_ir_evidence(
        sec_candidates=(sec_candidate(),),
        ir_releases=(from_financial_results, from_press_archive),
    )

    assert len(bundle.ir_releases) == 1
    assert bundle.ir_releases[0].canonical_release_url == from_financial_results.canonical_release_url
    assert bundle.sec_candidates[0].filing.accession == "0000002488-26-000121"


def test_duplicate_sec_accession_collapses_but_conflicting_candidate_does_not() -> None:
    candidate = sec_candidate()
    bundle = reconcile_sec_ir_evidence(sec_candidates=(candidate, candidate))
    assert len(bundle.sec_candidates) == 1
    assert bundle.source_priority == (EarningsSourcePriority.SEC,)

    conflict = SecEarningsCandidate(
        candidate.filing,
        (SecEarningsDetectionReason.EARNINGS_ATTACHMENT,),
    )
    with pytest.raises(ContractViolation, match="conflicting"):
        reconcile_sec_ir_evidence(sec_candidates=(candidate, conflict))


def test_same_ir_url_changed_hash_is_not_silently_deduplicated() -> None:
    with pytest.raises(ContractViolation, match="changed content hash"):
        reconcile_sec_ir_evidence(
            ir_releases=(amd_release(), amd_release(digest="d" * 64))
        )


def test_ir_only_fallback_is_valid_and_keeps_issuer_fiscal_label() -> None:
    release = nvda_release()
    bundle = reconcile_sec_ir_evidence(ir_releases=(release,))

    assert bundle.instrument_id == "NVDA"
    assert bundle.period_end == NVDA_PERIOD
    assert bundle.source_priority == (EarningsSourcePriority.ISSUER_IR,)
    assert bundle.ir_releases[0].fiscal_year_label == "FY2027"
    assert bundle.ir_releases[0].period_end.year == 2026


def test_reconciliation_rejects_cross_event_or_missing_sec_period() -> None:
    with pytest.raises(ContractViolation, match="one earnings event"):
        reconcile_sec_ir_evidence(
            sec_candidates=(sec_candidate(),),
            ir_releases=(nvda_release(),),
        )

    no_period = sec_candidate(period_end=None)
    with pytest.raises(ContractViolation, match="established period_end"):
        reconcile_sec_ir_evidence(sec_candidates=(no_period,))


def test_ir_source_boundary_rejects_generated_or_cross_issuer_urls() -> None:
    with pytest.raises(ContractViolation, match="official issuer host"):
        IrReleaseRecord(
            instrument_id="AMD",
            source=IrReleaseSource.AMD_IR,
            discovery_url="https://example.com/results",
            canonical_release_url="https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results",
            content_hash=ContentHash("e" * 64),
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=AMD_PERIOD,
        )

    with pytest.raises(ContractViolation, match="configured canary"):
        IrReleaseRecord(
            instrument_id="NVDA",
            source=IrReleaseSource.AMD_IR,
            discovery_url="https://ir.amd.com/financial-information/financial-results",
            canonical_release_url="https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results",
            content_hash=ContentHash("f" * 64),
            fiscal_year_label="FY2026",
            fiscal_quarter="Q2",
            period_end=AMD_PERIOD,
        )
