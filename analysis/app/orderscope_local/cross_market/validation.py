"""A0-002 CBRS multi-layer flow validation contract.

The validation boundary is source-neutral.  A series is identified by role and
measure so price, volume, yields, FX, consensus and short/borrow evidence can be
aligned without collapsing unlike observations into one scalar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Mapping

from orderscope_local.contracts import ContractViolation


class SeriesRole(StrEnum):
    CBRS = "CBRS"
    NVDA = "NVDA"
    US_MARKET = "US_MARKET"
    AI_SEMICONDUCTOR_PROXY = "AI_SEMICONDUCTOR_PROXY"
    UST_10Y = "UST_10Y"
    JGB_10Y = "JGB_10Y"
    USDJPY = "USDJPY"
    BTC = "BTC"


class SeriesMeasure(StrEnum):
    PRICE = "PRICE"
    VOLUME = "VOLUME"
    YIELD = "YIELD"
    FX_RATE = "FX_RATE"
    CONSENSUS_TARGET = "CONSENSUS_TARGET"
    SHORT_METRIC = "SHORT_METRIC"


class HypothesisRating(StrEnum):
    SUPPORT = "SUPPORT"
    PARTIAL = "PARTIAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


_REQUIRED_SERIES_KEYS = frozenset(
    {
        (SeriesRole.CBRS, SeriesMeasure.PRICE),
        (SeriesRole.CBRS, SeriesMeasure.VOLUME),
        (SeriesRole.NVDA, SeriesMeasure.PRICE),
        (SeriesRole.NVDA, SeriesMeasure.VOLUME),
        (SeriesRole.US_MARKET, SeriesMeasure.PRICE),
        (SeriesRole.US_MARKET, SeriesMeasure.VOLUME),
        (SeriesRole.AI_SEMICONDUCTOR_PROXY, SeriesMeasure.PRICE),
        (SeriesRole.AI_SEMICONDUCTOR_PROXY, SeriesMeasure.VOLUME),
        (SeriesRole.UST_10Y, SeriesMeasure.YIELD),
        (SeriesRole.JGB_10Y, SeriesMeasure.YIELD),
        (SeriesRole.USDJPY, SeriesMeasure.FX_RATE),
        (SeriesRole.BTC, SeriesMeasure.PRICE),
    }
)
_ALLOWED_OPTIONAL_KEYS = frozenset(
    {
        (SeriesRole.CBRS, SeriesMeasure.CONSENSUS_TARGET),
        (SeriesRole.CBRS, SeriesMeasure.SHORT_METRIC),
    }
)
_REQUIRED_HYPOTHESES = frozenset(
    {
        "H1_GLOBAL_MACRO_RELIEF",
        "H2_AI_THEME_FLOW",
        "H3_CBRS_SPECIFIC_REPRICING",
        "H4_SHORT_COVERING",
        "H5_JAPAN_TO_US_ROTATION",
    }
)


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _text(value: str, field: str, *, maximum: int = 512) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > maximum:
        raise ContractViolation(f"{field} must be bounded non-empty canonical text")


@dataclass(frozen=True, kw_only=True)
class A0ValidationWindows:
    baseline_start: datetime
    baseline_end: datetime
    primary_start: datetime
    primary_end: datetime

    def __post_init__(self) -> None:
        for value, field in (
            (self.baseline_start, "baseline_start"),
            (self.baseline_end, "baseline_end"),
            (self.primary_start, "primary_start"),
            (self.primary_end, "primary_end"),
        ):
            _utc(value, field)
        if self.baseline_start >= self.baseline_end:
            raise ContractViolation("baseline window must be non-empty and half-open")
        if self.primary_start >= self.primary_end:
            raise ContractViolation("primary window must be non-empty and half-open")
        if self.baseline_end > self.primary_start:
            raise ContractViolation("baseline window cannot overlap primary window")


@dataclass(frozen=True, kw_only=True)
class SeriesSpec:
    role: SeriesRole
    measure: SeriesMeasure
    series_id: str
    source_ref: str
    unit: str
    timezone: str

    def __post_init__(self) -> None:
        if not isinstance(self.role, SeriesRole):
            raise ContractViolation("role must be SeriesRole")
        if not isinstance(self.measure, SeriesMeasure):
            raise ContractViolation("measure must be SeriesMeasure")
        if (self.role, self.measure) not in _REQUIRED_SERIES_KEYS | _ALLOWED_OPTIONAL_KEYS:
            raise ContractViolation("role/measure combination is not supported by A0-002")
        for value, field in (
            (self.series_id, "series_id"),
            (self.source_ref, "source_ref"),
            (self.unit, "unit"),
            (self.timezone, "timezone"),
        ):
            _text(value, field)


@dataclass(frozen=True, kw_only=True)
class SeriesObservation:
    role: SeriesRole
    measure: SeriesMeasure
    analysis_date: date
    observed_at: datetime
    available_at: datetime
    value: float
    source_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.role, SeriesRole):
            raise ContractViolation("role must be SeriesRole")
        if not isinstance(self.measure, SeriesMeasure):
            raise ContractViolation("measure must be SeriesMeasure")
        if not isinstance(self.analysis_date, date) or isinstance(self.analysis_date, datetime):
            raise ContractViolation("analysis_date must be a calendar date")
        _utc(self.observed_at, "observed_at")
        _utc(self.available_at, "available_at")
        if self.available_at < self.observed_at:
            raise ContractViolation("available_at cannot precede observed_at")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not isfinite(float(self.value)):
            raise ContractViolation("value must be a finite numeric observation")
        _text(self.source_ref, "source_ref")


@dataclass(frozen=True, kw_only=True)
class HypothesisResult:
    hypothesis_id: str
    rating: HypothesisRating
    evidence_refs: tuple[str, ...]
    rationale: str

    def __post_init__(self) -> None:
        if self.hypothesis_id not in _REQUIRED_HYPOTHESES:
            raise ContractViolation("hypothesis_id must be one of the A0-002 validation hypotheses")
        if not isinstance(self.rating, HypothesisRating):
            raise ContractViolation("rating must be HypothesisRating")
        if not isinstance(self.evidence_refs, tuple):
            raise ContractViolation("evidence_refs must be an immutable tuple")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ContractViolation("evidence_refs cannot contain duplicates")
        for ref in self.evidence_refs:
            _text(ref, "evidence_ref")
        _text(self.rationale, "rationale", maximum=2048)
        if self.rating is HypothesisRating.UNKNOWN and self.evidence_refs:
            raise ContractViolation("UNKNOWN hypothesis result cannot claim positive evidence refs")
        if self.rating is not HypothesisRating.UNKNOWN and not self.evidence_refs:
            raise ContractViolation("rated hypothesis result requires evidence refs")


@dataclass(frozen=True, kw_only=True)
class A0ValidationCase:
    windows: A0ValidationWindows
    series: tuple[SeriesSpec, ...]
    hypotheses: tuple[HypothesisResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.windows, A0ValidationWindows):
            raise ContractViolation("windows must be A0ValidationWindows")
        if not isinstance(self.series, tuple):
            raise ContractViolation("series must be an immutable tuple")
        keys = [(item.role, item.measure) for item in self.series]
        if len(keys) != len(set(keys)):
            raise ContractViolation("series role/measure keys must be unique")
        missing = _REQUIRED_SERIES_KEYS - set(keys)
        if missing:
            names = sorted(f"{role.value}:{measure.value}" for role, measure in missing)
            raise ContractViolation(f"A0-002 required series are incomplete; missing={names}")
        unsupported = set(keys) - (_REQUIRED_SERIES_KEYS | _ALLOWED_OPTIONAL_KEYS)
        if unsupported:
            raise ContractViolation("A0-002 contains unsupported series role/measure keys")
        if not isinstance(self.hypotheses, tuple):
            raise ContractViolation("hypotheses must be an immutable tuple")
        hypothesis_ids = [item.hypothesis_id for item in self.hypotheses]
        if len(hypothesis_ids) != len(set(hypothesis_ids)):
            raise ContractViolation("hypothesis results must be unique")
        if set(hypothesis_ids) != _REQUIRED_HYPOTHESES:
            raise ContractViolation("A0-002 requires H1 through H5 results")


def aligned_timeline(
    *,
    case: A0ValidationCase,
    observations: tuple[SeriesObservation, ...],
    as_of: datetime,
) -> Mapping[date, Mapping[SeriesRole, Mapping[SeriesMeasure, float]]]:
    """Return analysis-date aligned observations visible as of ``as_of``.

    Source-specific observed/available timestamps remain on every observation.
    Missing measures/days are not forward-filled or interpolated.
    """
    _utc(as_of, "as_of")
    if not isinstance(observations, tuple):
        raise ContractViolation("observations must be an immutable tuple")
    source_by_key = {(spec.role, spec.measure): spec.source_ref for spec in case.series}
    rows: dict[date, dict[SeriesRole, dict[SeriesMeasure, float]]] = {}
    seen: set[tuple[SeriesRole, SeriesMeasure, date]] = set()
    for item in observations:
        if not isinstance(item, SeriesObservation):
            raise ContractViolation("observations must contain SeriesObservation values")
        key = (item.role, item.measure)
        if key not in source_by_key:
            raise ContractViolation("observation role/measure is not registered in validation case")
        if item.source_ref != source_by_key[key]:
            raise ContractViolation("observation source_ref does not match registered SeriesSpec")
        if item.available_at > as_of:
            continue
        day_key = (item.role, item.measure, item.analysis_date)
        if day_key in seen:
            raise ContractViolation("duplicate role/measure/analysis_date observation is not allowed")
        seen.add(day_key)
        rows.setdefault(item.analysis_date, {}).setdefault(item.role, {})[item.measure] = float(item.value)
    result: dict[date, dict[SeriesRole, dict[SeriesMeasure, float]]] = {}
    for day, roles in sorted(rows.items()):
        result[day] = {
            role: dict(sorted(measures.items(), key=lambda pair: pair[0].value))
            for role, measures in sorted(roles.items(), key=lambda pair: pair[0].value)
        }
    return result
