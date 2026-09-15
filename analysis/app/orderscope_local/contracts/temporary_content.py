"""Immutable lifecycle contract for content held outside durable metadata.

The contract records only a bounded reference and deletion audit fields.  It
never carries provider response bodies, credentials, or the content itself.
Physical storage and the retention worker remain downstream concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import RetentionClass
from .provider import assert_secret_free


class TemporaryContentState(StrEnum):
    STAGED = "staged"
    EXTRACTION_SUCCEEDED = "extraction_succeeded"
    EXCEPTION = "exception"
    DELETED = "deleted"


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _bounded(value: str, field: str, maximum: int = 512) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ContractViolation(f"{field} must be non-blank and bounded")
    assert_secret_free({field: value})
    lowered = value.casefold()
    if any(marker in lowered for marker in ("api_key=", "access_token=", "client_secret=", "password=")):
        raise ContractViolation(f"secret-like value crossed boundary at {field}")


@dataclass(frozen=True, kw_only=True)
class TemporaryContent:
    """Storage-neutral audit record for one temporary content reference."""

    content_ref: str
    retention_class: RetentionClass
    captured_at: datetime
    expires_at: datetime
    state: TemporaryContentState = TemporaryContentState.STAGED
    extraction_completed_at: datetime | None = None
    exception_reason: str | None = None
    deleted_at: datetime | None = None
    deletion_proof: str | None = None

    def __post_init__(self) -> None:
        _bounded(self.content_ref, "content_ref")
        if not isinstance(self.retention_class, RetentionClass):
            raise ContractViolation("retention_class must be a RetentionClass")
        if self.retention_class is RetentionClass.DURABLE_METADATA:
            raise ContractViolation("temporary content requires a temporary retention class")
        if not isinstance(self.state, TemporaryContentState):
            raise ContractViolation("state must be a TemporaryContentState")
        _utc(self.captured_at, "captured_at")
        _utc(self.expires_at, "expires_at")
        if self.expires_at < self.captured_at:
            raise ContractViolation("expires_at cannot be earlier than captured_at")
        if self.retention_class is RetentionClass.TEMPORARY_EXCEPTION and self.expires_at > self.captured_at + timedelta(days=30):
            raise ContractViolation("temporary exception content must expire within 30 days")

        for value, field in (
            (self.extraction_completed_at, "extraction_completed_at"),
            (self.deleted_at, "deleted_at"),
        ):
            if value is not None:
                _utc(value, field)
        if self.extraction_completed_at is not None and self.extraction_completed_at < self.captured_at:
            raise ContractViolation("extraction_completed_at cannot be earlier than captured_at")
        if self.deleted_at is not None and self.deleted_at < self.captured_at:
            raise ContractViolation("deleted_at cannot be earlier than captured_at")

        if self.exception_reason is not None:
            _bounded(self.exception_reason, "exception_reason", 1024)
        if self.deletion_proof is not None:
            _bounded(self.deletion_proof, "deletion_proof", 1024)

        if self.state is TemporaryContentState.STAGED:
            if self.extraction_completed_at is not None or self.deleted_at is not None:
                raise ContractViolation("staged content cannot have completion or deletion audit fields")
            if self.exception_reason is not None or self.deletion_proof is not None:
                raise ContractViolation("staged content cannot have exception or deletion proof")
        elif self.state is TemporaryContentState.EXTRACTION_SUCCEEDED:
            if self.retention_class is not RetentionClass.TEMPORARY_SUCCESS:
                raise ContractViolation("successful extraction requires temporary_success retention")
            if self.extraction_completed_at is None:
                raise ContractViolation("successful extraction requires extraction_completed_at")
            if self.exception_reason is not None or self.deleted_at is not None or self.deletion_proof is not None:
                raise ContractViolation("successful extraction cannot retain exception or deletion fields")
        elif self.state is TemporaryContentState.EXCEPTION:
            if self.retention_class is not RetentionClass.TEMPORARY_EXCEPTION:
                raise ContractViolation("exception content requires temporary_exception retention")
            if self.exception_reason is None:
                raise ContractViolation("exception content requires exception_reason")
            if self.deleted_at is not None and self.deletion_proof is None:
                raise ContractViolation("deleted exception content requires deletion_proof")
            if self.extraction_completed_at is not None:
                raise ContractViolation("exception content cannot claim successful extraction")
        elif self.state is TemporaryContentState.DELETED:
            if self.deleted_at is None or self.deletion_proof is None:
                raise ContractViolation("deleted content requires deleted_at and deletion_proof")
            if self.exception_reason is not None and self.retention_class is not RetentionClass.TEMPORARY_EXCEPTION:
                raise ContractViolation("exception reason requires temporary_exception retention")

        if self.retention_class is RetentionClass.TEMPORARY_EXCEPTION:
            if self.exception_reason is None and self.state in {
                TemporaryContentState.EXCEPTION,
                TemporaryContentState.DELETED,
            }:
                raise ContractViolation("temporary exception content requires exception_reason")


def validate_temporary_content(record: TemporaryContent) -> None:
    """Validate a lifecycle record at contract boundaries."""

    if not isinstance(record, TemporaryContent):
        raise ContractViolation("record must be TemporaryContent")
