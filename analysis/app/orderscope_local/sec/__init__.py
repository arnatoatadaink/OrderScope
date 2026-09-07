"""Provider-neutral SEC filing contracts."""

from .filing_records import (
    FilingRecord,
    FilingWrite,
    FilingWriteResult,
    SqliteFilingRecordRepository,
    filing_record_from_adapter,
)
from .filing_documents import (
    FilingDocumentAcquisition,
    SecDocumentTransport,
    SecFilingDocumentAcquirer,
    TemporaryContentStore,
)
from .form_filter import (
    SecFormDecision,
    SecFormFamily,
    SecFormRejectionReason,
    classify_filing_record,
    classify_sec_form,
)
from .submissions import (
    CANARY_COMPANIES,
    FixedIntervalSecRateLimiter,
    SEC_DATA_ORIGIN,
    SecCanaryCompany,
    SecRequestFailure,
    SecSubmissionsAdapter,
)
from .company_facts import (
    SecCompanyFactsAdapter,
    XbrlDimension,
    XbrlFact,
    XbrlFactPage,
    XbrlPeriod,
    normalize_xbrl_fact,
)

__all__ = [
    "FilingRecord",
    "FilingWrite",
    "FilingWriteResult",
    "SqliteFilingRecordRepository",
    "filing_record_from_adapter",
    "FilingDocumentAcquisition",
    "SecDocumentTransport",
    "SecFilingDocumentAcquirer",
    "TemporaryContentStore",
    "SecFormDecision",
    "SecFormFamily",
    "SecFormRejectionReason",
    "classify_filing_record",
    "classify_sec_form",
    "CANARY_COMPANIES",
    "FixedIntervalSecRateLimiter",
    "SEC_DATA_ORIGIN",
    "SecCanaryCompany",
    "SecRequestFailure",
    "SecSubmissionsAdapter",
    "SecCompanyFactsAdapter",
    "XbrlDimension",
    "XbrlFact",
    "XbrlFactPage",
    "XbrlPeriod",
    "normalize_xbrl_fact",
]
