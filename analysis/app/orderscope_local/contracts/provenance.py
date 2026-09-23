"""Provider-neutral provenance value objects.

This module records durable references and normalized metadata only.  Provider
response bodies, credentials, cursor state, and duplicate classification belong to
other boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
import re

from .errors import ContractViolation


_SHA256 = re.compile(r"[0-9a-f]{64}")


class TimestampPrecision(StrEnum):
    """Precision actually established by the source."""

    DATE_ONLY = "date_only"
    SECOND = "second"
    MICROSECOND = "microsecond"


@dataclass(frozen=True)
class SourceTimestamp:
    """A source time without inventing precision or a UTC instant.

    Exactly one of ``instant`` and ``calendar_date`` is present.  Instants are
    normalized contract values and therefore must be UTC.  ``source_timezone`` may
    retain the timezone label reported by the source; it is metadata and is never
    used to silently reinterpret the instant.
    """

    precision: TimestampPrecision
    instant: datetime | None = None
    calendar_date: date | None = None
    source_timezone: str | None = None

    def __post_init__(self) -> None:
        if (self.instant is None) == (self.calendar_date is None):
            raise ContractViolation("source timestamp must contain exactly one value")
        if self.source_timezone is not None and not self.source_timezone.strip():
            raise ContractViolation("source_timezone cannot be blank")
        if self.precision is TimestampPrecision.DATE_ONLY:
            if self.calendar_date is None:
                raise ContractViolation("date_only timestamp requires calendar_date")
            return
        if self.instant is None:
            raise ContractViolation("instant precision requires instant")
        _require_utc(self.instant, "source timestamp instant")
        if self.precision is TimestampPrecision.SECOND and self.instant.microsecond:
            raise ContractViolation("second precision cannot contain microseconds")

    @classmethod
    def date_only(cls, value: date, *, source_timezone: str | None = None) -> SourceTimestamp:
        if isinstance(value, datetime):
            raise ContractViolation("date_only requires a date, not a datetime")
        return cls(TimestampPrecision.DATE_ONLY, calendar_date=value, source_timezone=source_timezone)

    @classmethod
    def at(cls, value: datetime, *, source_timezone: str | None = None) -> SourceTimestamp:
        precision = TimestampPrecision.MICROSECOND if value.microsecond else TimestampPrecision.SECOND
        return cls(precision, instant=value, source_timezone=source_timezone)


@dataclass(frozen=True)
class SourceReference:
    """Permanent canonical URL, accession, document ID, or equivalent reference."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ContractViolation("source_ref cannot be blank")
        if len(self.value) > 2048:
            raise ContractViolation("source_ref exceeds 2048 characters")


@dataclass(frozen=True)
class ContentHash:
    """Digest of normalized source content; never the content itself."""

    digest: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.algorithm != "sha256":
            raise ContractViolation("only sha256 content hashes are supported")
        if not _SHA256.fullmatch(self.digest):
            raise ContractViolation("sha256 digest must be 64 lowercase hexadecimal characters")


@dataclass(frozen=True)
class ProviderRevision:
    """Opaque provider/source revision, when that source exposes one."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ContractViolation("provider_revision cannot be blank")
        if len(self.value) > 512:
            raise ContractViolation("provider_revision exceeds 512 characters")


@dataclass(frozen=True)
class Provenance:
    """Shared acquisition provenance for externally grounded records.

    Event, publication, filing, and source acceptance times are independent and
    nullable.  Acquisition, availability, and internal acceptance are required UTC
    instants.  No missing source time is inferred from an operational timestamp.
    """

    source_ref: SourceReference
    content_hash: ContentHash
    retrieved_at: datetime
    available_at: datetime
    accepted_at: datetime
    provider_revision: ProviderRevision | None = None
    event_time: SourceTimestamp | None = None
    published_at: SourceTimestamp | None = None
    filed_at: SourceTimestamp | None = None
    source_accepted_at: SourceTimestamp | None = None

    def __post_init__(self) -> None:
        _require_utc(self.retrieved_at, "retrieved_at")
        _require_utc(self.available_at, "available_at")
        _require_utc(self.accepted_at, "accepted_at")
        if self.available_at > self.retrieved_at:
            raise ContractViolation("available_at cannot be later than retrieved_at")
        if self.retrieved_at > self.accepted_at:
            raise ContractViolation("retrieved_at cannot be later than accepted_at")


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ContractViolation(f"{field} must include an explicit timezone")
    if value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
