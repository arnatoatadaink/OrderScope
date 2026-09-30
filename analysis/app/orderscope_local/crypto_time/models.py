"""Source-neutral 24/7 crypto time-window contracts for UWBS-071.

The module treats region-named windows as analysis buckets only.  It never
infers participant geography, trader identity, or causality from time of day.
Traditional-market boundaries are explicit context supplied by a caller or an
accepted calendar source; they are not guessed from a crypto timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ContractViolation(f"{field} must be non-blank and bounded")


class CryptoDayType(StrEnum):
    WEEKDAY = "weekday"
    WEEKEND = "weekend"


class TraditionalBoundaryType(StrEnum):
    NONE = "none"
    FRIDAY_TRADITIONAL_CLOSE = "friday_traditional_close"
    SUNDAY_TRADITIONAL_REOPEN = "sunday_traditional_reopen"
    MONDAY_CASH_OPEN = "monday_cash_open"
    HOLIDAY_OR_SHORTENED_SESSION = "holiday_or_shortened_session"
    PROVIDER_MAINTENANCE = "provider_maintenance"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class AnalysisWindow:
    """A UTC analysis bucket.

    Windows may overlap.  A label such as ``asia`` or ``us`` is descriptive
    only and must not be interpreted as participant nationality.
    """

    window_id: str
    start_utc: time
    end_utc: time

    def __post_init__(self) -> None:
        _identifier(self.window_id, "window_id")
        if self.start_utc.tzinfo is not None or self.end_utc.tzinfo is not None:
            raise ContractViolation("analysis-window clock times must be naive UTC wall-clock values")
        if self.start_utc == self.end_utc:
            raise ContractViolation("analysis window cannot span exactly 24 hours")


@dataclass(frozen=True, slots=True)
class TraditionalBoundaryContext:
    boundary_type: TraditionalBoundaryType
    boundary_at: datetime
    source_ref: str
    calendar_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.boundary_type, TraditionalBoundaryType):
            raise ContractViolation("boundary_type must be a TraditionalBoundaryType")
        if self.boundary_type is TraditionalBoundaryType.NONE:
            raise ContractViolation("explicit boundary context cannot use NONE")
        _utc(self.boundary_at, "boundary_at")
        _identifier(self.source_ref, "source_ref")
        if self.calendar_ref is not None:
            _identifier(self.calendar_ref, "calendar_ref")


@dataclass(frozen=True, slots=True)
class CryptoTimeContext:
    observed_at: datetime
    utc_date: str
    utc_hour: int
    day_type: CryptoDayType
    analysis_window_ids: tuple[str, ...]
    boundary_contexts: tuple[TraditionalBoundaryContext, ...] = ()

    def __post_init__(self) -> None:
        _utc(self.observed_at, "observed_at")
        if self.utc_date != self.observed_at.date().isoformat():
            raise ContractViolation("utc_date must match observed_at")
        if self.utc_hour != self.observed_at.hour:
            raise ContractViolation("utc_hour must match observed_at")
        expected_day_type = (
            CryptoDayType.WEEKEND if self.observed_at.weekday() >= 5 else CryptoDayType.WEEKDAY
        )
        if self.day_type is not expected_day_type:
            raise ContractViolation("day_type must match observed_at")
        if not isinstance(self.analysis_window_ids, tuple):
            raise ContractViolation("analysis_window_ids must be an immutable tuple")
        if len(self.analysis_window_ids) != len(set(self.analysis_window_ids)):
            raise ContractViolation("analysis_window_ids cannot contain duplicates")
        for window_id in self.analysis_window_ids:
            _identifier(window_id, "analysis_window_ids")
        if not isinstance(self.boundary_contexts, tuple):
            raise ContractViolation("boundary_contexts must be an immutable tuple")
        if any(not isinstance(item, TraditionalBoundaryContext) for item in self.boundary_contexts):
            raise ContractViolation("boundary_contexts must contain TraditionalBoundaryContext values")
