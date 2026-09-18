from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.sec import (
    FilingRecord,
    SecEarningsDetectionReason,
    SecFilingAttachmentHint,
    detect_sec_earnings_candidate,
)


NOW = datetime(2026, 9, 8, 10, tzinfo=timezone.utc)


def filing(*, form: str = "10-Q", accession: str = "0000002488-26-000121", **overrides):
    root = f"https://www.sec.gov/Archives/edgar/data/{int(accession[:10])}/{accession.replace('-', '')}"
    values = dict(
        accession=accession,
        content_hash="a" * 64,
        cik="0000002488",
        ticker="AMD",
        form=form,
        filed_at=date(2026, 8, 4),
        period_end=date(2026, 6, 27),
        primary_document_ref=f"{root}/amd.htm",
        source_ref=root,
        retrieved_at=NOW,
    )
    values.update(overrides)
    return FilingRecord(**values)


def attachment(record: FilingRecord, *, exhibit_type: str = "99.1", description: str = "Earnings Release"):
    return SecFilingAttachmentHint(
        document_ref=f"{record.source_ref}/ex99-1.htm",
        exhibit_type=exhibit_type,
        description=description,
    )


def test_10q_and_10k_are_candidates_without_inventing_result_values() -> None:
    q = detect_sec_earnings_candidate(filing(form="10-Q"))
    k = detect_sec_earnings_candidate(filing(form="10-K"))

    assert q is not None and k is not None
    assert q.reasons == (SecEarningsDetectionReason.PERIODIC_REPORT,)
    assert k.reasons == (SecEarningsDetectionReason.PERIODIC_REPORT,)
    assert not hasattr(q, "revenue")
    assert not hasattr(q, "actual_release_at")


def test_periodic_amendments_remain_distinct_candidates_by_accession() -> None:
    base = filing(form="10-Q", accession="0000002488-26-000120")
    amendment = filing(form="10-Q/A", accession="0000002488-26-000121")

    first = detect_sec_earnings_candidate(base)
    second = detect_sec_earnings_candidate(amendment)

    assert first is not None and second is not None
    assert first.filing.accession != second.filing.accession


def test_plain_8k_is_not_an_earnings_candidate() -> None:
    assert detect_sec_earnings_candidate(filing(form="8-K")) is None


def test_8k_item_202_is_an_explicit_candidate() -> None:
    candidate = detect_sec_earnings_candidate(
        filing(form="8-K"), item_numbers=("2.02", "9.01")
    )

    assert candidate is not None
    assert candidate.reasons == (SecEarningsDetectionReason.CURRENT_REPORT_ITEM_202,)
    assert candidate.attachment_refs == ()


def test_8k_earnings_attachment_is_candidate_and_preserves_ref() -> None:
    record = filing(form="8-K")
    hint = attachment(record, description="Quarterly Financial Results")

    candidate = detect_sec_earnings_candidate(record, attachments=(hint,))

    assert candidate is not None
    assert candidate.reasons == (SecEarningsDetectionReason.EARNINGS_ATTACHMENT,)
    assert candidate.attachment_refs == (hint.document_ref,)


def test_generic_99_1_does_not_imply_earnings() -> None:
    record = filing(form="8-K")
    generic = attachment(record, description="Investor Presentation")

    assert detect_sec_earnings_candidate(record, attachments=(generic,)) is None


def test_item_and_attachment_evidence_are_combined_without_duplication() -> None:
    record = filing(form="8-K")
    hint = attachment(record)

    candidate = detect_sec_earnings_candidate(
        record, item_numbers=("2.02",), attachments=(hint,)
    )

    assert candidate is not None
    assert candidate.reasons == (
        SecEarningsDetectionReason.CURRENT_REPORT_ITEM_202,
        SecEarningsDetectionReason.EARNINGS_ATTACHMENT,
    )


def test_non_earnings_forms_are_ignored() -> None:
    assert detect_sec_earnings_candidate(filing(form="S-3")) is None
    assert detect_sec_earnings_candidate(filing(form="4")) is None


def test_attachment_must_remain_under_filing_root() -> None:
    record = filing(form="8-K")
    hint = SecFilingAttachmentHint(
        document_ref="https://example.test/ex99-1.htm",
        exhibit_type="99.1",
        description="Earnings Release",
    )
    with pytest.raises(ContractViolation, match="outside the filing root"):
        detect_sec_earnings_candidate(record, attachments=(hint,))


def test_detection_inputs_are_bounded_contract_values() -> None:
    with pytest.raises(ContractViolation, match="item numbers"):
        detect_sec_earnings_candidate(filing(form="8-K"), item_numbers=(" 2.02",))
    with pytest.raises(ContractViolation, match="attachment-hint"):
        detect_sec_earnings_candidate(filing(form="8-K"), attachments=(object(),))
