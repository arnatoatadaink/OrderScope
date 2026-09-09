"""News temporary-content retention controller for N1-005.

Successful bodies are deleted only after extraction succeeded. Exception bodies
remain eligible for bounded retention but must be deleted no later than their
TemporaryContent expiry (which I0-006 caps at 30 days). The controller receives
an injected storage deleter and returns only an immutable deletion audit record;
raw content never crosses this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from orderscope_local.contracts import (
    ContractViolation,
    RetentionClass,
    TemporaryContent,
    TemporaryContentState,
)


NEWS_RETENTION_CONTROLLER_VERSION = "news-retention-controller-v0.1"


class TemporaryContentDeleter(Protocol):
    """Delete one opaque temporary-content reference and return durable proof."""

    def delete(self, *, content_ref: str) -> str: ...


@dataclass(frozen=True, slots=True)
class RetentionDecision:
    delete_now: bool
    due_at: datetime
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.delete_now, bool):
            raise ContractViolation("retention decision delete_now must be bool")
        _utc(self.due_at, "retention due_at")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 512:
            raise ContractViolation("retention decision reason must be bounded non-blank text")


def retention_decision(*, content: TemporaryContent, now: datetime) -> RetentionDecision:
    """Return the deterministic deletion decision for one temporary body."""

    if not isinstance(content, TemporaryContent):
        raise ContractViolation("content must be TemporaryContent")
    _utc(now, "retention now")

    if content.state is TemporaryContentState.DELETED:
        return RetentionDecision(delete_now=False, due_at=content.deleted_at, reason="already_deleted")

    if content.retention_class is RetentionClass.TEMPORARY_SUCCESS:
        if content.state is not TemporaryContentState.EXTRACTION_SUCCEEDED:
            raise ContractViolation("successful body deletion requires extraction_succeeded state")
        due_at = content.extraction_completed_at
        return RetentionDecision(
            delete_now=now >= due_at,
            due_at=due_at,
            reason="success_delete_after_extraction",
        )

    if content.retention_class is RetentionClass.TEMPORARY_EXCEPTION:
        if content.state is not TemporaryContentState.EXCEPTION:
            raise ContractViolation("exception body retention requires exception state")
        return RetentionDecision(
            delete_now=now >= content.expires_at,
            due_at=content.expires_at,
            reason="exception_delete_by_expiry",
        )

    raise ContractViolation("unsupported temporary retention class")


def delete_due_content(
    *,
    content: TemporaryContent,
    deleter: TemporaryContentDeleter,
    now: datetime,
) -> TemporaryContent:
    """Delete due content and return a durable DELETED lifecycle record.

    This call is intentionally strict: if content is not due, it does not invoke
    storage and returns the original immutable lifecycle record unchanged.
    """

    decision = retention_decision(content=content, now=now)
    if content.state is TemporaryContentState.DELETED or not decision.delete_now:
        return content

    try:
        proof = deleter.delete(content_ref=content.content_ref)
    except Exception as exc:
        raise ContractViolation("temporary content deletion failed") from exc
    _proof(proof)

    return TemporaryContent(
        content_ref=content.content_ref,
        retention_class=content.retention_class,
        captured_at=content.captured_at,
        expires_at=content.expires_at,
        state=TemporaryContentState.DELETED,
        extraction_completed_at=content.extraction_completed_at,
        exception_reason=content.exception_reason,
        deleted_at=now,
        deletion_proof=proof,
    )


def assert_exception_retention_compliant(*, content: TemporaryContent, now: datetime) -> None:
    """Raise when an exception body still exists at or beyond mandatory expiry."""

    if not isinstance(content, TemporaryContent):
        raise ContractViolation("content must be TemporaryContent")
    _utc(now, "retention now")
    if content.retention_class is not RetentionClass.TEMPORARY_EXCEPTION:
        return
    if content.state is TemporaryContentState.DELETED:
        return
    if now >= content.expires_at:
        raise ContractViolation("exception body retained beyond mandatory expiry")


def _proof(value: object) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 1024:
        raise ContractViolation("deletion proof must be bounded non-blank canonical text")
    lowered = value.casefold()
    if any(marker in lowered for marker in ("api_key=", "access_token=", "client_secret=", "password=")):
        raise ContractViolation("deletion proof must not contain secret-like values")


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
