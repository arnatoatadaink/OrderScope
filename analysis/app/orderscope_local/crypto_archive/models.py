"""Durable archive/catch-up contracts for normalized crypto derivatives snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class CryptoArchiveError(ValueError):
    """Raised when an archive or catch-up record violates UWBS-074 semantics."""


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise CryptoArchiveError(f"{field} must be UTC")


def _text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise CryptoArchiveError(f"{field} must be non-blank and bounded")


class ArchiveDisposition(StrEnum):
    INSERTED = "inserted"
    DUPLICATE_IDENTICAL = "duplicate_identical"
    REVISION_REPLACED = "revision_replaced"


class CatchUpState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    UNRECOVERABLE = "unrecoverable"


@dataclass(frozen=True, kw_only=True)
class SnapshotEnvelope:
    snapshot_key: str
    venue: str
    instrument_id: str
    observed_at: datetime
    accepted_at: datetime
    source_revision: str | None
    payload_sha256: str
    payload_json: str

    def __post_init__(self) -> None:
        for value, field in ((self.snapshot_key, "snapshot_key"), (self.venue, "venue"), (self.instrument_id, "instrument_id"), (self.payload_sha256, "payload_sha256"), (self.payload_json, "payload_json")):
            _text(value, field)
        _utc(self.observed_at, "observed_at")
        _utc(self.accepted_at, "accepted_at")
        if self.observed_at > self.accepted_at:
            raise CryptoArchiveError("observed_at cannot be later than accepted_at")
        if len(self.payload_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.payload_sha256):
            raise CryptoArchiveError("payload_sha256 must be lowercase hex sha256")
        if self.source_revision is not None:
            _text(self.source_revision, "source_revision")


@dataclass(frozen=True, kw_only=True)
class CatchUpWindow:
    catchup_id: str
    venue: str
    instrument_id: str
    start_at: datetime
    end_at: datetime
    detected_at: datetime
    state: CatchUpState = CatchUpState.PENDING
    reason: str = "missing_snapshot_window"

    def __post_init__(self) -> None:
        for value, field in ((self.catchup_id, "catchup_id"), (self.venue, "venue"), (self.instrument_id, "instrument_id"), (self.reason, "reason")):
            _text(value, field)
        for value, field in ((self.start_at, "start_at"), (self.end_at, "end_at"), (self.detected_at, "detected_at")):
            _utc(value, field)
        if self.start_at >= self.end_at:
            raise CryptoArchiveError("start_at must be earlier than end_at")
        if self.end_at > self.detected_at:
            raise CryptoArchiveError("catch-up window cannot extend beyond detection time")
        if not isinstance(self.state, CatchUpState):
            raise CryptoArchiveError("state must be CatchUpState")
