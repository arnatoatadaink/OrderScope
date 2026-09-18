"""Temporary News body acquisition boundary for N0-004.

Raw article content exists only between the provider transport and the injected
temporary store. Durable callers receive a TemporaryContent audit record plus a
content hash; the body itself never crosses this module boundary.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Protocol

from orderscope_local.contracts import (
    ContentHash,
    ContractViolation,
    RetentionClass,
    TemporaryContent,
    TemporaryContentState,
)

from .alpaca import ALPACA_NEWS_PROVIDER_KEY, AlpacaNewsRequestFailure


class NewsBodyTransport(Protocol):
    def get_article_content(self, *, article_id: str) -> str: ...


class TemporaryBodyStore(Protocol):
    def stage(self, *, provider_key: str, article_id: str, body: str, expires_at: datetime) -> str: ...


@dataclass(frozen=True, slots=True)
class NewsBodyAcquisition:
    article_id: str
    content_hash: ContentHash
    temporary_content: TemporaryContent

    def __post_init__(self) -> None:
        if not isinstance(self.article_id, str) or not self.article_id.strip() or len(self.article_id) > 512:
            raise ContractViolation("news body article_id must be bounded non-blank text")
        if not isinstance(self.content_hash, ContentHash):
            raise ContractViolation("news body content_hash must be ContentHash")
        if not isinstance(self.temporary_content, TemporaryContent):
            raise ContractViolation("news body temporary_content must be TemporaryContent")
        if self.temporary_content.state is not TemporaryContentState.STAGED:
            raise ContractViolation("newly acquired news body must be staged")


class AlpacaNewsBodyAccessor:
    """Acquire one provider body directly into expiring temporary storage."""

    def __init__(
        self,
        *,
        transport: NewsBodyTransport,
        store: TemporaryBodyStore,
        clock: Callable[[], datetime] | None = None,
        success_ttl: timedelta = timedelta(hours=6),
    ) -> None:
        if success_ttl <= timedelta(0) or success_ttl > timedelta(days=1):
            raise ContractViolation("news body success_ttl must be within (0, 1 day]")
        self._transport = transport
        self._store = store
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._success_ttl = success_ttl

    def acquire(self, *, article_id: str, body_capability: bool) -> NewsBodyAcquisition:
        if not isinstance(article_id, str) or not article_id.strip() or article_id != article_id.strip() or len(article_id) > 512:
            raise ContractViolation("news body article_id must be bounded non-blank text")
        if body_capability is not True:
            raise ContractViolation("news body acquisition is disabled when provider body capability is unavailable")

        captured_at = self._clock()
        _require_utc(captured_at, "captured_at")
        expires_at = captured_at + self._success_ttl

        try:
            body = self._transport.get_article_content(article_id=article_id)
        except AlpacaNewsRequestFailure:
            raise
        except Exception as exc:
            raise AlpacaNewsRequestFailure("body_transport_error", True) from exc

        if not isinstance(body, str) or not body.strip():
            raise AlpacaNewsRequestFailure("body_unavailable", False)
        body_bytes = body.encode("utf-8")
        if len(body_bytes) > 5 * 1024 * 1024:
            raise AlpacaNewsRequestFailure("body_too_large", False)

        digest = ContentHash(hashlib.sha256(body_bytes).hexdigest())
        try:
            content_ref = self._store.stage(
                provider_key=ALPACA_NEWS_PROVIDER_KEY,
                article_id=article_id,
                body=body,
                expires_at=expires_at,
            )
        except Exception as exc:
            raise AlpacaNewsRequestFailure("temporary_store_error", True) from exc

        record = TemporaryContent(
            content_ref=content_ref,
            retention_class=RetentionClass.TEMPORARY_SUCCESS,
            captured_at=captured_at,
            expires_at=expires_at,
            state=TemporaryContentState.STAGED,
        )
        return NewsBodyAcquisition(article_id=article_id, content_hash=digest, temporary_content=record)


def exception_record(
    *,
    content_ref: str,
    captured_at: datetime,
    reason: str,
    expires_at: datetime,
) -> TemporaryContent:
    """Create an exception lifecycle record; exceptions may never exceed 30 days."""

    return TemporaryContent(
        content_ref=content_ref,
        retention_class=RetentionClass.TEMPORARY_EXCEPTION,
        captured_at=captured_at,
        expires_at=expires_at,
        state=TemporaryContentState.EXCEPTION,
        exception_reason=reason,
    )


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
