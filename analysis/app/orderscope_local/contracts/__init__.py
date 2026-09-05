"""Provider-neutral contracts shared by external-information adapters."""

from .errors import ContractViolation

from .checkpoint import (
    AcquisitionCheckpoint,
    BoundedWindow,
    CheckpointError,
    CheckpointScope,
    CheckpointState,
    OpaqueCursor,
)
from .provider import (
    AdapterPage,
    AdapterRequest,
    ErrorInfo,
    assert_page_contract,
    assert_secret_free,
    collect_pages,
)
from .provenance import (
    ContentHash,
    Provenance,
    ProviderRevision,
    SourceReference,
    SourceTimestamp,
    TimestampPrecision,
)

__all__ = [
    "AcquisitionCheckpoint",
    "AdapterPage",
    "AdapterRequest",
    "BoundedWindow",
    "CheckpointScope",
    "CheckpointError",
    "CheckpointState",
    "ContractViolation",
    "ErrorInfo",
    "OpaqueCursor",
    "assert_page_contract",
    "assert_secret_free",
    "collect_pages",
    "ContentHash",
    "Provenance",
    "ProviderRevision",
    "SourceReference",
    "SourceTimestamp",
    "TimestampPrecision",
]
