"""UWBS-020 fixed catalyst-to-market reaction observation windows.

This module records deterministic reaction measurements for reviewed catalyst
windows.  It does not classify price rediscovery, catalyst strength, or causality.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from .errors import ContractViolation
from .fact_store import DerivedMetric


class CatalystReactionWindow(StrEnum):
    REACTION_5M = "reaction_5m"
    REACTION_30M = "reaction_30m"
    REACTION_1H = "reaction_1h"
    REACTION_SESSION_CLOSE = "reaction_session_close"
    REACTION_AFTER_HOURS = "reaction_after_hours"
    REACTION_NEXT_PREMARKET = "reaction_next_premarket"
    REACTION_NEXT_OPEN = "reaction_next_open"
    REACTION_NEXT_CLOSE = "reaction_next_close"
    REACTION_3D = "reaction_3d"
    REACTION_5D = "reaction_5d"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple) or not values:
        raise ContractViolation(f"{field} must be a non-empty immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class CatalystReactionObservation:
    subject_ref: str
    catalyst_ref: str
    window: CatalystReactionWindow
    window_start: datetime
    window_end: datetime
    return_percent: float
    source_record_ids: tuple[str, ...]
    calculated_at: datetime
    volume_ratio: float | None = None
    realized_volatility_ratio: float | None = None
    method_version: str = "catalyst-reaction-window-v0.1"

    def __post_init__(self) -> None:
        for value, field in (
            (self.subject_ref, "subject_ref"),
            (self.catalyst_ref, "catalyst_ref"),
            (self.method_version, "method_version"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
                raise ContractViolation(f"{field} must be bounded canonical text")
        if not isinstance(self.window, CatalystReactionWindow):
            raise ContractViolation("window must be CatalystReactionWindow")
        _utc(self.window_start, "window_start")
        _utc(self.window_end, "window_end")
        _utc(self.calculated_at, "calculated_at")
        if self.window_start >= self.window_end:
            raise ContractViolation("reaction window must be non-empty and half-open")
        if self.calculated_at < self.window_end:
            raise ContractViolation("calculated_at cannot precede window_end")
        _refs(self.source_record_ids, "source_record_ids")
        for value, field in (
            (self.return_percent, "return_percent"),
            (self.volume_ratio, "volume_ratio"),
            (self.realized_volatility_ratio, "realized_volatility_ratio"),
        ):
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
                    raise ContractViolation(f"{field} must be finite numeric data")
        if self.volume_ratio is not None and self.volume_ratio < 0:
            raise ContractViolation("volume_ratio cannot be negative")
        if self.realized_volatility_ratio is not None and self.realized_volatility_ratio < 0:
            raise ContractViolation("realized_volatility_ratio cannot be negative")

    def to_derived_metric(self, *, record_id: str, accepted_at: datetime) -> DerivedMetric:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.calculated_at:
            raise ContractViolation("accepted_at cannot precede calculated_at")
        return DerivedMetric(
            record_id=record_id,
            schema_version="catalyst-reaction-window-derived-metric-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.calculated_at,
            metric_name="catalyst_reaction_window",
            value={
                "catalyst_ref": self.catalyst_ref,
                "window": self.window.value,
                "window_start": self.window_start.isoformat(),
                "window_end": self.window_end.isoformat(),
                "return_percent": float(self.return_percent),
                "volume_ratio": float(self.volume_ratio) if self.volume_ratio is not None else None,
                "realized_volatility_ratio": float(self.realized_volatility_ratio) if self.realized_volatility_ratio is not None else None,
            },
            calculation_method="catalyst_reaction_window",
            method_version=self.method_version,
            as_of=self.calculated_at,
            input_record_ids=self.source_record_ids,
        )
