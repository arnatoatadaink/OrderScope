"""Provider-neutral contracts shared by external-information adapters."""

from .provider import (
    AdapterPage,
    AdapterRequest,
    ContractViolation,
    ErrorInfo,
    assert_page_contract,
    assert_secret_free,
    collect_pages,
)

__all__ = [
    "AdapterPage",
    "AdapterRequest",
    "ContractViolation",
    "ErrorInfo",
    "assert_page_contract",
    "assert_secret_free",
    "collect_pages",
]
