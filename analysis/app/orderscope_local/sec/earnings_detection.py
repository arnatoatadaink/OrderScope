"""Deterministic SEC earnings-candidate detection for E0-002.

Periodic reports are candidates by form. Current reports are candidates only when
explicit Item 2.02 or earnings-result attachment evidence is supplied. Generic
8-K or Exhibit 99.x presence is not enough to infer earnings semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re

from orderscope_local.contracts import ContractViolation

from .filing_records import FilingRecord
from .form_filter import SecFormFamily, classify_filing_record


_EXHIBIT = re.compile(r"99(?:\.[0-9]+)?")
_EARNINGS_TERMS = (
    "earnings",
    "financial results",
    "results of operations",
    "quarterly results",
    "annual results",
)


class SecEarningsDetectionReason(StrEnum):
    PERIODIC_REPORT = "periodic_report"
    CURRENT_REPORT_ITEM_202 = "current_report_item_2_02"
    EARNINGS_ATTACHMENT = "earnings_attachment"


@dataclass(frozen=True, slots=True)
class SecFilingAttachmentHint:
    document_ref: str
    exhibit_type: str
    description: str

    def __post_init__(self) -> None:
        for field, value in (
            ("document_ref", self.document_ref),
            ("exhibit_type", self.exhibit_type),
            ("description", self.description),
        ):
            if not isinstance(value, str) or not value or value != value.strip():
                raise ContractViolation(f"SEC attachment {field} must be canonical text")
        if len(self.document_ref) > 2048 or len(self.description) > 512:
            raise ContractViolation("SEC attachment metadata exceeds bounded size")


@dataclass(frozen=True, slots=True)
class SecEarningsCandidate:
    filing: FilingRecord
    reasons: tuple[SecEarningsDetectionReason, ...]
    attachment_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.filing, FilingRecord):
            raise ContractViolation("earnings candidate requires a FilingRecord")
        if not isinstance(self.reasons, tuple) or not self.reasons:
            raise ContractViolation("earnings candidate requires detection reasons")
        if any(not isinstance(reason, SecEarningsDetectionReason) for reason in self.reasons):
            raise ContractViolation("earnings candidate has an invalid detection reason")
        if tuple(dict.fromkeys(self.reasons)) != self.reasons:
            raise ContractViolation("earnings candidate reasons must be unique and ordered")
        if any(not isinstance(ref, str) or not ref for ref in self.attachment_refs):
            raise ContractViolation("earnings candidate attachment refs are invalid")
        if tuple(dict.fromkeys(self.attachment_refs)) != self.attachment_refs:
            raise ContractViolation("earnings candidate attachment refs must be unique")


def detect_sec_earnings_candidate(
    filing: FilingRecord,
    *,
    item_numbers: tuple[str, ...] = (),
    attachments: tuple[SecFilingAttachmentHint, ...] = (),
) -> SecEarningsCandidate | None:
    """Return a bounded SEC earnings candidate without extracting result values.

    10-Q/10-K filings, including amendments, are candidates directly. 8-K filings
    require explicit Item 2.02 or an attachment whose exhibit type and description
    both establish earnings/result semantics. Unsupported forms are ignored.
    """

    if not isinstance(filing, FilingRecord):
        raise ContractViolation("SEC earnings detection requires a FilingRecord")
    if not isinstance(item_numbers, tuple) or any(
        not isinstance(item, str) or not item or item != item.strip() for item in item_numbers
    ):
        raise ContractViolation("SEC item numbers must be canonical text tuples")
    if not isinstance(attachments, tuple) or any(
        not isinstance(item, SecFilingAttachmentHint) for item in attachments
    ):
        raise ContractViolation("SEC attachments must be attachment-hint tuples")

    decision = classify_filing_record(filing)
    if not decision.accepted:
        return None

    if decision.family in (SecFormFamily.QUARTERLY_REPORT, SecFormFamily.ANNUAL_REPORT):
        return SecEarningsCandidate(filing, (SecEarningsDetectionReason.PERIODIC_REPORT,))

    if decision.family is not SecFormFamily.CURRENT_REPORT:
        return None

    reasons: list[SecEarningsDetectionReason] = []
    attachment_refs: list[str] = []

    if "2.02" in item_numbers:
        reasons.append(SecEarningsDetectionReason.CURRENT_REPORT_ITEM_202)

    for attachment in attachments:
        if not _is_under_filing_root(filing, attachment.document_ref):
            raise ContractViolation("SEC attachment reference is outside the filing root")
        if _is_earnings_attachment(attachment):
            if SecEarningsDetectionReason.EARNINGS_ATTACHMENT not in reasons:
                reasons.append(SecEarningsDetectionReason.EARNINGS_ATTACHMENT)
            attachment_refs.append(attachment.document_ref)

    if not reasons:
        return None
    return SecEarningsCandidate(filing, tuple(reasons), tuple(attachment_refs))


def _is_earnings_attachment(attachment: SecFilingAttachmentHint) -> bool:
    exhibit = attachment.exhibit_type.upper()
    if _EXHIBIT.fullmatch(exhibit) is None:
        return False
    description = attachment.description.casefold()
    return any(term in description for term in _EARNINGS_TERMS)


def _is_under_filing_root(filing: FilingRecord, ref: str) -> bool:
    return ref.startswith(f"{filing.source_ref}/")
